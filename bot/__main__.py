from aiohttp import ClientSession
from discord import Intents
from discord.ext.commands import Bot
from .utils.meta import BOT_PREFIX
from .helpers.auth import getenv
from .helpers.extensions import load_ext

intents = Intents(
    guilds=True,
    members=True,
    emojis=True,
    voice_states=True,
    guild_messages=True,
    guild_reactions=True,
)


class TheBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop.create_task(self.sessionify())

    async def sessionify(self):
        self.ses = ClientSession()

    async def close(self):
        await self.ses.close()
        await super().close()


bot = TheBot(
    command_prefix=BOT_PREFIX,
    case_insensitive=True,
    intents=intents,
)

if __name__ == "__main__":
    assert (token := getenv("token"))
    load_ext(bot)
    bot.run(token)
