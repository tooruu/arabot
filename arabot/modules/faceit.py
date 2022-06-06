from datetime import datetime

from aiohttp import ClientSession
from arabot.core import Ara, Category, Cog, Context
from disnake import Embed
from disnake.ext.commands import command


class Faceit(Cog, category=Category.LOOKUP, keys={"faceit_key"}):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.session = ClientSession(headers={"Authorization": f"Bearer {self.faceit_key}"})

    @command(brief="View player's FACEIT profile")
    async def faceit(self, ctx: Context, nickname):
        players = await self.session.fetch_json(
            f"https://open.faceit.com/data/v4/search/players?nickname={nickname}&limit=1"
        )
        if not players["items"]:
            await ctx.send("Player not found")
            return
        player = await self.session.fetch_json(
            "https://open.faceit.com/data/v4/players/" + players["items"][0]["player_id"]
        )

        steam_link = (
            f"[Steam profile](https://www.steamcommunity.com/profiles/{player['steam_id_64']})"
        )
        country = player["country"].upper()
        friends = len(player["friends_ids"])
        try:
            last_infraction = datetime.strptime(
                player["last_infraction_date"], "%a %b %d %H:%M:%S UTC %Y"
            )
        except (KeyError, ValueError):
            last_infraction = ""
        else:
            last_infraction = " | Last infraction: " + last_infraction.strftime("%d %b %Y")

        embed = (
            Embed(
                color=0xFF5500,
                description=f"""{steam_link}
Country: {country} | Friends: {friends}{last_infraction}
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
                game.replace("_", " ").upper(),
                f"Player name: {player_name}\n"
                f"Region: {region}\n"
                f"Skill level: {skill_level}\n"
                f"ELO: {elo}",
            )
        await ctx.send(embed=embed)

    def cog_unload(self):
        self.ara.loop.create_task(self.session.close())


def setup(ara: Ara):
    ara.add_cog(Faceit(ara))
