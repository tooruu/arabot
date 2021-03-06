from discord.ext.commands import Cog
from datetime import datetime, timedelta


class Reaction(Cog, name="Eggs"):
    def __init__(self, client):
        self.bot = client
        self.THRESHOLD = timedelta(seconds=1.5)
        self.mapping = {}

    @Cog.listener("on_reaction_add")
    async def catch(self, reaction, user):
        self.mapping.setdefault(user, {})[reaction.message] = datetime.now()

    @Cog.listener("on_reaction_remove")
    async def release(self, reaction, user):
        try:
            if datetime.now() - self.mapping[user].pop(reaction.message) < self.THRESHOLD:
                await reaction.message.reply(f"__Reaction sniped:__\n{user.mention}: {reaction}", mention_author=False)
                if not self.mapping[user]:
                    del self.mapping[user]
        except KeyError as e:
            print(e)


def setup(client):
    client.add_cog(Reaction(client))
