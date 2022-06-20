from os import getenv as _getenv

from dotenv import load_dotenv as _load_dotenv

from .core import Ara

__version__ = "7.7.3"

_load_dotenv()
TESTING = bool(_getenv("testing"))
