import pytest, time, pytz
from datetime import datetime, timedelta
from collections import Counter
from pytest import mark
from tortoise.query_utils import Prefetch
from freezegun import freeze_time
from fastapi_users.jwt import decode_jwt

from app import ic, settings as s, red, exceptions as x
from app.auth import Account, Group, Role, get_jwt_strategy, UserManager, TOKEN_AUD, AuthHelper
from fixtures import SUPER_EMAIL, VERIFIED_EMAIL_SET, UNVERIFIED_EMAIL, INACTIVE_VERIFIED_EMAIL, \
    INACTIVE_UNVERIFIED_EMAIL, FIXTURE_PASSWORD



verified_email = list(VERIFIED_EMAIL_SET)[0]
login_user_dict = dict(username=verified_email, password=FIXTURE_PASSWORD)

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
        
    # @mark.focus
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
            assert data.get('access_token')
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
    async def test_access_token(self, client, mock_login):
        starter_dt = datetime(2099, 6, 1)
        
        # Logging in will always give you a new access_token
        with freeze_time(starter_dt) as ft:
            _, atoken1, _type1 = await mock_login()
            hashes = {atoken1}
            data = decode_jwt(atoken1, s.SECRET_KEY, [TOKEN_AUD])
            token_exp = datetime.utcfromtimestamp(data['exp'])
            assert token_exp == datetime.now() + timedelta(seconds=s.ACCESS_TOKEN_TTL)
            assert _type1 == 'bearer'
            # ic(datetime.utcfromtimestamp(exp).strftime('%Y-%m-%d %H:%M:%S'))
            
            ft.move_to('2022-06-01 00:00:01')
            _, atoken2, _type2 = await mock_login()
            hashes.add(atoken2)
            data = decode_jwt(atoken2, s.SECRET_KEY, [TOKEN_AUD])
            token_exp = datetime.utcfromtimestamp(data['exp'])
            assert token_exp == datetime.now() + timedelta(seconds=s.ACCESS_TOKEN_TTL)
            assert _type2 == 'bearer'
            assert len(hashes) == 2

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
    async def test_restricted(self, account: Account, client, mock_login):
        starter_dt = datetime(2099, 6, 1)
        
        with freeze_time(starter_dt) as ft:
            refresh_token, access_token, _ = await mock_login()
            
            headers = None
            data = await client.get('/private', headers=headers)
            assert data.status_code == 401
            
            headers = dict(authorization=access_token)
            data = await client.get('/private', headers=headers)
            assert data.status_code == 401
            
            # Fresh
            headers = dict(authorization=f'bearer {access_token}')
            data = await client.get('/private', headers=headers)
            data = data.json()
            assert data['email'] == verified_email
            assert data['id'] == str(account.id)

            # Exact exp
            ft.move_to(starter_dt + timedelta(seconds=s.ACCESS_TOKEN_TTL))
            data = await client.get('/private', headers=headers)
            assert data.status_code == 401
            
            # 1 sec early exp
            ft.move_to(starter_dt + timedelta(seconds=s.ACCESS_TOKEN_TTL) - timedelta(seconds=1))
            data = await client.get('/private', headers=headers)
            data = data.json()
            assert data['email'] == verified_email
            assert data['id'] == str(account.id)

            # 1 sec late exp
            ft.move_to(starter_dt + timedelta(seconds=s.ACCESS_TOKEN_TTL) + timedelta(seconds=1))
            data = await client.get('/private', headers=headers)
            assert data.status_code == 401
            
            
    @mark.focus
    async def test_refresh_access_token(self, client, mock_login):
        starter_dt = datetime(2099, 6, 1)
        exp = starter_dt + timedelta(seconds=s.REFRESH_TOKEN_TTL)
        exp_str = AuthHelper.format_expiresiso(exp.isoformat())
    
        with freeze_time(starter_dt) as ft:
            refresh_token, access_token, _ = await mock_login()
            headers = dict(authorization=f'bearer {access_token}')
            cookie = dict(refresh_token=refresh_token)
            
            # No cookie
            data = await client.post(f'{s.JWT_AUTH_PREFIX}/refresh', headers=headers)
            assert data.status_code == 403
            data = data.json()
            assert data['detail'] == 'INVALID_TOKEN'
            
            # Forced regeneration
            data = await client.post(f'{s.JWT_AUTH_PREFIX}/refresh', headers=headers, cookies=cookie)
            data = data.json()
            assert data['access_token']
            assert data['token_type'] == 'bearer'

            # Expired access token
            ft.move_to(starter_dt + timedelta(seconds=s.REFRESH_TOKEN_TTL))
            data = await client.post(f'{s.JWT_AUTH_PREFIX}/refresh', headers=headers, cookies=cookie)
            assert data.status_code == 401

        with freeze_time(starter_dt) as ft:
            refresh_token, access_token, _ = await mock_login()
            headers = dict(authorization=f'bearer {access_token}')
            cookie = dict(refresh_token=refresh_token)

            # Forced regeneration
            data = await client.post(f'{s.JWT_AUTH_PREFIX}/refresh', headers=headers, cookies=cookie)
            data = data.json()
            assert data['access_token']
            assert data['token_type'] == 'bearer'

            # 1 sec early
            # TESTME: Untested

            # 1 sec late
            # TESTME: Untested

            # Deleted cache
            cachekey = s.redis.REFRESH_TOKEN.format(refresh_token)
            red.delete(cachekey)
            data = await client.post(f'{s.JWT_AUTH_PREFIX}/refresh', headers=headers, cookies=cookie)
            assert data.status_code == 403
            data = data.json()
            assert data['detail'] == 'INVALID_TOKEN'


class TestGroup:
    async def test_groups(self, initdb):
        assert True