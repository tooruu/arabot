import logging
import re
from collections import defaultdict

import disnake
from disnake.ext import commands
from disnake.utils import escape_markdown, format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import I18N, AnyMember, AnyMemberOrUser, Twemoji


class GlobalOrGuildUserVariant(disnake.ui.View):
    def __init__(self, embeds: tuple[disnake.Embed, disnake.Embed]):
        super().__init__(timeout=None)
        self.embeds = embeds

    @disnake.ui.button(label="Global", style=disnake.ButtonStyle.blurple)
    async def global_variant(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[0])

    @disnake.ui.button(label="Server", style=disnake.ButtonStyle.blurple)
    async def guild_variant(self, button: disnake.ui.Button, inter: disnake.MessageInteraction):
        await inter.response.edit_message(embed=self.embeds[1])


class Userinfo(Cog, category=Category.GENERAL):
    @commands.command(aliases=["a", "pfp"], brief="Show user's avatar", usage="[user]")
    async def avatar(self, ctx: Context, *, member: AnyMemberOrUser = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        avatars = (
            disnake.Embed()
            .set_image(member.avatar or member.default_avatar)
            .set_footer(text=ctx._("global_avatar").format(member.display_name)),
            disnake.Embed()
            .set_image(member.display_avatar)
            .set_footer(text=ctx._("guild_avatar").format(member.display_name)),
        )

        if not getattr(member, "guild_avatar", None):
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=GlobalOrGuildUserVariant(avatars))

    @commands.command(
        aliases=["b"],
        brief="Show user's global banner",
        usage="[user]",
        extras={"note": "Due to a Discord limitation, server banners are irretrievable"},
    )
    async def banner(self, ctx: Context, *, member: AnyMemberOrUser = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        banner = (await ctx.ara.fetch_user(member.id)).banner
        if not banner:
            await ctx.send_("no_banner")
            return
        await ctx.send(
            embed=disnake.Embed()
            .set_image(banner.maxres)
            .set_footer(text=ctx._("their_banner", False).format(member.display_name))
        )

    @commands.command(
        aliases=["user", "dox", "doxx", "whois"], brief="View user's info", usage="[user]"
    )
    async def userinfo(self, ctx: Context, *, member: AnyMemberOrUser = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member = member or ctx.author
        embed = (
            disnake.Embed(
                title=member.display_name,
                url=f"https://discord.com/users/{member.id}",
                timestamp=utcnow(),
            )
            .set_thumbnail(url=member.avatar or member.default_avatar)
            .add_field(ctx._("created_on"), format_dt(member.created_at, "D"))
        )
        self._set_author(embed, member)
        await self._set_fields_description_image_color(embed, member, ctx)
        await ctx.send(embed=embed)

    @staticmethod
    def _set_author(embed: disnake.Embed, user: disnake.abc.User | disnake.Member) -> None:
        username, global_name, nickname = user.name, user.global_name, getattr(user, "nick", None)
        if (
            not global_name
            and not nickname
            or username == global_name == nickname
            or username in (global_name, nickname)
            and None in (global_name, nickname)
        ):
            return
        author_info = ("@" if user.discriminator == "0" else "") + str(user)
        if global_name and nickname and username != global_name != nickname:
            author_info += f" | {global_name}"
        embed.set_author(name=author_info, url=f"https://discord.com/users/{user.id}")

    @staticmethod
    async def _set_fields_description_image_color(
        embed: disnake.Embed, user: disnake.User | disnake.Member, ctx: Context
    ) -> None:
        description = defaultdict(list[str])
        if user.bot:
            description[0].append(ctx._("bot", False))
        if user.public_flags.spammer:
            description[0].append(f"**{ctx._('spammer')}**")

        if isinstance(user, disnake.Member):
            embed.set_footer(
                text=user.guild.name,
                icon_url=ctx.guild.icon and ctx.guild.icon.as_icon,
            )
            if user.guild_avatar:
                description[1].append(f"[{ctx._('guild_avatar')}]({user.guild_avatar})")
            if user.pending:
                description[0].append(ctx._("pending"))

            if user.joined_at:
                embed.add_field(ctx._("joined_on"), format_dt(user.joined_at, "D"))
            if user.premium_since:
                embed.add_field(ctx._("boosting_since"), format_dt(user.premium_since, "R"))
            embed.add_field(ctx._("top_perm_role"), user.top_perm_role.mention)
            if user.current_timeout:
                embed.add_field(ctx._("muted_until"), format_dt(user.current_timeout, "D"))
            elif user.voice and user.voice.channel:
                embed.add_field(ctx._("talking_in"), user.voice.channel.mention)
            user = await ctx.ara.fetch_user(user.id)  # `Member.banner` is always None
        elif not user.accent_color:  # Likely unreliable check if `User` is retrieved from cache
            user = await ctx.ara.fetch_user(user.id)  # Fetching as `User.banner` is not cached

        if user.accent_color:
            embed.color = user.accent_color
        if user.banner:
            embed.set_image(user.banner.with_size(512))

        embed.description = "\n".join(", ".join(description[line]) for line in sorted(description))

    @commands.command(
        aliases=["s", "st", "activity", "act"], brief="View user's activity", usage="[member]"
    )
    async def status(self, ctx: Context, *, member: AnyMember = False):
        if member is None:
            await ctx.send_("user_not_found", False)
            return
        member: disnake.Member = member or ctx.author
        embed: disnake.Embed = disnake.Embed(title=ctx._("activity", False)).with_author(member)
        self._add_status(embed, member)
        for activity in member.activities:
            if not embed.thumbnail:
                self._set_images_if_any(embed, activity)
            self._add_activity(embed, activity, ctx._)
        await ctx.send(embed=embed)

    @staticmethod
    def _add_activity(
        embed: disnake.Embed, activity: disnake.BaseActivity | disnake.Spotify, _: I18N
    ) -> None:
        name = body = ""
        match activity:
            case disnake.CustomActivity():
                if activity.emoji:
                    icon_url = (activity.emoji.url or Twemoji(activity.emoji.name).url) + "?size=32"
                else:
                    icon_url = None
                embed.set_footer(text=activity.name or "\u200b", icon_url=icon_url)
                return
            case disnake.Spotify():
                embed.color = activity.color
                name = activity.album
                body = f"[{', '.join(activity.artists)} – {activity.title}]({activity.track_url})"
            case disnake.Activity(name="Spotify", type=disnake.ActivityType.listening):
                name = activity.large_image_text
                body = f"{activity.state} – {activity.details}"
            case disnake.Game() | disnake.Activity(type=disnake.ActivityType.listening):
                if activity.start or activity.end:
                    name = activity.name
                else:
                    body = activity.name
            case disnake.Activity(
                type=disnake.ActivityType.playing
                | disnake.ActivityType.watching
                | disnake.ActivityType.competing
            ):
                party = ""
                if party_size := activity.party.get("size"):
                    current, max_ = party_size
                    party = f" ({current}/{max_})"

                if activity.details:
                    name, body = activity.name, activity.details
                    if activity.state:
                        body += f"\n{activity.state} {party}"
                elif activity.state:
                    name, body = activity.name, activity.state + party
                elif activity.start or activity.end:
                    name = activity.name + party
                else:
                    body = activity.name + party
            case disnake.Streaming():
                if activity.game and activity.name:
                    name = activity.game
                    body = f"[{activity.name}]({activity.url})"
                elif activity.game:
                    body = f"[{activity.game}]({activity.url})"
                elif activity.name:
                    body = f"[{activity.name}]({activity.url})"
                elif activity.platform:
                    body = f"[{activity.platform}]({activity.url})"
                else:
                    body = activity.url
            case _:
                logging.warning("Unknown activity type: %s", activity)
                return

        if activity.start:
            body += "\n" + _("started").format(format_dt(activity.start, "R"))
        if activity.end:
            if activity.start:
                body += ", " + _("ending_in").lower().format(format_dt(activity.end, "R"))
            else:
                body += "\n" + _("ending_in").format(format_dt(activity.end, "R"))

        body = re.sub(r"\\(\[.+\]\(.+\))", r"\1", escape_markdown(body))
        embed.add_field(_(activity.type.name).format(name), body, inline=False)

    @staticmethod
    def _add_status(embed: disnake.Embed, member: disnake.Member) -> None:
        statuses = {
            disnake.Status.online: "🟢",
            disnake.Status.idle: "🟠",
            disnake.Status.do_not_disturb: "⛔",
            disnake.Status.offline: "⚫",
        }
        if member.status is disnake.Status.offline:
            embed.description = statuses[member.status]
        else:
            devices = {"desktop": "💻", "mobile": "📱", "web": "🌐"}
            device_statuses = {d: [] for d in statuses}
            for device_name, device_icon in devices.items():
                device_status: disnake.Status = getattr(member, f"{device_name}_status")
                if device_status is not disnake.Status.offline:
                    device_statuses[device_status].append(device_icon)
            embed.description = " | ".join(
                f"{''.join(icons)}{statuses[st]}" for st, icons in device_statuses.items() if icons
            )

    @staticmethod
    def _set_images_if_any(
        embed: disnake.Embed, activity: disnake.BaseActivity | disnake.Spotify
    ) -> None:
        if isinstance(activity, disnake.Spotify) and activity.album_cover_url:
            embed.set_thumbnail(activity.album_cover_url)
        elif thumbnail := getattr(activity, "large_image_url", None):
            embed.set_thumbnail(fix_media_proxy_url(thumbnail))


def fix_media_proxy_url(asset_url: str) -> str:  # Remove in disnake 2.10
    if "/mp:" not in asset_url:
        return asset_url
    return "https://media.discordapp.net/" + asset_url.partition("/mp:")[2].removesuffix(".png")


def setup(ara: Ara):
    ara.add_cog(Userinfo())
