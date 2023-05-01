from decouple import config

from .development import *
from .production import *


class Settings:
    def __new__(cls, *, env: str):
        if env in ['development', 'develop', 'dev']:
            return DevSettings()
        elif env in ['staging', 'stage']:
            return StagingSettings()
        else:
            return ProductionSettings()
        
        
ENV = config('ENV', default='production')
settings = Settings(env=ENV)