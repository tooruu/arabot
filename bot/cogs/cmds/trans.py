from html import unescape
from discord import Embed
from discord.ext.commands import command, Cog
from ...utils.format_escape import dsafe
from ...helpers.auth import req_auth


class Trans(Cog, name="Commands"):
    def __init__(self, client, key):
        self.bot = client
        self.key = key

    @command(
        aliases=["trans", "tr"],
        brief="<target_lang> <text> | Translates text to target language",
    )
    async def translate(self, ctx, lang_to, *, text=None):
        if not text:
            await ctx.send("I need text to translate")
            return
        if len(text) > 1024:
            await ctx.send("Your text is too long,\ntrimming it to the first 1024 characters")
            text = text[:1024]
        trans = (
            await self.bot.fetch_json(
                "https://translation.googleapis.com/language/translate/v2",
                params={"key": self.key, "target": lang_to, "q": text},
            )
        )["data"]["translations"][0]
        embed = (
            Embed()
            .add_field(name=trans["detectedSourceLanguage"].upper(), value=dsafe(text)[:1024])
            .add_field(
                name=lang_to.upper(),
                value=dsafe(unescape(trans["translatedText"]))[:1024],
                inline=False,
            )
        )
        await ctx.send(embed=embed)


@req_auth("g_trans_key")
def setup(client, key):
    client.add_cog(Trans(client, key))
