from os import getenv
from subprocess import run

from dotenv import load_dotenv

__all__ = [
    "__version__",
    "Ara",
    "TESTING",
]

__version__ = "8.19.1"

run(("prisma", "db", "push"), check=True)
load_dotenv()
TESTING = bool(getenv("TESTING"))

# Load up bot after the code above has been executed
from .core import Ara  # noqa: E402
