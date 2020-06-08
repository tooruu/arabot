from discord import File
from discord.ext.commands import command, Cog
from discord.ext.tasks import loop
from .._utils import Queue
from io import BytesIO
from matplotlib.ticker import MaxNLocator
from matplotlib import use
use("AGG") #pylint: disable=wrong-import-position
from matplotlib import pyplot as plt

class Ping(Cog):
	def __init__(self, client, old_ping):
		self.bot = client
		self.old = old_ping
		self.log = Queue(60)
		self.store.start()

	@loop(minutes=1)
	async def store(self):
		self.log += round(self.bot.latency * 1000)

	@store.before_loop
	async def wait(self):
		await self.bot.wait_until_ready()

	@command()
	async def ping(self, ctx):
		# Plot graph
		x, y = range(self.log.size), self.log
		ax = plt.subplots(figsize=(3, 1))[1]
		plt.plot(x, y, linewidth=0.5)
		plt.subplots_adjust(bottom=0.2, right=0.97)
		plt.tick_params(axis="x", direction="in", labelbottom=False)
		plt.tick_params(labelsize=4, length=3, width=0.5, pad=0.3)
		plt.ylabel("Ping (ms)", fontsize=7)
		plt.xlabel("The last hour", fontsize=8)
		ax.set_xlim(x[0], x[-1])
		ax.set_ylim((min(y) if y[0] != 0 else sorted(set(y))[1]) - 5, max(y) + 5)
		ax.get_yaxis().set_major_locator(MaxNLocator(integer=True, nbins=5))
		plt.fill_between(x, y, color="cyan", alpha=0.45)

		# Send figure
		buf = BytesIO()
		plt.savefig(buf, dpi=180, format="png", transparent=False)
		buf.seek(0)
		await ctx.send(f":ping_pong: Pong after {self.bot.latency * 1000:.0f}ms!", file=File(buf, "ping.png"))
		plt.close()
		del buf

	def cog_unload(self):
		self.store.cancel()
		self.bot.remove_command("ping")
		self.bot.add_command(self.old)

def setup(client):
	client.add_cog(Ping(client, client.remove_command("ping")))