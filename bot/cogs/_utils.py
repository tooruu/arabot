from discord.ext.commands import (
	Converter, MemberConverter, EmojiConverter, PartialEmojiConverter, TextChannelConverter, VoiceChannelConverter, RoleConverter
)
from discord.ext.commands.errors import BadArgument
from discord.utils import find
from discord import Status, Activity
from os import environ

BOT_DEBUG = False
BOT_NAME = "AraBot"
BOT_PREFIX = "-" if BOT_DEBUG else ";"
BOT_VERSION = "1.6.17" #TODO: UPDATE!
if BOT_DEBUG:
	BOT_VERSION += " (DEBUG MODE)"

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
	2. Try to convert via subclass's method `find`

	# Example usage:
	class FindObject(Finder, AConverter, BConverter):
		@staticmethod
		def find(ctx, argument):
			return utils.find(lambda obj: obj.att == argument, ctx.obj_list)
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

	@staticmethod
	def find(ctx, argument):
		raise NotImplementedError("Derived classes need to implement this.")

class FindMember(Finder, MemberConverter):
	@staticmethod
	def find(ctx, argument):
		return find(
			lambda member: not member.bot and member.display_name.lower().startswith(argument.lower()), ctx.guild.members
		)

class FindEmoji(Finder, EmojiConverter, PartialEmojiConverter):
	@staticmethod
	def find(ctx, argument):
		ctx.bot.guilds.insert(0, ctx.bot.guilds.pop(ctx.bot.guilds.index(ctx.guild)))
		for guild in ctx.bot.guilds:
			if emote := find(
				lambda emoji: argument.lower() in emoji.name.lower() or argument.lower() == str(emoji.id), guild.emojis
			):
				return emote
		return f"https://raw.githubusercontent.com/astronautlevel2/twemoji/gh-pages/128x128/{format(ord(argument), 'x')}.png" if len(
			argument
		) == 1 else None

class FindTxChl(Finder, TextChannelConverter):
	@staticmethod
	def find(ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.text_channels)

class FindVcChl(Finder, VoiceChannelConverter):
	@staticmethod
	def find(ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.voice_channels)

class FindChl(Finder, TextChannelConverter, VoiceChannelConverter):
	@staticmethod
	def find(ctx, argument):
		return find(
			lambda chl: chl.name.lower().startswith(argument.lower()), ctx.guild.text_channels + ctx.guild.voice_channels
		)

class FindRole(Finder, RoleConverter):
	@staticmethod
	def find(ctx, argument):
		return lambda role: role.name.lower().startswith(argument.lower()), ctx.guild.roles

class Queue:
	def __init__(self, maxsize):
		self._items = [0] * maxsize
		self.size = maxsize

	def __repr__(self):
		return str(self._items)

	def __len__(self):
		return self.size

	def __str__(self):
		return str(self._items)

	def __getitem__(self, key):
		return self._items[key]

	def __iadd__(self, item):
		self.enqueue(item)
		return self

	def enqueue(self, item=0):
		del self._items[0]
		self._items.append(item)

	def items(self):
		return self._items

def getenv(*keys):
	if environ.get("token"):
		if len(keys) == 1:
			return environ[keys[0]]
		return (environ[k] for k in keys)
	with open("./.env") as s:
		secret = {line.partition("=")[0]: line.partition("=")[-1] for line in s.read().splitlines()}
	if len(keys) == 1:
		return secret[keys[0]]
	return (secret[k] for k in keys)

bold = lambda s: "**{}**".format(s.replace('*', '\\*'))

dsafe = lambda s: s.replace('*', '\\*').replace('_', '\\_').replace('~', '\\~').replace('|', '\\|').replace('`', '\\`')