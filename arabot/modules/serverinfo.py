import re
from collections import defaultdict
from collections.abc import Callable

import disnake
from disnake.ext import commands
from disnake.utils import format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyGuild, mono


class Serverinfo(Cog, category=Category.GENERAL):
    def __init__(self, presences_intent: bool):
        self.presences_intent = presences_intent

    @commands.command(aliases=["sa", "spfp"], brief="Show server's icon")
    async def serveravatar(self, ctx: Context):
        if not ctx.guild.icon:
            await ctx.send_("no_icon")
            return
        await ctx.send(
            embed=disnake.Embed(timestamp=utcnow())
            .set_image(url=ctx.guild.icon.maxres.compat)
            .set_footer(text=ctx.guild)
        )

    @commands.command(aliases=["sb"], brief="Show server's banner")
    async def serverbanner(self, ctx: Context):
        if not ctx.guild.banner:
            await ctx.send_("no_banner")
            return
        await ctx.send(
            embed=disnake.Embed(timestamp=utcnow())
            .set_image(url=ctx.guild.banner.maxres.compat)
            .set_footer(text=ctx._("their_banner", False).format(ctx.guild))
        )

    @commands.command(aliases=["server"], brief="View server's info", usage="[server]")
    async def serverinfo(self, ctx: Context, *, guild: AnyGuild = False):
        if guild is False:
            guild = ctx.guild
        elif guild is None:
            try:
                guild = await ctx.bot.fetch_guild_preview(int(ctx.argument_only))
            except (ValueError, disnake.NotFound):
                await ctx.send_("guild_not_found")
                return
        elif guild.unavailable:
            await ctx.send_("guild_unavailable")
            return

        _ = ctx._
        embed = (
            disnake.Embed(
                title=guild.name, url=f"https://discord.com/channels/{guild.id}", timestamp=utcnow()
            )
            .set_author(
                name=guild.id,
                icon_url="https://twemoji.maxcdn.com/v/latest/72x72/1f194.png",
                url=f"https://discord.com/channels/{guild.id}",
            )
            .set_thumbnail(url=guild.icon and guild.icon.compat)
        )
        self._set_description(embed, guild, _)
        self._set_footer(embed, guild)

        fields: dict[str, list[str]] = defaultdict(list)
        self._set_field_channels(fields[_("channels", False)], guild, _)
        self._set_field_members(fields[_("members", False)], guild, _)
        if guild.emojis:
            self._set_field_emojis_stickers(fields[_("emojis", False)], guild, _)
        elif guild.stickers:
            self._set_field_emojis_stickers(fields[_("stickers", False)], guild, _)
        self._set_field_general_info(fields[_("general_info")], guild, ctx.guild, _)
        self._set_field_moderation(fields[_("moderation")], guild, _)

        for name, values in fields.items():
            if not values:
                continue
            embed.add_field(
                name,
                re.sub(
                    r"^(.*?(?:(?=<t)|(?<!<t):))(.+)$", r"\1**\2**", "\n".join(values), flags=re.M
                ),
            )

        await ctx.send_ping(embed=embed)

    @staticmethod
    def _set_description(
        embed: disnake.Embed, guild: disnake.Guild | disnake.GuildPreview, _: Callable[[str], str]
    ) -> None:
        assets = []
        if isinstance(guild, disnake.Guild):
            if guild.vanity_url_code:
                assets.append(f"[{_('vanity_invite')}](https://discord.gg/{guild.vanity_url_code})")
            if guild.banner:
                assets.append(f"[{_('banner', False)}]({guild.banner.maxres})")
        if guild.splash:
            assets.append(f"[{_('invitation_splash')}]({guild.splash.maxres})")
        if guild.discovery_splash:
            assets.append(f"[{_('discovery_splash')}]({guild.discovery_splash.maxres})")
        embed.description = " • ".join(assets)
        if guild.description:
            embed.description += "\n" + guild.description

    @staticmethod
    def _set_footer(embed: disnake.Embed, guild: disnake.Guild | disnake.GuildPreview):
        shown_features = {"VERIFIED", "PARTNERED"}
        if features := [feature for feature in guild.features if feature in shown_features]:
            embed.set_footer(text=", ".join(features).capitalize() + " server")

    @staticmethod
    def _set_field_general_info(
        field_values: list,
        guild: disnake.Guild,
        current_guild: disnake.Guild,
        _: Callable[[str], str],
    ) -> None:
        if not isinstance(guild, disnake.Guild):
            return

        if guild == current_guild or guild.owner in current_guild.members:
            owner = f"<@{guild.owner_id}>"
        else:
            owner = mono(guild.owner or guild.owner_id)
        field_values.append(f"{_('owner')}: {owner}")
        field_values.append(_("created_on").format(format_dt(guild.created_at, "D")))
        field_values.append(f"{_('locale', False)}: {str(guild.preferred_locale).upper()}")
        field_values.append(f"{_('boost_level')}: {guild.premium_tier}")
        field_values.append(f"{_('upload_limit')}: {_('mb', 0).format(guild.filesize_limit >> 20)}")
        if guild.nsfw_level is not disnake.NSFWLevel.default:
            field_values.append(_(f"nsfw_level_{guild.nsfw_level}"))

    @staticmethod
    def _set_field_channels(
        field_values: list, guild: disnake.Guild, _: Callable[[str], str]
    ) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        if guild.categories:
            field_values.append(f"{_('categories')}: {len(guild.categories)}")
        if guild.text_channels:
            field_values.append(f"{_('text')}: {len(guild.text_channels)}")
        if guild.threads:
            field_values.append(f"{_('threads')}: {len(guild.threads)}")
        if guild.voice_channels:
            field_values.append(f"{_('voice')}: {len(guild.voice_channels)}")
        if guild.stage_channels:
            field_values.append(f"{_('stage')}: {len(guild.stage_channels)}")
        if guild.forum_channels:
            field_values.append(f"{_('forum')}: {len(guild.forum_channels)}")

    def _set_field_members(
        self, field_values: list, guild: disnake.Guild, _: Callable[[str], str]
    ) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        field_values.append(f"{_('total')}: {guild.approximate_member_count or guild.member_count}")

        presence_count = guild.approximate_presence_count
        if presence_count is None and self.presences_intent:
            presence_count = guild.presence_count
        if presence_count is not None:
            field_values.append(f"{_('online')}: {presence_count}")

        field_values.append(f"{_('bots')}: {sum(m.bot for m in guild.members)}")
        if guild.premium_subscribers:
            field_values.append(f"{_('boosters')}: {len(guild.premium_subscribers)}")

    @staticmethod
    def _set_field_moderation(
        field_values: list, guild: disnake.Guild, _: Callable[[str], str]
    ) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        admin_count = sum(not m.bot and m.guild_permissions.administrator for m in guild.members)
        field_values.append(f"{_('admins')}: {admin_count}")
        field_values.append(
            f"{_('verification_level')}: {_(f'verification_level_{guild.verification_level}')}"
        )
        field_values.append(_(f"nsfw_filter_{guild.explicit_content_filter}"))
        field_values.append("2FA: " + _("2fa_required" if guild.mfa_level else "2fa_not_required"))

    @staticmethod
    def _set_field_emojis_stickers(
        field_values: list, guild: disnake.Guild | disnake.GuildPreview, _: Callable[[str], str]
    ) -> None:
        if e_count := len(guild.emojis):
            e_animated_count = sum(e.animated for e in guild.emojis)
            e_static_count = e_count - e_animated_count
            e_animated_available_count = sum(e.animated and e.available for e in guild.emojis)
            e_static_available_count = sum(not e.animated and e.available for e in guild.emojis)

            field_values.append(f"{_('static')}: {e_static_count}")
            if e_static_available_count != e_static_count:
                field_values[-1] += f" ({_('available').format(e_static_available_count)})"

            field_values.append(f"{_('animated')}: {e_animated_count}")
            if e_animated_available_count != e_animated_count:
                field_values[-1] += f" ({_('available').format(e_animated_available_count)})"

        if not (s_count := len(guild.stickers)):
            return
        is_static_sticker = lambda s: s.format is disnake.StickerFormatType.png
        s_static_count = sum(map(is_static_sticker, guild.stickers))
        s_animated_count = s_count - s_static_count
        s_static_available_count = sum(is_static_sticker(s) and s.available for s in guild.stickers)
        s_animated_available_count = sum(
            not is_static_sticker(s) and s.available for s in guild.stickers
        )

        if e_count:
            field_values.append(f"**{_('stickers', False)}**")
        field_values.append(f"{_('static')}: {s_static_count}")
        if s_static_available_count != s_static_count:
            field_values[-1] += f" ({_('available').format(s_static_available_count)})"

        field_values.append(f"{_('animated')}: {s_animated_count}")
        if s_animated_available_count != s_animated_count:
            field_values[-1] += f" ({_('available').format(s_animated_available_count)})"


def setup(ara: Ara):
    ara.add_cog(Serverinfo(ara.intents.presences))
