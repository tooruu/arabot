from discord.ext.commands import command, Cog, PartialEmojiConverter
from .._utils import FindEmoji
import discord
from re import match

class Chemoji(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client

	@command(brief="<emoji> | Suggest new server emoji")
	async def chemoji(self, ctx, em_before: FindEmoji, em_after=None):
		if not em_before in ctx.guild.emojis:
			await ctx.send("Choose a valid server emoji to replace")
		elif em_after and ctx.message.attachments:
			await ctx.send("You can only have one suggestion type in submission")
		elif not (em_after or ctx.message.attachments):
			await ctx.send("You must include one emoji suggestion")
		else:
			if ctx.message.attachments:
				em_after = ctx.message.attachments[0].url
			if match(r"(https?|ftp)://(-\.)?([^\s/?\.#]+\.?)+(/[^\s]*)?$", em_after):
				async with self.bot.ses.get(em_after) as resp:
					if resp.status != 200 or not resp.content_type.startswith("image/"):
						await ctx.send(f"Link a valid image to replace {em_before} with")
						return
			elif match(r"<a?:[a-zA-Z0-9_]{2,32}:[0-9]{18,22}>$", em_after):
				if await FindEmoji().convert(ctx, em_after) in ctx.guild.emojis:
					await ctx.send(f"We already have {em_after}")
					return
				em_after = (await PartialEmojiConverter().convert(ctx, em_after)).url
			else:
				await ctx.send(f"Choose a valid emoji to replace {em_before} with")
				return
			embed = discord.Embed(title="wants to change this →", description="to that ↓").set_thumbnail(url=em_before.url)	.set_image(
				url=em_after
			).set_author(name=ctx.author.display_name, icon_url=ctx.author.avatar_url)
			message = await ctx.send(embed=embed)
			if not ctx.message.attachments:
				await ctx.message.delete()
			await message.add_reaction("👍")
			await message.add_reaction("👎")

def setup(client):
	client.add_cog(Chemoji(client))