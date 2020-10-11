from discord.ext.commands import Cog
from re import search
from asyncio import wait_for, TimeoutError, sleep

class EasterEggs(Cog):
	def __init__(self, client):
		self.bot = client
		self.running = False

	@Cog.listener("on_message")
	async def imposter(self, msg):
		if not self.running and not msg.author.bot and msg.author.voice and (chl:=msg.author.voice.channel) and (word:=search("\\b(impost[eo]r)\\b", msg.content.lower())):
			self.running = True
			TIMEOUT = 30
			word = word.group(1)
			await msg.channel.send("<:KonoDioDa:676949860502732803>")
			await msg.channel.send(f"You have {TIMEOUT} seconds to find the {word}!\nPing the person you think is the {word} to vote")
			voted, votes = [], {}
			check = lambda vote: vote.author not in voted and vote.mentions and search("^<@!?\d{15,21}>$", vote.content) and vote.channel == msg.channel and vote.author.voice and vote.author.voice.channel == chl and vote.mentions[0].voice and vote.mentions[0].voice.channel == chl and vote.mentions[0] != vote.author
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
			if len(voted) > 1:
				imposter = max(votes, key=lambda m: votes[m])
				await msg.channel.send(f"{imposter.mention} was the {word}.")
				await imposter.move_to(None, reason="The " + word)
			else:
				await msg.channel.send("No one was ejected.")
			sleep(60)
			self.running = False

def setup(client):
	client.add_cog(EasterEggs(client))
