from discord.ext.commands import command, Cog, check, group, errors
from ...utils.meta import BOT_NAME, BOT_VERSION
from ...utils.utils import is_dev
from ...utils.format_escape import bold


class General(Cog, name="Admin"):
    def __init__(self, client):
        self.bot = client

    @command(aliases=["ver", "v"], brief="| Show currently running bot's version")
    async def version(self, ctx):
        await ctx.send(f"{BOT_NAME} v{BOT_VERSION}")

    @check(is_dev)
    @group(aliases=["cogs"], invoke_without_command=True, hidden=True)
    async def cog(self, ctx):
        await ctx.send("Loaded cogs: " + ", ".join(bold(c) for c in self.bot.cogs))

    @check(is_dev)
    @cog.command(aliases=["enable"])
    async def load(self, ctx, *cogs):
        loaded = []
        for i in cogs:
            try:
                self.bot.load_extension(f"cogs.{i}")
                loaded.append(bold(i))
            except errors.ExtensionNotFound:
                await ctx.send(bold(i) + " was not found")
            except errors.ExtensionAlreadyLoaded:
                await ctx.send(bold(i) + " is already loaded")
            except (errors.ExtensionFailed, errors.NoEntryPointError):
                await ctx.send(bold(i) + " is an invalid extension")
        await ctx.send("Loaded " + (", ".join(loaded) or "nothing"))

    @check(is_dev)
    @cog.command(aliases=["disable"])
    async def unload(self, ctx, *cogs):
        unloaded = []
        for i in cogs:
            try:
                self.bot.unload_extension(f"cogs.{i}")
                unloaded.append(bold(i))
            except errors.ExtensionNotLoaded:
                pass
        await ctx.send("Unloaded " + (", ".join(unloaded) or "nothing"))

    @check(is_dev)
    @cog.command()
    async def reload(self, ctx, *cogs):
        reloaded = []
        for i in cogs:
            try:
                self.bot.reload_extension(f"cogs.{i}")
                reloaded.append(bold(i))
            except errors.ExtensionNotFound:
                await ctx.send(bold(i) + " was not found")
            except errors.ExtensionNotLoaded:
                self.bot.load_extension(f"cogs.{i}")
                reloaded.append(bold(i))
            except (errors.ExtensionFailed, errors.NoEntryPointError):
                await ctx.send(bold(i) + " is an invalid extension")
        await ctx.send("Reloaded " + (", ".join(reloaded) or "nothing"))


def setup(client):
    client.add_cog(General(client))
