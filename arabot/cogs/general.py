from arabot.core import Ara, Cog, Context
from arabot.utils import AnyEmoji, AnyMember, Category, bold
from disnake import ButtonStyle, Embed, Forbidden, MessageInteraction, ui
from disnake.ext.commands import BucketType, command, cooldown


class Avatar(ui.View):
    def __init__(self, avatars):
        super().__init__(timeout=None)
        self.avatars = avatars

    @ui.button(label="Default", style=ButtonStyle.blurple)
    async def user_avatar(self, button: ui.Button, interaction: MessageInteraction):
        await interaction.response.edit_message(embed=self.avatars[0])

    @ui.button(label="Server", style=ButtonStyle.blurple)
    async def server_avatar(self, button: ui.Button, interaction: MessageInteraction):
        await interaction.response.edit_message(embed=self.avatars[1])


class General(Cog, category=Category.GENERAL):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(aliases=["a", "pfp"], brief="Show user's avatar")
    async def avatar(self, ctx: Context, *, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        target = target or ctx.author
        avatars = (
            Embed()
            .set_image(url=target.avatar.with_static_format("png").url)
            .set_footer(text=f"{target.display_name}'s user avatar"),
            Embed()
            .set_image(url=target.display_avatar.with_static_format("png").url)
            .set_footer(text=f"{target.display_name}'s server avatar"),
        )

        if not target.guild_avatar:
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=Avatar(avatars))

    @command(
        aliases=["emote", "e"],
        brief="Show full-sized versions of emoji(s)",
    )
    async def emoji(self, ctx: Context, *emojis: AnyEmoji):
        emojis = list(dict.fromkeys(e for e in emojis if e))[:10]
        if not emojis:
            await ctx.send("No emojis found")
            return
        embed = Embed()
        for e in emojis:
            embed.add_field(name=e, value=f"[{e.name}]({e.url})", inline=False)
        await ctx.reply(embed=embed)

    @command(aliases=["r"], brief="Express your reaction with a big emoji")
    async def react(self, ctx: Context, emoji: AnyEmoji | None):
        if not emoji:
            await ctx.send("Emoji not found")
            return
        await ctx.message.delete()
        await ctx.send(
            embed=Embed()
            .set_image(url=emoji.url)
            .set_footer(
                text="reacted",
                icon_url=ctx.author.avatar.with_static_format("png").url,
            )
        )

    @cooldown(1, 60, BucketType.member)
    @command(brief="DM user to summon them")
    async def summon(self, ctx: Context, target: AnyMember = False, *, msg=None):
        if target is False:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Specify a user to summon")
            return
        if target is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("User not found")
            return
        if target.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("Cannot summon bots")
            return
        if target not in ctx.channel.members:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"{target.mention} doesn't have access to this channel")
            return
        invite = await ctx.guild.get_unlimited_invite() or Embed.Empty
        embed = Embed(
            description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}"
            "\n{}\n[Jump to message]({})".format(
                f"\n{bold(msg)}" if msg else "", ctx.message.jump_url
            )
        ).set_author(
            name=ctx.guild.name,
            url=invite,
            icon_url=ctx.guild.icon.with_static_format("png").url
            if ctx.guild.icon
            else Embed.Empty,
        )
        try:
            await target.send(embed=embed)
        except Forbidden:
            await ctx.send(f"Cannot send messages to {target.mention}")
        else:
            await ctx.send(f"Summoning {target.mention}")

    @command(brief="Show users's banner")
    async def banner(self, ctx: Context, target: AnyMember = False):
        if target is None:
            await ctx.send("User not found")
            return
        target = target or ctx.author
        banner = (await self.ara.fetch_user(target.id)).banner
        if not banner:
            await ctx.send("User has no banner")
            return
        await ctx.send(
            embed=Embed()
            .set_image(url=banner.with_static_format("png").with_size(4096).url)
            .set_footer(text=target.display_name + "'s banner")
        )

    @command(brief="Make Ara say something")
    async def say(self, ctx: Context, *, msg):
        await ctx.message.delete()
        await ctx.send(msg)


def setup(ara: Ara):
    ara.add_cog(General(ara))
