from os import getenv

from dotenv import load_dotenv

__version__ = "8.23.7"

load_dotenv()
TESTING = bool(getenv("TESTING"))

# Load up bot after the code above has been executed
from .core import Ara  # noqa: E402, F401
