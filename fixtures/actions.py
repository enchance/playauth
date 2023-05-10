import uuid

from app import ic, red
from app.settings import settings as s
from app.auth import Account, Group, AuthHelper
from .data import GROUP_FIXTURES


SUPER_EMAIL = 'super@gmail.com'
VERIFIED_EMAIL_SET = {'verified@gmail.com', 'ver2@app.co', 'ver3@app.co', 'ver4@app.co'}
UNVERIFIED_EMAIL = 'unverified@gmail.com'
INACTIVE_VERIFIED_EMAIL = 'inactive_verified@gmail.com'
INACTIVE_UNVERIFIED_EMAIL = 'inactive_unverified@gmail.com'
BANNED_EMAIL = 'banned@gmail.com'


async def seed_accounts() -> list[str]:
    """Create nenw accounts for testing"""
    total = 0
    password = 'pass123'        # noqa
    
    current_emails = await Account.all().values_list('email', flat=True)
    default_groups = await Group.filter(name__in=s.DEFAULT_GROUPS).only('id', 'name')
    
    def _cache_permissions(id: uuid.UUID, grouplist: list[Group]):      # noqa
        groupnames = {j.name for j in grouplist}
        acct_cachekey = s.redis.ACCOUNT_PERMISSIONS.format(id)
        accountperms = red.get(acct_cachekey) or set()
        
        for name in groupnames:
            group_cachekey = s.redis.GROUP_PERMISSIONS.format(name)
            group_perms = red.get(group_cachekey)
            accountperms = accountperms.union(group_perms)    # noqa
        accountperms and red.set(acct_cachekey, accountperms)
    
    def _cache_groups(id: uuid.UUID, datalist: list[Group]):
        cachekey = s.redis.ACCOUNT_GROUPS.format(account.id)
        red.set(cachekey, {i.name for i in datalist})
    
    
    # Super users
    dataset = {SUPER_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_superuser=True,
                                                       is_verified=True):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                
                if group := await Group.get_or_none(name='AdminGroup').only('id','name'):
                    await account.groups.add(group)
                    _cache_permissions(account.id, [group])
                    _cache_groups(account.id, [group])
                total += 1
    
    # Verified users
    createset = VERIFIED_EMAIL_SET - set(current_emails)
    if createset:
        for email in createset:
            if account := await AuthHelper.create_user(email=email, password=password, is_verified=True):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                total += 1
                
    # Unverified users
    # unverifiedset = {'unverified@gmail.com'}.union({random_email() for _ in range(2)})
    dataset = {UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                total += 1
    
    dataset = {INACTIVE_VERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password,is_verified=True,
                                                       is_active=False):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                total += 1
    
    dataset = {INACTIVE_UNVERIFIED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_active=False):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                total += 1
    
    dataset = {BANNED_EMAIL}
    createset = dataset - set(current_emails)
    if createset:
        for i in createset:
            if account := await AuthHelper.create_user(email=i, password=password, is_verified=True,
                                                       is_banned=True):
                await account.groups.add(*default_groups)
                _cache_permissions(account.id, default_groups)
                _cache_groups(account.id, default_groups)
                total += 1
    
    return [f'ACCOUNTS_CREATED - {total} new']


async def seed_groups() -> list[str]:
    total = 0
    grouplist = await Group.all().values_list('name', flat=True)
    
    ll = []
    nameset = set(grouplist)
    for name, datamap in GROUP_FIXTURES.items():
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
        
        cachekey = s.redis.GROUP_PERMISSIONS.format(name)
        red.set(cachekey, permset)
        nameset.add(name)
    ll and await Group.bulk_create(ll)
    
    # redis
    cachekey = s.redis.GROUPS
    nameset and red.set(cachekey, nameset)
    
    
    return [f'GROUPS_CREATED - {total} groups']