from discord.ext.commands import MemberConverter
from discord.ext.commands.errors import BadArgument
from discord.utils import find
from discord import Status, Activity

__all__ = ["isDev", "isValid", "arange", "FindMember", "setPresence"]


def isDev(ctx):
	return ctx.author.id in (337343326095409152, 447138372121788417)


def isValid(client, msg, invocator):
	return not msg.content.startswith(client.command_prefix
		) and msg.author != client.user and invocator.lower() in msg.content.lower()


async def arange(it: int):
	for v in range(it):
		yield v


class FindMember(MemberConverter):
	async def convert(self, ctx, argument):
		try:
			return await super().convert(ctx, argument)
		except BadArgument:
			return find(
				lambda member: not member.bot and member.name.lower().startswith(argument.lower()), ctx.guild.members
			)


async def setPresence(client, _type: int, name: str, _status: Status = None):
	if isinstance(_status, Status):
		await client.change_presence(status=_status, activity=Activity(name=name, type=_type))
	else:
		await client.change_presence(activity=Activity(name=name, type=_type))