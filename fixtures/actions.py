import uuid, secrets
from faker import Faker
from decouple import config

from app import (
    ic, red, SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL,
    INACTIVE_VERIFIED_EMAIL, INACTIVE_UNVERIFIED_EMAIL, FIXTURE_PASSWORD
)
from app.settings import settings as s
from app.auth import Account, Group, Role, AuthHelper
from .data import *


faker = Faker()

async def seed_accounts() -> list[str]:
    """Create nenw accounts for testing"""
    total = 0
    
    current_emails = await Account.all().values_list('email', flat=True)
    admin_role = await Role.get_or_none(name='admin')
        
    async def _set_role(acct: Account, role: Role):
        acct.role = role
        await acct.save(update_fields=['role_id'])
    
        # accounts: list[Account] = await Account.all().prefetch_related('groups')
        # for account in accounts:
        #     if account.email == 'ver2@app.co':
        #         account.authtoken = {}
        #     elif account.email == 'ver3@app.co':
        #         exp = '2030-01-01T00:00:00+00:00'
        #         account.authtoken = dict(expires=exp, blacklist=True, refresh_token='abc')
        #     elif account.email == 'ver4@app.co':
        #         exp = '2020-01-01T00:00:00+00:00'
        #         account.authtoken = dict(expires=exp, blacklist=True, refresh_token='abc')
        #     await account.save(update_fields=['authtoken'])

    # Super users
    dataset = {SUPER_EMAIL}     # noqa
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=FIXTURE_PASSWORD, is_superuser=True,
                                                       is_verified=True, display=faker.name()):
                await _set_role(account, admin_role)
                total += 1

    # Verified users
    createset = VERIFIED_EMAIL_SET - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=FIXTURE_PASSWORD, is_verified=True,
                                                       display=faker.name()):
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
            if account := await AuthHelper.create_user(email=i, password=FIXTURE_PASSWORD, display=faker.name()):
                total += 1

    dataset = {INACTIVE_VERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=FIXTURE_PASSWORD, is_verified=True,
                                                       is_active=False, display=faker.name()):
                total += 1

    dataset = {INACTIVE_UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=FIXTURE_PASSWORD, is_active=False,
                                                       display=faker.name()):
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