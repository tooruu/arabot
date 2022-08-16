import re
from collections import defaultdict

import disnake
from disnake.ext import commands
from disnake.utils import format_dt, utcnow

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import AnyGuild, mono


class Serverinfo(Cog, category=Category.GENERAL):
    def __init__(self, presences_intent: bool):
        self.presences_intent = presences_intent = presences_intent

    @commands.command(aliases=["sa", "spfp"], brief="Show server's icon")
    async def serveravatar(self, ctx: Context):
        if not ctx.guild.icon:
            await ctx.send("Server has no icon")
            return
        await ctx.send(
            embed=disnake.Embed(timestamp=utcnow())
            .set_image(url=ctx.guild.icon.maxres.compat)
            .set_footer(text=ctx.guild)
        )

    @commands.command(aliases=["sb"], brief="Show server's banner")
    async def serverbanner(self, ctx: Context):
        if not ctx.guild.banner:
            await ctx.send("Server has no banner")
            return
        await ctx.send(
            embed=disnake.Embed(timestamp=utcnow())
            .set_image(url=ctx.guild.banner.maxres.compat)
            .set_footer(text=f"{ctx.guild} banner")
        )

    @commands.command(aliases=["server"], brief="View server's info", usage="[server]")
    async def serverinfo(self, ctx: Context, *, guild: AnyGuild = False):
        if guild is False:
            guild = ctx.guild
        elif guild is None:
            try:
                guild = await ctx.bot.fetch_guild_preview(int(ctx.argument_only))
            except (ValueError, disnake.NotFound):
                await ctx.send("Server not found or is not discoverable")
                return
        elif guild.unavailable:
            await ctx.send("Server is unavailable")
            return

        embed = (
            disnake.Embed(
                title=guild.name, url=f"https://discord.com/channels/{guild.id}", timestamp=utcnow()
            )
            .set_author(
                name=guild.id,
                icon_url="https://twemoji.maxcdn.com/v/latest/72x72/1f194.png",
                url=f"https://discord.com/channels/{guild.id}",
            )
            .set_thumbnail(url=guild.icon.compat if guild.icon else disnake.Embed.Empty)
        )
        self._set_description(embed, guild)
        self._set_footer(embed, guild)

        fields: dict[str, list[str]] = defaultdict(list)
        self._set_field_channels(fields["Channels"], guild)
        self._set_field_members(fields["Members"], guild)
        if guild.emojis:
            self._set_field_emojis_stickers(fields["Emojis"], guild)
        elif guild.stickers:
            self._set_field_emojis_stickers(fields["Stickers"], guild)
        self._set_field_general_info(fields["General info"], guild, ctx.guild)
        self._set_field_moderation(fields["Moderation"], guild)

        for name, values in fields.items():
            if values:
                value = re.sub(
                    r"^(?!Created)(.*?:)(.+)$", r"\1**\2**", "\n".join(values), flags=re.MULTILINE
                )
                embed.add_field(name, value)

        await ctx.send_ping(embed=embed)

    @staticmethod
    def _set_description(embed: disnake.Embed, guild: disnake.Guild | disnake.GuildPreview) -> None:
        assets = []
        if isinstance(guild, disnake.Guild):
            if guild.vanity_url_code:
                assets.append(f"[Vanity invite](https://discord.gg/{guild.vanity_url_code})")
            if guild.banner:
                assets.append(f"[Banner]({guild.banner.maxres})")
        if guild.splash:
            assets.append(f"[Invitation image]({guild.splash.maxres})")
        if guild.discovery_splash:
            assets.append(f"[Discovery image]({guild.discovery_splash.maxres})")
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
        field_values: list, guild: disnake.Guild, current_guild: disnake.Guild
    ) -> None:
        if not isinstance(guild, disnake.Guild):
            return

        if guild == current_guild or guild.owner in current_guild.members:
            owner = f"<@{guild.owner_id}>"
        else:
            owner = mono(guild.owner or guild.owner_id)
        field_values.append(f"Owner: {owner}")
        field_values.append(f"Created on {format_dt(guild.created_at, 'D')}")
        field_values.append(f"Locale: {str(guild.preferred_locale).upper()}")
        field_values.append(f"Boost level: {guild.premium_tier}")
        field_values.append(f"Upload limit: {guild.filesize_limit >> 20} MB")  # I know this is MiB
        match guild.nsfw_level:
            case disnake.NSFWLevel.safe:
                field_values.append("NSFW level: safe")
            case disnake.NSFWLevel.age_restricted:
                field_values.append("May contain NSFW content")
            case disnake.NSFWLevel.explicit:
                field_values.append("Contains NSFW content")

    @staticmethod
    def _set_field_channels(field_values: list, guild: disnake.Guild) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        if guild.categories:
            field_values.append(f"Categories: {len(guild.categories)}")
        if guild.text_channels:
            field_values.append(f"Text: {len(guild.text_channels)}")
        if guild.threads:
            field_values.append(f"Threads: {len(guild.threads)}")
        if guild.voice_channels:
            field_values.append(f"Voice: {len(guild.voice_channels)}")
        if guild.stage_channels:
            field_values.append(f"Stage: {len(guild.stage_channels)}")
        if guild.forum_channels:
            field_values.append(f"Forum: {len(guild.forum_channels)}")

    def _set_field_members(self, field_values: list, guild: disnake.Guild) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        field_values.append(f"Total: {guild.approximate_member_count or guild.member_count}")

        presence_count = guild.approximate_presence_count
        if presence_count is None and self.presences_intent:
            presence_count = guild.presence_count
        if presence_count is not None:
            field_values.append(f"Online: {presence_count}")

        field_values.append(f"Bots: {sum(m.bot for m in guild.members)}")
        if guild.premium_subscribers:
            field_values.append(f"Boosters: {len(guild.premium_subscribers)}")

    @staticmethod
    def _set_field_moderation(field_values: list, guild: disnake.Guild) -> None:
        if not isinstance(guild, disnake.Guild):
            return
        admin_count = sum(not m.bot and m.guild_permissions.administrator for m in guild.members)
        field_values.append(f"Admins: {admin_count}")
        field_values.append(f"Verif. level: {guild.verification_level}")
        match guild.explicit_content_filter:
            case disnake.ContentFilter.disabled:
                field_values.append("NSFW filter: disabled")
            case disnake.ContentFilter.no_role:
                field_values.append("NSFW filter: only if no roles")
            case disnake.ContentFilter.all_members:
                field_values.append("NSFW filter: enabled")
        field_values.append("2FA: " + ("required" if guild.mfa_level else "not required"))

    @staticmethod
    def _set_field_emojis_stickers(
        field_values: list, guild: disnake.Guild | disnake.GuildPreview
    ) -> None:
        if e_count := len(guild.emojis):
            e_animated_count = sum(e.animated for e in guild.emojis)
            e_static_count = e_count - e_animated_count
            e_animated_available_count = sum(e.animated and e.available for e in guild.emojis)
            e_static_available_count = sum(not e.animated and e.available for e in guild.emojis)

            field_values.append(f"Static: {e_static_count}")
            if e_static_available_count != e_static_count:
                field_values[-1] += f" ({e_static_available_count} available)"

            field_values.append(f"Animated: {e_animated_count}")
            if e_animated_available_count != e_animated_count:
                field_values[-1] += f" ({e_animated_available_count} available)"

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
            field_values.append("**Stickers**")
        field_values.append(f"Static: {s_static_count}")
        if s_static_available_count != s_static_count:
            field_values[-1] += f" ({s_static_available_count} available)"

        field_values.append(f"Animated: {s_animated_count}")
        if s_animated_available_count != s_animated_count:
            field_values[-1] += f" ({s_animated_available_count} available)"


def setup(ara: Ara):
    ara.add_cog(Serverinfo(ara.intents.presences))
