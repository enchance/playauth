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
    grouplist = await Group.all().only('id', 'name')
    
    async def _add_default_groups(account_: Account):
        for i in s.DEFAULT_GROUPS:
            for grp in grouplist:
                if grp.name == i:
                    await account_.groups.add(grp)
    
    # Super users
    dataset = {SUPER_EMAIL}
    # superset = {random_email()}
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_superuser=True,
                                                       is_verified=True):
                await _add_default_groups(account)
                if group := await Group.get_or_none(name='AdminGroup'):
                    ic('ADDING EXTRA')
                    await account.groups.add(group)
                total += 1
    
    # Verified users
    createset = VERIFIED_EMAIL_SET - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_verified=True):
                await _add_default_groups(account)
                total += 1
    
    # Unverified users
    # unverifiedset = {'unverified@gmail.com'}.union({random_email() for _ in range(2)})
    dataset = {UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password):
                await _add_default_groups(account)
                total += 1
    
    dataset = {INACTIVE_VERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password,is_verified=True,
                                                 is_active=False):
                await _add_default_groups(account)
                total += 1
    
    dataset = {INACTIVE_UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_active=False):
                await _add_default_groups(account)
                total += 1
    
    dataset = {BANNED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_verified=True,
                                                       is_banned=True):
                await _add_default_groups(account)
                total += 1
    
    return [f'ACCOUNTS_CREATED - {total} new']


async def insert_groups() -> list[str]:
    total = 0
    grouplist = await Group.all().values_list('name', flat=True)
    
    ll = []
    for name, datamap in GROUP_FIXTURES.items():
        if name in grouplist:
            continue
            
        permlist = set()
        desc = datamap.pop('description')
        for title, perms in datamap.items():
            for i in perms:
                permlist.add(f'{title}.{i}')
        ll.append(Group(name=name, description=desc, permissions=permlist))
        total += 1
    ll and await Group.bulk_create(ll)
    
    
    return [f'GROUPS_CREATED - {total} groups']