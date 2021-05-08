from aiohttp import ClientSession
from datetime import datetime
from discord import Embed
from discord.ext.commands import command, Cog
from ...helpers.auth import req_auth


class Faceit(Cog, name="Commands"):
    def __init__(self, client, key):
        self.bot = client
        self.faceit_key = key
        self.session = ClientSession(headers={"Authorization": "Bearer " + self.faceit_key})

    @command(brief="<nickname> | View player's FACEIT profile")
    async def faceit(self, ctx, nickname):
        players = await self.bot.fetch_json(
            f"https://open.faceit.com/data/v4/search/players?nickname={nickname}&limit=1", session=self.session
        )
        if not players["items"]:
            await ctx.send("Player not found")
            return
        player = await self.bot.fetch_json(
            "https://open.faceit.com/data/v4/players/" + players["items"][0]["player_id"], session=self.session
        )

        steam_link = f"[Steam profile](https://www.steamcommunity.com/profiles/{player['steam_id_64']})"
        country = f"{player['country'].upper()}"
        friends = f"{len(player['friends_ids'])}"
        try:
            last_infraction = datetime.strptime(player["last_infraction_date"], "%a %b %d %H:%M:%S UTC %Y")
            last_infraction = last_infraction.strftime("%d %b %Y")
        except:
            last_infraction = "none"

        embed = (
            Embed(
                color=0xFF5500,
                description=f"""{steam_link}
Country: {country} | Friends: {friends} | Last infraction: {last_infraction}
FACEIT membership type: {player["membership_type"]}""",
            )
            .set_author(name=player["nickname"], url=player["faceit_url"].format(lang="en"))
            .set_thumbnail(url=player["avatar"])
        )
        for game in player["games"]:
            player_name = player["games"][game]["game_player_name"]
            region = player["games"][game]["region"]
            skill_level = player["games"][game]["skill_level"]
            elo = player["games"][game]["faceit_elo"]
            embed.add_field(
                name=game.replace("_", " ").upper(),
                value=f"""Player name: {player_name}
Region: {region}
Skill level: {skill_level}
ELO: {elo}""",
                inline=True,
            )
        await ctx.send(embed=embed)


@req_auth("faceit_key")
def setup(client, key):
    client.add_cog(Faceit(client, key))
