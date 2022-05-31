from os import getenv as _getenv

from dotenv import load_dotenv as _load_dotenv

__version__ = "6.11.4"

_load_dotenv()
TESTING = bool(_getenv("testing"))
