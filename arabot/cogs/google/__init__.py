from arabot.core import Ara
from arabot.core.utils import getkeys

from .ocr import OpticalCharacterRecognition
from .search import GSearch, ImageSearch
from .translate import Translate, TranslationClient
from .tts import TextToSpeech


def setup(ara: Ara):
    session = ara.session
    trans_client = TranslationClient(getkeys("g_trans_key")[0], session)
    ara.add_cog(Translate(trans_client))
    for cog in GSearch, ImageSearch, TextToSpeech, OpticalCharacterRecognition:
        ara.add_cog(cog(session))
