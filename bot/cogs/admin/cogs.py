from discord import Embed
from discord.ext.commands import Cog, check, group, errors
from ...utils.general import is_dev, Color


class Cogs(Cog, name="Admin"):
    def __init__(self, client):
        self.bot = client
        self.root = "bot.cogs"

    @check(is_dev)
    @group(aliases=["cogs"], invoke_without_command=True, hidden=True)
    async def cog(self, ctx):
        embed = Embed(color=Color.yellow).add_field(name="Loaded cogs", value="\n".join(self.bot.cogs))
        await ctx.send(embed=embed)

    @check(is_dev)
    @cog.command(aliases=["enable"])
    async def load(self, ctx, *cogs):
        exts = {k: [] for k in ("Successfully loaded", "Not found", "Already loaded", "Invalid")}
        for cog in cogs:
            try:
                self.bot.load_extension(f"{self.root}.{cog}")
                exts["Successfully loaded"].append(cog)
            except errors.ExtensionNotFound:
                exts["Not found"].append(cog)
            except errors.ExtensionAlreadyLoaded:
                exts["Already loaded"].append(cog)
            except (errors.ExtensionFailed, errors.NoEntryPointError):
                exts["Invalid"].append(cog)
        is_error = any((exts["Not found"], exts["Already loaded"], exts["Invalid"]))
        embed = Embed(color=Color.red if is_error else Color.green)
        for category, cog_list in exts.items():
            if cog_list:
                embed.add_field(name=category, value="\n".join(cog_list))
        await ctx.send(embed=embed if embed.fields else Embed(color=Color.yellow, description="Loaded nothing"))

    @check(is_dev)
    @cog.command(aliases=["disable"])
    async def unload(self, ctx, *cogs):
        exts = {k: [] for k in ("Successfully unloaded", "Not loaded")}
        for cog in cogs:
            try:
                self.bot.unload_extension(f"{self.root}.{cog}")
                exts["Successfully unloaded"].append(cog)
            except errors.ExtensionNotLoaded:
                exts["Not loaded"].append(cog)
        embed = Embed(color=Color.red if exts["Not loaded"] else Color.green)
        for category, cog_list in exts.items():
            if cog_list:
                embed.add_field(name=category, value="\n".join(cog_list))
        await ctx.send(embed=embed if embed.fields else Embed(color=Color.yellow, description="Unloaded nothing"))

    @check(is_dev)
    @cog.command()
    async def reload(self, ctx, *cogs):
        exts = {k: [] for k in ("Successfully reloaded", "Not found", "Not loaded", "Invalid")}
        for cog in cogs:
            try:
                self.bot.reload_extension(f"{self.root}.{cog}")
                exts["Successfully reloaded"].append(cog)
            except errors.ExtensionNotFound:
                exts["Not found"].append(cog)
            except errors.ExtensionNotLoaded:
                exts["Not loaded"].append(cog)
            except (errors.ExtensionFailed, errors.NoEntryPointError):
                exts["Invalid"].append(cog)
        is_error = any((exts["Not found"], exts["Not loaded"], exts["Invalid"]))
        embed = Embed(color=Color.red if is_error else Color.green)
        for category, cog_list in exts.items():
            if cog_list:
                embed.add_field(name=category, value="\n".join(cog_list))
        await ctx.send(embed=embed if embed.fields else Embed(color=Color.yellow, description="Reloaded nothing"))


def setup(client):
    client.add_cog(Cogs(client))
