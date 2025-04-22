from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ModelSchema(BaseModel):
    id: Optional[int]
    name: Optional[str]
    task_queue: Optional[str]
    task_name: Optional[str]

    class Config:
        from_attributes = True
        extra = 'ignore'


class TariffSchema(BaseModel):

    id: Optional[int]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    active: Optional[bool]
    total: Optional[int]
    user_id: Optional[int]
    model: Optional["ModelSchema"] = None

    class Config:
        from_attributes = True
        extra = 'ignore'


class UserRoleSchema(BaseModel):
    id: Optional[int]
    name: Optional[str]

    class Config:
        from_attributes = True


class RecognitionConfigurationSchema(BaseModel):

    id: Optional[int]
    model: Optional[str]
    task_id: Optional[str]
    batch_size: Optional[int]
    chunk_length: Optional[int]
    sample_rate: Optional[int]
    user_id: Optional[int]

    class Config:
        from_attributes = True
        extra = 'ignore'


class UserSchema(BaseModel):
    id: Optional[int] = None  # Ensuring the default is None
    created_date: Optional[datetime] = None
    updated_date: Optional[datetime] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None
    api_key: Optional[str] = None
    uuid: Optional[str] = None
    audience: Optional[str] = None
    role_id: Optional[int] = None
    tariff: Optional[list["TariffSchema"]] = None
    recognition: Optional["RecognitionConfigurationSchema"] = None
    role: Optional["UserRoleSchema"] = None

    class Config:
        from_attributes = True
        extra = 'ignore'

