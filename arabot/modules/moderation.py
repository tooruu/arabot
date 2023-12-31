import asyncio
import re
from contextlib import suppress

import disnake
from disnake.ext.commands import bot_has_permissions, command, has_permissions
from disnake.utils import format_dt

from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyMsgChl


class Moderation(Cog, category=Category.MODERATION, command_attrs=dict(hidden=True)):
    def __init__(self, ara: Ara):
        self.ara = ara

    @has_permissions(manage_messages=True)
    @bot_has_permissions(manage_messages=True)
    @command(aliases=["d"])
    async def purge(self, ctx: Context, amount: int | None = None):
        if amount:
            await ctx.channel.purge(limit=amount + 1)
        else:
            await ctx.message.delete()

    @has_permissions(manage_messages=True)
    @command()
    async def csay(self, ctx: Context, channel: AnyMsgChl, *, text: str):
        if not channel:
            await ctx.send_("channel_not_found", False)
            return
        am = disnake.AllowedMentions(users=True)
        silent = disnake.MessageFlags(
            suppress_notifications=ctx.message.flags.suppress_notifications
        )
        msg = await channel.send(text, allowed_mentions=am, flags=silent)
        await ctx.reply(msg.jump_url)

    @has_permissions(moderate_members=True)
    @bot_has_permissions(moderate_members=True)
    @command(brief="Timeout next user who sends message that matches regular expression")
    async def waitto(self, ctx: Context, mute_duration: float | None = 60, *, pattern: str):
        with suppress(disnake.Forbidden):
            await ctx.message.add_reaction(CustomEmoji.KannaStare)

        def bad_msg_check(msg: disnake.Message) -> bool:
            return bool(
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
                await bad_msg.reply_ping(
                    ctx._("user_muted_until", False).format(
                        bad_msg.author.mention, format_dt(bad_msg.author.current_timeout, style="F")
                    )
                )
                await bad_msg.add_reaction("🤫")
        finally:
            with suppress(disnake.NotFound):
                await ctx.message.remove_reaction(CustomEmoji.KannaStare, ctx.me)


def setup(ara: Ara):
    ara.add_cog(Moderation(ara))
