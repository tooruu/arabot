import re
from datetime import datetime
from typing import Any

from disnake import Embed, Message
from disnake.ext.commands import command
from disnake.utils import escape_markdown

from arabot.core import Ara, Category, Cog, Context, pfxless
from arabot.utils import EmbedPaginator, bold, replacechars


class Urban(Cog, category=Category.LOOKUP):
    def __init__(self, ara: Ara):
        self.ara = ara

    BASE_URL = "https://api.urbandictionary.com/v0/define"
    QUERY_PREFIX = r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)"
    WORDS_IGNORE = (
        r"about|better|da|dat|dis|goin|good|happenin|he|it|mine|my|new|next|she|so|stopp|that|the|"
        r"this|tho|up|ur|with|worse|wrong|your"
    )

    @command(aliases=["ud", "define", "whats"], brief="Search term in Urban Dictionary")
    async def urban(self, ctx: Context, *, term: str):
        for predefined, definition in self.definitions.items():
            if term.casefold() == predefined.casefold():
                await ctx.send(embed=Embed(title=predefined, description=definition))
                return

        if not (definitions := await self.fetch_definitions(term)):
            if ctx.prefix:  # send if command was invoked directly by user, not by urban_listener
                await ctx.send(ctx._("definition_not_found").format(bold(term)))
            return

        embeds = list[Embed]()
        for definition in definitions:
            embed = Embed(
                description=escape_markdown(replacechars(definition["definition"], "[]"))[:4096],
                title=escape_markdown(definition["word"])[:256],
                url=definition["permalink"],
                timestamp=datetime.fromisoformat(definition["written_on"][:-1]),
            )
            if definition["example"]:
                embed.add_field(
                    ctx._("example", False),
                    escape_markdown(replacechars(definition["example"], "[]"))[:1024],
                )
            embeds.append(embed)

        await ctx.send(embed=embeds[0], view=EmbedPaginator(embeds, author=ctx.author))

    async def fetch_definitions(self, query: str) -> list[dict[str, Any]] | None:
        data = await self.ara.session.fetch_json(self.BASE_URL, params={"term": query})
        return data.get("list")

    @pfxless(regex=rf"{QUERY_PREFIX}((?:(?!{WORDS_IGNORE}).)*?)\??$")
    async def urban_listener(self, msg: Message):
        if self.urban.enabled:
            term = re.search(rf"{self.QUERY_PREFIX}(.*?)\??$", msg.content, re.IGNORECASE)[1]
            await self.urban(await self.ara.get_context(msg), term=term)

    async def cog_load(self):
        await self.ara.wait_until_ready()
        self.definitions = {
            self.ara.name: "An awesome bot written by an awesome guy",
            self.ara.owner.display_name: "An awesome guy",
        }


def setup(ara: Ara):
    ara.add_cog(Urban(ara))
