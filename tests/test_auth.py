import pytest, time
from collections import Counter
from pytest import mark
from tortoise.query_utils import Prefetch

from app import ic, settings as s, red
from app.auth import Account, Group, Role
from fixtures import SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL, INACTIVE_VERIFIED_EMAIL, \
    INACTIVE_UNVERIFIED_EMAIL, BANNED_EMAIL



class TestAuth:
    # @mark.focus
    async def test_accounts(self, initdb):
        accounts = await Account.all().select_related('role')
        admin_role = await Role.get_or_none(name='admin').only('id')
        starter_role = await Role.get_or_none(name='starter').only('id')
        
        for i in accounts:
            if i.email == SUPER_EMAIL:
                assert i.role == admin_role
                assert i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email in VERIFIED_EMAIL_SET:
                assert i.role == starter_role
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == UNVERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert not i.is_verified
                assert i.is_active
                assert not i.is_banned
                assert i.options.get('lang') ==  'en-us'
            elif i.email == INACTIVE_VERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert i.is_verified
                assert not i.is_active
                assert i.options.get('lang') ==  'en-us'
                assert not i.is_banned
            elif i.email == INACTIVE_UNVERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert not i.is_verified
                assert not i.is_active
                assert not i.is_banned
            elif i.email == BANNED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert i.is_banned
            

    # @mark.focus
    async def test_cached_group_perms(self, initdb, group_fixture_data):
        for name in group_fixture_data['groups']:
            cachekey = s.redis.GROUP_PERMISSIONS.format(name)
            cached_perms = red.get(cachekey, set())
            assert Counter(cached_perms) == Counter(group_fixture_data[name])
            
    
    # @mark.focus
    async def test_groupset(self, account: Account):
        cachekey = s.redis.ACCOUNT_GROUPS.format(account.id)
        red.delete(cachekey)

        start = time.time()                                 # noqa
        dbdata = await account.groupset
        dbdur = time.time() - start

        start = time.time()
        cachedata = await account.groupset
        cachedur = time.time() - start

        assert dbdur > cachedur
        assert Counter(dbdata) == Counter(cachedata)
        
    
    @mark.focus
    async def test_permissionset(self, account: Account):
        for name in await account.groupset:
            red.delete(s.redis.GROUP_PERMISSIONS.format(name))
        
        start = time.time()                                 # noqa
        dbdata = await account.permissionset
        dbdur = time.time() - start

        start = time.time()
        cachedata = await account.permissionset
        cachedur = time.time() - start

        assert dbdur > cachedur
        assert Counter(dbdata) == Counter(cachedata)
        
    
    @mark.parametrize('args, partials, out', [
        (['AccountGroup'], True, True), (['UploadGroup'], True, True), (['AdminGroup'], True, False),
        (['account.read'], True, True), (['group.attach'], True, False),
        (['account.read', 'group.attach'], True, True), (['group.attach', 'account.read'], True, True),
        (['account.read', 'group.attach'], False, False), (['group.attach', 'account.read'], False, False),
        (['AccountGroup', 'account.read'], True, True),
        (['AdminGroup', 'account.read'], True, True), (['account.read', 'AdminGroup'], True, True),
        (['AdminGroup', 'account.read'], False, False),
        (['AdminGroup', 'account.read'], False, False), (['account.read', 'AdminGroup'], False, False),
        (['Foo'], True, False),
        (['Foo', 'account.read'], True, True), (['Foo', 'account.read'], False, False),
        (['xxx.yyy'], True, False),
        (['xxx.yyy', 'account.read'], True, True), (['xxx.yyy', 'account.read'], False, False),
    ])
    # @mark.focus
    async def test_has(self, account: Account, group_fixture_data, args, partials, out):
        assert await account.has(*args, partials=partials) == out


class TestGroup:
    async def test_groups(self, initdb):
        assert True