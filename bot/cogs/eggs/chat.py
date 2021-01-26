from re import match
from discord.ext.commands import Cog
from utils.utils import text_reaction


class Chat(Cog, name="Eggs"):
    def __init__(self, client):
        self.bot = client

    @text_reaction(check=lambda msg: len(msg.content) < 15)
    def who(msg):
        return "ur mom"

    @text_reaction(
        regex=r"^(?:i(?:['’]?m|\sam)\s)+(?:(?:an?|the)\s)?\w$",
        check=lambda msg: len(msg.content) < 20,
    )
    def im_hi(msg):
        regex = match(r"(?:i(?:['’]?m|\sam)\s)+(?:(?:an?|the)\s)?(\w)", msg.content.lower())
        return "hi " + regex.group(1)

    @text_reaction(regex="\\brac(?:e|ing)\\b", cd=15)
    def racing(msg):
        return "***RACING TIME***", "🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽🧑🏼‍🦽"

    @text_reaction(regex=";-;")
    def cry(msg):
        return msg.author.mention + " don't cry <:KannaPat:762774093723860993>"


def setup(client):
    client.add_cog(Chat(client))
