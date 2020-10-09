from discord.ext.commands import command, Cog
from .._utils import dsafe, getenv
from urllib.parse import quote
from discord import Embed
from json import loads

class Commands(Cog):
	def __init__(self, client):
		self.bot = client
		self.wolfram_id = getenv("wolfram_id")

	@command(brief="<query> | Answer a question?")
	async def calc(self, ctx, *, query):
		query = query.strip('`')
		async with ctx.typing():
			async with self.bot.ses.get(
				"https://api.wolframalpha.com/v2/query",
				params={
					"input": query,
					"format": "plaintext",
					"output": "json",
					"appid": self.wolfram_id,
					"units": "metric"
				}
			) as wa:
				wa = loads(await wa.text())["queryresult"]
			embed = Embed(
				color=0xf4684c, title=dsafe(query), url="https://www.wolframalpha.com/input/?i=" + quote(query, safe="")
			).set_footer(
				icon_url="https://cdn.iconscout.com/icon/free/png-512/wolfram-alpha-2-569293.png", text="Wolfram|Alpha"
			)
			if wa["success"]:
				if wa.get("warnings"):
					embed.description = wa["warnings"]["text"]
				for pod in wa["pods"]:
					if pod["id"] == "Input":
						embed.add_field(
							name="Input",
							value=
							f"[{dsafe(pod['subpods'][0]['plaintext'])}](https://www.wolframalpha.com/input/?i={quote(pod['subpods'][0]['plaintext'], safe='')})"
						)
					if pod.get("primary"):
						embed.add_field(
							name="Result",
							value="\n".join(dsafe(subpod["plaintext"]) for subpod in pod["subpods"]),
							inline=False
						)
						break
			else:
				if wa.get("tips"):
					embed.description = wa["tips"]["text"]
			await ctx.send(embed=embed)

def setup(client):
	client.add_cog(Commands(client))
