import uuid, secrets, pytz, math, time, ast
from contextlib import  asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, Depends, Response
from fastapi_users import UUIDIDMixin, BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    JWTStrategy, BearerTransport, AuthenticationBackend
)
from tortoise.query_utils import Prefetch

from app import settings as s, ic
# from .models import *
from .models import *
from .schemas import *


RESET_PASSWORD_TOKEN_AUD = f'{s.APPCODE}:reset'
VERIFY_TOKEN_AUD = f'{s.APPCODE}:verify'
TOKEN_AUD = f'{s.APPCODE}:auth'



class AuthHelper:
    @staticmethod
    def format_expiresiso(expiresiso: str) -> str:
        expiry = datetime.fromisoformat(expiresiso).strftime("%a, %d %b %Y %H:%M:%S GMT")
        return expiry
    
    @staticmethod
    def expiry_diff_minutes(expiresiso: str) -> int:
        """
        Returns the difference in minutes.
        :param expiresiso:  str, Data is assumed to be in datetime.isoformat() hence a str.
        :return:            int
        """
        now = datetime.now(tz=pytz.UTC)
        try:
            expiresdt = datetime.fromisoformat(expiresiso)
            diff_in_mins = math.floor((expiresdt - now).total_seconds() / 60)
            return diff_in_mins
        except TypeError:
            return 0
    
    @staticmethod
    async def fetch_cached_reftoken(token: str) -> str | None:
        """
        Get the reftoken from cache. If there is no token then return None.
        :param token:   refresh_token to search for
        :return:        str | None
        """
        # // TODO: Get iso from cache
        # expiresiso = '2023-05-06T10:47:00.906700+00:00'
        expiresiso = (datetime.now(tz=pytz.UTC) + timedelta(minutes=182)).isoformat()
        # expiresiso = None
        return expiresiso
    
    @classmethod
    def refresh_cookie_generator(cls, *, expiresiso: Optional[str] = None, **kwargs) -> dict:
        """Generate the data for a new cookie but not the cookie itself."""
        refresh_token = secrets.token_hex(nbytes=32)
        fallback_iso = (datetime.now(tz=pytz.UTC) + timedelta(seconds=s.REFRESH_TOKEN_TTL)).isoformat()
        
        cachedata = dict(token=refresh_token, expiresiso=fallback_iso)
        expires = cls.format_expiresiso(fallback_iso)
        try:
            if expiresiso:
                if expires := cls.format_expiresiso(expiresiso):
                    cachedata['expiresiso'] = expiresiso
                else:
                    raise ValueError()
        except (TypeError, ValueError):
            pass
            
        return {
            'key':      'refresh_token',
            'value':    refresh_token,
            'httponly': True,
            'expires':  expires,
            'path':     s.JWT_AUTH_PREFIX,
            'domain':   s.SITEURL,
            'cachedata': cachedata,
            **kwargs,
        }

    @staticmethod
    async def create_user(**kwargs):
        async with get_user_db_context() as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                return await user_manager.create(UserCreate(**kwargs, display=''))
            
    @staticmethod
    def parse_response_body(response: Response, charset: str = 'utf-8') -> dict:
        strdict = response.body.decode(charset)
        datamap = ast.literal_eval(strdict)
        return datamap


class UserManager(UUIDIDMixin, BaseUserManager[Account, uuid.UUID]):
    verification_token_secret = s.SECRET_KEY
    verification_token_lifetime_seconds = s.VERIFY_TOKEN_TTL
    verification_token_audience = VERIFY_TOKEN_AUD
    
    reset_password_token_secret = s.SECRET_KEY
    reset_password_token_lifetime_seconds = s.RESET_PASSWORD_TOKEN_TTL
    reset_password_token_audience = RESET_PASSWORD_TOKEN_AUD
    
    # TESTME: Untested
    async def on_after_register(self, account: Account, request: Optional[Request] = None):
        # ic(f"User {account.id} has registered [{account.email}].")
        
        if starter_role := await Role.get_or_none(name='starter'):
            account.role = starter_role
            await account.save(update_fields=['role_id'])
    
    
    # TESTME: Untested
    async def on_after_login(self, account: Account, request: Optional[Request] = None,
                             response: Optional[Response] = None):
        # Always generate a new refresh_token on login
        cookiedata = AuthHelper.refresh_cookie_generator()
        cachedata = cookiedata.pop('cachedata')
        # // TODO: Save cachedata to cache
        response.set_cookie(**cookiedata)

        datamap = AuthHelper.parse_response_body(response)
        access_token = datamap.get('access_token')
        # TODO: Save access_token to cache
        # ic(f"User {user.email} logged in. Refresh token: {refresh_token}.")

async def get_user_db():
    yield TortoiseUserDatabase(Account)
    
async def get_user_manager(user_db: TortoiseUserDatabase = Depends(get_user_db)):
    yield UserManager(user_db)

def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(secret=s.SECRET_KEY, lifetime_seconds=s.ACCESS_TOKEN_TTL, token_audience=[TOKEN_AUD])


# Transport, Backend, Route
bearer_transport = BearerTransport(tokenUrl="auth/login")
auth_backend = AuthenticationBackend(name="jwt",transport=bearer_transport, get_strategy=get_jwt_strategy)
fusers = FastAPIUsers[Account, uuid.UUID](get_user_manager, [auth_backend])

# Context: used to programmatically create users for tests
get_user_db_context = asynccontextmanager(get_user_db)
get_user_manager_context = asynccontextmanager(get_user_manager)

# Helpers
current_user = fusers.current_user(active=True, verified=True)
super_user = fusers.current_user(active=True, verified=True, superuser=True)
