from os import getenv as _getenv
from subprocess import run as _run

from dotenv import load_dotenv as _load_dotenv

_run(("prisma", "db", "push"), check=True)  # Migrate MongoDB
from .core import Ara

__version__ = "8.0.0-alpha2"

_load_dotenv()
TESTING = bool(_getenv("testing"))
