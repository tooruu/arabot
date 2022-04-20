from arabot.core import Ara
from arabot.utils import getkeys

from .search import GSearch, ImageSearch
from .translate import Translate, TranslationClient
from .tts import TextToSpeech


def setup(ara: Ara):
    ara.add_cog(GSearch(ara))

    ara.add_cog(ImageSearch(ara))

    trans_client = TranslationClient(getkeys("g_trans_key")[0], ara.session)
    ara.add_cog(Translate(trans_client))

    ara.add_cog(TextToSpeech(ara))
