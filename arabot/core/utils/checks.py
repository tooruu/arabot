from disnake.ext.commands import check


def is_in_guild(guild_id: int):
    return check(lambda ctx: ctx.guild and ctx.guild.id == guild_id)
