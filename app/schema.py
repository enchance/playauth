from enum import Enum


class Env(str, Enum):
    development = 'development'
    staging = 'staging'
    production = 'production'