import pytest
from pytest import mark

from app import ic
from app.auth import Account, Group


@mark.skip
# @mark.dev
async def dev(initdb):
    # group = await Group.get_or_none(name='EmptyGroup')
    # ic(group)
    # ic(type(group.permissions), group.permissions)

    # accounts = await Account.filter(email='verified@gmail.comx').only('id', 'email')
    # ic(type(accounts), accounts)
    
    account = await Account.get(email='super@gmail.com')
    await account.fetch_related('groups')
    ic(list(account.groups))
