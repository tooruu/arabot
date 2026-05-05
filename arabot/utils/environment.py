import platform
import sys
from collections.abc import Callable
from importlib.util import find_spec

import disnake

import arabot

type I18N = Callable[[str], str] | Callable[[str, int], str]


def fullqualname(suffix: str | None = None, *, depth: int = 1) -> str:
    """Return fully qualified name for nth call stack frame scope."""
    cf = sys._getframe(depth)
    qp = []
    if cm := cf.f_globals["__name__"]:
        qp.append(cm)
    # Cannot retrieve class name without mentioning `__class__` inside the method
    if (cn := cf.f_code.co_name) != "<module>":
        qp.append(cn)
    if suffix:
        qp.append(suffix)
    return ".".join(qp)


def system_info() -> str:
    match platform.system():
        case "Windows":
            os_info = platform.uname()
            os_ver = f"{os_info.system} {os_info.release} (version {os_info.version})"
        case "Darwin":
            os_info = platform.mac_ver()
            os_ver = f"Mac OSX {os_info[0]} {os_info[1]}"
        case "Linux" if find_spec("distro"):
            from distro import linux_distribution  # type: ignore[import-not-found]

            os_info: str = linux_distribution()
            os_ver = f"{os_info[0]} {os_info[1]}"
        case _:
            os_info = platform.uname()
            os_ver = f"{os_info[0]} {os_info[2]}"
    return f"""Debug Info:

OS version: {os_ver.strip()}
Python executable: {sys.executable}
Python version: {sys.version}
{disnake.__title__.title()} version: {disnake.__version__}
Bot version: {arabot.__version__}
"""
