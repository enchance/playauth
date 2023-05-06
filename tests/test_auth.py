import pytest
from collections import Counter
from pytest import mark
from tortoise.query_utils import Prefetch

from app import ic, settings as s
from app.auth import Account, Group
from fixtures import SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL, INACTIVE_VERIFIED_EMAIL, \
    INACTIVE_UNVERIFIED_EMAIL, BANNED_EMAIL



class TestAuth:
    @mark.focus
    async def test_accounts(self, initdb):
        accounts = await Account.all().prefetch_related(
            Prefetch('groups', queryset=Group.all().only('id', 'name'))
        )
        
        for i in accounts:
            # ic(list(i.groups))
            if i.email == SUPER_EMAIL:
                assert Counter([j.name for j in i.groups]) == \
                       Counter(s.DEFAULT_GROUPS + ['AdminGroup'])
                assert i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email in VERIFIED_EMAIL_SET:
                assert Counter([j.name for j in i.groups]) == Counter(s.DEFAULT_GROUPS)
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == UNVERIFIED_EMAIL:
                assert Counter([j.name for j in i.groups]) == Counter(s.DEFAULT_GROUPS)
                assert not i.is_superuser
                assert not i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == INACTIVE_VERIFIED_EMAIL:
                assert Counter([j.name for j in i.groups]) == Counter(s.DEFAULT_GROUPS)
                assert not i.is_superuser
                assert i.is_verified
                assert not i.is_active
                assert i.options.get('lang') ==  'en-us'
                assert not i.is_banned
            elif i.email == INACTIVE_UNVERIFIED_EMAIL:
                assert Counter([j.name for j in i.groups]) == Counter(s.DEFAULT_GROUPS)
                assert not i.is_superuser
                assert not i.is_verified
                assert not i.is_active
                assert not i.is_banned
            elif i.email == BANNED_EMAIL:
                assert Counter([j.name for j in i.groups]) == Counter(s.DEFAULT_GROUPS)
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert i.is_banned
            

class TestGroup:
    async def test_groups(self, initdb):
        assert True