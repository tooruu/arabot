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
	1.	Try to convert via derived class's second parent's
		`convert` method (implemented in discord.py)
	2. Try to find via `discord.utils.find` using custom lambda

	# Example usage:
   class FindObject(Finder, commands.ObjectConverter):
		@staticmethod
		def find(ctx, argument):
			return lambda obj: obj.att == argument, ctx.obj_list
    """
	async def convert(self, ctx, argument):
		try:
			if not issubclass(type(self).__bases__[1], Converter):
				raise TypeError
			return await type(self).__bases__[1].convert(self, ctx, argument)
		except BadArgument:
			return find(*self.find(ctx, argument))
		except (IndexError, TypeError):
			raise TypeError(f"2nd parent of <'{type(self).__name__}'> is not Converter")

	def find(self, ctx, argument):
		raise NotImplementedError("Derived classes need to implement this.")


class FindMember(Finder, MemberConverter):
	def find(self, ctx, argument):
		return lambda member: not member.bot and member.name.lower().startswith(argument.lower()), ctx.guild.members


class FindEmoji(Finder, EmojiConverter):
	def find(self, ctx, argument):
		return lambda emoji: emoji.name.lower().startswith(argument.lower()), ctx.guild.emojis


class FindTxChl(Finder, TextChannelConverter):
	def find(self, ctx, argument):
		return lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.text_channels


class FindVcChl(Finder, VoiceChannelConverter):
	def find(self, ctx, argument):
		return lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.voice_channels


class FindRole(Finder, RoleConverter):
	def find(self, ctx, argument):
		return lambda role: role.name.lower().startswith(argument.lower()), ctx.guild.roles