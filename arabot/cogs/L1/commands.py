from re import match

from arabot.core import Ara, Cog, Context
from arabot.utils import AnyEmoji, Category
from disnake import Embed
from disnake.ext.commands import PartialEmojiConverter, command


class L1Commands(Cog, category=Category.COMMUNITY):
    def __init__(self, ara: Ara):
        self.ara = ara

    @command(brief="Suggest server emoji")
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
        if match(r"https?://(-\.)?([^\s/?\.#]+\.?)+(/[^\s]*)?$", em_after):
            async with self.ara.session.get(em_after) as resp:
                if not resp.ok or not resp.content_type.startswith("image/"):
                    await ctx.send(f"Link a valid image to replace {em_before} with")
                    return
        elif match(r"<a?:[a-zA-Z0-9_]{2,32}:[0-9]{18,22}>$", em_after):
            if await AnyEmoji().convert(ctx, em_after) in ctx.guild.emojis:
                await ctx.send(f"We already have {em_after}")
                return
            em_after = (await PartialEmojiConverter().convert(ctx, em_after)).url
        else:
            await ctx.send(f"Choose a valid emoji to replace {em_before} with")
            return
        embed = (
            Embed(title="wants to change this →", description="to that ↓")
            .set_thumbnail(url=em_before.url)
            .set_image(url=em_after)
            .set_author(
                name=ctx.author.display_name,
                icon_url=ctx.author.avatar.with_static_format("png").url,
            )
        )
        message = await ctx.send(embed=embed)
        if not ctx.message.attachments:
            await ctx.message.delete()
        await message.add_reaction("👍")
        await message.add_reaction("👎")


def setup(ara: Ara):
    ara.add_cog(L1Commands(ara))
