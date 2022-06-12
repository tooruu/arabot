import re as _re

CUSTOM_EMOJI_RE = _re.compile(r"<a?:\w{2,32}:\d{17,20}>", _re.ASCII)
