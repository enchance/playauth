import secrets, pytz, math
from typing import Annotated, Any
from datetime import datetime, timedelta
from contextlib import asynccontextmanager
from fastapi import FastAPI, Body, Depends, Response, Header, HTTPException, Cookie
from fastapi.middleware.cors import CORSMiddleware

from app import settings as s, register_db, Env, ic
from app.auth import AccountRes, fusers, UserRead, UserCreate, auth_backend, current_user, bearer_transport, \
    get_jwt_strategy, AuthHelper, Account, Group, authrouter
from fixtures import fixture_router



async def on_startup():
    ic('STARTED')

async def on_shutdown():
    ic('STOPPED')
    
def get_app() -> FastAPI:
    config = dict(debug=s.DEBUG, title=s.SITENAME, version=s.VERSION,
                  on_startup=[on_startup], on_shutdown=[on_shutdown])
    if not s.DEBUG:
        config['docs_url'] = None
        config['redoc_url'] = None
        config['swagger_ui_oauth2_redirect_url'] = None
    app_ = FastAPI(**config)
    
    # Routes
    app_.include_router(fusers.get_register_router(UserRead, UserCreate), prefix='/auth', tags=['auth'])
    app_.include_router(fusers.get_auth_router(auth_backend, requires_verification=True), prefix='/auth', tags=['auth'])
    app_.include_router(authrouter, tags=['auth'])
    
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


# @app.get('/foo')
# async def foo(user: Annotated[Account, Depends(current_user)]):
#     return user.options