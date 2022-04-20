from collections.abc import Iterable

from arabot.utils import getkeys
from disnake import HTTPException, Message
from disnake.ext import commands


class Context(commands.Context):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ara: commands.Bot = self.bot

    async def reply(self, content: str | None = None, *, strict: bool = False, **kwargs) -> Message:
        reply = super().reply(content, **kwargs)

        if strict:
            return await reply

        try:
            return await reply
        except HTTPException:
            return await self.send(content, **kwargs)

    @property
    def argument_only(self) -> str:
        if not self.valid:
            return self.message.content

        content = self.message.content
        for p in self.prefix, *self.invoked_parents, self.invoked_with:
            content = content.removeprefix(p).lstrip()
        return content


class Category:
    GENERAL = "General"
    FUN = "Fun"
    META = "Meta"
    LOOKUP = "Lookup"
    COMMUNITY = "Community"
    MODERATION = "Moderation"
    GAMES = "Games"


class Cog(commands.Cog):
    def __init_subclass__(cls, category: Category = None, keys: Iterable[str] = (), **kwargs):
        cls.category = category
        for key_name, key in zip(keys, getkeys(*keys)):
            setattr(cls, key_name, key)
        super().__init_subclass__(**kwargs)
