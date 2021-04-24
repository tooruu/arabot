from discord.ext.commands import Cog
from datetime import datetime, timedelta
from discord.ext.tasks import loop
from ...utils.format_escape import bold


class Reaction(Cog, name="Eggs"):
    THRESHOLD = timedelta(seconds=3)
    COOLDOWN = timedelta(seconds=40)

    def __init__(self, client):
        self.bot = client
        self.mapping = {}
        self.purge.start()

    @Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if not await reaction.users().get(bot=True):
            on_cd = (
                self.mapping.setdefault(user.id, {}).setdefault(reaction.message.id, {}).get(hash(reaction), [False])[0]
            )
            self.mapping[user.id][reaction.message.id][hash(reaction)] = on_cd, datetime.now()

    @Cog.listener()
    async def on_reaction_remove(self, reaction, user):
        now = datetime.now()
        timestamp = self.mapping.get(user.id, {}).get(reaction.message.id, {}).get(hash(reaction), [None])
        no_bot_reactions = not await reaction.users().get(bot=True)
        no_cd = timestamp[0] is False

        if no_bot_reactions and no_cd and now - timestamp[1] <= self.THRESHOLD:
            # rate limit the reaction
            self.mapping[user.id][reaction.message.id][hash(reaction)] = True, now
            await reaction.message.reply(
                f"__Reaction sniped:__\n{bold(user.display_name)}: {reaction}", mention_author=False
            )

    @loop(seconds=3)
    async def purge(self):
        now = datetime.now()
        for user, messages in list(self.mapping.items()):
            for message, reactions in list(messages.items()):
                for reaction, timestamp in list(reactions.items()):
                    if now - timestamp[1] > (self.COOLDOWN if timestamp[0] else self.THRESHOLD):
                        del self.mapping[user][message][reaction]
                if not self.mapping[user][message]:
                    del self.mapping[user][message]
            if not self.mapping[user]:
                del self.mapping[user]

    def cog_unload(self):
        self.purge.cancel()


def setup(client):
    client.add_cog(Reaction(client))
