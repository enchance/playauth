import secrets, pytz, math
from typing import Annotated, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Depends, Response, Header, HTTPException, Cookie
from fastapi.responses import JSONResponse
from fastapi_users.authentication import JWTStrategy
from fastapi_users.authentication.transport.bearer import BearerResponse
from fastapi.middleware.cors import CORSMiddleware

from app import settings as s, register_db, Env, ic
from app.auth import AccountRes, fusers, UserRead, UserCreate, auth_backend, current_user, bearer_transport, \
    get_jwt_strategy, AuthHelper, Account, Group
from fixtures import fixture_router


def get_app() -> FastAPI:
    app_ = FastAPI()
    
    # Routes
    app_.include_router(fusers.get_register_router(UserRead, UserCreate), prefix='/auth', tags=['auth'])
    app_.include_router(fusers.get_auth_router(auth_backend), prefix='/auth', tags=['auth'])
    
    # Dev
    if s.ENV == Env.development:
        app_.include_router(fixture_router, prefix='/fixtures', tags=['fixtures'])
    
    # Tortoise
    register_db(app_)
    
    # CORS
    origins = [
        'http://localhost:3000', 'https://localhost:3000',
    ]
    app_.add_middleware(
        CORSMiddleware, allow_origins=origins, allow_credentials=True,
        allow_methods=['*'], allow_headers=["*"],
    )
    
    return app_


app = get_app()


@app.get('/private', response_model=AccountRes)
async def private(account: Account = Depends(current_user)):
    ic(type(account))
    ic(account.get_options())
    group = await Group.get_or_none(name='AccountGroup').only('id', 'name')
    ic(group)
    ic(group.foo())
    return account


@app.post(f"{s.JWT_AUTH_PREFIX}/refresh")
async def refresh_access_token(strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
                               refresh_token: Annotated[str, Cookie()] = None, user=Depends(current_user)):
    """
    Generates a new access_token if the refresh_token is still fresh.
    A missing refresh_token would warrant the user to login again.
    Refresh toknes are always regenerated but the expires date may remain the same.
    :param strategy:        JWT strat
    :param refresh_token:   Current refresh_token
    :param user:            Account
    :return:                str, New access_token
    """
    # https://github.com/fastapi-users/fastapi-users/discussions/350
    # https://stackoverflow.com/questions/57650692/where-to-store-the-refresh-token-on-the-client#answer-57826596

    try:
        if refresh_token is None:
            raise Exception()
        
        if cached_expiresiso := await AuthHelper.fetch_cached_reftoken(refresh_token):
            diff = AuthHelper.expiry_diff_minutes(cached_expiresiso)
            if diff <= 0:
                # // TODO: Delete any existing refresh_tokens in cache
                ic(f'LOGOUT ACCOUNT: {diff} mins')
                raise Exception()                                                                   # Logout
            if diff <= s.REFRESH_TOKEN_REGENERATE / 60:
                ic(f'FULL REGENERATION: {diff} mins')
                cookiedata = AuthHelper.refresh_cookie_generator()                                  # Regenerate expires
            else:
                ic(f'PARTIAL REGENERATION: {diff} mins')
                cookiedata = AuthHelper.refresh_cookie_generator(expiresiso=cached_expiresiso)      # Retain expires
        else:
            raise Exception()
    except Exception:
        # Frontend sends user to login
        raise HTTPException(status_code=401, detail='ACCESS_REVOKED')
    
    access_token = await strategy.write_token(user)
    content = BearerResponse(access_token=access_token, token_type='bearer')
    response = JSONResponse(content.dict())
    cachedata = cookiedata.pop('cachedata')
    # // TODO: Save cachedata to cache
    response.set_cookie(**cookiedata)
    return response
    
    # return await bearer_transport.get_login_response(token)
    # return await auth_backend.login(strategy, user)


# @app.get('/foo')
# async def foo(user: Annotated[Account, Depends(current_user)]):
#     return user.options