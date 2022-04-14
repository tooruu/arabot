from collections.abc import Iterable

from arabot.utils import Category, getkeys
from disnake import HTTPException, Message
from disnake.ext import commands


class Context(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ara = self.bot

    async def reply(self, content: str | None = None, *, strict: bool = False, **kwargs) -> Message:
        reply = super().reply(content, **kwargs)

        if strict:
            return await reply

        try:
            return await reply
        except HTTPException:
            return await self.send(content, **kwargs)


class ContextMixin:
    async def get_context(self, message: Message, *, cls=Context):
        return await super().get_context(message, cls=cls)


class Cog(commands.Cog):
    def __init_subclass__(cls, category: Category = None, keys: Iterable[str] = (), **kwargs):
        cls.category = category
        for key_name, key in zip(keys, getkeys(*keys)):
            setattr(cls, key_name, key)
        super().__init_subclass__(**kwargs)
