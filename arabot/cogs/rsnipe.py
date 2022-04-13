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
        self.mapping: dict[int, dict[int, dict[int, tuple[bool, datetime]]]] = {}
        self.purge.start()

    @Cog.listener()
    async def on_reaction_add(self, reaction: Reaction, user: User):
        if await reaction.users().get(bot=True):
            return
        on_cd = (
            self.mapping.setdefault(user.id, {})
            .setdefault(reaction.message.id, {})
            .get(hash(reaction), [False])[0]
        )
        self.mapping[user.id][reaction.message.id][hash(reaction)] = on_cd, utcnow()

    @Cog.listener()
    async def on_reaction_remove(self, reaction: Reaction, user: User):
        now = utcnow()
        on_cd, reacted_at = (
            self.mapping.get(user.id, {})
            .get(reaction.message.id, {})
            .get(hash(reaction), [None] * 2)
        )
        has_bot_reaction = await reaction.users().get(bot=True)
        within_threshold = reacted_at and now - reacted_at <= self.THRESHOLD

        if has_bot_reaction or on_cd or not within_threshold:
            return

        # rate limit the reaction
        self.mapping[user.id][reaction.message.id][hash(reaction)] = True, now
        await reaction.message.reply(
            embed=(
                Embed()
                .set_author(
                    name=user.display_name,
                    icon_url=user.display_avatar.with_static_format("png").url,
                )
                .set_image(
                    url=Twemoji(reaction.emoji).url
                    if isinstance(reaction.emoji, str)
                    else reaction.emoji.url + "?size=64"
                )
                .set_footer(text="Sniped reaction")
            )
        )

    @loop(minutes=1)
    async def purge(self):
        self.mapping = {
            user: messages
            for user, messages in self.mapping.items()
            for message, reactions in messages.items()
            for reaction, cd__time in reactions.items()
            if utcnow() - cd__time[1] <= (self.COOLDOWN if cd__time[0] else self.THRESHOLD)
        }

    def cog_unload(self):
        self.purge.cancel()


def setup(ara: Ara):
    ara.add_cog(ReactionSnipe(ara))
