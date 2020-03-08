from random import choice, choices
from discord.ext.commands import command, Cog, cooldown, BucketType, CommandOnCooldown


class Gacha(Cog):
	def __init__(self, client):
		self.bot = client

	rates = {
		"ValkS": .015,
		"ValkA": .135,
		"ValkB": .055,
		"FragS": .0127,
		"FragA": .1019,
		"Weap4": .0046,
		"Weap3": .075,
		"Stig4": .0073,
		"Stig3": .225,
		"UpMats": .1474,
		"EquEXP": .1474,
		"Coins": .0737,
	}

	pool = {
		"dorm": {
		"ValkS": [
		"Celestial Hymn", "Blood Rose", "Shadow Knight", "Herrscher of the Void", "Knight Moonbean",
		"Goushinnso Memento", "Black Nucleus", "Sixth Serenade", "Phoenix", "Lightning Empress",
		"Dimensional Breaker", "Violet Executer"
		],
		"ValkA": [
		"Luna Kindred", "Valkyrie Accipiter", "Valkyrie Pledge", "Sakuno Rondo", "Night Squire", "Flame Sakitama",
		"Wolf's Dawn", "Ritual Imayoh", "Gyakushin Miko", "Shadow Dash", "Valkyrie Bladestrike", "Valkyrie Ranger",
		"Divine Prayer", "Yamabuki Armor", "Valkyrie Triumph", "Arctic Kriegsmesser", "Snowy Sniper",
		"Scarlet Fusion"
		],
		"ValkB": ["Valkyrie Chariot", "Battle Storm", "White Comet", "Crimson Impulse"],
		"FragS": [
		"Celestial Hymn", "Blood Rose", "Shadow Knight", "Herrscher of the Void", "Knight Moonbean",
		"Goushinnso Memento", "Black Nucleus", "Sixth Serenade", "Phoenix", "Lightning Empress",
		"Dimensional Breaker", "Violet Executer"
		],
		"FragA": [
		"Luna Kindred", "Valkyrie Accipiter", "Valkyrie Pledge", "Sakuno Rondo", "Night Squire", "Flame Sakitama",
		"Wolf's Dawn", "Ritual Imayoh", "Gyakushin Miko", "Shadow Dash", "Valkyrie Bladestrike", "Valkyrie Ranger",
		"Divine Prayer", "Yamabuki Armor", "Valkyrie Triumph", "Arctic Kriegsmesser", "Snowy Sniper",
		"Scarlet Fusion"
		],
		"Weap4": ["Keys of the Void", "Path to Acheron", "Key of Reason", "Blood Dance", "Hekate's Gloom"],
		"Weap3": ["Azure Storm", "Nitro Crystal", "Dark Crusher"],
		"Stig4": [
		"Sirin", "Shakespeare", "Rasputin", "Nobel", "Beethoven", "Caravaggio", "Michelangelo", "Oath of Judah",
		"Jin Shengtan"
		],
		"Stig3": [
		"Charlemagne", "Elizabeth Bathory", "Galileo", "Ryunosuke Akutagawa", "Roald Amundsen", "Nikola Tesla",
		"Edison", "Attila", "Sakamoto Ryouma", "Ogier", "Shigure Kira", "Rinaldo", "Tchaikovsky", "Scott",
		"Wang Zhaojun"
		],
		"UpMats": [
		"Super EXP Chip", "ADV EXP Chip", "ADV Learning Chip", "Basic Learning Chip", "Microreactor",
		"Phase Shifter"
		],
		"EquEXP": ["Twin Soul Crystal", "Soul Crystal", "Twin Soul Shard", "Soul Shard"],
		"Coins": ["HOMEI Chest", "HOMU Chest", "HOLI Chest", "HOWO Chest", "HOLA Chest", "HOMI Chest"],
		}
	}

	@cooldown(1, 60, BucketType.user)
	@command()
	async def gacha(self, ctx, supply="dorm", pulls: int = 10):
		types = choices([*self.rates.keys()], self.rates.values(), k=pulls)
		drops = [
			choice(self.pool[supply.lower()][i])
			if "Stig" not in i else f"{choice(self.pool[supply.lower()][i])} ({choice(('T', 'M', 'B'))})" for i in types
		]
		await ctx.send("__Your **{}** supply drops:__\n{}".format(supply.capitalize(), "\n".join(drops)))

	@gacha.error
	async def on_error(self, ctx, error):
		if isinstance(error, CommandOnCooldown): # reset cd if command was invoked incorrectly
			return
		self.gacha.reset_cooldown(ctx)
		raise error


def setup(client):
	client.add_cog(Gacha(client))