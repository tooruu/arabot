import random
import re

import disnake
from disnake.ext import commands

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import CUSTOM_EMOJI_RE, AnyEmoji, AnyEmojis, AnyMember, AnyMemberOrUser, bold

HTTP_CATS_VALID_CODES = {
    # fmt: off
    100, 101, 102,
    200, 201, 202, 203, 204, 206, 207,
    300, 301, 302, 303, 304, 305, 307, 308,
    400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416,
    417, 418, 420, 421, 422, 423, 424, 425, 426, 429, 431, 444, 450, 451, 497, 498, 499,
    500, 501, 502, 503, 504, 506, 507, 508, 509, 510, 511, 521, 523, 525, 599,
}


class General(Cog, category=Category.GENERAL):
    def __init__(self, ara: Ara):
        self.ara = ara

    @commands.command(
        aliases=["emote", "e", "sticker"],
        brief="Show links to full-sized versions of emojis and stickers",
        usage="<emojis or stickers...>",
    )
    async def emoji(self, ctx: Context, *, emojis: AnyEmojis = None):
        if not (stickers := ctx.message.stickers) and emojis is None:
            ref_msg = await ctx.getch_reference_message()
            custom_emojis = ref_msg and CUSTOM_EMOJI_RE.findall(ref_msg.content)
            stickers = getattr(ref_msg, "stickers", stickers)
            if not custom_emojis and not stickers:
                await ctx.reply("You must provide emojis/stickers")
                return
            converter = commands.PartialEmojiConverter()
            emojis = [await converter.convert(ctx, ce) for ce in custom_emojis]

        filtered_emojis = list(dict.fromkeys(e for e in emojis if e)) if emojis else []
        if not filtered_emojis and not stickers:
            await ctx.reply("No emojis/stickers found")
            return

        await ctx.reply(
            embed=disnake.Embed(
                description="\n".join(
                    f"{item} - [Link]({item.url}?quality=lossless&size=4096)"
                    for item in filtered_emojis + stickers
                )
            )
        )

    @commands.command(aliases=["r"], brief="React to a message", usage="<emoji>")
    async def react(self, ctx: Context, emoji: AnyEmoji = False):
        if not (ref_msg := await ctx.getch_reference_message()):
            await ctx.reply("Reply to the message to react to")
            return
        if emoji is False:
            await ctx.reply("Specify an emoji to react with")
            return
        if not emoji:
            await ctx.reply("Emoji not found")
            return

        await ctx.message.delete()
        try:
            await ref_msg.add_reaction(emoji)
        except disnake.Forbidden:
            try:
                await ctx.message.add_reaction("⛔")
            except disnake.Forbidden:
                await ctx.reply_ping(f"Cannot add reactions to {ref_msg.author.mention}'s messages")

    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.command(brief="DM user to summon them", usage="<member> [text]")
    async def summon(self, ctx: Context, member: AnyMember = False, *, text=None):
        if member is False:
            ctx.reset_cooldown()
            await ctx.send("Specify a user to summon")
            return
        if member is None:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return
        if member.bot:
            ctx.reset_cooldown()
            await ctx.send("Cannot summon bots")
            return
        if member not in ctx.channel.members:
            ctx.reset_cooldown()
            await ctx.send_ping(f"{member.mention} doesn't have access to this channel")
            return
        invite = await ctx.guild.get_unlimited_invite_link() or disnake.Embed.Empty
        embed = disnake.Embed(
            description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}"
            "\n%s\n[Jump to message](%s)"
            % (f"\n{bold(text)}" if text else "", ctx.message.jump_url)
        ).set_author(
            name=ctx.guild.name,
            url=invite,
            icon_url=ctx.guild.icon.as_icon.compat if ctx.guild.icon else disnake.Embed.Empty,
        )
        try:
            await member.send(embed=embed)
        except disnake.Forbidden:
            ctx.reset_cooldown()
            await ctx.send_ping(f"Cannot send messages to {member.mention}")
        else:
            await ctx.send_ping(f"Summoning {member.mention}")

    @commands.command(brief="Suggest server emoji", usage="<server emoji> <new emoji>", hidden=True)
    async def chemoji(self, ctx: Context, em_before: AnyEmoji, em_after=None):
        if em_before not in ctx.guild.emojis:
            await ctx.send("Choose a valid server emoji to replace")
            return
        if em_after and ctx.message.attachments:
            await ctx.send("You can only have one suggestion type in submission")
            return
        if not (em_after or ctx.message.attachments):
            await ctx.send("You must include one emoji suggestion")
            return

        if ctx.message.attachments:
            em_after = ctx.message.attachments[0].url

        if re.fullmatch(r"https?://(-\.)?([^\s/?\.#]+\.?)+(/\S*)?", em_after):
            async with ctx.ara.session.get(em_after) as resp:
                if not (resp.ok and resp.content_type.startswith("image/")):
                    await ctx.send(f"Link a valid image to replace {em_before} with")
                    return
        elif re.fullmatch(r"<a?:\w{2,32}:\d{18,22}>", em_after, re.ASCII):
            emoji = await commands.PartialEmojiConverter().convert(ctx, em_after)
            if emoji in ctx.guild.emojis:
                await ctx.send(f"We already have {em_after}")
                return
            em_after = emoji.url
        else:
            await ctx.send(f"Choose a valid emoji to replace {em_before} with")
            return

        if not ctx.message.attachments:
            await ctx.message.delete()

        message = await ctx.send(
            embed=disnake.Embed(title="wants to change this →", description="to that ↓")
            .set_thumbnail(url=em_before.url)
            .set_image(url=em_after)
            .with_author(ctx.author)
        )
        await message.add_reaction("👍")
        await message.add_reaction("👎")

    @commands.command(brief="Make Ara say something", extras={"note": "Cannot ping roles"})
    async def say(self, ctx: Context, *, text):
        await ctx.message.delete()
        await ctx.send(text, allowed_mentions=disnake.AllowedMentions(users=True))

    @commands.command(name="8ball", aliases=["8b"], brief="Ask the magic 8 ball")
    async def eight_ball(self, ctx: Context):
        answer = random.choice(("Yes", "No"))
        await ctx.reply(f"🎱 | {answer}")

    @commands.command(
        aliases=["pick"], brief="Make a choice for you", usage="<option 1>|<option 2>|..."
    )
    async def choose(self, ctx: Context, *, options):
        options = options.split("|")
        if len(options) < 2:
            await ctx.send("Not enough options provided")
            return
        pick = random.choice(options).strip()
        await ctx.reply(f"I pick {pick}")

    @commands.command(
        aliases=["vote", "survey"],
        brief="Create a poll",
        usage="<topic> OR <topic>|<option 1>|<option 2>|...",
    )
    async def poll(self, ctx: Context, *, options):
        options = [opt.strip() for opt in options.split("|")]
        if not options:
            await ctx.send("Poll topic is required")
            return
        topic = options.pop(0)
        if len(options) == 1:
            await ctx.send("Not enough options provided")
            return
        if len(options) > 10:
            await ctx.send("More than 10 options provided")
            return
        options = options or ["Yes", "No"]

        await ctx.message.delete()
        indices = "1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣", "7️⃣", "8️⃣", "9️⃣", "🔟"
        body = "\n".join(f"{n} {option}" for n, option in zip(indices, options))
        embed = disnake.Embed(title=topic, description=body).with_author(ctx.author)
        poll = await ctx.send(embed=embed)
        for i in indices[: len(options)]:
            await poll.add_reaction(i)

    @commands.command(brief="Show HTTP status code cat picture")
    async def http(self, ctx: Context, http_status_code: int):
        await ctx.send(
            f"https://http.cat/{http_status_code}"
            if http_status_code in HTTP_CATS_VALID_CODES
            else "Invalid HTTP status code"
        )

    @commands.bot_has_permissions(manage_webhooks=True)
    @commands.command(
        aliases=["imp"],
        brief="Pretend to be somebody else",
        extras={"note": "Cannot ping roles"},
    )  # (c) 2022 by Kriz#0385
    async def impersonate(self, ctx: Context, user: AnyMemberOrUser, *, text):
        if user == ctx.me:
            await self.say(ctx, text=text)
            return
        if not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            await ctx.send("I lack permission to manage webhooks")
            return
        if not user:
            await ctx.reply("User not found")
            return

        await ctx.message.delete()
        webhook = await ctx.channel.create_webhook(name=user, avatar=user.display_avatar)
        await webhook.send(
            text,
            username=user.display_name,
            allowed_mentions=disnake.AllowedMentions(users=True),
        )
        await webhook.delete()


def setup(ara: Ara):
    ara.add_cog(General(ara))
