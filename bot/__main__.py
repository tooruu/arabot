from aiohttp import ClientSession
from discord import Intents
from discord.ext.commands import Bot
from utils.meta import BOT_PREFIX
from helpers.auth import getenv
from helpers.extensions import load_ext

intents = Intents(
    guilds=True,
    members=True,
    emojis=True,
    voice_states=True,
    guild_messages=True,
    guild_reactions=True,
)


async def sessionify(client):
    client.ses = ClientSession()


class TheBot(Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.loop.create_task(sessionify(self))

    async def close(self):
        await self.ses.close()
        await super().close()


if __name__ == "__main__":
    bot = TheBot(
        command_prefix=BOT_PREFIX,
        case_insensitive=True,
        intents=intents,
    )
    load_ext(bot)
    bot.run(getenv("token"))
