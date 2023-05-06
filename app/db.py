from fastapi import FastAPI
from tortoise.contrib.fastapi import register_tortoise

from .settings import settings as s
from decouple import config



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