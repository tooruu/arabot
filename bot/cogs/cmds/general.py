from glob import glob
from random import choice
from discord import Embed, Emoji, PartialEmoji
from discord.ext.commands import (
    command,
    Cog,
    check,
    has_permissions,
    MessageConverter,
    cooldown,
    BucketType,
    CommandOnCooldown,
)
from ...utils.converters import FindMember, FindEmoji, ChlMemberConverter
from ...utils.general import is_dev, get_master_invite
from ...utils.meta import BOT_NAME
from ...utils.format_escape import bold


class General(Cog, name="Commands"):
    def __init__(self, client):
        self.bot = client

    @command(brief="<user> | Tell chat you love someone")
    async def love(self, ctx, partner: FindMember):
        await ctx.send(f"{ctx.author.mention} loves {partner.mention} ❤️" if partner else "Love partner not found")

    @command(
        aliases=[
            "exit",
            "quit",
            "kill",
            "shine",
            "shineo",
            "die",
            "kys",
            "begone",
            "fuck",
        ],
        hidden=True,
    )
    @check(is_dev)
    async def stop(self, ctx):
        await ctx.send("I'm dying, master 🥶")
        print("Stopping!")
        await self.bot.close()

    @command(hidden=True)
    @check(is_dev)
    async def status(self, ctx, presence_type: int, *, name):
        if presence_type not in (0, 1, 2, 3):
            return
        await self.bot.set_presence(presence_type, name)

    @command(name="177013")
    async def _177013(self, ctx):
        await self.bot.set_presence(3, "177013 with yo mama")

    @command(aliases=["purge", "prune", "d"], hidden=True)
    @has_permissions(manage_messages=True)
    async def clear(self, ctx, amount: int = None):
        if amount:
            await ctx.channel.purge(limit=amount + 1)
        else:
            await ctx.message.delete()

    @command(aliases=["a", "pfp"], brief="<user> | Show full-sized version of user's avatar")
    async def avatar(self, ctx, target: FindMember = False):
        if target is None:
            await ctx.send("User not found")
        else:
            target = target or ctx.author
            await ctx.send(
                embed=Embed()
                .set_image(url=target.avatar_url_as(static_format="png"))
                .set_footer(text=target.display_name + "'s avatar")
            )

    @command(aliases=["r"], brief="<emoji> | Show your big reaction to everyone")
    async def react(self, ctx, emoji: FindEmoji):
        if emoji:
            await ctx.message.delete()
            await ctx.send(
                embed=Embed()
                .set_image(url=emoji.url)
                .set_footer(
                    text="reacted",
                    icon_url=ctx.author.avatar_url_as(static_format="png"),
                )
            )
        else:
            await ctx.send("Emoji not found")

    @command(
        aliases=["emote", "e"],
        brief="<emoji...> | Show full-sized versions of emoji(s)",
    )
    async def emoji(self, ctx, *emojis: FindEmoji):
        files = {
            f"{emoji} {emoji.url}" if isinstance(emoji, (Emoji, PartialEmoji)) else emoji
            for emoji in emojis
            if emoji is not None
        }
        await ctx.send("\n".join(files) if files else "No emojis found")

    @command(brief="<user> | DM user to summon them")
    async def summon(self, ctx, target: ChlMemberConverter, *, msg=None):
        if target and not target.bot:
            invite = await get_master_invite(ctx.guild) or Embed.Empty
            embed = Embed(
                description=f"{ctx.author.mention} is summoning you to {ctx.channel.mention}"
                "\n{}\n[Jump to message]({})".format(f"\n{bold(msg)}" if msg else "", ctx.message.jump_url)
            ).set_author(
                name=ctx.guild.name,
                url=invite,
                icon_url=ctx.guild.icon_url_as(static_format="png") or Embed.Empty,
            )
            await target.send(embed=embed)
            await ctx.send(f"Summoning {target.mention}")
            return
        await ctx.send("User not found")

    @command(brief="| Get a random inspirational quote")
    async def inspire(self, ctx):
        async with self.bot.ses.get("https://inspirobot.me/api?generate=true") as url:
            await ctx.send(await url.text())

    @command(hidden=True)
    @has_permissions(manage_messages=True)
    async def say(self, ctx, *, msg):
        await ctx.message.delete()
        await ctx.send(msg)

    @cooldown(1, 10, BucketType.channel)
    @command(brief="Who asked?", hidden=True)
    async def wa(self, ctx, msg: MessageConverter = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if not msg.author.bot:
                    break
            else:
                return
        for i in (
            "🇼",
            "🇭",
            "🇴",
            "🇦",
            "🇸",
            "🇰",
            "🇪",
            "🇩",
            "<:FukaWhy:677955897200476180>",
        ):
            await msg.add_reaction(i)

    @wa.error
    async def wa_ratelimit(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.message.delete()
            return
        raise error

    @command(hidden=True)
    async def lines(self, ctx):
        count = 0
        for g in glob("./bot/**/[!_]*.py", recursive=True):
            with open(g, encoding="utf8") as f:
                count += len(f.readlines())
        await ctx.send(f"{BOT_NAME} consists of **{count}** lines of Python code")

    @cooldown(1, 10, BucketType.channel)
    @command(brief="Who cares?", hidden=True)
    async def wc(self, ctx, msg: MessageConverter = None):
        await ctx.message.delete()
        if not msg:
            async for msg in ctx.history(limit=3):
                if not msg.author.bot:
                    break
            else:
                return
        for i in (
            "🇼",
            "🇭",
            "🇴",
            "🇨",
            "🇦",
            "🇷",
            "🇪",
            "🇸",
            "<:TooruWeary:685461000891531282>",
        ):
            await msg.add_reaction(i)

    @wc.error
    async def wc_ratelimit(self, ctx, error):
        if isinstance(error, CommandOnCooldown):
            await ctx.message.delete()
            return
        raise error

    @cooldown(3, 10, BucketType.guild)
    @command(aliases=["whom", "whose", "who's"], brief="| Pings random person")
    async def who(self, ctx):
        member = choice(ctx.guild.members)
        await ctx.reply(member.mention)


def setup(client):
    client.add_cog(General(client))
