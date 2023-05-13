import pytest
from pytest import mark

from app import ic
from app.auth import Account, Group



# @mark.skip
@mark.dev
async def dev(initdb):
    a = {2, 3, 4, 5}
    account = await Account.get_or_none(email='verified@gmail.com').prefetch_related('groups')
    # groupset = {i.name for i in account.groups}

    # groups = await Group.filter(name__in=['AdminGroup', 'AccountGroup']).values('id', 'name')
    # ic(groups)
    
    # a = a.intersection(b)
    # print(a)
    # print(set() or False)
    # x = {i for i in []}
    # print(type(x), x, len(x))
    
    # group = await Group.get_or_none(name='EmptyGroup')
    # ic(group)
    # ic(type(group.permissions), group.permissions)

    # ic(type(accounts), accounts)
    
    # account = await Account.get(email='super@gmail.com')
    # await account.fetch_related('groups')
    # ic(list(account.groups))
