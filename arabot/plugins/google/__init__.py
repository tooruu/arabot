from arabot.core import Ara, Config

from arabot.plugins.google.images import GoogleImages
from arabot.plugins.google.ocr import GoogleOCR
from arabot.plugins.google.search import GoogleSearch
from arabot.plugins.google.translate import GoogleTranslate, TranslationClient
from arabot.plugins.google.tts import GoogleTTS
from arabot.plugins.google.youtube import Youtube


def setup(ara: Ara):
    session = ara.session
    trans_client = TranslationClient(Config.g_trans_key, session)
    trans = GoogleTranslate(trans_client)
    ara.add_cog(trans)
    ara.add_cog(GoogleOCR(trans))
    for cog in GoogleSearch, GoogleImages, GoogleTTS, Youtube:
        ara.add_cog(cog(session))
