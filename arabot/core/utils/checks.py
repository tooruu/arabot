from disnake.ext.commands import check as _check


def is_in_guild(guild_id: int):
    return _check(lambda ctx: ctx.guild and ctx.guild.id == guild_id)
