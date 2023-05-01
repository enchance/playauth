from fastapi import FastAPI

from app import settings as s, register_db
from app.auth import Account


def get_app() -> FastAPI:
    app_ = FastAPI()
    
    # Tortoise
    register_db(app_)
    
    return app_


app = get_app()


@app.get('/')
async def create_user():
    account = await Account.create(username='abc', email='abc@gmail.com', hashed_password='foobar')
    return account