from discord.ext.commands import Cog
from datetime import datetime, timedelta
from discord.ext.tasks import loop
from ...utils.format_escape import bold


class Reaction(Cog, name="Eggs"):
    THRESHOLD = timedelta(seconds=1.5)

    def __init__(self, client):
        self.bot = client
        self.mapping = {}
        self.purge.start()

    @Cog.listener("on_reaction_add")
    async def catch(self, reaction, user):
        self.mapping.setdefault(user.id, {}).setdefault(reaction.message.id, {})[hash(reaction)] = datetime.now()

    @Cog.listener("on_reaction_remove")
    async def release(self, reaction, user):
        try:
            if datetime.now() - self.mapping[user.id][reaction.message.id].pop(hash(reaction)) <= self.THRESHOLD:
                await reaction.message.reply(
                    f"__Reaction sniped:__\n{bold(user.display_name)}: {reaction}", mention_author=False
                )
        except KeyError as e:
            print(e)

    @loop(seconds=30)
    async def purge(self):
        now = datetime.now()
        for user, messages in list(self.mapping.items()):
            for message, reactions in list(messages.items()):
                for reaction, timestamp in list(reactions.items()):
                    if now - timestamp > self.THRESHOLD:
                        del self.mapping[user][message][reaction]
                if not self.mapping[user][message]:
                    del self.mapping[user][message]
            if not self.mapping[user]:
                del self.mapping[user]


def setup(client):
    client.add_cog(Reaction(client))
