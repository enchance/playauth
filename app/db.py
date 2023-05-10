from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise
from limeutils import Red
from decouple import config

from .settings import settings as s



# Redis
REDIS_TTL = 3600 * 24 * 15
REDIS_CONFIG: dict = {
    'host': config('REDIS_HOST', 'localhost'),
    'port': config('REDIS_PORT', 6379),
    # 'password': os.getenv('REDIS_PASSWORD'),
}
REDIS_CUSTOM = {
    'pre': s.APPCODE,
    'ver': 'v1',
    'ttl': REDIS_TTL,
}
red = Red(**REDIS_CONFIG, **REDIS_CUSTOM)

# Postgres
DATABASE_URL = config('DATABASE_URL_DEV')
DATABASE_MODELS = [
    'aerich.models',
    'app.auth.models',
]
TORTOISE_ORM = {
    'connections': dict(default=DATABASE_URL),
    'apps': {
        'models': {
            'models': DATABASE_MODELS,
            'default_connection': 'default'
        }
    },
    'timezone': s.TIMEZONE,
    'use_tz': s.USE_TZ,
    'echo': True,
}


def register_db(app: FastAPI) -> None:
    d = dict(config=TORTOISE_ORM)
    if s.DEBUG:
        d['add_exception_handlers'] = True
    
    register_tortoise(app, **d)