from urllib.parse import quote_plus as safe
from discord import Embed
from discord.ext.commands import command, Cog
from ...utils.format_escape import bold, dsafe
from ...utils.meta import BOT_NAME
from ...utils.general import get_master_invite


class Urban(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client

    @command(brief="<term> | Search term in Urban Dictionary", aliases=["ud"])
    async def urban(self, ctx, *, term):
        if "tooru" == term.lower():
            invite = await get_master_invite(self.bot.get_guild(676889696302792774)) or Embed.Empty
            await ctx.send(embed=Embed(description="An awesome guy").set_author(name="tooru", url=invite))
            return
        if BOT_NAME.lower() == term.lower():
            invite = await get_master_invite(self.bot.get_guild(676889696302792774)) or Embed.Empty
            await ctx.send(
                embed=Embed(description="An awesome bot written by an awesome guy").set_author(
                    name=BOT_NAME, url=invite
                )
            )
            return
        ud = (await self.bot.fetch_json("https://api.urbandictionary.com/v0/define?term=" + safe(term))).get("list")
        if ud:
            desc = dsafe(
                "\n---------------------------------\n".join(
                    [result["definition"].replace("[", "").replace("]", "") for result in ud[:3]]
                )
            )
            if len(desc) > (maxlength := 2000):
                desc = ".".join(desc[:maxlength].split(".")[0:-1]) + "..."
            await ctx.send(
                embed=Embed(description=desc).set_author(
                    name=term,
                    url="https://www.urbandictionary.com/define.php?term=" + safe(term),
                )
            )
        else:
            if ctx.prefix:
                await ctx.send(f"Definition for {bold(term)} not found")


def setup(client):
    client.add_cog(Urban(client))
