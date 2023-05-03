import re

from disnake import Embed, Message
from disnake.ext.commands import command
from disnake.ext.tasks import loop
from disnake.utils import format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember


class RawDeletedMessage:
    __slots__ = "content", "author", "created_at", "deleted_at"

    def __init__(self, message: Message):
        self.content = message.content
        self.author = message.author
        self.created_at = message.created_at
        self.deleted_at = utcnow()


class MessageSnipe(Cog, category=Category.FUN):
    GROUP_AGE_THRESHOLD = 300  # seconds since last message to end group
    EMPTY = f"{__module__}.empty"
    IGNORED_COMMANDS_PATTERN = r"imp(?:ersonate)?|gp|ghostping|[wi][ca]|c?say"

    def __init__(self, ara: Ara):
        self.ara = ara
        self._cache: dict[int, list[RawDeletedMessage]] = {}
        self.purge_cache.start()

    @Cog.listener()
    async def on_message_delete(self, msg: Message):
        if (
            not msg.author.bot
            and msg.content
            and not (
                (pfx := await self.ara.command_prefix(self.ara, msg))
                and re.match(
                    rf"{re.escape(pfx)}(?:{self.IGNORED_COMMANDS_PATTERN})(?:$|\s)", msg.content, re.I
                )
            )
        ):
            self._cache.setdefault(msg.channel.id, []).append(RawDeletedMessage(msg))

    @loop(minutes=1)
    async def purge_cache(self):
        now = utcnow()
        self._cache = {
            channel_id: messages
            for channel_id, messages in self._cache.items()
            for msg in messages
            if (now - msg.deleted_at).total_seconds() <= 3600
        }

    @command(brief="View deleted messages within the last hour", usage="[member]")
    async def snipe(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        if ctx.channel.id not in self._cache:
            await ctx.send_(MessageSnipe.EMPTY, False)
            return
        msg_pool = list(
            filter(
                lambda m: not member or m.author == member,
                sorted(self._cache[ctx.channel.id], key=lambda msg: msg.created_at)[-10:],
            )
        )
        if not msg_pool:
            await ctx.send_(MessageSnipe.EMPTY, False)
            return
        embed = Embed(color=0x87011D)
        msg_group = []
        last_sender = msg_pool[0].author
        group_tail = msg_pool[0].created_at
        group_start = msg_pool[0].created_at

        for msg in msg_pool:
            if (
                msg.author != last_sender
                or (msg.created_at - group_tail).seconds >= self.GROUP_AGE_THRESHOLD
            ):
                field_name = f"{last_sender.display_name}, {format_dt(group_start, 'R')}:"
                msg_group = "\n".join(msg_group)[-1024:]
                embed.add_field(field_name, msg_group, inline=False)
                msg_group = []
                last_sender = msg.author
                group_start = msg.created_at
            group_tail = msg.created_at
            msg_group.append(msg.content)
        field_name = f"{last_sender.display_name}, {format_dt(group_start, 'R')}:"
        msg_group = "\n".join(msg_group)[-1024:]
        embed.add_field(field_name, msg_group, inline=False)
        while len(embed) > 6000:
            embed.remove_field(0)
        await ctx.send(embed=embed)

    @command(brief="View the last deleted message", usage="[member]")
    async def last(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        if ctx.channel.id not in self._cache:
            await ctx.send_(MessageSnipe.EMPTY, False)
            return
        try:
            last_msg = next(
                filter(
                    lambda m: not member or m.author == member,
                    reversed(self._cache[ctx.channel.id]),
                )
            )
        except StopIteration:
            await ctx.send_(MessageSnipe.EMPTY, False)
            return
        embed = Embed(color=0x87011D)
        field_name = f"{last_msg.author.display_name}, {format_dt(last_msg.created_at, 'R')}:"
        embed.add_field(field_name, last_msg.content[-1024:])
        await ctx.send(embed=embed)

    @purge_cache.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    def cog_unload(self):
        self.purge_cache.cancel()


def setup(ara: Ara):
    ara.add_cog(MessageSnipe(ara))
