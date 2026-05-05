import re

CUSTOM_EMOJI_RE = re.compile(r"<(?P<animated>a?):(?P<name>\w{2,32}):(?P<id>\d{17,20})>", re.ASCII)
