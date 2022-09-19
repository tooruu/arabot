from enum import Enum

import disnake


class Color(int, Enum):
    blurple = disnake.Color.from_rgb(88, 101, 242)
    green = disnake.Color.from_rgb(87, 242, 135)
    yellow = disnake.Color.from_rgb(254, 231, 92)
    fuchsia = disnake.Color.from_rgb(235, 69, 158)
    red = disnake.Color.from_rgb(237, 66, 69)
    black = disnake.Color.from_rgb(35, 39, 42)


class CustomEmoji:
    CommuThink = "<:ct:973587602798153760>"
    Doubt = "<:doubt:978288495489613854>"
    FukaWhy = "<:FukaWhy:937695447626182676>"
    KannaGun = "<:KannaGun:1012630928687894630>"
    KannaPat = "<:KannaPat:937695447718453248>"
    KannaStare = "<:KannaStare:971188689428443276>"
    KonoDioDa = "<:KonoDioDa:937687826693251102>"
    MeiStare = "<:MeiStare:937695447932370994>"
    TeriCelebrate = "<:TeriCelebrate:937695453506596906>"
    TooruWeary = "<:TooruWeary:937695447487774743>"


class Category(str, Enum):
    NO_CATEGORY = "No category"
    GENERAL = "General"
    FUN = "Fun"
    META = "Meta"
    LOOKUP = "Lookup"
    COMMUNITY = "Community"
    MODERATION = "Moderation"
    WAIFUS = "Reaction pictures"
    SETTINGS = "Settings"

    def __str__(self) -> str:
        return self.value
