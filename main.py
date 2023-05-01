from typing import Annotated
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from app import settings as s, register_db, Env
from app.auth import Account, AccountResponse


def get_app() -> FastAPI:
    app_ = FastAPI()
    
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


@app.get('/', response_model=AccountResponse)
async def create_user():
    #  OAuth
    # account = await Account.create(display='abc', email='abc@gmail.com', hashed_password='foobar',
    #                                oauth_name='', access_token='', refresh_token='', account_id='')
    account = await Account.create(display='abc', email='abc@gmail.com', hashed_password='foobar')
    return account


@app.put('/')
async def update(email: Annotated[str, Body()], username: Annotated[str, Body()]):
    account = await Account.get(email=email).only('id', 'email', 'username')
    account.username = username
    await account.save(update_fields=['username'])
    return account