from io import BytesIO
from random import choice
from urllib.parse import quote

from aiohttp import ClientResponseError
from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyMember, CustomEmoji
from disnake import AllowedMentions, ApplicationCommandInteraction, File, Forbidden, Message
from disnake.ext.commands import BucketType, command, cooldown, message_command


class Fun(Cog, category=Category.FUN):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(brief="Get a random inspirational quote")
    async def inspire(self, ctx: Context):
        async with self.ara.session.get("https://inspirobot.me/api?generate=true") as r:
            image_link = await r.text()
        await ctx.send(image_link)

    @command(brief="Get a randomly generated face", aliases=["person"])
    async def face(self, ctx: Context):
        async with self.ara.session.get("https://thispersondoesnotexist.com/image") as r:
            image = BytesIO(await r.read())
            await ctx.send(file=File(image, "face.png"))

    @cooldown(1, 10, BucketType.channel)
    @command(brief="Who asked?", hidden=True)
    async def wa(self, ctx: Context, msg: Message = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if msg.webhook_id or not msg.author.bot:
                    break
            else:
                return
        for i in (
            "🇼",
            "🇭",
            "🇴",
            "🇦",
            "🇸",
            "🇰",
            "🇪",
            "🇩",
            CustomEmoji.FUKAWHY,
        ):
            await msg.add_reaction(i)

    @message_command(name="Who asked?")
    async def whoasked(self, inter: ApplicationCommandInteraction, msg: Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in (
                "🇼",
                "🇭",
                "🇴",
                "🇦",
                "🇸",
                "🇰",
                "🇪",
                "🇩",
                CustomEmoji.FUKAWHY,
            ):
                await msg.add_reaction(i)
        except Forbidden:
            await (await inter.original_message()).edit(
                content="I don't have permission to add reactions"
            )
        else:
            await (await inter.original_message()).edit(content="Reactions added")

    @cooldown(1, 10, BucketType.channel)
    @command(brief="Who cares?", hidden=True)
    async def wc(self, ctx: Context, msg: Message = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if msg.webhook_id or not msg.author.bot:
                    break
            else:
                return
        for i in (
            "🇼",
            "🇭",
            "🇴",
            "🇨",
            "🇦",
            "🇷",
            "🇪",
            "🇸",
            CustomEmoji.TOORUWEARY,
        ):
            await msg.add_reaction(i)

    @message_command(name="Who cares?")
    async def whocares(self, inter: ApplicationCommandInteraction, msg: Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in (
                "🇼",
                "🇭",
                "🇴",
                "🇨",
                "🇦",
                "🇷",
                "🇪",
                "🇸",
                CustomEmoji.FUKAWHY,
            ):
                await msg.add_reaction(i)
        except Forbidden:
            await (await inter.original_message()).edit(
                content="I don't have permission to add reactions"
            )
        else:
            await (await inter.original_message()).edit(content="Reactions added")

    @cooldown(3, 90, BucketType.guild)
    @command(aliases=["whom", "whose", "who's", "whos"], brief="Pings random person")
    async def who(self, ctx: Context):
        member = choice(ctx.channel.members)
        await ctx.reply(member.mention)

    @command(aliases=["gp"], brief="Pings person without mention", hidden=True)
    async def ghostping(self, ctx: Context, target: AnyMember, *, msg):
        await ctx.message.delete()
        if not target:
            return
        invis = "||​||" * 198 + " _" * 6
        await ctx.send(f"{msg} {invis} {target.mention}", allowed_mentions=AllowedMentions.all())

    @command(name="8ball", aliases=["8b"], brief="Ask the magic 8 ball")
    async def eight_ball(self, ctx: Context, *, question=" "):
        try:
            url = "https://8ball.delegator.com/magic/JSON/" + quote(question, safe="")
            json = await self.ara.session.fetch_json(url)
            answer = json["magic"]["answer"]
        except ClientResponseError:
            answer = choice(("Yes", "No"))
        await ctx.reply(f"🎱 | {answer}")


def setup(ara: Ara):
    ara.add_cog(Fun(ara))
