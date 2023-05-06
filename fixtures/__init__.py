from fastapi import APIRouter

from .actions import *
from .data import *



fixture_router = APIRouter()

@fixture_router.get('/init', summary='Initial data for the project')
async def init(accounts: bool = True, groups: bool = True) -> list[str]:
    success = []
    
    if groups:
        success += await insert_groups()
    if accounts:
        success += await insert_accounts()
        
    return success