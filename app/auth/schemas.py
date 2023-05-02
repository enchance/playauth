import uuid
from typing import Optional
from pydantic import Field
from fastapi_users import schemas

from app import settings as s


class UserRead(schemas.BaseUser[uuid.UUID]):
    display: str


class UserCreate(schemas.BaseUserCreate):
    display: str = Field(..., max_length=s.DISPLAY_MAX)


class UserUpdate(schemas.BaseUserUpdate):
    display: Optional[str] = Field(None, max_length=s.DISPLAY_MAX)