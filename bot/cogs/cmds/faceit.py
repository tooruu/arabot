from discord.ext.commands import command, Cog
from aiohttp import ClientSession as WebSession
import discord
from .._utils import getenv

class Commands(Cog):
	def __init__(self, client):
		self.bot = client
		self.faceit_key = getenv("faceit_key")

	@command(brief="<nickname> | View player's FACEIT profile")
	async def faceit(self, ctx, nickname):
		async with WebSession(headers={"Authorization": "Bearer " + self.faceit_key}) as ses:
			async with ses.get(
				f"https://open.faceit.com/data/v4/search/players?nickname={nickname}&limit=1"
			) as player_search:
				if not (await player_search.json())["items"]:
					await ctx.send("Player not found")
					return
				async with ses.get(
					"https://open.faceit.com/data/v4/players/" + (await player_search.json())["items"][0]["player_id"]
				) as player:
					player = await player.json()
		embed = discord.Embed(
			color=0xFF5500,
			description=
			f"[Steam profile](https://www.steamcommunity.com/profiles/{player['steam_id_64']})\nCountry: {player['country'].upper()} | Friends: {len(player['friends_ids'])} | Bans: {len(player['bans'])}\nFACEIT membership type: {player['membership_type']}"
		).set_author(name=player["nickname"],
			url=player["faceit_url"].format(lang="en")).set_thumbnail(url=player["avatar"])
		for game in player["games"]:
			embed.add_field(
				name=game.replace("_", " ").upper(),
				value=f"""Player name: {player['games'][game]['game_player_name']}
			Region: {player['games'][game]['region']}
			Skill level: {player['games'][game]['skill_level']}
			ELO: {player['games'][game]['faceit_elo']}""",
				inline=True
			)
		await ctx.send(embed=embed)

def setup(client):
	client.add_cog(Commands(client))
