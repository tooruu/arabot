import random
import re
from asyncio import sleep

import disnake
from disnake.ext import commands

from arabot.core import Ara, Cog, CustomEmoji, pfxless
from arabot.utils import is_in_guild

GULAG = (
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
""".replace("b", "🅱️")
    .replace("c", CustomEmoji.CommuThink)
    .split("\n\n")
)
BAD_GAMES = re.compile(
    r"\b(кс|cs|мм|mm|ра[фс]т|r(af|us)t|фортнайт|fortnite|осу|osu|дест[еи]ни|destiny)\b",
    re.IGNORECASE,
)
AT_SOMEONE = re.compile(r"@some(?:one|body)", re.IGNORECASE)


class Chat(Cog):
    def __init__(self, ara: Ara):
        self.ara = ara
        self._ = lambda key, msg, scope_depth=1: ara.i18n.getl(
            key, msg.guild.preferred_locale, scope_depth + (scope_depth > 0)
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
            msg = await msg.channel.send("***Toki yo tomare!***")
            for i in "Ichi", "Ni", "San", "Yon", "Go":
                await sleep(1.5)
                msg = await msg.edit(f"{msg.content}\n*{i} byou keika*")
            await sleep(1)
            await msg.edit(msg.content + "\nToki wa ugokidasu")
            await sleep(1)
            await msg.delete()
        except disnake.Forbidden:
            return
        finally:
            await msg.channel.set_permissions(msg.guild.default_role, overwrite=old_perms)

    @is_in_guild(433298614564159488)
    @pfxless(regex=BAD_GAMES)
    async def badgames(self, msg: disnake.Message):
        game_name = BAD_GAMES.search(msg.content)[0]
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

    @pfxless(regex=AT_SOMEONE, plain_text_only=False)
    async def somebody(self, msg: disnake.Message):
        if (
            isinstance(msg.channel, disnake.Thread)
            or len(msg.channel.members) <= 1
            or not msg.channel.permissions_for(msg.guild.me).manage_webhooks
        ):
            return

        await msg.delete()
        someone = random.choice(msg.channel.members)
        sender = await self.ara.fetch_webhook("somebody", msg)
        await sender.send(
            AT_SOMEONE.sub(someone.mention, msg.content),
            username=msg.author.display_name,
            avatar_url=msg.author.display_avatar,
            allowed_mentions=disnake.AllowedMentions(users=True),
        )

    @pfxless(regex="^ok$", allow_bots=True)
    async def ok(self, msg: disnake.Message):
        await msg.add_reaction(CustomEmoji.MeiStare)


def setup(ara: Ara):
    ara.add_cog(Chat(ara))
