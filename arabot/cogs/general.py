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

    @commands.command(aliases=["r"], brief="Express your reaction with a big emoji")
    async def react(self, ctx: Context, emoji: AnyEmoji | None):
        if not emoji:
            await ctx.send("Emoji not found")
            return
        await ctx.message.delete()
        await ctx.send(
            embed=disnake.Embed()
            .set_image(url=emoji.url)
            .set_footer(
                text="reacted",
                icon_url=ctx.author.display_avatar.as_icon.compat.url,
            )
        )

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
    async def banner(self, ctx: Context, target: AnyMember = False):
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
            .set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.display_avatar.as_icon.compat.url,
            )
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

def setup(ara: Ara):
    ara.add_cog(General(ara))
