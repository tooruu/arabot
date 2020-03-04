from discord.ext.commands import (
	Converter, MemberConverter, EmojiConverter, TextChannelConverter, VoiceChannelConverter, RoleConverter
)
from discord.ext.commands.errors import BadArgument
from discord.utils import find
from discord import Status, Activity

#__all__ = ["isDev", "isValid", "arange", "FindMember", "setPresence", "FFindMember"]


def isDev(ctx):
	return ctx.author.id in (337343326095409152, 447138372121788417)


def isValid(client, msg, invocator):
	return not msg.content.startswith(client.command_prefix
		) and msg.author != client.user and invocator.lower() in msg.content.lower()


async def setPresence(client, _type: int, name: str, _status: Status = None):
	if isinstance(_status, Status):
		await client.change_presence(status=_status, activity=Activity(name=name, type=_type))
	else:
		await client.change_presence(activity=Activity(name=name, type=_type))


class Finder(Converter):
	"""
	Abstract class to convert *argument* to desired class.
	1.	Try to convert via subclass's parents'
		`convert` methods (implemented in discord.py)
	2. Try to find via subclass's method `find`

	# Example usage:
   class FindObject(Finder, commands.ObjectConverter):
		@staticmethod
		def find(ctx, argument):
			return lambda obj: obj.att == argument, ctx.obj_list
    """
	def __init__(self):
		if len(type(self).__bases__) == 1:
			raise IndexError(f"<'{type(self).__name__}'> must have at least 2 parents")
		for base in type(self).__bases__[1:]:
			if not issubclass(base, Converter):
				raise TypeError(f"Parents of <'{type(self).__name__}'> are not derived from Converter")

	async def convert(self, ctx, argument):
		for conv in type(self).__bases__[1:]:
			try:
				return await conv().convert(ctx, argument)
			except BadArgument:
				pass
		return self.find(ctx, argument)

	def find(self, ctx, argument):
		raise NotImplementedError("Derived classes need to implement this.")


class FindMember(Finder, MemberConverter):
	def find(self, ctx, argument):
		return find(lambda member: not member.bot and member.name.lower().startswith(argument.lower()), ctx.guild.members)


class FindEmoji(Finder, EmojiConverter):
	def find(self, ctx, argument):
		return find(lambda emoji: emoji.name.lower().startswith(argument.lower()), ctx.guild.emojis)


class FindTxChl(Finder, TextChannelConverter):
	def find(self, ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.text_channels)


class FindVcChl(Finder, VoiceChannelConverter):
	def find(self, ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.voice_channels)


class FindChl(Finder, TextChannelConverter, VoiceChannelConverter):
	def find(self, ctx, argument):
		return find(
			lambda chl: chl.name.lower().startswith(argument.lower()), ctx.guild.text_channels + ctx.guild.voice_channels
		)


class FindRole(Finder, RoleConverter):
	def find(self, ctx, argument):
		return lambda role: role.name.lower().startswith(argument.lower()), ctx.guild.roles