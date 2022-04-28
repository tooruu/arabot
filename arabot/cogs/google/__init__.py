from arabot.core import Ara
from arabot.utils import getkeys

from .search import GSearch, ImageSearch
from .translate import Translate, TranslationClient
from .tts import TextToSpeech


def setup(ara: Ara):
    session = ara.session
    trans_client = TranslationClient(getkeys("g_trans_key")[0], session)
    ara.add_cog(Translate(trans_client))
    ara.add_cog(GSearch(session))
    ara.add_cog(ImageSearch(session))
    ara.add_cog(TextToSpeech(session))
