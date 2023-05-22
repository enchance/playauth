import uuid
from decouple import config

from app import ic, red
from app.settings import settings as s
from app.auth import Account, Group, Role, AuthHelper
from .data import *


SUPER_EMAIL = 'super@gmail.com'
VERIFIED_EMAIL_SET = {'verified@gmail.com', 'ver2@app.co', 'ver3@app.co', 'ver4@app.co'}    # Don't change order
UNVERIFIED_EMAIL = 'unverified@gmail.com'
INACTIVE_VERIFIED_EMAIL = 'inactive_verified@gmail.com'
INACTIVE_UNVERIFIED_EMAIL = 'inactive_unverified@gmail.com'
BANNED_EMAIL = 'banned@gmail.com'


async def seed_accounts() -> list[str]:
    """Create nenw accounts for testing"""
    total = 0
    password = 'pass123'        # noqa
    
    current_emails = await Account.all().values_list('email', flat=True)
    admin_role = await Role.get_or_none(name='admin')
    starter_role = await Role.get_or_none(name='starter')
    
    def _cache_groups(uid: uuid.UUID, datalist: set[str]):
        cachekey = s.redis.ACCOUNT_GROUPS.format(uid)
        red.set(cachekey, datalist)       # noqa
        
    async def _set_role(acct: Account, role: Role):
        acct.role = role
        await acct.save(update_fields=['role_id'])
    
    # Super users
    dataset = {SUPER_EMAIL}     # noqa
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_superuser=True,
                                                       is_verified=True):
                await _set_role(account, admin_role)
                _cache_groups(account.id, set(account.role.groups))
                total += 1
    
    # Verified users
    createset = VERIFIED_EMAIL_SET - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_verified=True):
                _cache_groups(account.id, set(account.role.groups))
                total += 1
                
                # Custom perms
                if account.email == list(VERIFIED_EMAIL_SET)[0]:
                    account.perms = {'perms.attach', '-account.update'}
                    await account.save(update_fields=['perms'])
                
                
    # Unverified users
    dataset = {UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password):
                _cache_groups(account.id, set(account.role.groups))
                total += 1
    
    dataset = {INACTIVE_VERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password,is_verified=True,
                                                       is_active=False):
                _cache_groups(account.id, set(account.role.groups))
                total += 1
    
    dataset = {INACTIVE_UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_active=False):
                _cache_groups(account.id, set(account.role.groups))
                total += 1
    
    dataset = {BANNED_EMAIL}                                                                        # noqa
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_verified=True,
                                                       is_banned=True):
                _cache_groups(account.id, set(account.role.groups))
                total += 1
    
    return [f'ACCOUNTS_CREATED - {total} new']


async def seed_groups() -> list[str]:
    total = 0
    grouplist = await Group.all().values_list('name', flat=True)
    env = config('ENV')
    fixturemap = env == 'development' and {**GROUP_FIXTURES_DEV} or {**GROUP_FIXTURES_PROD}
    
    ll = []
    nameset = set(grouplist)
    for name, datamap in fixturemap.items():
        if name in grouplist:
            continue
            
        permset = set()
        desc = datamap.pop('description')
        if datamap:
            for title, perms in datamap.items():
                for i in perms:
                    permset.add(f'{title}.{i}')
        else:
            permset = None
        ll.append(Group(name=name, description=desc, permissions=permset))
        total += 1
        
        # Cache
        cachekey = s.redis.GROUP_PERMISSIONS.format(name)
        red.set(cachekey, permset)
        nameset.add(name)
    ll and await Group.bulk_create(ll)
    
    # redis
    cachekey = s.redis.GROUPS
    nameset and red.set(cachekey, nameset)
    
    return [f'GROUPS_CREATED - {total} groups']


async def seed_roles() -> list[str]:
    total = 0
    fixturemap = {**ROLE_FIXTURES}
    
    ll = []
    for name, groups in fixturemap.items():
        ll.append(Role(name=name, groups=groups))
        total += 1
    ll and await Role.bulk_create(ll)

    return [f'ROLES_CREATED - {total} roles']