import asyncio
import re
from contextlib import suppress

import disnake
from disnake.ext.commands import command, has_permissions

from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyTChl


class Moderation(Cog, category=Category.MODERATION, command_attrs=dict(hidden=True)):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["d"])
    @has_permissions(manage_messages=True)
    async def purge(self, ctx: Context, amount: int | None = None):
        if amount:
            await ctx.channel.purge(limit=amount + 1)
        else:
            await ctx.message.delete()

    @command()
    @has_permissions(manage_messages=True)
    async def csay(self, ctx: Context, channel: AnyTChl, *, text: str):
        await ctx.message.delete()
        if channel:
            await channel.send_ping(text)

    @command()
    @has_permissions(moderate_members=True)
    async def waitto(self, ctx: Context, mute_duration: float | None = 60, *, pattern: str):
        with suppress(disnake.Forbidden):
            await ctx.message.add_reaction(CustomEmoji.KannaStare)

        def bad_msg_check(msg: disnake.Message):
            return (
                msg.channel == ctx.channel
                and not msg.author.bot
                and ctx.author.top_perm_role > msg.author.top_perm_role
                and re.search(pattern, msg.content, re.IGNORECASE)
            )

        try:
            bad_msg: disnake.Message = await ctx.ara.wait_for(
                "message", check=bad_msg_check, timeout=300
            )
        except asyncio.TimeoutError:
            return
        else:
            with suppress(disnake.Forbidden):
                await bad_msg.author.timeout(duration=mute_duration)
                await bad_msg.reply_ping(f"{bad_msg.author.mention} has been muted for 1 minute")
                await bad_msg.add_reaction("🤫")
        finally:
            with suppress(disnake.NotFound):
                await ctx.message.remove_reaction(CustomEmoji.KannaStare, ctx.me)


def setup(ara: Ara):
    ara.add_cog(Moderation(ara))
