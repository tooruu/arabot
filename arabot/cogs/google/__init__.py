from os import getenv

from arabot.core import Ara

from .ocr import OpticalCharacterRecognition
from .search import GSearch, ImageSearch
from .translate import Translate, TranslationClient
from .tts import TextToSpeech


def setup(ara: Ara):
    session = ara.session
    trans_client = TranslationClient(getenv("g_trans_key"), session)
    trans = Translate(trans_client)
    ara.add_cog(trans)
    ara.add_cog(OpticalCharacterRecognition(trans))
    for cog in GSearch, ImageSearch, TextToSpeech:
        ara.add_cog(cog(session))
