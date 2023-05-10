import pytest
from pytest import mark

from app import ic
from app.auth import Account, Group


@pytest.skip
# @mark.dev
async def test_dev(initdb):
    accounts = await Account.filter(email='verified@gmail.comx').only('id', 'email')
    ic(type(accounts), accounts)