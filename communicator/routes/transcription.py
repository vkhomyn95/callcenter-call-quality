import json
import os

from fastapi import APIRouter, Query, Depends
from sqlalchemy.orm import Session
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse, FileResponse
from starlette.templating import Jinja2Templates

from communicator.database import elastic
from communicator.database.database import get_db
from communicator.utils.crud import load_simple_users, load_user_by_id
from communicator.variables import variables

router = APIRouter()

templates = Jinja2Templates(directory=variables.base_dir + "/templates")


@router.get("/", response_class=HTMLResponse)
async def transcriptions(
        request: Request,
        page: int = Query(1, alias="page"),
        limit: int = Query(10, alias="limit"),
        task_id: str = Query(None, alias="task_id"),
        user_id: int = Query(None, alias="user_id"),
        db: Session = Depends(get_db)
):
    """
    Handle the display of recognitions.

    - Retrieves and paginates recognitions based on user role and query parameters.
    - Renders the 'recognitions.html' template with the recognition data.

    Query Parameters:
        - page (int): The page number for pagination (default is 1).
        - limit (int): The number of recognitions per page (default is 10).
        - campaign_id (str): Filter by campaign ID.
        - acd_id (str): Filter by acd ID.
        - task_id (str): Filter by request UUID.

    Returns:
        - A rendered template with the recognitions data.
        - A redirect to the 'login' page if the user is not authenticated.
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    offset = (page - 1) * limit

    if await is_admin(request):
        searched_recognitions = elastic.load_recognitions(user_id, task_id, limit, offset)
        recognitions_count = elastic.count_recognitions(user_id, task_id)
    else:
        searched_recognitions = elastic.load_recognitions(session_user["id"], task_id, limit, offset)
        recognitions_count = elastic.count_recognitions(session_user["id"], task_id)

    total_pages = 1 if recognitions_count <= limit else (recognitions_count + (limit - 1)) // limit

    # Render the template with the data
    return templates.TemplateResponse(
        'transcriptions.html',
        {
            'request': request,
            'recognitions': searched_recognitions,
            'total_pages': total_pages,
            'page': page,
            'start_page': max(1, page - 2),
            'end_page': min(total_pages, page + 2),
            'users': load_simple_users(db) if await is_admin(request) else [],
            'filter': {
                "user_id": user_id,
                "task_id": task_id,
            },
            'current_user': session_user
        }
    )


@router.get('/{transcription_id}', response_class=HTMLResponse)
async def transcription(request: Request, transcription_id: str, db: Session = Depends(get_db)):
    """
    Handle the display of a single recognition and its related recognitions.

    - Retrieves the recognition by ID.
    - For admins, retrieves related recognitions and calculates average confidence.
    - For regular users, retrieves only the recognitions related to the user.
    - Renders the 'recognition.html' template with the recognition and related data.

    Args:
        transcription_id (int): The ID of the recognition to be retrieved.

    Returns:
        - A rendered template with the recognition data.
        - A redirect to the 'login' page if the user is not authenticated.
        :param db:
        :param transcription_id:
        :param request:
    """
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    if await is_admin(request):
        searched_recognition = elastic.load_recognition_by_id(None, transcription_id)
    else:
        searched_recognition = elastic.load_recognition_by_id(session_user["id"], transcription_id)

    if not searched_recognition:
        return RedirectResponse(url="/404", status_code=404)

    merged_recognitions = []
    timestamps = set()
    user = load_user_by_id(db, searched_recognition["user_id"]) if searched_recognition is not None else None

    if searched_recognition["transcription"]:
        for recognition in searched_recognition["transcription"]:
            if recognition:
                for chunk in recognition["chunks"]:
                    merged_recognitions.append(chunk)
                    timestamps.add(chunk["timestamp"][0])
        merged_recognitions.sort(key=lambda x: x['timestamp'][0])
    searched_recognition["result"] = merged_recognitions
    searched_recognition["user"] = user

    return templates.TemplateResponse(
        'transcription.html',
        {
            'request': request,
            'recognition': searched_recognition,
            'current_user': session_user
        }
    )


@router.get('/{transcription_id}/audio/{channel}/date/{received_date}', response_class=HTMLResponse)
async def transcription_audio(request: Request, transcription_id: str, channel: int, received_date):
    session_user = await get_user(request)

    if not session_user:
        return RedirectResponse(url="/login/", status_code=303)

    filename = f"{transcription_id}_{channel}.wav"

    # Construct the full file path based on the audio directory and filename
    file_path = os.path.join(get_save_directory(received_date), filename)

    # Check if the file exists
    if os.path.exists(file_path):
        # Serve the file using FileResponse
        return FileResponse(file_path, media_type='audio/wav', filename=filename)
    else:
        # Handle file not found (you can return a 404 or any other appropriate response)
        return RedirectResponse(url="/404", status_code=404)


def get_save_directory(received_date):
    # Create directory path based on received date (year/month/day)
    year, month, day = received_date.split('T')[0].split("-")
    save_dir = os.path.join(variables.file_dir, year, month, day)

    # Create the directories if they do not exist
    os.makedirs(save_dir, exist_ok=True)
    return save_dir


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