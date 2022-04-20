import aiohttp as _aiohttp
import disnake as _disnake

from .converters import *
from .format import *
from .utils import *

_aiohttp.ClientSession.fetch_json = fetch_json
_disnake.Guild.get_unlimited_invite = get_unlimited_invite
_disnake.abc.Messageable.temp_mute_member = temp_mute_channel_member
_disnake.Message.rsearch = rmsg_search
_disnake.VoiceChannel.connect_play_disconnect = connect_play_disconnect
_disnake.Asset.compat = property(lambda self: self.with_static_format("png"))
