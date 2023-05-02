from decouple import config


class BaseSettings:
    APPCODE = 'PLAY'
    ENV = config('ENV')
    TIMEZONE = 'UTC'
    USE_TZ = True
    SITEURL = 'http://localhost:9000'
    
    # Account
    DISPLAY_MAX = 4
    PASSWORD_MIN = 12
    
    # Authentication
    SECRET_KEY = config('SECRET_KEY')
    ACCESS_TOKEN_TTL = 3600                 # sec
    REFRESH_TOKEN_TTL = 3600 * 24 * 7       # sec
    VERIFY_TOKEN_TTL = 3600 * 2             # sec
    RESET_PASSWORD_TOKEN_TTL = 3600         # sec