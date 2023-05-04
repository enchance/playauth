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
from app.auth import Account, AccountRes, fusers, UserRead, UserCreate, auth_backend, current_user, bearer_transport, \
    get_jwt_strategy, expiry_diff_minutes, fetch_cached_reftoken, refresh_cookie_generator


def get_app() -> FastAPI:
    app_ = FastAPI()
    
    # Routes
    app_.include_router(fusers.get_register_router(UserRead, UserCreate), prefix='/auth')
    app_.include_router(fusers.get_auth_router(auth_backend), prefix='/auth')
    
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
def private(account: Account = Depends(current_user)):
    return account


@app.post(f"{s.JWT_AUTH_PREFIX}/refresh")
async def refresh_access_token(strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
                               refresh_token: Annotated[str, Cookie()] = None, user=Depends(current_user)):
    """
    Generates a new access_token if the refresh_token is still fresh. A missing refresh_token would warrant the
    user to login in again.
    :param strategy:
    :param refresh_token:
    :param user:
    :return:
    """
    # https://github.com/fastapi-users/fastapi-users/discussions/350
    # https://stackoverflow.com/questions/57650692/where-to-store-the-refresh-token-on-the-client#answer-57826596

    try:
        if refresh_token is None:
            raise Exception()
        if cached_expiresiso := await fetch_cached_reftoken(refresh_token):
            diff = expiry_diff_minutes(cached_expiresiso)
            ic(f'DIFF: {diff}')
            if diff <= 0:
                # // TODO: Delete any existing refresh_tokens in cache
                raise Exception()                                                       # Logout
            if diff <= s.REFRESH_TOKEN_REGENERATE / 60:
                cookiedata = refresh_cookie_generator()                                 # Regenerate
            else:
                cookiedata = refresh_cookie_generator(expiresiso=cached_expiresiso)     # Retain
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