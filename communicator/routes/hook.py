import json
import typing
import logging
from datetime import timezone, timedelta

from fastapi import APIRouter, HTTPException, Query
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates

from communicator.utils.webhook_jobs import get_jobs, QueueJobRegistryStats, JobDataDetailed, get_job, delete_job_id, \
    requeue_job_id
from communicator.utils.webhook_queues import (
    QueueRegistryStats,
    get_job_registry_amount, delete_jobs_for_queue,
)
from communicator.utils.webhook_workers import get_workers, WorkerData
from communicator.variables import variables

router = APIRouter()

templates = Jinja2Templates(directory=variables.base_dir + "/templates")

prefix = "/webhooks"


@router.get("/queues", response_class=HTMLResponse)
async def hook_queues(request: Request):
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
            queue_data = get_job_registry_amount(variables.redis_url)

            protocol = request.url.scheme

            return templates.TemplateResponse(
                "webhook/queues.html",
                {
                    "request": request,
                    "queue_data": queue_data,
                    "active_tab": "active_tab",
                    "prefix": prefix,
                    "protocol": protocol,
                    'current_user': session_user
                },
            )
        except Exception as e:
            logging.error(f"=== An error occurred reading queues data template: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading queues data template {}".format(e),
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/queues/json", response_model=list[QueueRegistryStats])
async def read_queues(request: Request):
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
            queue_data = get_job_registry_amount(variables.redis_url)

            return queue_data
        except Exception as e:
            logging.error(f"=== An error occurred reading queues data json: ", e)
            raise HTTPException(
                status_code=500, detail="An error occurred reading queues data json"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.delete("/queues/{queue_name}")
async def delete_jobs_in_queue(request: Request, queue_name: str):
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        try:
            deleted_ids = delete_jobs_for_queue(queue_name, variables.redis_url)
            return deleted_ids
        except Exception as e:
            logging.error(f"=== An error occurred while deleting jobs in queue: ", e)
            raise HTTPException(
                status_code=500, detail="An error occurred while deleting jobs in queue"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/workers", response_class=HTMLResponse)
async def hook_workers(request: Request):
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
            worker_data = get_workers(variables.redis_url)

            active_tab = "workers"

            protocol = request.url.scheme

            return templates.TemplateResponse(
                "webhook/workers.html",
                {
                    "request": request,
                    "worker_data": worker_data,
                    "active_tab": active_tab,
                    "prefix": prefix,
                    "protocol": protocol,
                    'current_user': session_user
                },
            )
        except Exception as e:
            logging.error(f"=== An error occurred reading worker data template: ", e)
            raise HTTPException(
                status_code=500, detail="An error occurred while reading workers"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/workers/json", response_model=list[WorkerData])
async def read_workers(request: Request):
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
            worker_data = get_workers(variables.redis_url)

            return worker_data
        except Exception as e:
            logging.error(f"=== An error occurred reading queues data json: ", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred while reading worker data in json",
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/jobs", response_class=HTMLResponse)
async def hook_jobs(
        request: Request,
        queue_name: str = Query("all"),
        state: str = Query("all"),
        page: int = Query(1),
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
            job_data = get_jobs(variables.redis_url, queue_name, state, page=page)

            active_tab = "jobs"

            protocol = request.url.scheme

            return templates.TemplateResponse(
                "webhook/jobs.html",
                {
                    "request": request,
                    "job_data": job_data,
                    "active_tab": active_tab,
                    "prefix": prefix,
                    "protocol": protocol,
                    "current_user": session_user,
                },
            )
        except Exception as e:
            logging.error("An error occurred reading jobs data template:", e)
            raise HTTPException(
                status_code=500,
                detail="An error occurred reading jobs data template",
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/jobs/json", response_model=list[QueueJobRegistryStats])
async def read_jobs(
    request: Request,
    queue_name: str = Query("all"),
    state: str = Query("all"),
    page: int = Query(1),
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
            job_data = get_jobs(variables.redis_url, queue_name, state, page=page)

            return job_data
        except Exception as e:
            logging.error("An error occurred reading jobs data json:", e)
            raise HTTPException(
                status_code=500, detail="An error occurred reading jobs data json"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.get("/job/{job_id}", response_model=JobDataDetailed)
async def get_job_data(job_id: str, request: Request):
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
            job = get_job(variables.redis_url, job_id)
            css = None
            col_exc_info = None

            active_tab = "job"

            protocol = request.url.scheme

            return templates.TemplateResponse(
                "webhook/job.html",
                {
                    "request": request,
                    "job_data": job,
                    "active_tab": active_tab,
                    "css": css,
                    "col_exc_info": col_exc_info,
                    "prefix": prefix,
                    "protocol": protocol,
                    "current_user": session_user,
                },
            )
        except Exception as e:
            logging.error("An error occurred fetching a specific job:", e)
            raise HTTPException(
                status_code=500, detail="An error occurred fetching a specific job"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.delete("/job/{job_id}")
async def delete_job(job_id: str, request: Request):
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
            delete_job_id(variables.redis_url, job_id=job_id)
        except Exception as e:
            logging.error("An error occurred while deleting a job:", e)
            raise HTTPException(
                status_code=500, detail="An error occurred delete a specific job"
            )
    else:
        return RedirectResponse(url="/login/", status_code=303)


@router.post("/job/{job_id}/requeue")
async def requeue_job(job_id: str, request: Request):
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
            requeue_job_id(variables.redis_url, job_id=job_id)
        except Exception as e:
            logging.error("An error occurred while requeue a job:", e)
            raise HTTPException(
                status_code=500, detail="An error occurred requeue a specific job"
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
