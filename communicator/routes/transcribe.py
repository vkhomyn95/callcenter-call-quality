import typing
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from io import BytesIO

import torchaudio
from fastapi import APIRouter, UploadFile, File, Query, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from starlette import status
from torchaudio import AudioMetaData

from communicator.database.database import get_db
from communicator.job.start import celery
from communicator.resampler.resampler import Resampler
from communicator.utils.crud import load_user_by_api_key, decrement_user_tariff


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

    if user is None:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Not valid access_token'
        )

    tariff = None
    for plan in user.tariff:
        if plan.model.name == user.recognition.model and plan.active:
            tariff = plan

    if tariff is None:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Tariff license for {user.recognition.model} model does not exist or inactive.'
        )

    if tariff.total < duration:
        raise CustomHTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f'Current tariff license quota {tariff.total} is less than required {duration} seconds.'
        )

    received_date = datetime.now(timezone.utc).isoformat()[:-9]

    resampler = Resampler(unique_uuid).resample(info, audio, received_date)

    if len(resampler) == 0:
        raise CustomHTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f'Failed to upload talk record file.'
        )

    talk_record_id = int(talk_record_id) if talk_record_id else None

    task = celery.send_task(
        tariff.model.task_name,
        args=[received_date, duration, info.num_channels, user.id, talk_record_id, resampler, unique_uuid, origin],
        queue=tariff.model.task_queue
    )

    decrement_user_tariff(db, tariff.id, round(duration))

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
