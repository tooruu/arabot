from discord.ext.commands import command, Cog
from .._utils import dsafe
import discord
from aiohttp import ClientSession as WebSession, ContentTypeError
from jikanpy import AioJikan
from urllib.parse import quote_plus as safe, quote
from io import BytesIO
from re import match

class Commands(Cog):
	def __init__(self, client):
		self.bot = client

	@command(aliases=["source"], brief="<link|attachment> | Find anime source for an image")
	async def sauce(self, ctx, image_url=None):
		if image_url := ctx.message.attachments[0].url if ctx.message.attachments else image_url if image_url.startswith(
			"http"
		) else None:
			async with ctx.typing():
				async with WebSession() as session:
					async with session.get("https://trace.moe/api/search?url=" + quote(image_url)) as tmoe_resp:
						try:
							mal_resp = (
								await
								AioJikan(session=session).anime((tmoe_resp := (await tmoe_resp.json())["docs"][0])["mal_id"])
							)
						except ContentTypeError:
							await ctx.send(
								"Unfortunately, the image was rejected by our sauce provider.\nHowever, you can still find the sauce manually at\nhttps://trace.moe/?url="
								+ safe(image_url)
							)
						else:
							async with session.get(
								#"https://trace.moe/preview.php",
								#params={
								#"anilist_id": tmoe_resp["anilist_id"],
								#"file": quote(tmoe_resp["filename"]),
								#"t": str(tmoe_resp["at"]),
								#"token": tmoe_resp["tokenthumb"]
								#}
								f"https://trace.moe/{tmoe_resp['anilist_id']}/{quote(tmoe_resp['filename'])}",
								params={
								"start": str(tmoe_resp["from"]),
								"end": str(tmoe_resp["to"]),
								"token": tmoe_resp["tokenthumb"]
								}
							) as preview:
								preview = discord.File(BytesIO(await preview.read()), tmoe_resp["filename"]) if preview.status == 200 else None
							#pylint: disable=used-before-assignment
							await ctx.send(
								f"Episode {tmoe_resp['episode']} ({int(tmoe_resp['at']/60)}:{int(tmoe_resp['at']%60):02d})"
								if tmoe_resp["episode"] else None,
								file=preview,
								embed=discord.Embed(
								color=32767,
								description=
								f"Similarity: {tmoe_resp['similarity']:.1%} | Score: {mal_resp['score']} | {mal_resp['status']}"
								).set_author(name=mal_resp["title"],
								url=mal_resp["url"]).set_thumbnail(url=mal_resp["image_url"]).add_field(
								name="Synopsis",
								value=dsafe(s if len(s := mal_resp["synopsis"].partition(" [")[0]) <=
								(maxlength := 600) else '.'.join(s[:maxlength].split('.')[0:-1]) + '...')
								).set_footer(
								text=f"Requested by {ctx.author.display_name} | Powered by trace.moe",
								icon_url=ctx.author.avatar_url
								)
							)

def setup(client):
	client.add_cog(Commands(client))