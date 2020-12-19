from discord.ext.commands import (
	Converter, MemberConverter, EmojiConverter, PartialEmojiConverter, TextChannelConverter, VoiceChannelConverter,
	RoleConverter, Cog, MinimalHelpCommand
)
from discord.ext.commands.errors import BadArgument
from discord.utils import find
from discord import Status, Activity, Embed
from os import environ, walk
from os.path import basename
from re import search
from datetime import datetime

BOT_DEBUG = False
BOT_NAME = "AraBot"
BOT_PREFIX = ("-", ) if BOT_DEBUG else (";", "ara ")
BOT_VERSION = "2.15.3"
# 1.0.0 major changes
# 0.1.0 new features
# 0.0.1 minor improvements & bugfixes
if BOT_DEBUG:
	BOT_VERSION += " (DEBUG MODE)"

is_dev = lambda ctx: ctx.author.id in (337343326095409152, 447138372121788417, 401490060156862466)

is_valid = lambda client, msg, expr="": not any(msg.content.startswith(pfx)
	for pfx in ('>', *client.command_prefix)) and not msg.author.bot and search(expr, msg.content.lower())

async def set_presence(client, _type: int, name: str, _status: Status = None):
	await client.change_presence(
		status=_status if isinstance(_status, Status) else None, activity=Activity(name=name, type=_type)
	)

class Finder(Converter):
	"""
	Abstract class to convert *argument* to desired type.
	1.	Try to convert via subclass's parents'
		`convert` methods (implemented in discord.py)
	2. Try to convert via subclass's own method `find`

	# Example usage:
	class FindObject(Finder, AConverter, BConverter):
		@staticmethod
		async def find(ctx, argument):
			return utils.find(lambda obj: obj.att == argument, ctx.obj_list) or await thing()
	"""
	def __init__(self):
		if len(self.__class__.__bases__) == 1:
			raise IndexError(f"<'{self.__class__.__name__}'> must have at least 2 parents")
		if not all(issubclass(base, Converter) for base in self.__class__.__bases__[1:]):
			raise TypeError(f"Parents of <'{self.__class__.__name__}'> are not derived from Converter")

	async def convert(self, ctx, argument):
		for conv in self.__class__.__bases__[1:]:
			try:
				return await conv().convert(ctx, argument)
			except BadArgument:
				pass
		return await self.find(ctx, argument)

	@staticmethod
	async def find(ctx, argument):
		raise NotImplementedError("Derived classes need to implement this.")

class FindMember(Finder, MemberConverter):
	@staticmethod
	async def find(ctx, argument):
		result = find(
			lambda member: argument.lower() in member.display_name.lower(), ctx.guild.members
		)
		return result or find(
			lambda member: argument.lower() in member.name.lower(), ctx.guild.members
		)

class FindEmoji(Finder, EmojiConverter, PartialEmojiConverter):
	@staticmethod
	async def find(ctx, argument):
		ctx.bot.guilds.insert(0, ctx.bot.guilds.pop(ctx.bot.guilds.index(ctx.guild)))
		for guild in ctx.bot.guilds:
			if emote := find(
				lambda emoji: argument.lower() in emoji.name.lower() or argument.lower() == str(emoji.id), guild.emojis
			):
				return emote
		return f"https://raw.githubusercontent.com/astronautlevel2/twemoji/gh-pages/128x128/{ord(argument):x}.png" if len(
			argument
		) == 1 else None

class FindTxChl(Finder, TextChannelConverter):
	@staticmethod
	async def find(ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.text_channels)

class FindVcChl(Finder, VoiceChannelConverter):
	@staticmethod
	async def find(ctx, argument):
		return find(lambda chan: chan.name.lower().startswith(argument.lower()), ctx.guild.voice_channels)

class FindChl(Finder, TextChannelConverter, VoiceChannelConverter):
	@staticmethod
	async def find(ctx, argument):
		return find(
			lambda chl: chl.name.lower().startswith(argument.lower()), ctx.guild.text_channels + ctx.guild.voice_channels
		)

class FindRole(Finder, RoleConverter):
	@staticmethod
	async def find(ctx, argument):
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

def load_ext(client):
	for path, _, files in walk("bot/cogs"):
		if basename(path := path[4:])[0] != "_":
			path = path.replace("/", ".").replace("\\", ".") + "."
			for cog in files:
				if cog[0] != "_" and cog.endswith(".py"):
					client.load_extension(path + cog[:-3])
					print(f"Loaded {path}{cog[:-3]}")

class text_reaction:
	def __init__(self, *, cd=0, regex=None, check=None, send=True):
		self.expr = regex
		self.check = check
		self.send = send
		self._cd = cd if cd > 0 else -1
		self._last_call = datetime(1970, 1, 1)

	def __call__(self, func):
		self.expr = self.expr or "\\b{}\\b".format(func.__name__.replace('_', '\\s'))

		@Cog.listener("on_message")
		async def event(itself, msg):
			if (datetime.now() - self._last_call).seconds > self._cd and is_valid(itself.bot, msg,
				self.expr) and (self.check is None or self.check(msg)):
				if self.send:
					resp = func(msg)
					if isinstance(resp, (list, tuple)):
						for i in resp:
							await msg.channel.send(i)
					else:
						await msg.channel.send(str(resp))
				else:
					await func(itself, msg)
				self._last_call = datetime.now()

		event.__name__ = func.__name__
		return event

class BlacklistMatch(Exception):
	def __init__(self, hit):
		self.hit = hit

class Blacklist(Converter):
	BLACKLIST = "ight imma head out",

	async def convert(self, ctx, arg):
		if arg in self.BLACKLIST:
			raise BlacklistMatch(arg)
		return arg

class Help(MinimalHelpCommand):
	#def get_command_signature(self, command):
	#	return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)

	async def send_bot_help(self, mapping):
		help = Embed()
		help.set_author(name=BOT_NAME, icon_url=str(self.context.bot.user.avatar_url_as(static_format="png")))
		for cog in mapping:
			if cog and mapping[cog]:
				help.add_field(
					name=bold(cog.qualified_name),
					value='\n'.join(f"`{cmd.name}`" for cmd in mapping[cog])
				)
		await self.get_destination().send(embed=help)
