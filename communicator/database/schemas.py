from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TariffSchema(BaseModel):

    id: Optional[int]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    active: Optional[bool]
    total: Optional[int]
    user_id: Optional[int]

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

    id: Optional[int]
    created_date: Optional[datetime]
    updated_date: Optional[datetime]
    first_name: Optional[str]
    last_name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    username: Optional[str]
    password: Optional[str]
    api_key: Optional[str]
    uuid: Optional[str]
    audience: Optional[str]
    role_id: Optional[int]
    tariff: Optional[TariffSchema]
    recognition: Optional[RecognitionConfigurationSchema]
    role: Optional[UserRoleSchema]

    class Config:
        from_attributes = True
        extra = 'ignore'
