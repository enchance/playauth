from decouple import config
from .base import BaseSettings



class LocalSettings(BaseSettings):
    DEBUG = True
    
    # Account
    PASSWORD_MIN = 4
    
    # Authentication
    ACCESS_TOKEN_TTL = 60 * 60 * 24
    # ACCESS_TOKEN_TTL = 60 * 30
    # ACCESS_TOKEN_TTL = 1