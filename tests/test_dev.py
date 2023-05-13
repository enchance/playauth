import pytest
from pytest import mark

from app import ic
from app.auth import Account, Group



# @mark.skip
@mark.dev
async def test_dev(initdb):
    a = {2, 3, 4, 5}
    
    # a = a.intersection(b)
    # print(a)
    # print(set() or False)
    # x = {i for i in []}
    # print(type(x), x, len(x))
    
    # group = await Group.get_or_none(name='EmptyGroup')
    # ic(group)
    # ic(type(group.permissions), group.permissions)

    # accounts = await Account.filter(email='verified@gmail.comx').only('id', 'email')
    # ic(type(accounts), accounts)
    
    # account = await Account.get(email='super@gmail.com')
    # await account.fetch_related('groups')
    # ic(list(account.groups))
