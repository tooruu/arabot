import random
from asyncio import sleep
from contextlib import suppress
from io import BytesIO

import disnake
from aiohttp import ClientSession
from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyMember
from disnake.ext import commands
from numpy.random import default_rng


class Fun(Cog, category=Category.FUN):
    def __init__(self, session: ClientSession):
        self.session = session

    @commands.command(brief="Get a random inspirational quote")
    async def inspire(self, ctx: Context):
        async with self.session.get("https://inspirobot.me/api?generate=true") as r:
            image_link = await r.text()
        await ctx.send(image_link)

    @commands.command(aliases=["person"], brief="Get a randomly generated face")
    async def face(self, ctx: Context):
        async with self.session.get("https://thispersondoesnotexist.com/image") as r:
            image = BytesIO(await r.read())
            await ctx.send(file=disnake.File(image, "face.png"))

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="Who asked?", usage="[message or reply]", hidden=True)
    async def wa(self, ctx: Context, message: disnake.Message = None):
        with suppress(disnake.Forbidden):
            await ctx.message.delete()
            if not message and not (message := await ctx.getch_reference_message()):
                async for message in ctx.history(limit=4):
                    if message.webhook_id or not message.author.bot:
                        break
                else:
                    return
            for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
                await message.add_reaction(i)

    @commands.message_command(name="Who asked?")
    async def whoasked(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message("I don't have permission to add reactions")
        else:
            await inter.edit_original_message("Reactions added")

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="Who cares?", usage="[message or reply]", hidden=True)
    async def wc(self, ctx: Context, message: disnake.Message = None):
        with suppress(disnake.Forbidden):
            await ctx.message.delete()
            if not message and not (message := await ctx.getch_reference_message()):
                async for message in ctx.history(limit=4):
                    if message.webhook_id or not message.author.bot:
                        break
                else:
                    return
            for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
                await message.add_reaction(i)

    @commands.message_command(name="Who cares?")
    async def whocares(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message("I don't have permission to add reactions")
        else:
            await inter.edit_original_message("Reactions added")

    @commands.command(aliases=["whom", "whose", "who's", "whos"], brief="Pings random person")
    async def who(self, ctx: Context):
        member = random.choice(ctx.channel.members)
        await ctx.reply(embed=disnake.Embed().with_author(member))

    @commands.command(aliases=["gp"], brief="Secretly ping a person", hidden=True)
    async def ghostping(self, ctx: Context, member: AnyMember, *, text):
        await ctx.message.delete()
        if not member:
            return
        invis_bug = "||\u200b||" * 198 + "_ _"
        if len(message := text + invis_bug + member.mention) <= 2000:
            await ctx.send_mention(message)

    @commands.cooldown(1, 60 * 60 * 24 * 1.75, commands.BucketType.member)
    @commands.command(aliases=["ren"], brief="Rename a person", cooldown_after_parsing=True)
    async def rename(self, ctx: Context, member: AnyMember, *, nick: str | None = None):
        if not member:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return
        if nick and len(nick) > 32:
            ctx.reset_cooldown()
            await ctx.send("Nickname cannot exceed 32 characters")
            return
        if member == ctx.author:
            ctx.reset_cooldown()
        elif ctx.author.top_perm_role < member.top_perm_role:
            ctx.reset_cooldown()
            await ctx.send("Cannot rename users ranked higher than you")
            return

        try:
            await member.edit(nick=nick)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.send("I don't have permission to rename this user")
            return

        await ctx.tick()

    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.command(aliases=["x"], brief="Doubt someone", usage="[member or reply]")
    async def doubt(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return

        if member:
            if member == ctx.author:
                ctx.reset_cooldown()
                await ctx.send("Never doubt yourself!")
                return

            async for msg_x in ctx.history(limit=20):
                if msg_x.author == member:
                    break
            else:
                ctx.reset_cooldown()
                await ctx.reply("Message not found")
                return

        elif not (msg_x := await ctx.getch_reference_message()):
            if msg_x is False:
                if history := await ctx.history(before=ctx.message, limit=1).flatten():
                    msg_x = history[0]
            if not msg_x:
                ctx.reset_cooldown()
                await ctx.reply("Message not found")
                return

        try:
            await msg_x.add_reaction(CustomEmoji.Doubt)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.reply(f"Cannot react to {msg_x.author.mention}'s messages")
            return

        await sleep(20)
        try:
            msg_x = await ctx.fetch_message(msg_x.id)
        except disnake.NotFound:
            await ctx.reply(f"Message was deleted {CustomEmoji.TooruWeary}")
            return

        if reaction := disnake.utils.find(lambda r: str(r) == CustomEmoji.Doubt, msg_x.reactions):
            await msg_x.reply(f"{reaction.count - 1} people have doubted {msg_x.author.mention}")
        else:
            await msg_x.reply("Someone cleared all doubts 👀")

    @commands.cooldown(1, 1800, commands.BucketType.member)
    @commands.command(brief="Find out someone's pp size", usage="[member]")
    async def pp(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send("User not found")
            return
        member = member or ctx.author
        size = round(default_rng().triangular(1, 15, 25))
        pp = f"3{'='*(size-1)}D"
        await ctx.send(f"{member.mention}'s pp size is **{size} cm**\n{pp}")


def setup(ara: Ara):
    ara.add_cog(Fun(ara.session))
