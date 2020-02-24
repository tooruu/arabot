from discord.ext.commands import Cog #, command
event = Cog.listener


class Communism(Cog):
	def __init__(self, client):
		self.client = client

	isValid = lambda self, msg, invocator: not msg.content.startswith(
		self.client.command_prefix
	) and msg.author != self.client.user and invocator.lower() in msg.content.lower()

	@event()
	async def on_message(self, msg):
		if self.isValid(msg, "communism"):
			await msg.channel.send(
				""":b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:
:b::b::b::b::b::b::b::b:<:CommuThink:676973669796544542>:b::b::b::b::b::b:
:b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b::b:
:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:"""
			)
			await msg.channel.send(
				"""
:b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b::b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:
:b::b::b::b:<:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:<:CommuThink:676973669796544542><:CommuThink:676973669796544542>:b::b:
:b::b::b::b::b::b::b::b::b::b::b::b::b::b::b:"""
			)


def setup(client):
	client.add_cog(Communism(client))