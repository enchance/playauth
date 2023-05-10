from decouple import config



class RedisKeys:
    GROUPS = 'app:groups'
    GROUP_PERMISSIONS = 'group:{}-permissions'
    ACCOUNT_TOKEN = 'user:{}-token'
    ACCOUNT_PERMISSIONS = 'user:{}-permissions'


class BaseSettings:
    APPCODE = 'PLAY'
    ENV = config('ENV')
    TIMEZONE = 'UTC'
    USE_TZ = True
    SITEURL = 'http://localhost:9000'
    
    # Redis
    redis = RedisKeys()
    
    # Account
    DISPLAY_MAX = 4
    PASSWORD_MIN = 12
    
    # Authentication
    DEFAULT_GROUPS = ['AccountGroup']
    SECRET_KEY = config('SECRET_KEY')
    ACCESS_TOKEN_TTL = 3600 * 24 * 3        # sec
    REFRESH_TOKEN_TTL = 3600 * 24 * 7       # sec
    VERIFY_TOKEN_TTL = 3600 * 2             # sec
    RESET_PASSWORD_TOKEN_TTL = 3600         # sec
    REFRESH_TOKEN_REGENERATE = 3600 * 3     # sec
    
    # Routes
    JWT_AUTH_PREFIX = '/auth/jwt'

    # Defaults
    DEFAULT_ACCOUNT_OPTIONS: dict = {
        # Update CacheAccountToRedis if you update this
        'timezone': '+0000',
        'lang': 'en-us',
        'fiat': 'USD',
        'theme': 'base-theme',
        'date_format': '%Y-%m-%d %H:%M:%S',
        'limit_count': 10,
    }
