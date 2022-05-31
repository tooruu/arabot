import disnake
from arabot.core import AnyMember, Ara, Category, Cog, Context
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
            .set_footer(text=f"{target.display_name}'s user avatar"),
            disnake.Embed()
            .set_image(url=target.display_avatar.compat.url)
            .set_footer(text=f"{target.display_name}'s server avatar"),
        )

        if not target.guild_avatar:
            await ctx.send(embed=avatars[0])
            return

        await ctx.send(embed=avatars[1], view=AvatarView(avatars))

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


def setup(ara: Ara):
    ara.add_cog(Userinfo(ara))
