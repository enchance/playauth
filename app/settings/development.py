from decouple import config
from .base import BaseSettings



class DevSettings(BaseSettings):
    DEBUG = True