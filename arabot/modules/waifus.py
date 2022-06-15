from __future__ import annotations

import random
from itertools import chain

from arabot.core import Ara, Category, Cog, Context
from disnake import Embed
from disnake.ext.commands import Command
from waifu import WaifuAioClient
from waifu.utils import ImageCategories, ImageTypes


class Waifus(Cog, category=Category.WAIFUS):
    def __init__(self, waifu_client: WaifuAioClient):
        self.wclient = waifu_client

    async def get_category_image(self, reaction: str, is_nsfw_channel: bool) -> str:
        if all(reaction in category for category in ImageCategories.values()):
            if is_nsfw_channel:
                category = random.choice((self.wclient.sfw, self.wclient.nsfw))
            else:
                category = self.wclient.sfw
        elif reaction in ImageCategories[ImageTypes.nsfw]:
            category = self.wclient.nsfw
        else:
            category = self.wclient.sfw

        return await category(reaction)

    async def __waifu(self, ctx: Context):
        image_url = await self.get_category_image(ctx.command.name, ctx.channel.is_nsfw())
        await ctx.send(embed=Embed().set_image(url=image_url).with_author(ctx.author))

    __locals = locals()
    for __reaction_type in set(chain(*ImageCategories.values())):
        __locals[__reaction_type] = Command(__waifu, name=__reaction_type)

    __locals.pop("__reaction_type", None)
    del __locals


def setup(ara: Ara):
    waifu_client = WaifuAioClient(ara.session)
    ara.add_cog(Waifus(waifu_client))
