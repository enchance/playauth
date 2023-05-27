import datetime

import pytest, time
from collections import Counter
from pytest import mark
from tortoise.query_utils import Prefetch
from freezegun import freeze_time

from app import ic, settings as s, red, exceptions as x
from app.auth import Account, Group, Role
from fixtures import SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL, INACTIVE_VERIFIED_EMAIL, \
    INACTIVE_UNVERIFIED_EMAIL, FIXTURE_PASSWORD



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
                assert i.options.get('lang') ==  'en-us'
            elif i.email in VERIFIED_EMAIL_SET:
                assert i.role == starter_role
                assert not i.is_superuser
                assert i.is_verified
                assert i.is_active
                assert i.options.get('lang') ==  'en-us'
            elif i.email == UNVERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert not i.is_verified
                assert i.is_active
                assert i.options.get('lang') ==  'en-us'
            elif i.email == INACTIVE_VERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert i.is_verified
                assert not i.is_active
                assert i.options.get('lang') ==  'en-us'
            elif i.email == INACTIVE_UNVERIFIED_EMAIL:
                assert i.role == starter_role
                assert not i.is_superuser
                assert not i.is_verified
                assert not i.is_active
            

    # @mark.focus
    async def test_cache_group_permissions(self, initdb, group_fixture_data):
        for name in group_fixture_data['groups']:
            cachekey = s.redis.GROUP_PERMISSIONS.format(name)
            cached_perms = red.get(cachekey, set())
            assert Counter(cached_perms) == Counter(group_fixture_data[name])
            
    
    # @mark.focus
    async def test_cached_account_groups(self, initdb):
        account = await Account.get(email=UNVERIFIED_EMAIL).only('id').select_related('role')
        superuser = await Account.get(email=SUPER_EMAIL).only('id').select_related('role')
        
        cachekey = s.redis.ACCOUNT_GROUPS.format(account.id)
        assert Counter(account.role.groups) == Counter(list(red.get(cachekey)))

        cachekey = s.redis.ACCOUNT_GROUPS.format(superuser.id)
        assert Counter(superuser.role.groups) == Counter(list(red.get(cachekey)))
        
    
    # @mark.focus
    async def test_groups(self, account: Account):
        cachekey = s.redis.ACCOUNT_GROUPS.format(account.id)
        red.delete(cachekey)

        start = time.time()                                 # noqa
        dbdata = await account.groups
        dbdur = time.time() - start

        start = time.time()
        cachedata = await account.groups
        cachedur = time.time() - start

        assert dbdur > cachedur
        assert Counter(dbdata) == Counter(cachedata)
        
    
    # @mark.focus
    async def test_permissions(self, account: Account):
        for name in await account.groups:
            red.delete(s.redis.GROUP_PERMISSIONS.format(name))
        
        start = time.time()                                 # noqa
        dbdata = await account.permissions
        dbdur = time.time() - start

        start = time.time()
        cachedata = await account.permissions
        cachedur = time.time() - start

        assert dbdur > cachedur
        assert Counter(dbdata) == Counter(cachedata)
        
    
    @mark.parametrize('args, partials, out', [
        (['AccountGroup'], True, True), (['UploadGroup'], True, True), (['AdminGroup'], True, False),
        (['account.read'], True, True), (['role.read'], True, False),
        (['account.read', 'role.read'], True, True), (['role.read', 'account.read'], True, True),
        (['account.read', 'role.read'], False, False), (['role.read', 'account.read'], False, False),
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
        
    # @mark.focus
    async def test_custom_perms(self, account: Account):
        assert await account.has('perms.attach')
        assert not await account.has('account.update')
        
    @mark.focus
    async def test_change_role(self, account: Account, superuser: Account):
        starter_role = await Role.get_or_none(name='starter')
        admin_role = await Role.get_or_none(name='admin')
        permset = {'avatar.update', 'avatar.read', 'perms.attach', 'account.read'}
        
        assert await account.permissions == permset
        assert account.role == starter_role
        
        with pytest.raises(x.PermissionsException):
            await account.change_role(account, admin_role)
            
        assert await superuser.change_role(account, admin_role) is None
        assert await account.permissions == permset
        assert account.role == starter_role


class TestAuthIntegration:
    # @mark.focus
    async def test_route_login(self, client):
        for i in {SUPER_EMAIL, list(VERIFIED_EMAIL_SET)[0]}:
            data = await client.post('/auth/login',
                                     data=dict(username=i, password=FIXTURE_PASSWORD))
            data = data.json()
            assert Counter(['access_token', 'token_type']) == Counter(data.keys())
            assert data.get('token_type') == 'bearer'
        
        for i in {INACTIVE_VERIFIED_EMAIL, INACTIVE_UNVERIFIED_EMAIL}:
            data = await client.post('/auth/login',
                                     data=dict(username=i, password=FIXTURE_PASSWORD))
            detail = data.json()['detail']
            assert detail == 'LOGIN_BAD_CREDENTIALS'

        data = await client.post('/auth/login',
                                 data=dict(username=UNVERIFIED_EMAIL, password=FIXTURE_PASSWORD))
        detail = data.json()['detail']
        assert detail == 'LOGIN_USER_NOT_VERIFIED'

        data = await client.post('/auth/login',
                                 data=dict(username='ver2@app.co', password=FIXTURE_PASSWORD))
        data = data.json()
        assert Counter(['access_token', 'token_type']) == Counter(data.keys())
        assert data.get('token_type') == 'bearer'

    # @mark.focus
    # async def test_access_token(self, mock_login, mock_token):
    #     with freeze_time('2099-06-01 00:00:00') as ft:
    #         # await _clear_authtoken()
    #         _, atoken1, _type1 = await mock_login()
    #         hashes = {atoken1}
    #         ft.move_to('2022-06-01 00:00:01')
    #         _, atoken2, _type2 = await mock_login()
    #         hashes.add(atoken2)
    #         assert atoken1
    #         assert _type1 == 'bearer' and _type2 == 'bearer'
    #         assert len(hashes) == 2
    
        # with freeze_time('2099-06-01 00:00:00') as ft:
        #     # await _clear_authtoken()
        #     refresh_token, access_token, _ = await mock_login()
        #     hashes = {access_token}
        #
        #     ft.move_to('2022-06-01 00:00:01')
        #     await mock_token(refresh_token, access_token)
        #     # hashes.add(atoken)
        #     # assert _type == 'bearer'
        #     # assert len(hashes) == 2

        # with freeze_time('2022-06-01 00:00:00') as ft:
        #     await _clear_authtoken()
        #     refresh_token, access_token, _ = await mock_login(client)
        #     hashes = {access_token}
        #
        #     ft.move_to('2022-06-02 21:59:59')
        #     atoken, _type = await mock_token(client, refresh_token, access_token)
        #     hashes.add(atoken)
        #     assert _type == 'bearer'
        #     assert len(hashes) == 2
        #
        # with freeze_time('2022-06-01 00:00:00') as ft:
        #     await _clear_authtoken()
        #     refresh_token, access_token, _ = await mock_login(client)
        #     hashes = {access_token}
        #
        #     ft.move_to('2022-06-03 00:00:00')
        #     with pytest.raises(KeyError, match='access_token'):
        #         await mock_token(client, refresh_token, access_token)
        #         hashes.add(atoken)
        #     assert len(hashes) == 1
        #
        # datelist = [
        #     '2022-06-03 00:00:01',
        #     '2022-06-03 00:00:02',
        #     '2022-06-03 00:01:02',
        #     '2022-06-03 01:01:02',
        # ]
        # for date_str in datelist:
        #     with freeze_time('2022-06-01 00:00:00') as ft:
        #         await _clear_authtoken()
        #         refresh_token, access_token, _ = await mock_login(client)
        #         hashes = {access_token}
        #
        #         ft.move_to(date_str)
        #         match = 'Cookie expires date must be greater than the date now'
        #         with pytest.raises(ValueError, match=match):
        #             await mock_token(client, refresh_token, access_token)
        #             hashes.add(atoken)
        #         assert len(hashes) == 1

    # @mark.focus
    # async def test_refresh_token(self, initdb, client, mock_login, mock_token):
    #     # 1 secord before s.REFRESH_TOKEN_CUTOFF
    #     with freeze_time('2099-06-01 00:00:00') as ft:
    #         pass
    #         # account = await Account.get(email=login_dict['username']).values('id')
    #         # userid = account['id']
    #         # await clear_refresh_token(userid)
    #         refresh_token, access_token, _ = await mock_login()
    #
    #         ft.move_to('2099-06-01 00:00:01')
    #         # await mock_token(client, refresh_token, access_token)
    #         # authtoken, userid = await get_authtoken()
    #         # rtoken_redis = await Account.fetch(userid, 'authtoken_token')
    #         # assert rtoken_redis == refresh_token
    #         # assert rtoken_redis == authtoken['refresh_token']
    #         # ic(authtoken)
    #
    #         # ft.move_to('2022-06-02 21:59:59')
    #         # await mock_token(client, refresh_token, access_token)
    #         # authtoken, _ = await get_authtoken()
    #         # rtoken_redis = await Account.fetch(userid, 'authtoken_token')
    #         # assert rtoken_redis == refresh_token
    #         # assert rtoken_redis == authtoken['refresh_token']
    #         # # ic(authtoken)
        

class TestGroup:
    async def test_groups(self, initdb):
        assert True