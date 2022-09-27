from collections import defaultdict
from datetime import datetime

from disnake import Embed, Member
from disnake.ext.commands import command
from disnake.ext.tasks import loop
from disnake.utils import format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember


class NicknameSnipe(Cog, category=Category.FUN):
    EMPTY_SNIPE_MSG = "No nicknames found for {}"
    MAX_NICKS = 6
    PURGE_AFTER_DAYS = 7

    def __init__(self, ara: Ara):
        self.ara = ara
        self._cache: dict[int, dict[int, list[tuple[str, datetime]]]] = defaultdict(
            lambda: defaultdict(list)
        )
        self.purge_cache.start()

    @Cog.listener()
    async def on_member_update(self, before: Member, after: Member):
        if before.display_name == after.display_name:
            return
        now = utcnow()
        history = self._cache[before.guild.id][before.id]
        if not history:
            # We don't know when the `before` nick was set but we can't use None
            # because we still need to track days to later purge this nick from cache.
            # Command is supposed to check if the first two datetimes are the same,
            # and replace the first one with something more meaningful than current time.
            history.append((before.display_name, now))
        history.append((after.display_name, now))

    @loop(hours=1)
    async def purge_cache(self):
        now = utcnow()
        self._cache = defaultdict(
            lambda: defaultdict(list),
            {
                guild_id: defaultdict(
                    list,
                    {
                        member_id: [
                            (nick, changed_at)
                            for nick, changed_at in nicks[-self.MAX_NICKS:]
                            if (now - changed_at).days < self.PURGE_AFTER_DAYS  # fmt: skip
                        ]
                        for member_id, nicks in members.items()
                        if nicks
                    },
                )
                for guild_id, members in self._cache.items()
                if members
            },
        )

    @command(aliases=["sn", "ns"], brief="View recent nick history of a user")
    async def nicksnipe(self, ctx: Context, *, member: AnyMember):
        if member is None:
            await ctx.send_("User not found")
            return

        history = self._cache.get(ctx.guild.id, {}).get(member.id, [])[:]
        if not history:
            await ctx.send(ctx._(self.EMPTY_SNIPE_MSG).format(member.display_name))
            return

        if history[0][1] == history[1][1]:
            history[0] = (history[0][0], None)  # Check the comment in `on_member_update`

        embed = Embed()
        for nick, changed_at in history[-self.MAX_NICKS :]:  # noqa: E203
            when = format_dt(changed_at, "R") if changed_at else ctx._("Sometime in the past")
            embed.add_field(when, nick, inline=False)

        await ctx.send(embed=embed)

    @purge_cache.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    def cog_unload(self):
        self.purge_cache.cancel()


def setup(ara: Ara):
    ara.add_cog(NicknameSnipe(ara))
