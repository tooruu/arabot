import re
from datetime import datetime
from typing import Any

from arabot.core import Ara, Category, Cog, Context, pfxless
from arabot.utils import EmbedPaginator, bold, dsafe, repchars
from disnake import Embed
from disnake.ext.commands import command


class Urban(Cog, category=Category.LOOKUP):
    def __init__(self, ara: Ara):
        self.ara = ara

    BASE_URL = "https://api.urbandictionary.com/v0/define"
    QUERY_PREFIX = r"^(?:wh?[ao]t(?:['’]?s|\sis)\s)"
    WORDS_IGNORE = "|".join(
        (
            "up",
            "good",
            "with",
            "it",
            "this",
            "that",
            "so",
            "the",
            "about",
            "goin",
            "happenin",
            "wrong",
            "my",
            "your",
            "ur",
            "next",
            "da",
            "dis",
            "dat",
            "new",
            "he",
            "she",
            "better",
            "worse",
            "tho",
        )
    )

    @command(aliases=["ud", "define", "whats"], brief="Search term in Urban Dictionary")
    async def urban(self, ctx: Context, *, term: str):
        for predefined, definition in self.definitions.items():
            if term.lower() == predefined.lower():
                await ctx.send(embed=Embed(title=predefined, description=definition))
                return

        if not (definitions := await self.fetch_definitions(term)):
            if ctx.prefix:  # if command was invoked directly by user, not by urban_listener
                await ctx.send(f"Definition for {bold(term)} not found")
            return

        embeds = [
            Embed(
                description=dsafe(repchars(definition["definition"], "[]"))[:4096],
                title=dsafe(definition["word"])[:256],
                url=definition["permalink"],
                timestamp=datetime.fromisoformat(definition["written_on"][:-1]),
            ).add_field("Example", dsafe(repchars(definition["example"], "[]"))[:1024])
            for definition in definitions
        ]

        await ctx.send(embed=embeds[0], view=EmbedPaginator(embeds, author=ctx.author))

    async def fetch_definitions(self, query: str) -> list[dict[str, Any]] | None:
        data = await self.ara.session.fetch_json(self.BASE_URL, params={"term": query})
        return data.get("list")

    @pfxless(regex=rf"{QUERY_PREFIX}((?:(?!{WORDS_IGNORE}).)*?)\??$")
    async def urban_listener(self, msg):
        if self.urban.enabled:
            term = re.search(rf"{self.QUERY_PREFIX}(.*?)\??$", msg.content, re.IGNORECASE)[1]
            await self.urban(await self.ara.get_context(msg), term=term)

    async def cog_load(self):
        await self.ara.wait_until_ready()
        self.definitions = {
            self.ara.name: "An awesome bot written by an awesome guy",
            self.ara.owner.name: "An awesome guy",
        }


def setup(ara: Ara):
    ara.add_cog(Urban(ara))
