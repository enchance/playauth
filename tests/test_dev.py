import pytest
from pytest import mark

from app import ic
from app.auth import Account, Group



# @mark.skip
@mark.dev
async def test_dev(initdb):
    a = {2, 3, 4, 5}
    account = await Account.get_or_none(email='verified@gmail.com').select_related('role')
    # superuser = await Account.get(email='super@gmail.com').select_related('role')
    # groupset = {i.name for i in account.groups}
    
    # ic({1, 2} == {2, 1})
    
    # custom_perms = account.perms or []
    # ic(type(custom_perms), custom_perms)
    # account.perms = {'aaa.bbb'}
    # await account.save(update_fields=['perms'])
    # custom_perms = account.perms
    # ic(type(custom_perms), custom_perms)

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
    
    # await account.fetch_related('groups')
    # ic(account.role)
