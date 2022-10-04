import re
from asyncio import sleep

import disnake
from disnake.ext import commands

from arabot.core import Ara, Cog, CustomEmoji, pfxless
from arabot.utils import is_in_guild

GULAG = (
    (
        """
bbbbbbbbbbbbbbb
bbbbbbbbcbbbbbb
bbbbbccbccbbbbb
bbbbcccbbccbbbb
bbbccccbbbccbbb
bccccccbbbbccbb
bbccbcccbbbcccb

bbbbbbcccbbbccb
bbbbbbbcccbcccb
bbbbcbbbcccccbb
bbbcccbbbcccbbb
bcccbccccccccbb
bccbbbcccbbccbb
bbbbbbbbbbbbbbb
"""
    )
    .replace("b", "🅱️")
    .replace("c", CustomEmoji.CommuThink)
    .split("\n\n")
)


class Chat(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara
        self._ = lambda key, msg, scope_depth=1: ara.i18n.getl(
            self.ara.i18n.getl(key, msg.guild.preferred_locale, scope_depth + (scope_depth > 0))
        )

    @commands.check(lambda msg: len(msg.content) < 15)
    @pfxless(chance=0.5)
    async def who(self, msg: disnake.Message):
        await msg.channel.send(self._("ur_mom", msg))

    @commands.check(lambda msg: len(msg.content) < 20)
    @pfxless(regex=r"^([ıi](['’]?m|\sam)\s)+((an?|the)\s)?\w+$", chance=0.5)
    async def im_hi(self, msg: disnake.Message):
        regex = re.match(r"(?:[ıi](?:['’]?m|\sam)\s)+(?:(?:an?|the)\s)?(\w+)", msg.content.lower())
        await msg.channel.send(f"hi {regex[1]}")

    @pfxless(regex=";-;")
    async def cry(self, msg: disnake.Message):
        await msg.reply(self._("uncry", msg) + f" {CustomEmoji.KannaPat}")

    @commands.cooldown(1, 60, commands.BucketType.channel)
    @pfxless()
    async def za_warudo(self, msg: disnake.Message):
        old_perms = msg.channel.overwrites_for(msg.guild.default_role)
        temp_perms = msg.channel.overwrites_for(msg.guild.default_role)
        temp_perms.send_messages = False
        try:
            await msg.channel.set_permissions(msg.guild.default_role, overwrite=temp_perms)
            await msg.channel.send(CustomEmoji.KonoDioDa)
            msgs = [await msg.channel.send("***Toki yo tomare!***")]
            for i in "Ichi", "Ni", "San", "Yon", "Go":
                await sleep(1.5)
                msgs.append(await msg.channel.send(f"*{i} byou keika*"))
            await sleep(1)
            msgs.append(await msg.channel.send("Toki wa ugoki dasu"))
            await sleep(1)
            await msg.channel.delete_messages(msgs)
        except disnake.Forbidden:
            return
        finally:
            await msg.channel.set_permissions(msg.guild.default_role, overwrite=old_perms)

    BAD_GAMES = re.compile(
        r"\b(кс|cs|мм|mm|ра[фс]т|r(af|us)t|фортнайт|fortnite|осу|osu|дест[еи]ни|destiny)\b",
        re.IGNORECASE,
    )

    @is_in_guild(433298614564159488)
    @pfxless(regex=BAD_GAMES)
    async def badgames(self, msg: disnake.Message):
        game_name = self.BAD_GAMES.search(msg.content)[0]
        message = f"{game_name}? ебать ты гей 🤡"
        try:
            await msg.author.timeout(duration=20, reason="геюга ебаная")
        except disnake.Forbidden:
            pass
        else:
            message += ", иди в мут нахуй"
        await msg.channel.send(message)

    @commands.cooldown(1, 60, commands.BucketType.channel)
    @pfxless(regex=r"\b(communis[mt]|gulag)\b")
    async def communism(self, msg: disnake.Message):
        for camp in GULAG:
            await msg.channel.send(camp)


def setup(ara: Ara):
    ara.add_cog(Chat(ara))
