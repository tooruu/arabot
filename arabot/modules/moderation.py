import asyncio
import re
from contextlib import suppress

import disnake
from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyTChl
from disnake.ext.commands import command, has_permissions


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
            await channel.send(text)

    @command()
    @has_permissions(manage_channels=True)
    async def mutenext(self, ctx: Context, timeout: int | None = 60, *, pattern: str):
        await ctx.message.add_reaction(CustomEmoji.KannaStare)

        def bad_msg_check(msg: disnake.Message):
            return (
                msg.channel == ctx.channel
                and not msg.author.bot
                and re.search(pattern, msg.content, re.IGNORECASE)
            )

        try:
            bad_msg = await ctx.ara.wait_for("message", check=bad_msg_check, timeout=timeout)
        except asyncio.TimeoutError:
            return
        else:
            with suppress(disnake.Forbidden):
                await bad_msg.add_reaction("🤫")
            await bad_msg.temp_channel_mute_author(
                success_msg=lambda: bad_msg.reply(
                    f"{bad_msg.author.mention} has been muted for 1 minute"
                ),
                failure_msg=True,
            )
        finally:
            with suppress(disnake.NotFound):
                await ctx.message.remove_reaction(CustomEmoji.KannaStare, ctx.me)


def setup(ara: Ara):
    ara.add_cog(Moderation(ara))
