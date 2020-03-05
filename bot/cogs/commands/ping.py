from discord.ext.commands import command, Cog
from datetime import datetime, timedelta
from discord.ext.tasks import loop
from .._utils import Queue
from io import BytesIO
from matplotlib import use
use("AGG")
from matplotlib import pyplot as plt, dates as md
from random import choices
from discord import File


class Ping(Cog):
	def __init__(self, client):
		self.bot = client
		self.log = Queue(60)
		self.store.start()

	@loop(minutes=1)
	async def store(self):
		self.log.enqueue(self.bot.latency * 1000)

	@store.before_loop
	async def wait(self):
		await self.bot.wait_until_ready()

	@command()
	async def ping(self, ctx):
		x = [datetime.now() + timedelta(minutes=i) for i in range(-self.log.size, 0)]
		y = self.log
		ax = plt.subplots()[1]
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
		self.countdown.cancel()


def setup(client):
	client.add_cog(Ping(client))