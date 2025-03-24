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
class TranscriptionResponse:
    unique_uuid: str
    task_id: str
    status: str
    talk_record_id: int


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


@router.post("/transcribe", response_model=TranscriptionResponse, name="transcribe")
async def transcribe(
        token: str = Depends(get_token),
        file: UploadFile = File(...),
        talk_record_id: str = Query(None, alias="talk_record_id"),
        origin: str = Query(None, alias="origin"),
        db: Session = Depends(get_db)
) -> TranscriptionResponse:
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

    received_date = datetime.now(timezone.utc).isoformat()[:-9]

    resampler = Resampler(unique_uuid).resample(info, audio, received_date)

    talk_record_id = int(talk_record_id) if talk_record_id else None

    task_name = "transcribe_scribe_v1" if user.recognition.model == "voiptime_premium" else "transcribe_openai_whisper"
    task_queue = "scribe_v1_queue" if user.recognition.model == "voiptime_premium" else "openai_whisper_queue"

    task = celery.send_task(
        task_name,
        args=[received_date, duration, info.num_channels, user.id, talk_record_id, resampler, unique_uuid, origin],
        queue=task_queue
    )

    decrement_user_tariff(db, user.tariff.id, round(duration))

    return TranscriptionResponse(unique_uuid, task.id, task.status, talk_record_id)


@router.post("/transcribe-url", response_model=TranscriptionResponse, name="transcribe-url")
async def transcribe_url(
        request: Request,
        token: str = Depends(get_token),
        user_id: str = Query(None, alias="user_id"),
        talk_record_id: str = Query(None, alias="talk_record_id"),
        origin: str = Query(None, alias="origin"),
        db: Session = Depends(get_db)
) -> TranscriptionResponse:
    unique_uuid = str(uuid.uuid4())

    payload = await request.json()

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

    talk_record_id = int(talk_record_id) if talk_record_id else None

    task = celery.send_task(
        "transcribe",
        args=[received_date, duration, info.num_channels, user_id, talk_record_id, resampler, unique_uuid, origin]
    )

    decrement_user_tariff(db, user.tariff.id, round(duration))

    return TranscriptionResponse(unique_uuid, task.id, task.status, talk_record_id)


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
