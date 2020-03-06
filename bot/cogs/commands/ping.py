from discord import File
from discord.ext.commands import command, Cog
from datetime import datetime, timedelta
from discord.ext.tasks import loop
from .._utils import Queue
from io import BytesIO
from matplotlib import use
use("AGG")
from matplotlib import pyplot as plt, dates as md


class Ping(Cog):
	def __init__(self, client):
		self.bot = client
		self.old = self.bot.remove_command("ping")
		self.log = Queue(60)
		self.store.start()

	@loop(minutes=1)
	async def store(self):
		self.log.enqueue(round(self.bot.latency * 1000))

	@store.before_loop
	async def wait(self):
		await self.bot.wait_until_ready()

	@command()
	async def ping(self, ctx):
		x = [datetime.now() + timedelta(minutes=i) for i in range(-self.log.size, 0)]
		y = self.log
		y = [
			102, 101, 105, 100, 100, 100, 102, 115, 100, 101, 102, 104, 102, 98, 103, 106, 100, 100, 130, 102, 103, 100,
			101, 100, 101, 110, 101, 109, 102, 101, 101, 101, 101, 100, 103, 100, 100, 102, 106, 101, 102, 101, 102, 100,
			102, 113, 101, 101, 110, 102, 103, 100, 111, 103, 102, 102, 99, 101, 102, 109
		]
		ax = plt.subplots(figsize=(4, 1))[1]
		plt.plot(x, y)
		plt.ylabel("Ping (ms)")
		plt.xlabel("The last hour")
		ax.set_xlim(x[0], x[-1])
		ax.xaxis.set_major_locator(md.MinuteLocator(interval=1))
		ax.xaxis.set_major_formatter(md.DateFormatter(""))

		# Send figure
		buf = BytesIO()
		plt.savefig(buf, format="png")
		buf.seek(0)
		await ctx.send(f":ping_pong: Pong after {round(self.bot.latency, 3)}ms!", file=File(buf, "ping.png"))
		plt.clf() # Delete opened figure

	@command()
	async def showlog(self, ctx):
		await ctx.send(str(self.log))

	def cog_unload(self):
		self.store.cancel()
		self.bot.remove_command("ping")
		self.bot.add_command(self.old)


def setup(client):
	client.add_cog(Ping(client))