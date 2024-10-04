from fastapi import HTTPException

from .api import router
from .auth import router
from .transcribe import router
from .transcription import router
from .user import router
from .hook import router
from .flower import router


class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int, detail: str):
        super().__init__(status_code=status_code, detail=detail)
        self.success = False
        self.message = detail
