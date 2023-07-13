import uuid, secrets, pytz, math, time, ast
from typing import Annotated
from contextlib import  asynccontextmanager
from datetime import datetime, timedelta
from typing import Optional
from fastapi import Request, Depends, Response, Cookie, APIRouter, HTTPException
from fastapi.responses import JSONResponse
from fastapi_users.authentication.transport.bearer import BearerResponse
from fastapi_users import UUIDIDMixin, BaseUserManager, FastAPIUsers
from fastapi_users.authentication import (
    JWTStrategy, BearerTransport, AuthenticationBackend
)
from tortoise.query_utils import Prefetch

from app import (
    settings as s, ic, SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL,
    INACTIVE_VERIFIED_EMAIL, INACTIVE_UNVERIFIED_EMAIL, FIXTURE_PASSWORD
)
# from .models import *
from .models import *
from .schemas import *
from ..exceptions import InvalidToken


RESET_PASSWORD_TOKEN_AUD = f'{s.APPCODE}:reset'
VERIFY_TOKEN_AUD = f'{s.APPCODE}:verify'
TOKEN_AUD = f'{s.APPCODE}:auth'



class AuthHelper:
    @staticmethod
    def format_expiresiso(expiresiso: str) -> str:
        """
        Format a datetime in iso format to a string for use in cookie generation.
        :param expiresiso:  str datetime in iso format
        :return:            str fit for a cookie
        """
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
    async def fetch_cached_reftoken(refresh_token: str) -> str:
        """
        Get the reftoken from cache. If there is no token then return None.
        :param refresh_token:   refresh_token to search for
        :return:                str, expiresiso of refresh_token
        """
        # // TODO: Get iso from cache
        # expiresiso = '2023-05-06T10:47:00.906700+00:00'
        # expiresiso = (datetime.now(tz=pytz.UTC) + timedelta(minutes=182)).isoformat()
        # # expiresiso = None
        # return expiresiso
        cachekey = s.redis.REFRESH_TOKEN.format(refresh_token)
        if _ := red.exists(cachekey):
            d = red.get(cachekey)
            return d['exp']
        raise InvalidToken()
    
    @classmethod
    def refresh_cookie_generator(cls, *, refresh_token: Optional[str] = None, expiresiso: Optional[str] = None,
                                 **kwargs) -> dict:
        """Generate the data for a new cookie but not the cookie itself."""
        token = refresh_token or secrets.token_hex(nbytes=32)
        fallback_iso = (datetime.now(tz=pytz.UTC) + timedelta(seconds=s.REFRESH_TOKEN_TTL)).isoformat()
        
        # data_dict = dict(expiresiso=fallback_iso)
        expires = cls.format_expiresiso(fallback_iso)
        try:
            if expiresiso:
                if expires := cls.format_expiresiso(expiresiso):
                    pass
                    # data_dict['expiresiso'] = expiresiso
                else:
                    raise ValueError()
        except (TypeError, ValueError):
            pass
            
        return {
            'key':      'refresh_token',
            'value':    token,
            'httponly': True,
            'expires':  expires,
            'path':     s.JWT_AUTH_PREFIX,
            'domain':   s.SITEURL,
            'expiresiso': expiresiso or fallback_iso,
            **kwargs,
        }

    @staticmethod
    async def create_user(**kwargs):
        async with get_user_db_context() as user_db:
            async with get_user_manager_context(user_db) as user_manager:
                return await user_manager.create(UserCreate(**kwargs))
            
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
        admin_role = await Role.get_or_none(name=RoleTypes.admin.name)
        starter_role = await Role.get_or_none(name=RoleTypes.starter.name)

        if account.email == SUPER_EMAIL and s.DEBUG:
            account.role = admin_role
            account.is_verified = True
            await account.save(update_fields=['role_id', 'is_verified'])
        elif account.email in {UNVERIFIED_EMAIL, INACTIVE_UNVERIFIED_EMAIL} and s.DEBUG:
            account.role = starter_role
            await account.save(update_fields=['role_id'])
        else:
            account.role = starter_role
            account.is_verified = True
            await account.save(update_fields=['role_id', 'is_verified'])

        cachekey = s.redis.ACCOUNT_GROUPS.format(account.id)    # noqa
        red.set(cachekey, set(account.role.groups))
    
    
    # TESTME: Untested
    async def on_after_login(self, account: Account, request: Optional[Request] = None,
                             response: Optional[Response] = None):
        # Always generate a new refresh_token on login
        cookiedata = AuthHelper.refresh_cookie_generator()
        expiresiso = cookiedata.pop('expiresiso')
        response.set_cookie(**cookiedata)
        
        cachekey = s.redis.REFRESH_TOKEN.format(cookiedata['value'])
        red.set(cachekey, dict(uid=str(account.id), exp=expiresiso))

        # datamap = AuthHelper.parse_response_body(response)
        # access_token = datamap.get('access_token')
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