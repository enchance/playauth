from typing import Annotated
from fastapi import APIRouter, Cookie
from fastapi.responses import JSONResponse
from fastapi_users.authentication.transport.bearer import BearerResponse
from tortoise.exceptions import BaseORMException

from ..auth import *


authrouter = APIRouter()

@authrouter.get('/private', response_model=AccountRes)
async def private(account: Account = Depends(current_user)):
    # ic(account)
    # ic(account.get_options())
    # group = await Group.get_or_none(name='AccountGroup').only('id', 'name')
    # ic(group)
    # ic(group.foo())
    return account


@authrouter.post(f"{s.JWT_AUTH_PREFIX}/refresh")
async def refresh_access_token(strategy: Annotated[JWTStrategy, Depends(get_jwt_strategy)],
                               refresh_token: Annotated[str, Cookie()] = None,
                               account: Account = Depends(current_user)):
    """
    Generates a new access_token if the refresh_token is still fresh.
    A missing refresh_token would warrant the user to login again.
    Refresh toknes are always regenerated but the expires date may remain the same.
    :param account:         Account
    :param strategy:        JWT strat
    :param refresh_token:   Current refresh_token
    :return:                str, New access_token
    """
    # https://github.com/fastapi-users/fastapi-users/discussions/350
    # https://stackoverflow.com/questions/57650692/where-to-store-the-refresh-token-on-the-client#answer-57826596
    if refresh_token is None:
        raise InvalidToken()
    
    cachekey = s.redis.REFRESH_TOKEN.format(refresh_token)
    
    if expdateiso := await AuthHelper.fetch_cached_reftoken(refresh_token):
        diff = AuthHelper.expiry_diff_minutes(expdateiso)
        # ic(f'DIFF: {diff} mins')
        if diff <= 0:
            # TESTME: Untested
            red.delete(cachekey)
            ic(f'LOGOUT: {diff} mins')
            raise InvalidToken()                                                            # Logout
        if diff <= s.REFRESH_TOKEN_REGENERATE / 60:
            # Generate a new random cookie
            # TESTME: Untested
            ic(f'WINDOW REGENERATION: {diff} mins')
            cookiedata = AuthHelper.refresh_cookie_generator()                              # Regenerate cookie
        else:
            # Use the same cookie data
            # TESTME: Untested
            ic(f'FORCED REGENERATION: {diff} mins')
            cookiedata = AuthHelper.refresh_cookie_generator(expiresiso=expdateiso,
                                                             refresh_token=refresh_token)          # Same cookie
    else:
        raise InvalidToken()
    
    # Create new access token
    access_token = await strategy.write_token(account)
    content = BearerResponse(access_token=access_token, token_type='bearer')
    
    # Return new access token with a new refresh token on the side
    response = JSONResponse(content.dict())
    expiresiso = cookiedata.pop('expiresiso')
    response.set_cookie(**cookiedata)
    
    # Save new refresh token to cache
    cachekey = s.redis.REFRESH_TOKEN.format(cookiedata['value'])
    red.set(cachekey, dict(uid=str(account.id), exp=expiresiso))
    
    return response
    
    # return await bearer_transport.get_login_response(token)
    # return await auth_backend.login(strategy, user)