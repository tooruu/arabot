from discord import Embed
from discord.ext.commands import MinimalHelpCommand
from ..utils.meta import BOT_NAME
from ..utils.format_escape import bold


class Help(MinimalHelpCommand):
    # def get_command_signature(self, command):
    # 	return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)

    async def send_bot_help(self, mapping):
        help = Embed().set_author(name=BOT_NAME, icon_url=self.context.bot.user.avatar_url_as(static_format="png"))
        for cog in mapping:
            if cog and mapping[cog]:
                help.add_field(name=bold(cog.qualified_name), value="\n".join(f"`{cmd.name}`" for cmd in mapping[cog]))
        await self.get_destination().send(embed=help)
