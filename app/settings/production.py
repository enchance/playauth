from decouple import config
from .base import BaseSettings


class ProductionSettings(BaseSettings):
    DEBUG = False


class StagingSettings(ProductionSettings):
    DEBUG = True