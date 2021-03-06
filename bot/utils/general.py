from re import search
from datetime import datetime
from discord import Colour
from discord.ext.commands import Converter, Cog


def is_dev(ctx) -> bool:
    return ctx.author.id in (337343326095409152, 447138372121788417, 401490060156862466)


def is_root(ctx) -> bool:
    return ctx.author.id == 447138372121788417


def is_valid(client, msg, expr="") -> bool:
    return (
        not any(msg.content.startswith(pfx) for pfx in (">", *client.command_prefix))
        and not msg.author.bot
        and search(expr, msg.content.lower())
    )


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


class text_reaction:
    def __init__(self, *, cd=0, regex=None, check=None, string_send=True, reply=False):
        self.expr = regex
        self.check = check
        self.send = string_send
        self.reply = reply
        self._cd = cd if cd > 0 else -1
        self._last_call = datetime(1970, 1, 1)

    def __call__(self, func):
        self.expr = self.expr or "\\b{}\\b".format(func.__name__.replace("_", "\\s"))

        @Cog.listener("on_message")
        async def event(itself, msg):
            if (
                (datetime.now() - self._last_call).seconds > self._cd
                and is_valid(itself.bot, msg, self.expr)
                and (self.check is None or self.check(msg))
            ):
                method = msg.reply if self.reply else msg.channel.send
                if self.send:
                    resp = func(msg)
                    if isinstance(resp, (list, tuple)):
                        await method(str(resp[0]))
                        for i in resp[1:]:
                            await msg.channel.send(str(i))
                    elif resp:
                        await method(str(resp))
                else:
                    await func(itself, msg)
                self._last_call = datetime.now()

        event.__name__ = func.__name__
        return event


class BlacklistMatch(Exception):
    def __init__(self, hit, desc):
        self.hit = hit
        self.desc = desc


class QueryFilter(Converter):
    BLACKLIST = {
        "ight imma head out": "Please use `.iiho` instead of `{ctx.prefix}{ctx.invoked_with}`",
    }

    async def convert(self, ctx, arg):
        if ctx.guild.id == 676889696302792774 and arg in self.BLACKLIST:
            raise BlacklistMatch(arg, self.BLACKLIST[arg].format(ctx=ctx))
        return arg


class Color:
    red = Colour.from_rgb(218, 76, 82)
    yellow = Colour.from_rgb(254, 163, 42)
    green = Colour.from_rgb(39, 159, 109)


async def get_master_invite(guild):
    for i in await guild.invites():
        if i.max_uses == 0:
            return i.url
