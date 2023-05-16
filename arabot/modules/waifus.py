from aiohttp import ClientResponseError
from disnake import Embed
from disnake.ext import commands
from waifu import APIException, ImageCategories, WaifuAioClient

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember, humanjoin

REACTION_MAPPING: dict[str, dict] = {
    "bite": {
        "no_mentions": "{author} wants to bite someone...",
        "mentions": "{author} bites {target}",
    },
    "blowjob": {
        "brief": "Give someone a blowjob",
        "no_mentions": "{author} wants to give someone a blowjob...",
        "mentions": "{author} gives {target} a blowjob",
    },
    "blush": {
        "brief": None,
        "no_mentions": "{author} is blushing",
        "self_mention": "{author} is blushing",
        "mentions": "{target} make{s} {author} blush",
    },
    "bonk": {
        "no_mentions": "{author} wants to bonk someone...",
        "mentions": "{author} bonks {target}",
        "protect_bot": True,
    },
    "bully": {
        "no_mentions": "{author} wants to bully someone...",
        "mentions": "{author} bullies {target}",
        "protect_bot": True,
    },
    "cringe": {
        "brief": "Cringe at someone",
        "no_mentions": "{author} is cringing",
        "mentions": "{author} cringes at {target}",
        "protect_bot": True,
    },
    "cry": {
        "brief": "Cry on someone's shoulders",
        "no_mentions": "{author} is crying",
        "self_mention": "{author} is crying",
        "mentions": "{author} is crying on {target}'s shoulders",
    },
    "cuddle": {
        "no_mentions": "{author} wants to cuddle someone...",
        "mentions": "{author} cuddles {target}",
    },
    "dance": {
        "brief": "Dance with someone",
        "no_mentions": "{author} is dancing",
        "self_mention": "{author} is dancing",
        "mentions": "{author} is dancing with {target}",
    },
    "glomp": {
        "no_mentions": "{author} wants to glomp someone...",
        "mentions": "{author} glomps {target}",
    },
    "handhold": {
        "brief": "Hold someone's hand",
        "no_mentions": "{author} wants to hold someone's hand...",
        "self_mention": "{author} holds their own hand 🤨",
        "mentions": "{author} holds {target}'s hand",
    },
    "happy": {
        "brief": None,
        "no_mentions": "{author} is happy",
        "self_mention": "{author} is happy",
        "mentions": "{target} make{s} {author} happy",
    },
    "highfive": {
        "no_mentions": "{author} wants to highfive someone...",
        "mentions": "{author} gives {target} a highfive",
    },
    "hug": {
        "no_mentions": "{author} wants to hug someone...",
        "mentions": "{author} hugs {target}",
    },
    "kick": {
        "no_mentions": "{author} wants to kick someone...",
        "mentions": "{author} kicks {target}",
        "protect_bot": True,
    },
    "kill": {
        "no_mentions": "{author} wants to kill someone...",
        "mentions": "{author} kills {target}",
        "protect_bot": True,
    },
    "kiss": {
        "no_mentions": "{author} wants to kiss someone...",
        "mentions": "{author} kisses {target}",
    },
    "lick": {
        "no_mentions": "{author} wants to lick someone...",
        "mentions": "{author} licks {target}",
    },
    "nom": {
        "brief": "Eat someone",
        "no_mentions": "{author} is eating",
        "mentions": "{author} eats {target}",
    },
    "pat": {
        "no_mentions": "{author} wants to pat someone...",
        "mentions": "{author} pats {target}",
    },
    "poke": {
        "no_mentions": "{author} wants to poke someone...",
        "mentions": "{author} pokes {target}",
    },
    "slap": {
        "no_mentions": "{author} wants to slap someone...",
        "mentions": "{author} slaps {target}",
        "protect_bot": True,
    },
    "smile": {
        "brief": "Smile at someone",
        "no_mentions": "{author} is smiling",
        "mentions": "{author} smiles at {target}",
    },
    "smug": {
        "brief": None,
        "no_mentions": "( ͡° ͜ʖ ͡°)",
        "mentions": "( ͡° ͜ʖ ͡°)",
    },
    "wave": {
        "brief": "Wave at someone",
        "no_mentions": "{author} waves at someone...",
        "self_mention": "{author} waves at someone...",
        "mentions": "{author} waves at {target}",
    },
    "wink": {
        "brief": "Wink at someone",
        "no_mentions": "{author} is winking",
        "self_mention": "{author} is winking",
        "mentions": "{author} winks at {target}",
    },
    "yeet": {
        "no_mentions": "{author} wants to yeet someone...",
        "mentions": "{author} yeets {target}",
        "protect_bot": True,
    },
}


class WaifuCommandsMeta(commands.CogMeta):
    def __new__(cls, name, bases, attrs, *args, **kwargs):
        command_callback = attrs[f"_{name}__callback"]

        for reaction_type in ImageCategories["sfw"]:
            command_attrs = cls.__get_command_attrs(reaction_type)
            attrs[reaction_type] = commands.command(**command_attrs)(command_callback)

        nsfw_group = attrs["nsfw"]
        for reaction_type in ImageCategories["nsfw"]:
            command_attrs = cls.__get_command_attrs(reaction_type)
            attrs[f"nsfw_{reaction_type}"] = nsfw_group.command(**command_attrs)(command_callback)

        return super().__new__(cls, name, bases, attrs, *args, **kwargs)

    @staticmethod
    def __get_command_attrs(reaction_name: str) -> dict:
        command_attrs = {"name": reaction_name}
        if reaction_data := REACTION_MAPPING.get(reaction_name):
            command_attrs.update(
                brief=reaction_data.get("brief", f"{reaction_name.capitalize()} someone"),
                usage="[members...]",
            )
        else:
            command_attrs.update(
                brief=f"Show random {reaction_name}",
                usage="",  # Setting this to None will make ;help inspect params automatically (bad)
            )
        return command_attrs


class Waifus(Cog, category=Category.WAIFUS, metaclass=WaifuCommandsMeta):
    NSFW_IN_SFW_CHANNEL = f"{__module__}.nsfw_in_sfw_channel"

    def __init__(self, waifu_client: WaifuAioClient):
        self.wclient = waifu_client

    @commands.group(invoke_without_command=True)
    async def nsfw(self, ctx: Context):
        if not ctx.channel.is_nsfw():
            await ctx.reply_(Waifus.NSFW_IN_SFW_CHANNEL, False)
            return
        await ctx.send(
            embed=Embed().add_field(
                ctx._("available_categories"),
                "\n".join(c.name for c in self.nsfw.walk_commands()),
            )
        )

    # pylint: disable=unused-private-member
    async def __callback(self, ctx: Context, *targets: AnyMember):
        method = self.wclient.nsfw if ctx.command.parent else self.wclient.sfw
        if method == self.wclient.nsfw and not ctx.channel.is_nsfw():
            await ctx.reply_(Waifus.NSFW_IN_SFW_CHANNEL, False)
            return
        targets = list(dict.fromkeys(t for t in targets if t))
        reaction_type = ctx.command.name
        embed = Embed(title=reaction_type.title())
        try:
            image_url = await method(reaction_type)
        except (APIException, ClientResponseError):
            embed.set_footer(text=ctx._("image_failed"))
        else:
            embed.set_footer(text=ctx._("powered_by", False).format("waifu.pics"))
            embed.set_image(url=image_url)
        if reaction_data := REACTION_MAPPING.get(reaction_type):
            match targets:
                case []:
                    description = reaction_data["no_mentions"]
                case [ctx.author]:
                    if not (description := reaction_data.get("self_mention")):
                        menstr = reaction_data["mentions"]
                        if menstr.index("{target}") > menstr.index("{author}"):
                            description = menstr.replace("{target}", "themselves")
                        else:
                            description = menstr.replace("{author}", "themselves").replace(
                                "{target}", "{author}"
                            )
                case _ if reaction_data.get("protect_bot") and ctx.me in targets:
                    description = (
                        reaction_data["mentions"]
                        .replace("{author}", ctx.me.mention)
                        .replace("{target}", "{author}")
                    )
                case _:
                    if ctx.author in targets:
                        targets.remove(ctx.author)
                    description = reaction_data["mentions"]
            embed.description = description.format(
                author=ctx.author.mention,
                target=humanjoin(getattr(t, "mention", t) for t in targets),
                s="s" if len(targets) == 1 else "",
                ve="s" if len(targets) == 1 else "ve",
            )
        await ctx.send_ping(embed=embed)


def setup(ara: Ara):
    waifu_client = WaifuAioClient(ara.session)
    ara.add_cog(Waifus(waifu_client))
