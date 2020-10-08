from discord.ext.commands import command, Cog
from .._utils import getenv, dsafe
from aiohttp import ClientSession as WebSession
from discord import Embed

class Commands(Cog):
	def __init__(self, client):
		self.bot = client
		self.key = getenv("g_trans_key")

	@command(aliases=["trans", "tr"], brief="<target_lang> <text> | Translates text to target language")
	async def translate(self, ctx, lang_to, *, text=None):
		if not text:
			await ctx.send("I need text to translate")
			return
		async with WebSession() as session:
			async with session.get("https://translation.googleapis.com/language/translate/v2", params={
				"key": self.key,
				"target": lang_to,
				"q": text
			}) as trans:
				if trans.status != 200:
					await ctx.send("Invalid argument")
					return
				trans = (await trans.json())["data"]["translations"][0]
		embed = Embed()
		embed.add_field(name=trans["detectedSourceLanguage"], value=dsafe(text))
		embed.add_field(name=lang_to, value=dsafe(trans["translatedText"]), inline=False)
		await ctx.send(embed=embed)

def setup(client):
	client.add_cog(Commands(client))
