import uuid
from typing import Optional
from pydantic import Field, validator
from fastapi_users import schemas

from app import settings as s


class UserRead(schemas.BaseUser[uuid.UUID]):
    """
    Data you want visible in the current_user dependency. Each must have a value or default or
    the sky will fall on your head, you'll go blind, and you'll get a girlfriend.
    """
    display: str


class UserCreate(schemas.BaseUserCreate):
    """Data needed to create a new account"""
    display: str = Field(..., max_length=s.DISPLAY_MAX)
    password2: str
    
    @validator('password')
    def valid_password(cls, val: str):
        if len(val) < s.PASSWORD_MIN:
            raise ValueError(f'Password should be at least {s.PASSWORD_MIN} characters')
        return val
    
    @validator('password2')
    def same_password(cls, val: str, values: dict):
        if 'password' in values and val != values['password']:
            raise ValueError('Passwords do not match')
        return val


class UserUpdate(schemas.BaseUserUpdate):
    display: Optional[str] = Field(None, max_length=s.DISPLAY_MAX)