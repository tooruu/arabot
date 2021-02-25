from asyncio import TimeoutError
from discord import Embed
from discord.ext.commands import Cog, group, check
from ...utils.utils import is_dev
from ...utils.format_escape import bold
from ...helpers.auth import req_auth


class Trello(Cog, name="Commands"):
    def __init__(self, client, keys):
        self.bot = client
        self.key, self.token = keys
        self.TODO_ID = "5f83b280d843221ed1677555"
        self.CARDS_URL = "https://api.trello.com/1/cards"

    @check(is_dev)
    @group(invoke_without_command=True)
    async def trello(self, ctx):
        ...

    @check(is_dev)
    @trello.group(invoke_without_command=True)
    async def todo(self, ctx):
        ...

    @check(is_dev)
    @todo.command(aliases=["new", "create"])
    async def add(self, ctx, *, title=None):
        if not title:
            await ctx.send("You must provide new card's title")
            return
        params = {
            "key": self.key,
            "token": self.token,
            "idList": self.TODO_ID,
            "name": title,
        }

        wiz = await ctx.send(embed=Embed(title=f"Do you want to add a description for {bold(title)}?"))

        async def edit(txt):
            await wiz.edit(embed=Embed(title=txt))

        for r in ("☑️", "➡️", "❌"):
            await wiz.add_reaction(r)
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=15,
                check=lambda r, u: u == ctx.author and r.message == wiz and r.emoji in ("☑️", "➡️", "❌"),
            )
        except TimeoutError:
            await wiz.clear_reactions()
            await wiz.edit(embed=Embed(title="Command timed out"), delete_after=7)
            return
        if reaction.emoji == "❌":
            await wiz.clear_reactions()
            await wiz.edit(embed=Embed(title="Command aborted"), delete_after=7)
            return
        if reaction.emoji == "➡️":
            await wiz.remove_reaction(reaction, user)
        if reaction.emoji == "☑️":
            await wiz.clear_reactions()
            await edit("Enter description for " + bold(title))
            try:
                message = await self.bot.wait_for(
                    "message",
                    timeout=60,
                    check=lambda m: m.author == ctx.author and m.channel == ctx.channel,
                )
            except TimeoutError:
                await wiz.edit(embed=Embed(title="Command timed out"), delete_after=7)
                return
            await message.delete()
            params["desc"] = message.content

        await wiz.edit(
            embed=Embed(
                title=f"Do you want to attach any files to {bold(title)}?",
                description=f"Added description:\n{params['desc']}" if params.get("desc") else Embed.Empty,
            )
        )
        for r in ("☑️", "➡️", "❌"):
            await wiz.add_reaction(r)
        try:
            reaction, user = await self.bot.wait_for(
                "reaction_add",
                timeout=15,
                check=lambda r, u: u == ctx.author and r.message == wiz and r.emoji in ("☑️", "➡️", "❌"),
            )
        except TimeoutError:
            await wiz.clear_reactions()
            await wiz.edit(embed=Embed(title="Command timed out"), delete_after=7)
            return
        if reaction.emoji == "❌":
            await wiz.clear_reactions()
            await wiz.edit(embed=Embed(title="Command aborted"), delete_after=7)
            return
        if reaction.emoji == "☑️":
            for r in ("☑️", "➡️", "❌"):
                await wiz.remove_reaction(r, self.bot.user)
            await edit("Unreact when you're done uploading all files")
            try:  # TODO: Add files support
                await self.bot.wait_for(
                    "reaction_remove",
                    timeout=60,
                    check=lambda r, u: u == ctx.author and r.message == wiz and r.emoji == "☑️",
                )
            except TimeoutError:
                await wiz.clear_reactions()
                await edit("Command timed out")
                return
        await wiz.clear_reactions()

        async with self.bot.ses as session:
            async with session.post(self.CARDS_URL, params=params):
                pass
        await edit("Created card " + bold(title))

    @check(is_dev)
    @todo.command()
    async def view(self, ctx):
        ...


@req_auth("trello_key", "trello_token")
def setup(client, keys):
    client.add_cog(Trello(client, keys))
