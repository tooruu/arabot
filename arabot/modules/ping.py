from collections import deque
from io import BytesIO

import matplotlib.pyplot as plt
from disnake import File
from disnake.ext.commands import command
from disnake.ext.tasks import loop
from matplotlib.axes import Axes

from arabot.core import Ara, Category, Cog, Context
from arabot.utils import I18N


class Ping(Cog, category=Category.META):
    def __init__(self, ara: Ara):
        self.ara = ara
        self.log = deque([0] * 60, 60)
        self.store.start()
        self.fig, ax = plt.subplots(figsize=(3, 1), dpi=180, layout="constrained")
        self.ax: Axes = ax
        self.ax.tick_params("x", direction="in", labelbottom=False)
        self.ax.tick_params(labelsize=4, length=3, width=0.5, pad=0.3)

    @loop(minutes=1)
    async def store(self):
        self.log.append(round(self.ara.latency * 1000))

    @store.before_loop
    async def ensure_ready(self):
        await self.ara.wait_until_ready()

    @command(brief="View Discord server's connectivity")
    async def ping(self, ctx: Context):
        self.plot_graph(ctx._)
        image = self.plt_to_file()
        self.ax.clear()
        await ctx.send(ctx._("pong").format(f"{ctx.ara.latency * 1000:.0f}"), file=image)

    def plot_graph(self, _: I18N):
        y_padding = 5
        x, y = range(self.log.maxlen), self.log
        self.ax.set_ylabel(_("y_label"), fontsize=7)
        self.ax.set_xlabel(_("x_label"), fontsize=8)
        self.ax.set_ylim(min(set(y) - {0} or [y_padding]) - y_padding, max(y) + y_padding)
        self.ax.set_xlim(0, self.log.maxlen - 1)
        self.ax.fill_between(x, y, color="cyan", alpha=0.45)
        self.ax.plot(x, y, linewidth=0.5)

    def plt_to_file(self) -> File:
        buf = BytesIO()
        self.fig.savefig(buf)
        buf.seek(0)
        return File(buf, "ping.png")

    def cog_unload(self):
        self.store.cancel()
        plt.close(self.fig)


def setup(ara: Ara):
    ara.add_cog(Ping(ara))
