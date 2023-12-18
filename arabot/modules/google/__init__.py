from os import getenv

from arabot import Ara

from .images import GoogleImages
from .ocr import GoogleOCR
from .search import GoogleSearch
from .translate import GoogleTranslate, TranslationClient
from .tts import GoogleTTS
from .youtube import Youtube


def setup(ara: Ara):
    session = ara.session
    trans_client = TranslationClient(getenv("G_TRANS_KEY"), session)
    trans = GoogleTranslate(trans_client)
    ara.add_cog(trans)
    ara.add_cog(GoogleOCR(trans))
    for cog in GoogleSearch, GoogleImages, GoogleTTS, Youtube:
        ara.add_cog(cog(session))
