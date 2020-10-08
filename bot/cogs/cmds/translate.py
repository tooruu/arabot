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
		if len(text) > 1024:
			await ctx.send("Your text is too long,\ntrimming it to the first 1024 characters")
			text = text[:1024]
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
		embed.add_field(name=trans["detectedSourceLanguage"].upper(), value=dsafe(text)[:1024])
		embed.add_field(name=lang_to.upper(), value=dsafe(trans["translatedText"])[:1024], inline=False)
		await ctx.send(embed=embed)

def setup(client):
	client.add_cog(Commands(client))
