import re as _re
from collections.abc import Iterable as _Iterable


def bold(s: str) -> str:
    return "**{}**".format(s.replace("*", r"\*"))


def underline(s: str) -> str:
    return "__{}__".format(s.replace("_", r"\_"))


def italic(s: str) -> str:
    return "*{}*".format(s.replace("*", r"\*"))


def strikethrough(s: str) -> str:
    return "~~{}~~".format(s.replace("~", r"\~"))


def dsafe(s: str) -> str:
    return _re.sub(r"([*_~|`])", r"\\\1", s)


def spoiler(s: str) -> str:
    return "||{}||".format(s.replace("|", r"\|"))


def mono(s: str) -> str:
    return "`{}`".format(s.replace("`", r"\`"))


def codeblock(s: str, lang: str = "") -> str:
    return "```{}\n{}\n```".format(lang, s.replace("```", "``\u200b`"))


def unping(s: str) -> str:
    return s.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")


def repchars(s: str, chars: str, rep: str = "") -> str:
    return _re.sub(f"[{_re.escape(chars)}]", rep, s)


def humanjoin(s: _Iterable[str], /) -> str:
    return " and ".join(", ".join(s).rsplit(", ", 1))


cb = code = codeblock
