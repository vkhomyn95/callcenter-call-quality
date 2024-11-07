import json
import logging
import time
import typing
from functools import total_ordering

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from tornado import web

from communicator.utils.flower_broker import Broker
from communicator.utils.flower_tasks import iter_tasks, get_task_by_id
from communicator.utils.flower_template import humanize, format_time
from communicator.variables import variables

router = APIRouter()

templates = Jinja2Templates(directory=variables.base_dir + "/templates")

templates.env.filters['humanize'] = humanize
templates.env.filters['format_time'] = format_time

prefix = "/flowers"


@total_ordering
class Comparable:
    """
    Compare two objects, one or more of which may be None.  If one of the
    values is None, the other will be deemed greater.
    """

    def __init__(self, value):
        self.value = value

    def __eq__(self, other):
        return self.value == other.value

    def __lt__(self, other):
        try:
            return self.value < other.value
        except TypeError:
            return self.value is None


@router.get("/workers", response_class=HTMLResponse)
async def flower_workers(
        request: Request,
        refresh: bool = False,
        json: bool = False,
):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            events = request.app.state.flower_app.events.state

            # Refresh workers if requested
            if refresh:
                try:
                    await update_workers(request.app.state.flower_app)
                except Exception as e:
                    logging.error('Failed to update workers: %s', e)

            # Collect workers' data
            workers = {}
            for name, values in events.counter.items():
                if name not in events.workers:
                    continue
                worker = events.workers[name]
                info = dict(values)
                info.update(as_dict(worker))
                info.update(status=worker.alive)
                workers[name] = info

            # Purge offline workers based on `purge_offline_workers` option
            if variables.purge_offline_workers is not None:
                timestamp = int(time.time())
                offline_workers = []
                for name, info in workers.items():
                    if info.get('status', True):
                        continue

                    heartbeats = info.get('heartbeats', [])
                    last_heartbeat = int(max(heartbeats)) if heartbeats else None
                    if not last_heartbeat or timestamp - last_heartbeat > variables.purge_offline_workers:
                        offline_workers.append(name)

                # Remove offline workers
                for name in offline_workers:
                    workers.pop(name)

            # Return JSON response if requested, otherwise render HTML
            if json:
                return JSONResponse(content={"data": list(workers.values())})
            else:
                # Render HTML template (Jinja2)
                return templates.TemplateResponse("flower/workers.html", {
                    "request": request,
                    "workers": workers,
                    "broker":  request.app.state.flower_app.capp.connection().as_uri(),
                    "current_user": session_user
                })
        except Exception as e:
            logging.error(f"=== An error occurred reading workers flower data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading workers flower data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/worker/{worker_id}", response_class=HTMLResponse)
async def flower_worker(
        request: Request,
        worker_id: str
):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            app = request.app.state.flower_app
            try:
                await update_workers(request.app.state.flower_app)
            except Exception as e:
                logging.error('Failed to update workers: %s', e)

            worker = app.workers.get(worker_id)

            if worker is None:
                raise web.HTTPError(404, f"Unknown worker '{worker_id}'")
            if 'stats' not in worker:
                raise web.HTTPError(404, f"Unable to get stats for '{worker_id}' worker")

            return templates.TemplateResponse("flower/worker.html", {
                "request": request,
                "worker": dict(worker, name=worker_id),
                "current_user": session_user
            })
        except Exception as e:
            logging.error(f"=== An error occurred reading flower worker data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading flower worker data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.post("/workers/cancel-consumer/{worker_name}/queue/{queue}", response_class=HTMLResponse)
async def flower_workers(
        request: Request,
        refresh: bool = False,
        worker_name: str = None,
        queue: str = None,
):
    """
    Handles the worker consumers.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            def is_worker(worker_name):
                return worker_name and worker_name in request.app.state.flower_app.workers

            if not is_worker(worker_name):
                raise web.HTTPError(404, f"Unknown worker '{worker_name}'")
            logging.info(" == Canceling consumer '%s' '%s' worker", queue, worker_name)
            response = request.app.state.flower_app.capp.control.broadcast(
                'cancel_consumer', arguments={'queue': queue},
                destination=[worker_name], reply=True)
            if response and 'ok' in response[0][worker_name]:
                return JSONResponse(dict(message=f"Canceling consumer for worker {worker_name}"))
            else:
                logging.error(" == Canceling consumer '%s' '%s' worker failed", queue, worker_name, response)
                return JSONResponse(dict(message=f"Failed to cancel '{queue}' consumer from '{worker_name}' worker"))
        except Exception as e:
            logging.error(f"=== An error occurred canceling consumers flower data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading canceling flower consumer template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/tasks", response_class=HTMLResponse)
async def flower_tasks(
        request: Request,
        page: int = Query(1, alias="page"),
        limit: int = Query(10, alias="limit"),
):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            app = request.app.state.flower_app
            offset = (page - 1) * limit
            # time = 'natural-time' if app.options.natural_time else 'time'
            # if app.capp.conf.timezone:
            #     time += '-' + str(app.capp.conf.timezone)

            return templates.TemplateResponse("flower/tasks.html", {
                "request": request,
                "tasks": [],
                "columns": "name,uuid,state,args,kwargs,result,received,started,runtime,worker",
                "time": "time",
                'page': page,
                'total_pages': 1,
                'start_page': max(1, page - 2),
                'end_page': min(1, page + 2),
                "current_user": session_user
            })

        except Exception as e:
            logging.error(f"=== An error occurred reading workers flower data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading workers flower data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/tasks/datatable")
async def flower_tasks_datatable(
        request: Request,
        draw: int = Query(1, alias="page"),
        start: int = Query(0, alias="start"),
        state: str = Query(0, alias="state"),
        length: int = Query(10, alias="length"),
        search: str = Query(None, alias="search"),
        column: int = Query(1, alias="column"),
        sort_by: str = Query(None, alias="sort_by"),
        sort_order: str = Query("desc", alias="sort_order"),
        page: int = Query(1, alias="page"),
        limit: int = Query(10, alias="limit"),
):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        offset = (page - 1) * limit

        # total_pages = 1 if users_count <= limit else (users_count + (limit - 1)) // limit

        app = request.app.state.flower_app

        def key(item):
            return Comparable(getattr(item[1], sort_by))

        def format_task(task):
            uuid, args = task
            return uuid, args

        sorted_tasks = sorted(
            iter_tasks(
                app.events,
                limit=limit,
                offset=offset,
                state=state if state != 'all' else None,
                search=dict(args=[search]) if search else dict(),
            )
        )

        filtered_tasks = []

        for task in sorted_tasks[start:start + length]:
            task_dict = as_dict(format_task(task)[1])
            if task_dict.get('worker'):
                task_dict['worker'] = task_dict['worker'].hostname
                task_dict.pop("root")

            filtered_tasks.append(task_dict)

        return {
            "draw": draw,
            "data": filtered_tasks,
            "recordsTotal": len(sorted_tasks),
            "recordsFiltered": len(sorted_tasks),
            'page': page,
            'total_pages': 100,
            'start_page': max(1, page - 2),
            'end_page': min(100, page + 2),
        }
        # except Exception as e:
        #     logging.error(f"=== An error occurred reading tasks data json: ", e)
        #     raise HTTPException(
        #         status_code=500, detail="An error occurred reading tasks data json"
        #     )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/task/{task_id}", response_class=HTMLResponse)
async def flower_task(
        request: Request,
        task_id: str
):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            app = request.app.state.flower_app

            task = get_task_by_id(app.events, task_id)

            if task is None:
                raise web.HTTPError(404, f"Unknown task '{task_id}'")

            return templates.TemplateResponse("flower/task.html", {
                "request": request,
                "task": task,
                "current_user": session_user
            })
        except Exception as e:
            logging.error(f"=== An error occurred reading flower task data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading flower task data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/broker", response_class=HTMLResponse)
async def flower_broker(request: Request):
    """
    Handles the user management page for administrators.

    Returns:
        HTMLResponse: The rendered HTML of the user management page if the user is an admin.
                      Redirects to the login page if no user is in session.
                      Redirects to the user's personal page if the user is not an admin.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            app = request.app.state.flower_app

            http_api = None
            if app.transport == 'amqp' and variables.celery_broker:
                http_api = variables.celery_broker_api

            try:
                broker = Broker(
                    app.capp.connection(connect_timeout=1.0).as_uri(include_password=True),
                    http_api=http_api,
                    broker_options=app.capp.conf.broker_transport_options,
                    broker_use_ssl=app.capp.conf.broker_use_ssl
                )
            except NotImplementedError as exc:
                raise web.HTTPError(
                    404, f"'{app.transport}' broker is not supported") from exc

            queues = []
            try:
                queues = await broker.queues(get_active_queue_names(app))
            except Exception as e:
                logging.error("Unable to get flower queues: '%s'", e)

            return templates.TemplateResponse("flower/broker.html", {
                "request": request,
                "broker_url": app.capp.connection().as_uri(),
                "queues": queues,
                "current_user": session_user
            })

        except Exception as e:
            logging.error(f"=== An error occurred reading queue flower data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading queues flower data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


async def get_user(request: Request) -> dict:
    """
    Retrieve the current session user.

    Args:
        request (Request): The current request object.

    Returns:
        dict: The session user if exists, else None.
    """
    return json.loads(request.session.get("user"))


async def is_admin(request: Request):
    """
    Check if the current session user is an admin.

    Args:
        request (Request): The current request object.

    Returns:
        bool: True if the user is an admin, else False.
    """
    user_data = await get_user(request)
    return user_data["role"]["name"] == 'admin'


def flash(request: Request, message: typing.Any, category: str = "primary") -> None:
    if "_messages" not in request.session:
        request.session["_messages"] = []
        request.session["_messages"].append({"message": message, "category": category})


def get_flashed_messages(request: Request):
    return request.session.pop("_messages") if "_messages" in request.session else []


def as_dict(worker):
    """
        Convert worker object to dictionary.
        """
    if hasattr(worker, '_fields'):
        return {k: getattr(worker, k) for k in worker._fields}
    else:
        return info(worker)


def info(worker):
    """
    Extract necessary fields from worker object.
    """
    _fields = ('hostname', 'pid', 'freq', 'heartbeats', 'clock',
               'active', 'processed', 'loadavg', 'sw_ident',
               'sw_ver', 'sw_sys')

    return {key: getattr(worker, key, None) for key in _fields}


async def update_workers(app, worker_name=None):
    return app.inspector.inspect(worker_name)


def get_active_queue_names(app):
    queues = set([])
    for _, info in app.workers.items():
        for queue in info.get('active_queues', []):
            queues.add(queue['name'])

    if not queues:
        queues = set([app.capp.conf.task_default_queue]) | {q.name for q in app.capp.conf.task_queues or [] if q.name}
    return sorted(queues)
