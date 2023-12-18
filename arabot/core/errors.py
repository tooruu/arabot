from disnake.ext.commands.errors import CommandError


class StopCommand(CommandError):
    """Interrupt command execution from within nested function calls."""
