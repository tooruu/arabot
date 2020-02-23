from discord.ext.commands import command, Cog, MemberConverter, errors
from discord import Member
from discord.utils import find


class FindMember(MemberConverter):
	async def convert(self, ctx, argument):
		try:
			return await MemberConverter().convert(ctx, argument)
		except errors.BadArgument:
			return find(
				lambda member: not member.bot and member.name.lower().
				startswith(argument.lower()), ctx.guild.members
			) or argument


class Love(Cog):
	def __init__(self, client):
		self.client = client

	@command()
	async def love(self, ctx, target: FindMember):
		await ctx.send(
			f"{ctx.author.mention} loves {target.mention} :heart:"
			if isinstance(target, Member) else f"User **{target}** not found"
		)


def setup(client):
	client.add_cog(Love(client))