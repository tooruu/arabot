# pylint: disable=wrong-import-position
from os import getenv as _getenv
from subprocess import run as _run

from dotenv import load_dotenv as _load_dotenv

__version__ = "8.14.2"

_run(("prisma", "db", "push"), check=True)
_load_dotenv()
TESTING = bool(_getenv("testing"))

from .core import Ara
