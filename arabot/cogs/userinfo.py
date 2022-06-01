from collections import defaultdict

import disnake
from arabot.core import AnyMember, AnyMemberOrUser, Ara, Category, Cog, Context
from disnake.ext import commands
from disnake.utils import format_dt


class GlobalOrGuildUserVariant(disnake.ui.View):
    def __init__(self, embeds):
        super().__init__(timeout=None)
        self.embeds = embeds

    @disnake.ui.button(label="Global", style=disnake.ButtonStyle.blurple)
    async def global_variant(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[0])

    @disnake.ui.button(label="Server", style=disnake.ButtonStyle.blurple)
    async def guild_variant(self, _button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[1])


class Userinfo(Cog, category=Category.GENERAL):
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
            .set_footer(text=f"{target.display_name}'s global avatar"),
            disnake.Embed()
            .set_image(url=target.display_avatar.compat.url)
            .set_footer(text=f"{target.display_name}'s server avatar"),
        )

        if not target.guild_avatar:
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=GlobalOrGuildUserVariant(avatars))

    @commands.command(aliases=["b"], brief="Show user's banner")
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
            .set_footer(text=f"{target.display_name}'s banner")
        )

    @commands.command(aliases=["user", "dox", "doxx", "whois"], brief="View user's info")
    async def userinfo(self, ctx: Context, *, target: AnyMemberOrUser = False):
        if target is None:
            await ctx.send("User not found")
            return
        target = target or ctx.author
        embed = (
            disnake.Embed(
                color=target.accent_color or disnake.Embed.get_default_color(),
                title=target,
                url=f"https://discord.com/users/{target.id}",
                timestamp=disnake.utils.utcnow(),
            )
            .set_author(
                name=target.id,
                icon_url="https://twemoji.maxcdn.com/v/latest/72x72/1f194.png",
                url=f"https://discord.com/users/{target.id}",
            )
            .set_thumbnail(url=(target.avatar or target.default_avatar).compat.url)
            .add_field("Created at", format_dt(target.created_at, "D"))
        )
        description = defaultdict(list)
        if target.bot:
            description[0].append("Bot")
        if target.public_flags.spammer:
            description[0].append("**Marked as spammer**")

        if target.banner:
            description[1].append(f"[Banner]({target.banner.url})")

        if isinstance(target, disnake.Member):
            embed.set_footer(text=target.guild.name, icon_url=ctx.guild.icon.as_icon.compat.url)
            if target.guild_avatar:
                description[1].append(f"[Server avatar]({target.guild_avatar.url})")
            if target.pending:
                description[0].append("Pending verification")

            if target.joined_at:
                embed.add_field("Joined at", format_dt(target.joined_at, "D"))
            if target.nick:
                embed.add_field("Nickname", target.nick)
            if target.activity:
                embed.add_field("Activity", target.activity.name)
            if target.premium_since:
                embed.add_field("Boosting since", format_dt(target.premium_since, "R"))
            if target.current_timeout:
                embed.add_field("Muted until", format_dt(target.current_timeout, "D"))
            elif target.voice and target.voice.channel:
                embed.add_field("Talking in", target.voice.channel.mention)
            embed.add_field("Highest role", target.top_role.mention)

        embed.description = "\n".join(", ".join(description[line]) for line in sorted(description))
        await ctx.send(embed=embed)


def setup(ara: Ara):
    ara.add_cog(Userinfo(ara))
