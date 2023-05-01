from decouple import config

from .local import *
from .production import *


class Settings:
    def __new__(cls, *, env: str):
        if env == 'development':
            return LocalSettings()
        elif env == 'staging':
            return StagingSettings()
        else:
            return ProductionSettings()
        
        
ENV = config('ENV', default='production')
settings = Settings(env=ENV)