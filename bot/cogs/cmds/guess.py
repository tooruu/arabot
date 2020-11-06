from discord.ext.commands import command, Cog, check, BucketType, cooldown
from asyncio import wait_for, TimeoutError, sleep
from random import randint

class Guess(Cog, name="Commands"):
	def __init__(self, client):
		self.bot = client

	@cooldown(1, 120, BucketType.guild)
	@command(hidden=True)
	@check(lambda ctx: ctx.guild.id == 676889696302792774)
	async def guess(self, ctx, MAX: int=20):
		# Initializing
		TIMEOUT = 20
		MUTED_ROLE = ctx.guild.get_role(751868258130329732)
		NUMBER = randint(1, MAX)
		await ctx.send(
			f":game_die: You have {TIMEOUT} seconds to guess a number between 1-{MAX}."
		)
		# Voting phase
		guesses = {}
		def check(vote):
			if vote.channel == ctx.channel and vote.author not in guesses:
				try:
					return int(vote.content) not in guesses.values() and 1 <= int(vote.content) <= MAX
				except ValueError:
					pass

		async def ensure():
			while True:
				vote = await self.bot.wait_for("message", check=check)
				await vote.add_reaction('✅')
				guesses[vote.author] = int(vote.content)

		try:
			await wait_for(ensure(), timeout=TIMEOUT)
		except TimeoutError:
			pass
		# Ejection phase
		if len(guesses) > 1:
			winner = min(guesses, key=lambda m: abs(guesses[m] - NUMBER))
			await ctx.send(f"{winner.mention} Congrats, {'you guessed' if guesses[winner] == NUMBER else 'your guess was the closest one to'} the number {NUMBER} <:TeriCelebrate:676915184698130469>\nEnjoy your 1 minute mute!")
			await winner.add_roles(MUTED_ROLE, reason="Guessed the number")
			await sleep(60)
			await winner.remove_roles(MUTED_ROLE, reason="Have mercy")
		else:
			await ctx.send("No one has won.")

def setup(client):
	client.add_cog(Guess(client))
