import random
from asyncio import sleep
from contextlib import suppress
from io import BytesIO

import disnake
from aiohttp import ClientSession
from disnake.ext import commands
from numpy.random import default_rng

from arabot.core import Ara, Category, Cog, Context, CustomEmoji
from arabot.utils import AnyMember

ADDING_REACTIONS = "Adding reactions"
NO_REACTION_PERMS = "I don't have permission to add reactions"
REACTIONS_ADDED = "Reactions added"
NO_GUILD_MEMBERS_INTENT = "I lack `GUILD_MEMBERS` Priviliged Intent to run this command"


class Fun(Cog, category=Category.FUN):
    def __init__(self, session: ClientSession):
        self.session = session

    @commands.command(brief="Get a random inspirational quote")
    async def inspire(self, ctx: Context):
        async with self.session.get("https://inspirobot.me/api?generate=true") as r:
            image_link = await r.text()
        await ctx.send(embed=disnake.Embed().set_image(url=image_link))

    @commands.command(aliases=["person"], brief="Get a randomly generated face")
    async def face(self, ctx: Context):
        async with self.session.get("https://thispersondoesnotexist.com/image") as r:
            image = BytesIO(await r.read())
        embed = disnake.Embed().set_image(file=disnake.File(image, "face.png"))
        await ctx.send(embed=embed)

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
        await inter.response.send_message(inter._(ADDING_REACTIONS), ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message(inter._(NO_REACTION_PERMS))
        else:
            await inter.edit_original_message(inter._(REACTIONS_ADDED))

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="I asked!", usage="[message or reply]", hidden=True)
    async def ia(self, ctx: Context, message: disnake.Message = None):
        with suppress(disnake.Forbidden):
            await ctx.message.delete()
            if not message and not (message := await ctx.getch_reference_message()):
                async for message in ctx.history(limit=4):
                    if message.webhook_id or not message.author.bot:
                        break
                else:
                    return
            for i in "🇮", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.MeiStare:
                await message.add_reaction(i)

    @commands.message_command(name="I asked!")
    async def iasked(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message(inter._(ADDING_REACTIONS), ephemeral=True)
        try:
            for i in "🇮", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.MeiStare:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message(inter._(NO_REACTION_PERMS))
        else:
            await inter.edit_original_message(inter._(REACTIONS_ADDED))

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
        await inter.response.send_message(inter._(ADDING_REACTIONS), ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message(inter._(NO_REACTION_PERMS))
        else:
            await inter.edit_original_message(inter._(REACTIONS_ADDED))

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="I care!", usage="[message or reply]", hidden=True)
    async def ic(self, ctx: Context, message: disnake.Message = None):
        with suppress(disnake.Forbidden):
            await ctx.message.delete()
            if not message and not (message := await ctx.getch_reference_message()):
                async for message in ctx.history(limit=4):
                    if message.webhook_id or not message.author.bot:
                        break
                else:
                    return
            for i in "🇮", "🇨", "🇦", "🇷", "🇪", CustomEmoji.MeiStare:
                await message.add_reaction(i)

    @commands.message_command(name="I care!")
    async def icare(self, inter: disnake.ApplicationCommandInteraction, msg: disnake.Message):
        await inter.response.send_message(inter._(ADDING_REACTIONS), ephemeral=True)
        try:
            for i in "🇮", "🇨", "🇦", "🇷", "🇪", CustomEmoji.MeiStare:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_message(inter._(NO_REACTION_PERMS))
        else:
            await inter.edit_original_message(inter._(REACTIONS_ADDED))

    @commands.command(aliases=["whom", "whose", "who's", "whos"], brief="Pings random person")
    async def who(self, ctx: Context):
        if isinstance(channel := ctx.channel, disnake.Thread):
            if len(members := await channel.fetch_members()) <= 1:
                await ctx.send_(NO_GUILD_MEMBERS_INTENT)
                return
            member = ctx.guild.get_member(random.choice(members).id)
        else:
            if len(members := channel.members) <= 1:
                await ctx.send_(NO_GUILD_MEMBERS_INTENT)
                return
            member = random.choice(channel.members)

        await ctx.reply(embed=disnake.Embed().with_author(member))

    @commands.command(
        aliases=["gp"],
        brief="Secretly ping a person",
        hidden=True,
        extras={"note": "This is a bug that only works on PC"},
    )
    async def ghostping(self, ctx: Context, member: AnyMember, *, text):
        await ctx.message.delete()
        if not member:
            return
        invis_bug = "||\u200b||" * 198 + "_ _"
        if len(message := text + invis_bug + member.mention) <= 2000:
            await ctx.send(message, allowed_mentions=disnake.AllowedMentions(users=True))

    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 60 * 60 * 24 * 1.75, commands.BucketType.member)
    @commands.command(aliases=["ren"], brief="Rename a person", cooldown_after_parsing=True)
    async def rename(self, ctx: Context, member: AnyMember, *, nick: str | None = None):
        if not member:
            ctx.reset_cooldown()
            await ctx.send_("User not found")
            return
        if nick and len(nick) > 32:
            ctx.reset_cooldown()
            await ctx.send_("Nickname cannot exceed 32 characters")
            return
        if member == ctx.author:
            ctx.reset_cooldown()
        elif ctx.author.top_perm_role < member.top_perm_role:
            ctx.reset_cooldown()
            await ctx.send_("Cannot rename users ranked higher than you")
            return

        try:
            await member.edit(nick=nick)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.send_("I don't have permission to rename this user")
            return

        await ctx.tick()

    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.command(aliases=["x"], brief="Doubt someone", usage="[member or reply]")
    async def doubt(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("User not found")
            return

        if member:
            if member == ctx.author:
                await ctx.send_("Never doubt yourself!")
                return

            async for msg_x in ctx.history(limit=20):
                if msg_x.author == member:
                    break
            else:
                await ctx.reply_("Message not found")
                return

        elif not (msg_x := await ctx.getch_reference_message()):
            if msg_x is False:
                if history := await ctx.history(before=ctx.message, limit=1).flatten():
                    msg_x = history[0]
            if not msg_x:
                await ctx.reply_("Message not found")
                return

        try:
            await msg_x.add_reaction(CustomEmoji.Doubt)
        except disnake.Forbidden:
            await ctx.reply_ping(
                ctx._("Cannot react to {}'s messages").format(msg_x.author.mention)
            )
            return

        await sleep(20)
        try:
            msg_x = await ctx.fetch_message(msg_x.id)
        except disnake.NotFound:
            await ctx.reply(f"{ctx._('Message was deleted')} {CustomEmoji.TooruWeary}")
            return

        if reaction := disnake.utils.find(lambda r: str(r) == CustomEmoji.Doubt, msg_x.reactions):
            await msg_x.reply(
                ctx._("{} people have doubted {}").format(reaction.count - 1, msg_x.author.mention)
            )
        else:
            await msg_x.reply(ctx._("Someone cleared all doubts 👀"))

    @commands.cooldown(1, 1800, commands.BucketType.member)
    @commands.command(brief="Find out someone's pp size", usage="[member]")
    async def pp(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("User not found")
            return
        member = member or ctx.author
        size = round(default_rng().triangular(1, 15, 25))
        pp = f"3{'='*(size-1)}D"
        await ctx.send(ctx._("{}'s pp size is **{} cm**\n{}").format(member.mention, size, pp))


def setup(ara: Ara):
    ara.add_cog(Fun(ara.session))
