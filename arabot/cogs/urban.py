import re
from urllib.parse import quote_plus

from arabot.core import Ara, Category, Cog, Context, pfxless
from arabot.core.utils import bold, dsafe
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

    @command(aliases=["ud"], brief="Search term in Urban Dictionary")
    async def urban(self, ctx: Context, *, term: str):
        if term.lower() == ctx.ara.owner.name.lower():
            invite = (
                await ctx.ara.get_guild(676889696302792774).get_unlimited_invite() or Embed.Empty
            )
            await ctx.send(
                embed=Embed(description="An awesome guy").set_author(
                    name=ctx.ara.owner.name.lower(), url=invite
                )
            )
            return

        if term.lower() == ctx.ara.name.lower():
            invite = (
                await ctx.ara.get_guild(676889696302792774).get_unlimited_invite() or Embed.Empty
            )
            await ctx.send(
                embed=Embed(description="An awesome bot written by an awesome guy").set_author(
                    name=ctx.ara.name, url=invite
                )
            )
            return

        data = await ctx.ara.session.fetch_json(self.BASE_URL, params={"term": quote_plus(term)})
        if not (ud := data.get("list")):
            if ctx.prefix:
                await ctx.send(f"Definition for {bold(term)} not found")
            return

        embed = Embed().set_author(
            name=term,
            url="https://www.urbandictionary.com/define.php?term=" + quote_plus(term),
        )

        for result in ud[:3]:
            definition = result["definition"].replace("[", "").replace("]", "")
            embed.add_field(result["word"], dsafe(definition)[:1024], inline=False)
        await ctx.send(embed=embed)

    @pfxless(regex=QUERY_PREFIX + rf"((?:(?!{WORDS_IGNORE}).)*?)\??$")
    async def urban_listener(self, msg):
        if self.urban.enabled:
            term = re.search(self.QUERY_PREFIX + r"(.*?)\??$", msg.content, re.IGNORECASE).group(1)
            await self.urban(await self.ara.get_context(msg), term=term)


def setup(ara: Ara):
    ara.add_cog(Urban(ara))
