# pylint: disable=wrong-import-position
from os import getenv as _getenv
from subprocess import run as _run

from dotenv import load_dotenv as _load_dotenv

__version__ = "8.0.0-beta1"

_load_dotenv()
TESTING = bool(_getenv("testing"))

if not _getenv("HEROKU_APP_ID"):
    _run(("prisma", "db", "push"), check=True)

from .core import Ara
