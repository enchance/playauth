import secrets, pytz, math
from typing import Annotated, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Depends, Response, Header, HTTPException, Cookie
from fastapi_users.authentication import JWTStrategy
from fastapi.middleware.cors import CORSMiddleware

from app import settings as s, register_db, Env, ic
from app.auth import Account, AccountRes, fusers, UserRead, UserCreate, auth_backend, current_user, bearer_transport, \
    get_jwt_strategy, expiry_diff_minutes, fetch_cached_reftoken, refresh_cookie_generator


def get_app() -> FastAPI:
    app_ = FastAPI()
    
    # Routes
    app_.include_router(fusers.get_register_router(UserRead, UserCreate), prefix='/auth')
    app_.include_router(fusers.get_auth_router(auth_backend), prefix="/auth")
    
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


# @app.get('/', response_model=AccountRes)
# async def create_user():
#     #  OAuth
#     # account = await Account.create(display='abc', email='abc@gmail.com', hashed_password='foobar',
#     #                                oauth_name='', access_token='', refresh_token='', account_id='')
#     account = await Account.create(display='abc', email='abc@gmail.com', hashed_password='foobar')
#     return account
#
#
# @app.put('/')
# async def update(email: Annotated[str, Body()], username: Annotated[str, Body()]):
#     account = await Account.get(email=email).only('id', 'email', 'username')
#     account.username = username
#     await account.save(update_fields=['username'])
#     return account


@app.get('/private', response_model=AccountRes)
def private(account: Account = Depends(current_user)):
    return account


@app.get("/auth/jwt/refresh")
async def refresh_acstoken(resp: Response, strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
                           refresh_token: Annotated[str, Cookie()] = None, user=Depends(current_user)):
    # https://github.com/fastapi-users/fastapi-users/discussions/350
    # https://stackoverflow.com/questions/57650692/where-to-store-the-refresh-token-on-the-client#answer-57826596

    # // TODO: Create a new reftoken with the same expiry and respond with that
    try:
        if cached_reftoken := await fetch_cached_reftoken(refresh_token):
            diff = expiry_diff_minutes(cached_reftoken)
            if diff <= 0:
                raise Exception()
            if diff <= s.REFRESH_TOKEN_REGENERATE / 60:
                cookie = refresh_cookie_generator()
                # // TODO: Save token, expiry to cache
                resp.set_cookie(**cookie)
        else:
            raise Exception()
    except Exception:
        # Frontend sends user to /auth/login
        raise HTTPException(status_code=401, detail='ACCESS_REVOKED')
    
    token = await strategy.write_token(user)
    return await bearer_transport.get_login_response(token)
    
    # return await auth_backend.login(strategy, user)