from discord.ext.commands import Cog
from re import search
from asyncio import wait_for, TimeoutError, sleep

class Imposter(Cog, name="Eggs"):
	def __init__(self, client):
		self.bot = client
		self.running = False

	@Cog.listener("on_message")
	async def imposter(self, msg):
		if not self.running and not msg.author.bot and msg.author.voice and (chl :=
			msg.author.voice.channel) and [not m.bot
			for m in chl.members].count(True) > 2 and (word := search("\\b(impost[eo]r)\\b", msg.content.lower())):
			# Initializing
			self.running = True
			TIMEOUT = 30
			word = word.group(1)
			await msg.channel.send("<:KonoDioDa:676949860502732803>")
			await msg.channel.send(
				f"You have {TIMEOUT} seconds to find the {word}!\nPing the person you think is the {word} to vote"
			)
			# Voting phase
			voted, votes = [], {}
			check = lambda vote: vote.author not in voted and vote.mentions and search("^<@!?\d{15,21}>$", vote.
				content) and vote.channel == msg.channel and vote.author.voice and vote.author.voice.channel == chl and (
				target := vote.mentions[0]
				).voice and target.voice.channel == chl and target != vote.author and not target.bot

			async def ensure():
				while True:
					vote = await self.bot.wait_for("message", check=check)
					await vote.delete()
					voted.append(vote.author)
					votes[vote.mentions[0]] = votes.get(vote.mentions[0], 0) + 1

			try:
				await wait_for(ensure(), timeout=TIMEOUT)
			except TimeoutError:
				pass
			# Ejection phase
			if len(voted) > 1 and list(votes.values()).count(
				votes[(imposter := max(votes, key=lambda m: votes[m]))]
			) == 1 and imposter.voice and imposter.voice.channel == chl:
				await msg.channel.send(f"{imposter.mention} was the {word}.")
				await imposter.move_to(None, reason="The " + word)
			else:
				await msg.channel.send("No one was ejected.")
			await sleep(60)
			self.running = False

def setup(client):
	client.add_cog(Imposter(client))
