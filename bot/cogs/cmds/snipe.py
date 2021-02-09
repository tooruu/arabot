from discord.ext.commands import command, Cog
from discord.ext.tasks import loop
from datetime import datetime
from discord import Embed
from utils.converters import FindMember


class Snipe(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client
        self.log = {}
        self.purge.start()

    @Cog.listener()
    async def on_message_delete(self, msg):
        if not msg.author.bot:
            self.log.setdefault(msg.channel, {})[msg] = datetime.now()

    @loop(minutes=1)
    async def purge(self):
        now = datetime.now()
        for channel in self.log:
            for message, deleted_at in self.log[channel].items():
                if (now - deleted_at).seconds > 3600:
                    del self.log[channel][message]

    @command(brief="| View deleted messages within the last hour")
    async def snipe(self, ctx, target: FindMember = None):
        if self.log.get(ctx.channel):
            embed = Embed()
            now = datetime.now()
            last_sender = None
            msg_group = []
            group_timestamp = None
            msg_pool = sorted(self.log[ctx.channel].items(), key=lambda message: message[0].created_at)
            if target:
                msg_pool = [(m, t) for m, t in msg_pool if m.author == target]
            for msg, timestamp in msg_pool:
                if last_sender is None:
                    last_sender = msg.author
                    group_timestamp - msg.created_at
                elif msg.author != last_sender:
                    title = f"{last_sender.display_name}, {(now - msg.created_at).seconds//60}m ago:"
                    embed.add_field(name=title, value="\n".join(msg_group), inline=False)
                    last_sender = msg.author
                    msg_group = []
                msg_group.append(msg.content)
            if msg_group:
                title = f"{last_sender.display_name}, {(now - msg.created_at).seconds//60}m ago:"
                embed.add_field(name=title, value="\n".join(msg_group), inline=False)
                await ctx.send(embed=embed)
                return
        await ctx.send("Nothing to snipe here :eyes:")

    @purge.before_loop
    async def wait(self):
        await self.bot.wait_until_ready()


def cog_unload(self):
    self.purge.cancel()


def setup(client):
    client.add_cog(Snipe(client))
