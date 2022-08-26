from disnake.ext.commands.errors import CommandError


class StopCommand(CommandError):
    "Helper exception that easily interrupts command execution from within nested function calls."
