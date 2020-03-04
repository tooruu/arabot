from discord.ext import commands
from discord.ext.commands import Cog
from discord.ext.commands.errors import *
from ._utils import setPresence
#import discord


class Listeners(Cog):
	def __init__(self, client):
		self.bot = client

	@Cog.listener()
	async def on_ready(self):
		await setPresence(self.bot, 3, "#lewd")
		print("Ready!")

	@Cog.listener()
	async def on_command_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown):
			await ctx.send(error)
			return
		if hasattr(ctx.command, "on_error") or isinstance(
			error, ( # Ignore following errors
			commands.CommandNotFound,
			MissingPermissions,
			CheckFailure,
			BadArgument,
			MissingRequiredArgument,
			)
		):
			return
		raise error


def setup(client):
	client.add_cog(Listeners(client))