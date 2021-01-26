from discord.ext.commands import Converter
from discord.ext.commands.errors import BadArgument


class Finder(Converter):
    """
    Abstract class to convert *argument* to desired type.
    1. Try to convert via subclass's parents'
        `convert` methods (implemented in discord.py)
    2. Try to convert via subclass's own method `find`

    # Example usage:
    ```
    class FindObject(Finder, AConverter, BConverter):
        @staticmethod
        async def find(ctx, argument):
            return utils.find(lambda obj: obj.att == argument, ctx.obj_list) or await thing()
    ```
    """

    def __init__(self):
        if len(self.__class__.__bases__) == 1:
            raise IndexError(f"<'{self.__class__.__name__}'> must have at least 2 parents")
        if not all(issubclass(base, Converter) for base in self.__class__.__bases__[1:]):
            raise TypeError(f"Parents of <'{self.__class__.__name__}'> are not derived from Converter")

    async def convert(self, ctx, argument):
        for conv in self.__class__.__bases__[1:]:
            try:
                return await conv().convert(ctx, argument)
            except BadArgument:
                pass
        return await self.find(ctx, argument)

    @staticmethod
    async def find(ctx, argument):
        raise NotImplementedError("Derived classes need to implement this.")
