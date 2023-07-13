from fastapi import APIRouter, Response
from tortoise.exceptions import DoesNotExist

from app import ic
from app.auth import Account, RoleTypes


devrouter = APIRouter()


@devrouter.get('/')
async def index(response: Response):
    x = RoleTypes.starter
    print(type(x.name), x.name)
    
    # try:
    #     # data = await Account.get(email='super@gmail.com').only('id')
    #     exists = await Account.exists(email='super@gmail.comx')
    #     ic(exists)
    # except DoesNotExist as err:
    #     ic(err)
    return 'I am alive!'