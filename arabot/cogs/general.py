import random
import re

import disnake
from arabot.core import AnyEmoji, AnyMember, Ara, Category, Cog, Context
from arabot.core.utils import bold
from disnake.ext import commands


class AvatarView(disnake.ui.View):
    def __init__(self, avatars):
        super().__init__(timeout=None)
        self.avatars = avatars

    @disnake.ui.button(label="Default", style=disnake.ButtonStyle.blurple)
    async def user_avatar(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.avatars[0])

    @disnake.ui.button(label="Server", style=disnake.ButtonStyle.blurple)
    async def server_avatar(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.avatars[1])


class General(Cog, category=Category.GENERAL):
    def __init__(self, ara: Ara):
        self.ara = ara

    @commands.command(aliases=["a", "pfp"], brief="Show user's avatar")
    async def avatar(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        target = target or ctx.author
        avatars = (
            disnake.Embed()
            .set_image(url=(target.avatar or target.default_avatar).compat.url)
            .set_footer(text=f"{target.display_name}'s user avatar"),
            disnake.Embed()
            .set_image(url=target.display_avatar.compat.url)
            .set_footer(text=f"{target.display_name}'s server avatar"),
        )

        if not target.guild_avatar:
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=AvatarView(avatars))

    @commands.command(aliases=["emote", "e"], brief="Show full-sized versions of emoji(s)")
    async def emoji(self, ctx: Context, *emojis: AnyEmoji):
        emojis = list(dict.fromkeys(e for e in emojis if e))[:10]
        if not emojis:
            await ctx.send("No emojis found")
            return
        embed = disnake.Embed()
        for emoji in emojis:
            embed.add_field(emoji, f"[{emoji.name}]({emoji.url})", inline=False)
        await ctx.reply(embed=embed)

    @commands.command(aliases=["r"], brief="React to a message")
    async def react(self, ctx: Context, emoji: AnyEmoji = False):
        await ctx.message.delete()
        if not (ref_msg := await ctx.getch_reference_message()):
            await ctx.send("Reply to the message to react to")
            return
        if emoji is False:
            await ctx.reply("Specify an emoji to react with")
            return
        if not emoji:
            await ctx.send("Emoji not found")
            return

        try:
            await ref_msg.add_reaction(emoji)
        except disnake.Forbidden:
            try:
                await ctx.message.add_reaction("⛔")
            except disnake.Forbidden:
                await ctx.reply(f"Cannot add reactions to {ref_msg.author.mention}'s messages")

    @commands.cooldown(1, 60, commands.BucketType.member)
    @commands.command(brief="DM user to summon them")
    async def summon(self, ctx: Context, target: AnyMember = False, *, msg=None):
        if target is False:
            ctx.reset_cooldown()
            await ctx.send("Specify a user to summon")
            return
        if target is None:
            ctx.reset_cooldown()
            await ctx.send("User not found")
            return
        if target.bot:
            ctx.reset_cooldown()
            await ctx.send("Cannot summon bots")
            return
        if target not in ctx.channel.members:
            ctx.reset_cooldown()
            await ctx.send(f"{target.mention} doesn't have access to this channel")
            return
        invite = await ctx.guild.get_unlimited_invite() or disnake.Embed.Empty
        embed = disnake.Embed(
            description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}"
            "\n%s\n[Jump to message](%s)" % (f"\n{bold(msg)}" if msg else "", ctx.message.jump_url)
        ).set_author(
            name=ctx.guild.name,
            url=invite,
            icon_url=ctx.guild.icon.compat.url if ctx.guild.icon else disnake.Embed.Empty,
        )
        try:
            await target.send(embed=embed)
        except disnake.Forbidden:
            await ctx.send_mention(f"Cannot send messages to {target.mention}")
        else:
            await ctx.send_mention(f"Summoning {target.mention}")

    @commands.command(brief="Show user's banner")
    async def banner(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        target = target or ctx.author
        banner = (await ctx.ara.fetch_user(target.id)).banner
        if not banner:
            await ctx.send("User has no banner")
            return
        await ctx.send(
            embed=disnake.Embed()
            .set_image(url=banner.compat.with_size(4096).url)
            .set_footer(text=target.display_name + "'s banner")
        )

    @commands.command(brief="Suggest server emoji")
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

    @commands.command(brief="Make Ara say something")
    async def say(self, ctx: Context, *, msg):
        await ctx.message.delete()
        await ctx.send(msg)

    @commands.command(name="8ball", aliases=["8b"], brief="Ask the magic 8 ball")
    async def eight_ball(self, ctx: Context):
        answer = random.choice(("Yes", "No"))
        await ctx.reply(f"🎱 | {answer}")

    @commands.command(aliases=["pick"], brief="Make a choice for you")
    async def choose(self, ctx: Context, *, options):
        options = options.split("|")
        if len(options) < 2:
            await ctx.send("Not enough options provided")
            return
        pick = random.choice(options).strip()
        await ctx.reply(f"I pick {pick}")

    @commands.command(aliases=["vote"], brief="Create a poll and count votes")
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

    @commands.command(brief="HTTP Status Cats")
    async def http(self, ctx: Context, status_code: int):
        await ctx.send(
            f"https://http.cat/{status_code}"
            # fmt: off
            if status_code in {
                100, 101, 102,
                200, 201, 202, 203, 204, 206, 207,
                300, 301, 302, 303, 304, 305, 307, 308,
                400, 401, 402, 403, 404, 405, 406, 407, 408, 409, 410, 411, 412, 413, 414, 415, 416,
                417, 418, 420, 421, 422, 423, 424, 425, 426, 429, 431, 444, 450, 451, 497, 498, 499,
                500, 501, 502, 503, 504, 506, 507, 508, 509, 510, 511, 521, 523, 525, 599
            }
            # fmt: on
            else "Invalid status code"
        )


def setup(ara: Ara):
    ara.add_cog(General(ara))
