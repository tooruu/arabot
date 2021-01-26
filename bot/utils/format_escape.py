def bold(s) -> str:
    return "**{}**".format(s.replace("*", "\\*"))


def underline(s) -> str:
    return "__{}__".format(s.replace("_", "\\_"))


def italic(s) -> str:
    return "*{}*".format(s.replace("*", "\\*"))


def strikethrough(s) -> str:
    return "~~{}~~".format(s.replace("~", "\\~"))


def dsafe(s) -> str:
    return s.replace("*", "\\*").replace("_", "\\_").replace("~", "\\~").replace("|", "\\|").replace("`", "\\`")
