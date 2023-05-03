import logging
from enum import IntEnum
from pprint import pformat

from aiohttp import ClientSession
from disnake import Embed
from disnake.ext.commands import command
from jikanpy import AioJikan

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import dsafe


class Source(IntEnum):
    hmags = 0
    hanime = 1
    hcg = 2
    ddb_objects = 3
    ddb_samples = 4
    Pixiv = 5
    Pixivhistorical = 6
    anime = 7
    seiga = 8
    Danbooru = 9
    drawr = 10
    nijie = 11
    yandere = 12
    animeop = 13
    IMDb = 14
    Shutterstock = 15
    FAKKU = 16
    nhentai = 18
    twoD_market = 19
    medibang = 20
    Anime = 21
    HAnime = 22
    Movies = 23
    Shows = 24
    gelbooru = 25
    konachan = 26
    sankaku = 27
    anime_pictures = 28
    E621 = 29
    IdolComplex = 30
    bcy_illust = 31
    bcy_cosplay = 32
    portalgraphics = 33
    dA = 34
    pawoo = 35
    madokami = 36
    mangadex = 37
    ehentai = 38
    ArtStation = 39
    FurAffinity = 40
    Twitter = 41
    FurryNetwork = 42


class Sauce(Cog, category=Category.LOOKUP, keys={"saucenao_key"}):
    def __init__(self, session: ClientSession):
        self.session = session

    @command(aliases=["source"], brief="Find source for an image", usage="<image or reply>")
    async def sauce(self, ctx: Context):
        await ctx.trigger_typing()
        image_url = await ctx.rsearch("image_url")
        if not image_url:
            await ctx.send("No image or link provided")
            return

        nao_json = await self.session.fetch_json(
            "https://saucenao.com/search.php",
            params={
                "output_type": 2,
                "api_key": self.saucenao_key,
                "db": 999,
                "numres": 1,
                "url": image_url,
            },
        )
        if nao_json["header"]["status"]:
            error = nao_json["header"].get("message")
            logging.error(f"Sauce failed for {image_url}" + (f"\n{error}" if error else ""))
            await ctx.reply(f"Failed to fetch results.\n{error or ''}")
            return
        if not nao_json["header"]["results_returned"]:
            await ctx.reply("No results found")
            return
        data = nao_json["results"][0]["data"]
        header = nao_json["results"][0]["header"]
        embed = Embed()
        try:
            match header["index_id"]:
                case (
                    Source.Anime
                    | Source.HAnime
                    | Source.Movies
                    | Source.Shows
                    | Source.hanime
                    | Source.IMDb
                    | Source.anime
                ):
                    embed.color = 0x2E51A2
                    mal_json = (
                        await AioJikan(session=self.session).anime(data["mal_id"])
                        if "mal_id" in data
                        else None
                    )
                    embed.description = ""
                    if episode := data.get("part"):
                        embed.description += f"Episode {episode}"
                        if timecode := data.get("est_time"):
                            embed.description += f" - {timecode.lstrip('0:')}"
                        embed.description += "\n"
                    embed.description += f"Similarity: {header['similarity']}%"
                    if mal_json:
                        embed.description += f" | Score: {mal_json['score']}"
                        synopsis = dsafe(mal_json["synopsis"].partition(" [")[0])
                        if len(synopsis) > (maxlen := 600):
                            synopsis = ".".join(synopsis[:maxlen].split(".")[:-1]) + "..."
                        embed.set_image(url=mal_json["image_url"])
                        embed.add_field("Synopsis", synopsis)
                        embed.set_thumbnail(url=header["thumbnail"])
                    else:
                        embed.set_image(url=header["thumbnail"])
                    embed.title = mal_json["title"] if mal_json else data["source"]
                    embed.url = mal_json["url"] if mal_json else data["ext_urls"][0]

                case Source.Pixiv:
                    embed.color = 0x0095F2
                    embed.title = data["title"]
                    embed.url = f"https://www.pixiv.net/artworks/{data['pixiv_id']}"
                    embed.description = f"Similarity: {header['similarity']}%"
                    embed.set_author(
                        name=data["member_name"],
                        url=f"https://www.pixiv.net/users/{data['member_id']}",
                    )
                    embed.set_image(url=header["thumbnail"])

                case Source.dA:
                    embed.title = data["title"]
                    embed.url = data["ext_urls"][0]
                    embed.set_author(name=data["author_name"], url=data["author_url"])
                    embed.set_image(url=header["thumbnail"])

                case (
                    Source.Danbooru
                    | Source.yandere
                    | Source.gelbooru
                    | Source.konachan
                    | Source.sankaku
                    | Source.anime_pictures
                    | Source.E621
                    | Source.IdolComplex
                    | _
                ):
                    embed.color = 0x9E2720
                    embed.url = data.get("ext_urls", [Embed.Empty])[0]
                    embed.title = (
                        data.get("title")
                        or data.get("eng_name")
                        or data.get("source")
                        or data.get("jp_name")
                        or ("Post" if embed.url else Embed.Empty)
                    )
                    embed.description = f"Similarity: {header['similarity']}%"
                    match data.get("creator"):
                        # pylint: disable=used-before-assignment
                        case str() as c if c not in {"", "Unknown"}:
                            embed.set_author(name=c)
                        case list() as c if c != ["Unknown"]:
                            embed.set_author(name=", ".join(c))
                    if not (embed.author or embed.title):
                        raise KeyError
                    embed.set_image(url=header["thumbnail"])
        except KeyError:
            logging.error("Sauce failed: %s", pformat(data))
            data["similarity"] = header["similarity"]
            raw_data = "\n".join(f"{k}: {v}" for k, v in data.items())
            embed.description = (
                "Couldn't parse result, dumping raw data:" f"```yaml\n{raw_data}\n```"
            )
        embed.set_footer(
            text="Powered by SauceNAO",
            icon_url="https://i.imgur.com/Ynoqpam_d.png",
        )
        await ctx.reply(embed=embed)
        # Debug info
        logging.debug(image_url)
        data |= header
        raw_data = "\n".join(f"{k}: {v}" for k, v in data.items())
        logging.debug(raw_data, end="\n\n")


def setup(ara: Ara):
    ara.add_cog(Sauce(ara.session))
