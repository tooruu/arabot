import re as _re

CUSTOM_EMOJI_RE = _re.compile(r"<(?P<animated>a?):(?P<name>\w{2,32}):(?P<id>\d{17,20})>", _re.ASCII)
