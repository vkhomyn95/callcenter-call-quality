import typing
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import httpx
import torchaudio
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from starlette import status
from starlette.requests import Request
from torchaudio import AudioMetaData

from communicator.database.database import get_db
from communicator.utils.crud import load_user_by_api_key, decrement_user_tariff
from communicator.job.start import celery
from communicator.resampler.resampler import Resampler


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.success = False
        self.message = detail


@dataclass
class TranscriptionRequest:
    request_id: str
    task_id: str


router = APIRouter()
get_bearer_token = HTTPBearer(auto_error=False)


async def get_token(
    auth: typing.Optional[HTTPAuthorizationCredentials] = Depends(get_bearer_token),
    access_token: str = Query(None, alias="access_token"),
) -> str:
    if auth and (token := auth.credentials):
        return token

    if access_token:
        return access_token

    raise CustomHTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No token provided in header or as query parameter."
    )


@router.post("/transcribe", response_model=TranscriptionRequest, name="transcribe")
async def transcribe(
        token: str = Depends(get_token),
        file: UploadFile = File(...),
        talk_record_id: str = Query(None, alias="talk_record_id"),
        origin: str = Query(None, alias="origin"),
        db: Session = Depends(get_db)
) -> TranscriptionRequest:
    unique_uuid = str(uuid.uuid4())

    audio = await file.read()
    info: AudioMetaData = torchaudio.info(BytesIO(audio))
    duration = info.num_frames / info.sample_rate

    user = load_user_by_api_key(db, token)
    if user is None or user.tariff.total < duration:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Not valid access_token or tariff limit reached. Required {duration} seconds'
        )

    resampler = Resampler(unique_uuid).resample(info, audio)

    received_date = datetime.now(timezone.utc).isoformat()[:-9]

    task = celery.send_task(
        "transcribe",
        args=[received_date, duration, info.num_channels, user.id, talk_record_id, resampler, unique_uuid, origin]
    )

    decrement_user_tariff(db, user.tariff.id, round(duration))

    return TranscriptionRequest(unique_uuid, task.id)


@router.post("/transcribe-url", response_model=TranscriptionRequest, name="transcribe-url")
async def transcribe_url(
        request: Request,
        token: str = Depends(get_token),
        user_id: str = Query(None, alias="user_id"),
        talk_record_id: str = Query(None, alias="talk_record_id"),
        db: Session = Depends(get_db)
) -> TranscriptionRequest:
    unique_uuid = str(uuid.uuid4())

    payload = await request.json()
    print(payload)

    response = None
    async with httpx.AsyncClient() as client:
        response = await client.get(payload["file"][0])
        response.raise_for_status()
    info: AudioMetaData = torchaudio.info(BytesIO(response.content))
    duration = info.num_frames / info.sample_rate

    user = load_user_by_api_key(db, token)
    if user is None or user.tariff.total < duration:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Not valid access_token or tariff limit reached. Required {duration} seconds'
        )

    resampler = Resampler(unique_uuid).resample(info, response.content)

    received_date = datetime.now(timezone.utc).isoformat()[:-9]

    task = celery.send_task(
        "transcribe",
        args=[received_date, duration, info.num_channels, user_id, talk_record_id, resampler, unique_uuid]
    )
    print(task)

    decrement_user_tariff(db, user.tariff.id, round(duration))

    return TranscriptionRequest(unique_uuid, task.id)


@router.get("/transcribe/{task_id}", name="transcription")
def transcription(task_id: str):
    result = celery.AsyncResult(task_id)
    print(result)

    return {
        "status": result.state,
        "successful": result.successful(),
        "task_id": result.task_id,
        "done_at": result.date_done,
        "transcription": result.result if result.ready() else None,
    }
