from datetime import datetime, timedelta

from arabot.core import Ara, Cog
from arabot.utils import Twemoji
from disnake import Embed, Reaction, User
from disnake.ext.tasks import loop
from disnake.utils import utcnow


class ReactionSnipe(Cog):
    THRESHOLD = timedelta(seconds=3)
    COOLDOWN = timedelta(seconds=40)

    def __init__(self, ara: Ara):
        self.ara = ara
        self._cache: dict[int, dict[int, dict[int, tuple[bool, datetime]]]] = {}
        self.purge_cache.start()

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        if await reaction.users().get(bot=True):
            return
        on_cd = (
            self._cache.setdefault(user.id, {})
            .setdefault(reaction.message.id, {})
            .get(hash(reaction), [False])[0]
        )
        self._cache[user.id][reaction.message.id][hash(reaction)] = on_cd, utcnow()

    @Cog.listener()
    async def on_reaction_remove(self, reaction: Reaction, user: User):
        now = utcnow()
        on_cd, reacted_at = (
            self._cache.get(user.id, {})
            .get(reaction.message.id, {})
            .get(hash(reaction), [None] * 2)
        )
        has_bot_reaction = await reaction.users().get(bot=True)
        within_threshold = reacted_at and now - reacted_at <= self.THRESHOLD

        if has_bot_reaction or on_cd or not within_threshold:
            return

        # rate limit the reaction
        self._cache[user.id][reaction.message.id][hash(reaction)] = True, now
        await reaction.message.reply(
            embed=Embed()
            .set_image(
                url=Twemoji(reaction.emoji).url
                if isinstance(reaction.emoji, str)
                else f"{reaction.emoji.url}?size=64"
            )
            .set_footer(text="Sniped reaction")
            .with_author(user)
        )

    @loop(minutes=1)
    async def purge_cache(self):
        self._cache = {
            user: messages
            for user, messages in self._cache.items()
            for message, reactions in messages.items()
            for reaction, cd__time in reactions.items()
            if utcnow() - cd__time[1] <= (self.COOLDOWN if cd__time[0] else self.THRESHOLD)
        }

    def cog_unload(self):
        self.purge_cache.cancel()


def setup(ara: Ara):
    ara.add_cog(ReactionSnipe(ara))
