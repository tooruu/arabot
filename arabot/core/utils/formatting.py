import re as _re
from datetime import datetime as _datetime
from typing import Any as _Any


def bold(s: _Any) -> str:
    return "**{}**".format(str(s).replace("*", r"\*"))


def underline(s: _Any) -> str:
    return "__{}__".format(str(s).replace("_", r"\_"))


def italic(s: _Any) -> str:
    return "*{}*".format(str(s).replace("*", r"\*"))


def strikethrough(s: _Any) -> str:
    return "~~{}~~".format(str(s).replace("~", r"\~"))


def dsafe(s: _Any) -> str:
    return _re.sub(r"([*_~|`])", r"\\\1", str(s))


def spoiler(s: _Any) -> str:
    return "||{}||".format(str(s).replace("|", r"\|"))


def mono(s: _Any) -> str:
    return "`{}`".format(str(s).replace("`", r"\`"))


def codeblock(s: _Any, lang: str = "") -> str:
    return "```{}\n{}\n```".format(lang, str(s).replace("```", "``\u200b`"))


def unping(s: _Any) -> str:
    return str(s).replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")


cb = code = codeblock


class DTFormat:
    ST = SHORT_TIME = "t"  # 16:20
    LT = LONG_TIME = "T"  # 16:20:30
    SD = SHORT_DATE = "d"  # 20/04/2021
    LD = LONG_DATE = "D"  # 20 April 2021
    SDT = SHORT_DATE_TIME = "f"  # 20 April 2021 16:20
    LDT = LONG_DATE_TIME = "F"  # Tuesday, 20 April 2021 16:20
    R = RELATIVE = "R"  # 2 months ago


def dtformat(timestamp: _datetime | int | float, fmt: DTFormat = DTFormat.RELATIVE) -> str:
    if isinstance(timestamp, _datetime):
        timestamp = timestamp.timestamp()
    return f"<t:{int(timestamp)}:{fmt}>"
