from enum import IntEnum, StrEnum, unique

import disnake


class Color(IntEnum):
    BLURPLE = disnake.Color.from_rgb(88, 101, 242)
    GREEN = disnake.Color.from_rgb(87, 242, 135)
    YELLOW = disnake.Color.from_rgb(254, 231, 92)
    FUCHSIA = disnake.Color.from_rgb(235, 69, 158)
    RED = disnake.Color.from_rgb(237, 66, 69)
    BLACK = disnake.Color.from_rgb(35, 39, 42)


@unique
class CustomEmoji(StrEnum):
    CommuThink = "<:CommuThink:1263811976874692690>"
    Doubt = "<:Doubt:1263802926694928394>"
    FukaWhy = "<:FukaWhy:1263802934345334847>"
    KannaGun = "<:KannaGun:1263802940771270768>"
    KannaPat = "<:KannaPat:1263802948618555484>"
    KannaStare = "<:KannaStare:1263802954356359262>"
    KonoDioDa = "<:KonoDioDa:1263802959796502682>"
    MeiStare = "<:MeiStare:1263802965895155774>"
    TeriCelebrate = "<:TeriCelebrate:1263802971779629066>"
    TooruWeary = "<:TooruWeary:1263802976997478412>"


@unique
class Category(StrEnum):
    NO_CATEGORY = "No category"
    GENERAL = "General"
    FUN = "Fun"
    META = "Meta"
    LOOKUP = "Lookup"
    COMMUNITY = "Community"
    MODERATION = "Moderation"
    WAIFUS = "Reaction pictures"
    SETTINGS = "Settings"
