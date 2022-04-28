def bold(s: str) -> str:
    return "**{}**".format(s.replace("*", r"\*"))


def underline(s: str) -> str:
    return "__{}__".format(s.replace("_", r"\_"))


def italic(s: str) -> str:
    return "*{}*".format(s.replace("*", r"\*"))


def strikethrough(s: str) -> str:
    return "~~{}~~".format(s.replace("~", r"\~"))


def dsafe(s: str) -> str:
    return (
        s.replace("*", r"\*")
        .replace("_", r"\_")
        .replace("~", r"\~")
        .replace("|", r"\|")
        .replace("`", r"\`")
    )


def spoiler(s: str) -> str:
    return "||{}||".format(s.replace("|", r"\|"))


def mono(s: str) -> str:
    return "`{}`".format(s.replace("`", r"\`"))


def code(s: str, lang: str = "") -> str:
    return "```{}\n{}\n```".format(lang, s.replace("```", "``\u200b`"))


def unping(s: str) -> str:
    return s.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")


codeblock = cb = code
