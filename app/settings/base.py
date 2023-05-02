from decouple import config


class BaseSettings:
    ENV = config('ENV')
    TIMEZONE = 'UTC'
    USE_TZ = True
    
    # Account
    DISPLAY_MAX = 4
    