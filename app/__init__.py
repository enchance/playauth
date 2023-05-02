from icecream import IceCreamDebugger

from .schema import *
from .settings import settings
from .db import register_db



ic = IceCreamDebugger(includeContext=True)
ic.enabled = settings.DEBUG