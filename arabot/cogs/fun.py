from asyncio import sleep
from io import BytesIO
from random import choice

import disnake
from aiohttp import ClientSession
from arabot.core import AnyMember, Ara, Category, Cog, Context, CustomEmoji
from disnake.ext import commands


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
    @commands.command(brief="Who asked?", hidden=True)
    async def wa(self, ctx: Context, msg: disnake.Message = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if msg.webhook_id or not msg.author.bot:
                    break
            else:
                return
        for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
            await msg.add_reaction(i)

    @commands.message_command(name="Who asked?")
    async def whoasked(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await (await inter.original_message()).edit("I don't have permission to add reactions")
        else:
            await (await inter.original_message()).edit("Reactions added")

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="Who cares?", hidden=True)
    async def wc(self, ctx: Context, msg: disnake.Message = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if msg.webhook_id or not msg.author.bot:
                    break
            else:
                return
        for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
            await msg.add_reaction(i)

    @commands.message_command(name="Who cares?")
    async def whocares(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message("Adding reactions", ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await (await inter.original_message()).edit("I don't have permission to add reactions")
        else:
            await (await inter.original_message()).edit("Reactions added")

    @commands.cooldown(3, 90, commands.BucketType.guild)
    @commands.command(aliases=["whom", "whose", "who's", "whos"], brief="Pings random person")
    async def who(self, ctx: Context):
        member = choice(ctx.channel.members)
        user_profile = disnake.Embed().set_author(
            name=member.display_name,
            icon_url=member.display_avatar.as_icon.compat.url,
            url=f"https://discord.com/users/{member.id}",
        )
        await ctx.reply(embed=user_profile)

    @commands.command(aliases=["gp"], brief="Secretly ping a person", hidden=True)
    async def ghostping(self, ctx: Context, target: AnyMember, *, msg):
        await ctx.message.delete()
        if not target:
            return
        invis_bug = "||\u200b||" * 198 + "_ _"
        if len(message := msg + invis_bug + target.mention) <= 2000:
            await ctx.send_mention(message)

    @commands.command(aliases=["ren"], brief="Rename a person", cooldown_after_parsing=True)
    @commands.cooldown(1, 60 * 60 * 24 * 3.5, commands.BucketType.member)
    async def rename(self, ctx: Context, target: AnyMember, *, nick: str | None = None):
        if not target:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return
        if target == ctx.author:
            ctx.reset_cooldown()
            await ctx.send("Cannot rename yourself")
            return

        # Get highest role that has at least one permission to exclude dummy roles e.g. colors
        get_top_role = lambda r: r.permissions.value != 0
        author_role = next(filter(get_top_role, reversed(ctx.author.roles)), ctx.guild.default_role)
        target_role = next(filter(get_top_role, reversed(target.roles)), ctx.guild.default_role)

        if author_role < target_role:
            ctx.reset_cooldown()
            await ctx.send("Cannot rename users ranked higher than you")
            return
        if nick and len(nick) > 32:
            ctx.reset_cooldown()
            await ctx.send("Nickname too long")
            return

        try:
            await target.edit(nick=nick)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.send("I don't have permission to rename this user")
            return

        await ctx.tick()

    @commands.command(aliases=["x"], brief="Doubt someone")
    @commands.max_concurrency(1, commands.BucketType.channel)
    async def doubt(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return

        if target:
            if target == ctx.author:
                ctx.reset_cooldown()
                await ctx.send("Never doubt yourself!")
                return

            async for msg_x in ctx.history(limit=20):
                if msg_x.author == target:
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
            await msg_x.reply("Someone cleared all the doubts 👀")


def setup(ara: Ara):
    ara.add_cog(Fun(ara.session))
