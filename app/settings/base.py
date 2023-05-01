from decouple import config


class BaseSettings:
    TIMEZONE = 'UTC'
    USE_TZ = True