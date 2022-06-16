from aiohttp import ClientResponseError
from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember, humanjoin
from disnake import Embed
from disnake.ext import commands
from waifu import APIException, ImageCategories, WaifuAioClient

REACTION_MAPPING: dict[str, tuple[str, str]] = {
    "bite": ("{author} wants to bite someone...", "{author} bites {target}"),
    "blowjob": ("{author} wants to give someone a blowjob...", "{author} gives {target} a blowjob"),
    "blush": ("{author} is blushing", "{target} make{s} {author} blush"),
    "bonk": ("{author} wants to bonk someone...", "{author} bonks {target}"),
    "bully": ("{author} wants to bully someone...", "{author} bullies {target}"),
    "cringe": ("{author} is cringing", "{target} make{s} {author} cringe"),
    "cry": ("{author} is crying", "{author} is crying on {target}'s shoulders"),
    "cuddle": ("{author} wants to cuddle someone...", "{author} cuddles {target}"),
    "dance": ("{author} is dancing", "{author} is dancing with {target}"),
    "glomp": ("{author} wants to glomp someone...", "{author} glomps {target}"),
    "handhold": ("{author} wants to hold someone's hand...", "{author} holds {target}'s hand"),
    "happy": ("{author} is happy", "{target} make{s} {author} happy"),
    "highfive": ("{author} wants to highfive someone...", "{author} gives {target} a highfive"),
    "hug": ("{author} wants to hug someone...", "{author} hugs {target}"),
    "kick": ("{author} wants to kick someone...", "{author} kicks {target}"),
    "kill": ("{author} wants to kill someone...", "{author} kills {target}"),
    "kiss": ("{author} wants to kiss someone...", "{author} kisses {target}"),
    "lick": ("{author} wants to lick someone...", "{author} licks {target}"),
    "nom": ("{author} is eating", "{author} eats {target}"),
    "pat": ("{author} wants to pat someone...", "{author} pats {target}"),
    "poke": ("{author} wants to poke someone...", "{author} pokes {target}"),
    "slap": ("{author} wants to slap someone...", "{author} slaps {target}"),
    "smile": ("{author} is smiling", "{author} smiles at {target}"),
    "smug": ("( ͡° ͜ʖ ͡°)", "( ͡° ͜ʖ ͡°)"),
    "wave": ("{author} waves at someone...", "{author} waves at {target}"),
    "wink": ("{author} is winking", "{author} winks at {target}"),
    "yeet": ("{author} wants to yeet someone...", "{author} yeets {target}"),
}


class WaifuCommandsMeta(commands.CogMeta):
    def __new__(mcls, name, bases, attrs, *args, **kwargs):
        command_callback = attrs[f"_{name}__callback"]
        for reaction_type in ImageCategories["sfw"]:
            attrs[reaction_type] = commands.command(
                name=reaction_type,
                usage="[members...]" if reaction_type in REACTION_MAPPING else "",
            )(command_callback)
        nsfw_group = attrs["nsfw"]
        for reaction_type in ImageCategories["nsfw"]:
            attrs[f"nsfw_{reaction_type}"] = nsfw_group.command(
                name=reaction_type,
                usage="[members...]" if reaction_type in REACTION_MAPPING else "",
            )(command_callback)

        return super().__new__(mcls, name, bases, attrs, *args, **kwargs)


class Waifus(Cog, category=Category.WAIFUS, metaclass=WaifuCommandsMeta):
    def __init__(self, waifu_client: WaifuAioClient):
        self.wclient = waifu_client

    @commands.group(invoke_without_command=True)
    async def nsfw(self, ctx: Context):
        await ctx.send(
            embed=Embed().add_field(
                "Available categories",
                "\n".join(c.name for c in self.nsfw.walk_commands()),
            )
        )

    # pylint: disable=unused-private-member
    async def __callback(self, ctx: Context, *targets: AnyMember):
        targets = [t for t in targets if t]
        reaction_type = ctx.command.name
        embed = Embed(title=reaction_type.title())
        method = self.wclient.nsfw if ctx.command.parent else self.wclient.sfw
        try:
            image_url = await method(reaction_type)
        except (APIException, ClientResponseError):
            embed.set_footer(text="Failed to get image")
        else:
            embed.set_footer(text="Powered by waifu.pics")
            embed.set_image(url=image_url)
        if reaction_type in REACTION_MAPPING:
            embed.description = REACTION_MAPPING[reaction_type][len(targets) > 0].format(
                author=ctx.author.mention,
                target=humanjoin(t.mention for t in targets),
                s="s" if len(targets) == 1 else "",
                ve="s" if len(targets) == 1 else "ve",
            )
        await ctx.send_ping(embed=embed)


def setup(ara: Ara):
    waifu_client = WaifuAioClient(ara.session)
    ara.add_cog(Waifus(waifu_client))
