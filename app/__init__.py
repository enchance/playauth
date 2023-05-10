from icecream import IceCreamDebugger

from .schemas import *
from .settings import settings
from .db import register_db, red



ic = IceCreamDebugger(includeContext=True)
ic.enabled = settings.DEBUG