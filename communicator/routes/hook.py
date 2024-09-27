import json
import typing

from fastapi import APIRouter, HTTPException
from starlette.responses import HTMLResponse, RedirectResponse
from starlette.templating import Jinja2Templates
from starlette.requests import Request

from communicator.utils.webhook_queues import (
    QueueRegistryStats,
    convert_queue_data_to_json_dict,
    convert_queues_dict_to_dataframe,
    delete_jobs_for_queue,
    get_job_registry_amount,
)


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
                    "rq_dashboard_version": "rq_dashboard_version",
                    "protocol": protocol,
                    'current_user': session_user
                },
            )
        except Exception as e:
            # logger.exception("An error occurred reading queues data template:", e)
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
            # logger.exception("An error occurred reading queues data json:", e)
            raise HTTPException(
                status_code=500, detail="An error occurred reading queues data json"
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
