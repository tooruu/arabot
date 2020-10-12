from discord.ext.commands import command, Cog
from urllib.parse import quote_plus as safe
from .._utils import bold, dsafe
from discord import Embed

class Urban(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client

	@command(brief="<term> | Search term in Urban Dictionary", aliases=["ud"])
	async def urban(self, ctx, *, term):
		if "tooru" in term.lower():
			await ctx.send(
				embed=Embed(description="An awesome guy").set_author(name="tooru", url="https://discord.gg/YdEXsZN")
			)
			return
		if "arabot" in term.lower():
			await ctx.send(
				embed=Embed(description="An awesome bot written by an awesome guy").set_author(name="AraBot", url="https://discord.gg/YdEXsZN")
			)
			return
		async with self.bot.ses.get("https://api.urbandictionary.com/v0/define?term="+ safe(term)) as ud:
			ud = await ud.json()
		if ud := ud.get("list"):
			await ctx.send(
				embed=Embed(
					description=dsafe(s if len(s := "\n---------------------------------\n".
						join([result["definition"].replace("[", "").replace("]", "") for result in ud[:3]])) <=
						(maxlength := 2000) else '.'.join(s[:maxlength].split('.')[0:-1]) + '...')
				).set_author(name=term, url="https://www.urbandictionary.com/define.php?term=" + safe(term))
			)
		else:
			await ctx.send(f"Definition for {bold(term)} not found")

def setup(client):
	client.add_cog(Urban(client))
