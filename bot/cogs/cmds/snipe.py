from datetime import datetime
from discord import Embed
from discord.ext.commands import command, Cog
from discord.ext.tasks import loop
from utils.converters import FindMember


class RawDeletedMessage:
    __slots__ = "content", "author", "created_at", "deleted_at"

    def __init__(self, message):
        self.content = message.content
        self.author = message.author
        self.created_at = message.created_at
        self.deleted_at = datetime.utcnow()


class Snipe(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client
        self.log = {}
        self.purge.start()

    @Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.author.bot and msg.content:
            self.log.setdefault(msg.channel, []).append(RawDeletedMessage(msg))

    @loop(minutes=1)
    async def purge(self):
        now = datetime.utcnow()
        for channel in self.log:
            for message in self.log[channel]:
                if (now - message.deleted_at).seconds > 3600:
                    self.log[channel].remove(message)

    @command(brief="| View deleted messages within the last hour")
    async def snipe(self, ctx, target: FindMember = None):
        if self.log.get(ctx.channel):
            msg_pool = sorted(self.log[ctx.channel], key=lambda message: message.created_at)
            if target:
                msg_pool = [m for m in msg_pool if m.author == target]
            msg_pool = msg_pool[:10]
            if msg_pool:
                embed = Embed(color=0x87011D)
                now = datetime.utcnow()
                msg_group = []
                last_sender = msg_pool[0].author
                group_tail = msg_pool[0].created_at
                group_start = msg_pool[0].created_at
                GROUP_AGE_THRESHOLD = 300

                for msg in msg_pool:
                    if msg.author != last_sender or (msg.created_at - group_tail).seconds >= GROUP_AGE_THRESHOLD:
                        title = f"{last_sender.display_name}, {(now - group_start).seconds // 60}m ago:"
                        embed.add_field(name=title, value="\n".join(msg_group)[-1024:], inline=False)
                        msg_group = []
                        last_sender = msg.author
                        group_start = msg.created_at
                    group_tail = msg.created_at
                title = f"{last_sender.display_name}, {(now - group_start).seconds // 60}m ago:"
                embed.add_field(name=title, value="\n".join(msg_group)[-1024:], inline=False)
                while len(embed) > 6000:
                    del embed.fields[0]
                try:
                    await ctx.send(embed=embed)
                except Exception:
                    await ctx.send("I was coded by a retard so there you have an ~~unhandled exception~~ error")
                return

        await ctx.send("Nothing to snipe here :eyes:")

    @purge.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()


def cog_unload(self):
    self.purge.cancel()


def setup(client):
    client.add_cog(Snipe(client))
