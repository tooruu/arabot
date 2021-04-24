from re import search
from discord.ext.commands import Cog
from ...utils.general import text_reaction


class Urban(Cog, name="Eggs"):
    def __init__(self, client):
        self.bot = client

    @text_reaction(
        string_send=False,
        regex=r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)((?:(?!up|good|with|it|this|that|so|the|about|goin|happenin|wrong|your|ur|next|da|dis|dat).)*?)\??$",
        check=lambda msg: len(msg.content) < 25,
    )
    async def urban_listener(self, msg):
        term = search(r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)(.*?)\??$", msg.content.lower()).group(1)
        if urban := self.bot.get_command("urban"):
            await urban(await self.bot.get_context(msg), term=term)


def setup(client):
    client.add_cog(Urban(client))
