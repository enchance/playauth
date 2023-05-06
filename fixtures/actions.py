from app import ic
from app.settings import settings as s
from app.auth import Account, Group, AuthHelper
from .data import GROUP_FIXTURES


SUPER_EMAIL = 'super@gmail.com'
VERIFIED_EMAIL_SET = {'verified@gmail.com', 'ver2@app.co', 'ver3@app.co', 'ver4@app.co'}
UNVERIFIED_EMAIL = 'unverified@gmail.com'
INACTIVE_VERIFIED_EMAIL = 'inactive_verified@gmail.com'
INACTIVE_UNVERIFIED_EMAIL = 'inactive_unverified@gmail.com'
BANNED_EMAIL = 'banned@gmail.com'

async def insert_accounts() -> list[str]:
    """Create nenw accounts for testing"""
    total = 0
    password = 'pass123'        # noqa
    current_emails = await Account.all().values_list('email', flat=True)
    
    # Super users
    dataset = {SUPER_EMAIL}
    # superset = {random_email()}
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if _ := await AuthHelper.create_user(email=email, password=password, is_superuser=True,
                                                 is_verified=True):
                total += 1
    
    # Verified users
    createset = VERIFIED_EMAIL_SET - set(current_emails)
    if createset:
        for email in createset:
            if _ := await AuthHelper.create_user(email=email, password=password, is_verified=True):
                total += 1
    
    # Unverified users
    # unverifiedset = {'unverified@gmail.com'}.union({random_email() for _ in range(2)})
    dataset = {UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password):
                total += 1
    
    dataset = {INACTIVE_VERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password,is_verified=True,
                                                 is_active=False):
                total += 1
    
    dataset = {INACTIVE_UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password, is_active=False):
                total += 1
    
    dataset = {BANNED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if _ := await AuthHelper.create_user(email=i, password=password, is_verified=True,
                                                 is_banned=True):
                total += 1
    
    return [f'ACCOUNTS_CREATED - {total} new']


async def insert_groups() -> list[str]:
    total = 0
    accounts = await Account.all().only('id').prefetch_related('groups')
    grouplist = await Group.all().values_list('name', flat=True)
    
    for name, datamap in GROUP_FIXTURES.items():
        if name in grouplist:
            continue
        
        desc = datamap.pop('description')
        permlist = set()
        for title, perms in datamap.items():
            for i in perms:
                permlist.add(f'{title}.{i}')
        
        group = await Group.create(name=name, description=desc, permissions=permlist)
        total += 1
        
        # Add to account
        if group.name in s.DEFAULT_GROUPS:
            for account in accounts:
                await account.groups.add(group)
    
    return [f'GROUPS_CREATED - {total} groups']