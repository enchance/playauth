from fastapi import APIRouter

from app import ic
from app.auth import Account, AuthHelper



fixture_router = APIRouter()

@fixture_router.get('/init', summary='Initial data for the project')
async def init(accounts: bool = True) -> list[str]:
    success = []
    
    if accounts:
        success += await insert_accounts()
        
    return success


async def insert_accounts() -> list[str]:
    """Create nenw accounts for testing"""
    total = 0
    password = 'pass123'        # noqa
    current_emails = await Account.all().values_list('email', flat=True)
    
    # Super users
    dataset = {'super@gmail.com'}
    # superset = {random_email()}
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if _ := await AuthHelper.create_user(email=email, password=password, is_superuser=True,
                                                 is_verified=True):
                total += 1
    
    # Verified users
    dataset = {'verified1@gmail.com', 'ver2@app.co', 'ver3@app.co', 'ver4@app.co'}
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if _ := await AuthHelper.create_user(email=email, password=password, is_verified=True):
                total += 1
    
    # Unverified users
    # unverifiedset = {'unverified@gmail.com'}.union({random_email() for _ in range(2)})
    dataset = {'unverified@gmail.com'}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password):
                total += 1
    
    dataset = {'inactive_verified@gmail.com'}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password, is_active=False,
                                                 is_verified=True):
                total += 1
    
    dataset = {'inactive_unverified@gmail.com'}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password, is_active=False):
                total += 1
    
    dataset = {'banned@gmail.com'}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password, is_verified=True,
                                                 is_banned=True):
                total += 1
    
    return [f'ACCOUNTS_CREATED - {total} new']