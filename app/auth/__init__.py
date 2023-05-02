import uuid
from typing import Optional
from fastapi import Request, Depends
from fastapi_users import UUIDIDMixin, BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    JWTStrategy, BearerTransport, AuthenticationBackend
)

from app import settings as s, ic
from .models import *
from .schemas import *


RESET_PASSWORD_TOKEN_AUD = f'{s.APPCODE}:reset'
VERIFY_TOKEN_AUD = f'{s.APPCODE}:verify'
TOKEN_AUD = f'{s.APPCODE}:auth'


class UserManager(UUIDIDMixin, BaseUserManager[Account, uuid.UUID]):
    verification_token_secret = s.SECRET_KEY
    verification_token_lifetime_seconds = s.VERIFY_TOKEN_TTL
    verification_token_audience = VERIFY_TOKEN_AUD
    
    reset_password_token_secret = s.SECRET_KEY
    reset_password_token_lifetime_seconds = s.RESET_PASSWORD_TOKEN_TTL
    reset_password_token_audience = RESET_PASSWORD_TOKEN_AUD

    # async def on_after_register(self, user: Account, request: Optional[Request] = None):
    #     ic(f"User {user.id} has registered.")
    #
    # async def on_after_forgot_password(self, user: Account, token: str, request: Optional[Request] = None):
    #     ic(f"User {user.id} has forgot their password. Reset token: {token}")
    #
    # async def on_after_request_verify(self, user: Account, token: str, request: Optional[Request] = None):
    #     ic(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_manager(user_db: TortoiseUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=s.SECRET_KEY, lifetime_seconds=s.ACCESS_TOKEN_TTL, token_audience=[TOKEN_AUD])


# Transport, Backend, Route
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")
auth_backend = AuthenticationBackend(name="jwt",transport=bearer_transport, get_strategy=get_jwt_strategy)
fusers = FastAPIUsers[Account, uuid.UUID](get_user_manager, [auth_backend])

# Helpers
current_user = fusers.current_user(active=True, verified=True)
super_user = fusers.current_user(active=True, verified=True, superuser=True)