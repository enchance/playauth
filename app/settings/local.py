from decouple import config
from .base import BaseSettings



class LocalSettings(BaseSettings):
    DEBUG = True
    
    # Account
    PASSWORD_MIN = 4