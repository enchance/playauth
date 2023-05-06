import uuid
from datetime import datetime
from typing import Optional
from pydantic import Field, validator, BaseModel, EmailStr
from fastapi_users import schemas, models

from app import settings as s


class UserRead(schemas.BaseUser[uuid.UUID]):
    pass


class UserCreate(schemas.BaseUserCreate):
    """Data needed to create a new account"""
    display: str = Field(..., max_length=s.DISPLAY_MAX)
    # password2: str
    
    @validator('password')
    def valid_password(cls, val: str):
        if len(val) < s.PASSWORD_MIN:
            raise ValueError(f'Password should be at least {s.PASSWORD_MIN} characters')
        return val
    
    # @validator('password2')
    # def same_password(cls, val: str, values: dict):
    #     if 'password' not in values:
    #         raise ValueError('Missing retyped password')
    #     if val != values['password']:
    #         raise ValueError('Passwords do not match')
    #     return val


class UserUpdate(schemas.BaseUserUpdate):
    display: Optional[str] = Field(None, max_length=s.DISPLAY_MAX)


class AccountRes(BaseModel):
    id: uuid.UUID
    display: str
    email: str