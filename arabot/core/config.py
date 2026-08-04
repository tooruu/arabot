from pydantic_settings import BaseSettings, SettingsConfigDict


def singleton[T](cls: type[T]) -> T:
    return cls()


@singleton
class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    token: str
    database_url: str
    debug_mode: bool = False

    g_search_key: str
    g_isearch_key: str
    g_cse: str
    g_yt_key: str
    faceit_key: str
    wolfram_id: str
    g_trans_key: str
    g_tts_key: str
    saucenao_key: str
    g_ocr_key: str
    openweather_key: str
    elevenlabs_api_key: str
    piston_key: str
    nvidia_api_key: str
