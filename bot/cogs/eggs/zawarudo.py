from asyncio import sleep
from discord.ext.commands import Cog
from ...utils.general import is_valid


class ZaWarudo(Cog, name="Eggs"):
    def __init__(self, client):
        self.bot = client
        self.running = False

    @Cog.listener("on_message")
    async def za_warudo(self, msg):
        if not self.running and is_valid(self.bot, msg, "za warudo"):
            self.running = True
            old_perms = msg.channel.overwrites_for(msg.guild.default_role)
            temp_perms = msg.channel.overwrites_for(msg.guild.default_role)
            temp_perms.send_messages = False
            msgs = []
            await msg.channel.set_permissions(msg.guild.default_role, overwrite=temp_perms)
            await msg.channel.send("<:KonoDioDa:937687826693251102>")
            msgs.append(await msg.channel.send("***Toki yo tomare!***"))
            for i in (
                "Ichi",
                "Ni",
                "San",
                "Yon",
                "Go",
            ):  # Ichi Ni San Yon Go Roku Nana Hachi Kyu
                await sleep(2)
                msgs.append(await msg.channel.send(content=f"*{i} byou keika*"))
            await sleep(1)
            msgs.append(await msg.channel.send("Toki wa ugoki dasu"))
            await sleep(1)
            await msg.channel.delete_messages(msgs)
            await msg.channel.set_permissions(msg.guild.default_role, overwrite=old_perms)
            await sleep(20)
            self.running = False


def setup(client):
    client.add_cog(ZaWarudo(client))
