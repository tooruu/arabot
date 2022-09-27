from collections import deque
from io import BytesIO

from disnake import File
from disnake.ext.commands import command
from disnake.ext.tasks import loop
from matplotlib import pyplot as plt
from matplotlib.ticker import MaxNLocator

from arabot.core import Ara, Category, Cog, Context


class Ping(Cog, category=Category.META):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.log = deque([0] * 60, 60)
        self.store.start()

    @loop(minutes=1)
    async def store(self):
        self.log.append(round(self.ara.latency * 1000))

    @store.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    @command(brief="View Discord server's connectivity")
    async def ping(self, ctx: Context):
        self.plot_graph()
        image = self.plt_to_file()
        await ctx.send(ctx._("🏓 Pong - {}ms").format(f"{ctx.ara.latency * 1000:.0f}"), file=image)

    def plot_graph(self):
        y_padding = 5
        x, y = range(self.log.maxlen), self.log
        ax = plt.subplots(figsize=(3, 1))[1]
        plt.plot(x, y, linewidth=0.5)
        plt.subplots_adjust(bottom=0.2, right=0.97)
        plt.tick_params(axis="x", direction="in", labelbottom=False)
        plt.tick_params(labelsize=4, length=3, width=0.5, pad=0.3)
        plt.ylabel("Ping (ms)", fontsize=7)
        plt.xlabel("The last hour", fontsize=8)
        ax.set_xlim(x[0], x[-1])
        ax.set_ylim(min(set(y) - {0} or [y_padding]) - y_padding, max(y) + y_padding)
        ax.get_yaxis().set_major_locator(MaxNLocator(integer=True, nbins=5))
        plt.fill_between(x, y, color="cyan", alpha=0.45)

    @staticmethod
    def plt_to_file() -> File:
        buf = BytesIO()
        plt.savefig(buf, dpi=180, format="png", transparent=False)
        buf.seek(0)
        file = File(buf, "ping.png")
        plt.close()
        del buf
        return file

    def cog_unload(self):
        self.store.cancel()


def setup(ara: Ara):
    ara.add_cog(Ping(ara))
