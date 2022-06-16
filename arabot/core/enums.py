from enum import Enum

import disnake


class Color(int, Enum):
    # red = Color.from_rgb(218, 76, 82)
    # yellow = Color.from_rgb(254, 163, 42)
    # green = Color.from_rgb(39, 159, 109)
    blurple = disnake.Color.from_rgb(88, 101, 242)
    green = disnake.Color.from_rgb(87, 242, 135)
    yellow = disnake.Color.from_rgb(254, 231, 92)
    fuchsia = disnake.Color.from_rgb(235, 69, 158)
    red = disnake.Color.from_rgb(237, 66, 69)
    black = disnake.Color.from_rgb(35, 39, 42)


class CustomEmoji:
    KonoDioDa = "<:KonoDioDa:937687826693251102>"
    TeriCelebrate = "<:TeriCelebrate:937695453506596906>"
    FukaWhy = "<:FukaWhy:937695447626182676>"
    TooruWeary = "<:TooruWeary:937695447487774743>"
    KannaPat = "<:KannaPat:937695447718453248>"
    MeiStare = "<:MeiStare:937695447932370994>"
    KannaStare = "<:KannaStare:971188689428443276>"
    CommuThink = "<:ct:973587602798153760>"
    Doubt = "<:doubt:978288495489613854>"


class Category(str, Enum):
    NO_CATEGORY = "No category"
    GENERAL = "General"
    FUN = "Fun"
    META = "Meta"
    LOOKUP = "Lookup"
    COMMUNITY = "Community"
    MODERATION = "Moderation"
    GAMES = "Games"
    WAIFUS = "Reaction pictures"

    def __str__(self) -> str:
        return self.value
