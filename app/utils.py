import random, secrets, re, jwt, pytz
from urllib.parse import urlencode
from datetime import datetime, timedelta
from typing import Optional, Union
# from eth_account import Account
from functools import reduce
from collections import defaultdict
from http.cookies import SimpleCookie
from pydantic import SecretStr
from fastapi_users.jwt import SecretType, JWT_ALGORITHM



# # TESTME: Untested
# def random_addr() -> str:
#     private_key = f'0x{secrets.token_hex(32)}'
#     account = Account.from_key(private_key)
#     return account.address

# TESTME: Untested
def in_string(phrase, message) -> bool:
    return bool(re.search(phrase, message))

# TESTME: Untested
def timezones() -> list:
    return random.choice([
        '−1200', '−1100', '−1000', '−0930', '−0900', '−0800', '−0700', '−0600', '−0500', '−0400',
        '−0330', '−0300', '−0200', '−0100', '+0000', '+0100', '+0200', '+0300', '+0330', '+0400',
        '+0430', '+0500', '+0530', '+0545', '+0600', '+0630', '+0700', '+0800', '+0845', '+0900',
        '+0930', '+1000', '+1030', '+1100', '+1200', '+1245', '+1300', '+1400'
    ])

# TESTME: Untested
def groupby(key, seq):
    return reduce(lambda grp, val: grp[key(val)].append(val) or grp, seq, defaultdict(list))

# TESTME: Untested
def extract_refresh_token(cookie_data: str, name: Optional[str] = 'refresh_token'):
    """
    Extract the refresh_token value from a cookie string.
    Data extracted from `cookie_data = dict(data.headers)['set-cookie']` where data
    is the return value of a request.
    :param cookie_data:     Cookie string
    :param name:            Refresh token name. Usually just `refresh_token`.
    :return:                str
    """
    cookie = SimpleCookie()
    cookie.load(cookie_data)
    d = {key: val.value for key, val in cookie.items()}
    return d[name]

def truncate_string(datastr: str, *, length: Optional[int] = 30, morestr: Optional[str] = '...',
                    wallet: Optional[bool] = False):
    if not datastr:
        return datastr
    
    if wallet:
        return f'{datastr[:4]}{morestr}{datastr[-4:]}'
    else:
        if len(datastr) > length:
            return f'{datastr[:length]}{morestr}'
        return datastr

# TESTME: Untested
def generate_jwt(payload: dict, secret_key: SecretType, *, expires: Optional[datetime] = None,
                 ttl: Optional[int] = 3600 * 3) -> str:
    """
    Generate a JWT token to be used somewhere.
    :param payload:         Token payload
    :param secret_key:      Secret key
    :param expires:         Expiry date
    :param ttl:             ttl
    :return:                New JWT token
    """
    def _get_secret_value(secret: SecretType) -> str:
        if isinstance(secret, SecretStr):
            return secret.get_secret_value()
        return secret
    
    if not expires:
        expires = datetime.now(tz=pytz.UTC) + timedelta(seconds=ttl)
        
    payload['exp'] = expires
    return jwt.encode(payload, _get_secret_value(secret_key), algorithm=JWT_ALGORITHM)

# TESTME: Untested
def makeurl(base_url, **params: Union[str, int, float]) -> str:
    """
    Create a url
    :param base_url:    Base url
    :param params:      Variables
    :return:            Completed url
    """
    url = f'{base_url}'
    url = params and f'{url}?{urlencode(params)}' or url
    return url

# TESTME: Untested
def namegen(basename: str, nbytes: Optional[int] = 4) -> str:
    return f'{basename}-{secrets.token_hex(nbytes=nbytes)}'

# def flatten_query_result(key: str, query_result: List[dict], unique: bool = True) -> list:
#     """
#     Used for list of dict taken from db results. Get only the values of the key supplied.
#     :param key:             Dict key ot extract.
#     :param query_result:    List of values from the key specified
#     :param unique:          Only return unique values
#     :return:                list
#     """
#     flattened = [i[key] for i in query_result]
#     if unique:
#         return list(set(flattened))
#     return flattened
#
# def get_random_password(length: int = 32):
#     lower = string.ascii_lowercase
#     upper = string.ascii_uppercase
#     num = string.digits
#     symbols = string.punctuation
#     characters = lower + upper + num + symbols
#
#     temp = random.sample(characters, length)
#     return "".join(temp)
#
# def drop_prefixes(data: dict, *, split: str = '__', overwrite: bool = True) -> dict:
#     """
#     Removes prefixes from strings such as those from tortoise relationship fields.
#     E.g. 'tablename__field' becomes 'field' for easier access
#     If the key already exists then a number is appended.
#     :param data:        The dict to clean
#     :param split:       Split the text by this
#     :param overwrite:   If the key already exists then it can be preserved or not
#     :return:            dict
#     """
#     clean = {}
#     done = set()
#     count = 1
#     for key, val in data.items():
#         name = key.split(split)
#         if overwrite or key not in done:
#             clean[name[-1]] = val
#         else:
#             clean[f'{name[-1]}{count}'] = val
#             count += 1
#         done.add(key)
#     return clean
#
# def set_scratch(cachekey, val, ttl: int = 10):
#     """
#     Save data to cache for testing (one-off only)
#     :param cachekey:    Key to save in
#     :param val:         Value of key
#     :param ttl:         Seconds before it's deleted
#     :return:            int
#     """
#     if s.DEBUG:
#         return red.set(cachekey, val, ttl=ttl)
#
# def get_scratch(cachekey):
#     """
#     Read contents of testkey then delete immediately.
#     :param cachekey:    Key to save in
#     :return:            Contents of the key
#     """
#     data = red.get(cachekey)
#     red.delete(cachekey)
#     return data
