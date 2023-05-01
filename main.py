from typing import Annotated
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware

from app import settings as s, register_db, Env
from app.auth import Account


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


@app.get('/')
async def create_user():
    account = await Account.create(username='abc', email='abc@gmail.com', hashed_password='foobar')
    return account

@app.put('/')
async def update(email: Annotated[str, Body()], username: Annotated[str, Body()]):
    account = await Account.get(email=email).only('id', 'email', 'username')
    account.username = username
    await account.save(update_fields=['username'])
    return account