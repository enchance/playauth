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

from app import settings as s, ic
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
    def refresh_cookie_generator(cls, *, expiresiso: Optional[str] = None, **kwargs) -> dict:
        """Generate the data for a new cookie but not the cookie itself."""
        refresh_token = secrets.token_hex(nbytes=32)
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
            'value':    refresh_token,
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



authrouter = APIRouter()

@authrouter.get('/private', response_model=AccountRes)
async def private(account: Account = Depends(current_user)):
    # ic(account)
    # ic(account.get_options())
    # group = await Group.get_or_none(name='AccountGroup').only('id', 'name')
    # ic(group)
    # ic(group.foo())
    return account


@authrouter.post(f"{s.JWT_AUTH_PREFIX}/refresh")
async def refresh_access_token(strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
                               refresh_token: Annotated[str, Cookie()] = None,
                               account: Account = Depends(current_user)):
    """
    Generates a new access_token if the refresh_token is still fresh.
    A missing refresh_token would warrant the user to login again.
    Refresh toknes are always regenerated but the expires date may remain the same.
    :param account:         Account
    :param strategy:        JWT strat
    :param refresh_token:   Current refresh_token
    :return:                str, New access_token
    """
    # https://github.com/fastapi-users/fastapi-users/discussions/350
    # https://stackoverflow.com/questions/57650692/where-to-store-the-refresh-token-on-the-client#answer-57826596
    cachekey = s.redis.REFRESH_TOKEN.format(refresh_token)
    
    if refresh_token is None:
        raise InvalidToken()
    
    if expdateiso := await AuthHelper.fetch_cached_reftoken(refresh_token):
        diff = AuthHelper.expiry_diff_minutes(expdateiso)
        if diff <= 0:
            # TESTME: Untested
            red.delete(cachekey)
            # ic(f'LOGOUT: {diff} mins')
            raise InvalidToken()                                                                   # Logout
        if diff <= s.REFRESH_TOKEN_REGENERATE / 60:
            # TESTME: Untested
            # ic(f'WINDOW REGENERATION: {diff} mins')
            cookiedata = AuthHelper.refresh_cookie_generator()                                  # Regenerate expires
        else:
            # TESTME: Untested
            # ic(f'FORCED REGENERATION: {diff} mins')
            cookiedata = AuthHelper.refresh_cookie_generator(expiresiso=expdateiso)      # Retain expires
    else:
        raise InvalidToken()
    
    access_token = await strategy.write_token(account)
    content = BearerResponse(access_token=access_token, token_type='bearer')
    response = JSONResponse(content.dict())
    expiresiso = cookiedata.pop('expiresiso')
    response.set_cookie(**cookiedata)

    cachekey = s.redis.REFRESH_TOKEN.format(cookiedata['value'])
    red.set(cachekey, dict(uid=str(account.id), exp=expiresiso))
    
    return response
    
    # return await bearer_transport.get_login_response(token)
    # return await auth_backend.login(strategy, user)