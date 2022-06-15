import re as _re
from typing import Any as _Any
from typing import Iterable as _Iterable


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


def repchars(s: str, chars: str, rep: str = "") -> str:
    return _re.sub(f"[{_re.escape(chars)}]", rep, s)


def humanjoin(s: _Iterable[str], /):
    return " and ".join(", ".join(s).rsplit(", ", 1))


cb = code = codeblock
