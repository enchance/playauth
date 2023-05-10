import logging, pytz
from datetime import datetime
from logging.handlers import RotatingFileHandler
from fastapi.logger import logger
from icecream import IceCreamDebugger

from .schemas import *
from .settings import settings
from .db import register_db, red



# Icecream
ic = IceCreamDebugger(includeContext=True)
ic.enabled = settings.DEBUG


# Logs
now = datetime.now(pytz.timezone('UTC'))
formatter = '[%(asctime)s] %(levelname)s %(funcName)s:%(lineno)d - %(message)s'
formatter = logging.Formatter(formatter)

warning_handler = RotatingFileHandler(f'logs/{now:%Y-%m} warning.log',
                                      maxBytes=500000, backupCount=10)
warning_handler.setFormatter(formatter)
warning_handler.setLevel(logging.WARNING)
logger.addHandler(warning_handler)

critical_handler = RotatingFileHandler(f'logs/{now:%Y-%m} critical.log',
                                       maxBytes=500000, backupCount=10)
critical_handler.setFormatter(formatter)
critical_handler.setLevel(logging.CRITICAL)
logger.addHandler(critical_handler)