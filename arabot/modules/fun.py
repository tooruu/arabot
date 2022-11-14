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


class Fun(Cog, category=Category.FUN):
    ADDING_REACTIONS = f"{__module__}.adding_reactions"
    MESSAGE_DELETED = f"{__module__}.message_deleted"
    REACTIONS_ADDED = f"{__module__}.reactions_added"

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
        with suppress(disnake.Forbidden, disnake.NotFound):
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
        await inter.response.send_message(inter._(Fun.ADDING_REACTIONS, False), ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.FukaWhy:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_response(
                inter._("no_perms_to", False).format("add reactions")
            )
        except disnake.NotFound:
            await inter.edit_original_response(inter._(Fun.MESSAGE_DELETED, False))
        else:
            await inter.edit_original_response(inter._(Fun.REACTIONS_ADDED, False))

    @commands.cooldown(1, 10, commands.BucketType.channel)
    @commands.command(brief="I asked!", usage="[message or reply]", hidden=True)
    async def ia(self, ctx: Context, message: disnake.Message = None):
        with suppress(disnake.Forbidden, disnake.NotFound):
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
        await inter.response.send_message(inter._(Fun.ADDING_REACTIONS, False), ephemeral=True)
        try:
            for i in "🇮", "🇦", "🇸", "🇰", "🇪", "🇩", CustomEmoji.MeiStare:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_response(
                inter._("no_perms_to", False).format("add reactions")
            )
        except disnake.NotFound:
            await inter.edit_original_response(inter._(Fun.MESSAGE_DELETED, False))
        else:
            await inter.edit_original_response(inter._(Fun.REACTIONS_ADDED, False))

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
        await inter.response.send_message(inter._(Fun.ADDING_REACTIONS, False), ephemeral=True)
        try:
            for i in "🇼", "🇭", "🇴", "🇨", "🇦", "🇷", "🇪", "🇸", CustomEmoji.TooruWeary:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_response(
                inter._("no_perms_to", False).format("add reactions")
            )
        else:
            await inter.edit_original_response(inter._(Fun.REACTIONS_ADDED, False))

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
        await inter.response.send_message(inter._(Fun.ADDING_REACTIONS, False), ephemeral=True)
        try:
            for i in "🇮", "🇨", "🇦", "🇷", "🇪", CustomEmoji.MeiStare:
                await msg.add_reaction(i)
        except disnake.Forbidden:
            await inter.edit_original_response(
                inter._("no_perms_to", False).format("add reactions")
            )
        else:
            await inter.edit_original_response(inter._(Fun.REACTIONS_ADDED))

    @commands.command(aliases=["whom", "whose", "who's", "whos"], brief="Pings random person")
    async def who(self, ctx: Context):
        if isinstance(channel := ctx.channel, disnake.Thread):
            if len(members := await channel.fetch_members()) <= 1:
                await ctx.send(ctx._("no_priviliged_intent", False).format("GUILD_MEMBERS"))
                return
            member = ctx.guild.get_member(random.choice(members).id)
        else:
            if len(members := channel.members) <= 1:
                await ctx.send(ctx._("no_priviliged_intent", False).format("GUILD_MEMBERS"))
                return
            member = random.choice(channel.members)

        await ctx.reply(embed=disnake.Embed().with_author(member))

    @commands.command(
        aliases=["gp"],
        brief="Secretly ping a person",
        hidden=True,
        extras={"note": "This is a Discord bug that may be fixed in the future"},
    )
    async def ghostping(self, ctx: Context, member: AnyMember, *, text):
        await ctx.message.delete()
        if not member:
            return
        invis_bug = "||\u200b||" * 250
        if len(message := text + invis_bug + member.mention) <= 2000:
            await ctx.send(message, allowed_mentions=disnake.AllowedMentions(users=True))

    @commands.bot_has_permissions(manage_nicknames=True)
    @commands.cooldown(1, 60 * 60 * 24 * 1.75, commands.BucketType.member)
    @commands.command(aliases=["ren"], brief="Rename a person", cooldown_after_parsing=True)
    async def rename(self, ctx: Context, member: AnyMember, *, nick: str | None = None):
        if not member:
            ctx.reset_cooldown()
            await ctx.send_("user_not_found", False)
            return
        if nick and len(nick) > 32:
            ctx.reset_cooldown()
            await ctx.send_("too_long")
            return
        if member == ctx.author:
            ctx.reset_cooldown()
        elif ctx.author.top_perm_role < member.top_perm_role:
            ctx.reset_cooldown()
            await ctx.send_("rank_too_low")
            return

        try:
            await member.edit(nick=nick)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.send(ctx._("no_perms_to", False).format("rename this user"))
            return

        await ctx.tick()

    @commands.max_concurrency(1, commands.BucketType.channel)
    @commands.command(aliases=["x"], brief="Doubt someone", usage="[member or reply]")
    async def doubt(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return

        if member:
            if member == ctx.author:
                await ctx.send_("never_doubt_yourself")
                return

            async for msg_x in ctx.history(limit=20):
                if msg_x.author == member:
                    break
            else:
                await ctx.reply_("message_not_found", False)
                return

        elif not (msg_x := await ctx.getch_reference_message()):
            if msg_x is False:
                if history := await ctx.history(before=ctx.message, limit=1).flatten():
                    msg_x = history[0]
            if not msg_x:
                await ctx.reply_("message_not_found", False)
                return

        try:
            await msg_x.add_reaction(CustomEmoji.Doubt)
        except disnake.Forbidden:
            await ctx.reply_ping(ctx._("cant_react_to", False).format(msg_x.author.mention))
            return

        await sleep(20)
        try:
            msg_x = await ctx.fetch_message(msg_x.id)
        except disnake.NotFound:
            await ctx.reply(f"{ctx._('message_deleted')} {CustomEmoji.TooruWeary}")
            return

        if reaction := disnake.utils.find(lambda r: str(r) == CustomEmoji.Doubt, msg_x.reactions):
            await msg_x.reply(
                ctx._("people_doubted").format(reaction.count - 1, msg_x.author.mention)
            )
        else:
            await msg_x.reply(ctx._("doubts_cleared"))

    @commands.cooldown(1, 1800, commands.BucketType.member)
    @commands.command(brief="Find out someone's pp size", usage="[member]")
    async def pp(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        size = round(default_rng().triangular(1, 15, 25))
        pp = f"3{'='*(size-1)}D"
        await ctx.send(ctx._("pp").format(member.mention, size, pp))


def setup(ara: Ara):
    ara.add_cog(Fun(ara.session))
