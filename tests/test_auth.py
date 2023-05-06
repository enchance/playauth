import pytest
from pytest import mark

from app import ic
from app.auth import Account
from fixtures import SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL, INACTIVE_VERIFIED_EMAIL, \
    INACTIVE_UNVERIFIED_EMAIL, BANNED_EMAIL



class TestAuth:
    # @mark.focus
    async def test_accounts(self, initdb):
        accounts = await Account.all()
        for i in accounts:
            if i.email == SUPER_EMAIL:
                # TODO: Check groups once integrated
                assert i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email in VERIFIED_EMAIL_SET:
                # TODO: Check groups once integrated
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == UNVERIFIED_EMAIL:
                # TODO: Check groups once integrated
                assert not i.is_superuser
                assert not i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == INACTIVE_VERIFIED_EMAIL:
                # TODO: Check groups once integrated
                assert not i.is_superuser
                assert i.is_verified
                assert not i.is_active
                assert i.options.get('lang') ==  'en-us'
                assert not i.is_banned
            elif i.email == INACTIVE_UNVERIFIED_EMAIL:
                # TODO: Check groups once integrated
                assert not i.is_superuser
                assert not i.is_verified
                assert not i.is_active
                assert not i.is_banned
            elif i.email == BANNED_EMAIL:
                # TODO: Check groups once integrated
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert i.is_banned
            

class TestGroup:
    async def test_groups(self, initdb):
        assert True