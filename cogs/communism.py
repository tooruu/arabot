from discord.ext.commands import Cog #, command
event = Cog.listener


class Communism(Cog):
	def __init__(self, client):
		self.client = client

	@event()
	async def on_message(self, msg):
		if not msg.content[
			0] == ";" and "communism" in msg.content and not msg.author == self.client.user:
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
			await self.client.process_commands(msg) # this prevents on_message blocking code


def setup(client):
	client.add_cog(Communism(client))