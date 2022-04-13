from re import search
from urllib.parse import quote_plus

from arabot.core import Ara, Cog, Context, pfxless
from arabot.utils import Category, bold, dsafe
from disnake import Embed
from disnake.ext.commands import check, command


class Urban(Cog, category=Category.LOOKUP):

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

    def __init__(self, ara: Ara):
        self.ara = ara

    @command(brief="Search term in Urban Dictionary", aliases=["ud"])
    async def urban(self, ctx: Context, *, term: str):
        if term.lower() == self.ara.owner.name.lower():
            invite = (
                await self.ara.get_guild(676889696302792774).get_unlimited_invite() or Embed.Empty
            )
            await ctx.send(
                embed=Embed(description="An awesome guy").set_author(
                    name=self.ara.owner.name.lower(), url=invite
                )
            )
            return

        if term.lower() == self.ara.name.lower():
            invite = (
                await self.ara.get_guild(676889696302792774).get_unlimited_invite() or Embed.Empty
            )
            await ctx.send(
                embed=Embed(description="An awesome bot written by an awesome guy").set_author(
                    name=self.ara.name, url=invite
                )
            )
            return

        if ud := (
            await self.ara.session.fetch_json(
                "https://api.urbandictionary.com/v0/define?term=" + quote_plus(term)
            )
        ).get("list"):
            embed = Embed()
            for result in ud[:3]:
                d = dsafe(result["definition"].replace("[", "").replace("]", ""))[:1024]
                embed.add_field(name=result["word"], value=d, inline=False)

            await ctx.send(embed=embed)
        elif ctx.prefix:
            await ctx.send(f"Definition for {bold(term)} not found")

        if not (
            ud := (
                await self.ara.session.fetch_json(
                    "https://api.urbandictionary.com/v0/define?term=" + quote_plus(term)
                )
            ).get("list")
        ):
            if ctx.prefix:
                await ctx.send(f"Definition for {bold(term)} not found")
            return
        embed = Embed().set_author(
            name=term,
            url="https://www.urbandictionary.com/define.php?term=" + quote_plus(term),
        )
        for result in ud[:3]:
            d = dsafe(result["definition"].replace("[", "").replace("]", ""))[:1024]
            embed.add_field(name=result["word"], value=d, inline=False)
        await ctx.send(embed=embed)

    @pfxless(regex=QUERY_PREFIX + rf"((?:(?!{WORDS_IGNORE}).)*?)\??$")
    @check(lambda msg: len(msg.content) < 25)
    async def urban_listener(self, msg):
        term = search(self.QUERY_PREFIX + r"(.*?)\??$", msg.content.casefold()).group(1)
        if self.urban.enabled:
            await self.urban(await self.ara.get_context(msg), term=term)


def setup(ara: Ara):
    ara.add_cog(Urban(ara))
