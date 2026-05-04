import os
from pydantic_settings import BaseSettings, SettingsConfigDict

DOTENV = os.path.join(os.path.dirname(__file__), "../../.env")
class Settings(BaseSettings):
    PROJECT_NAME: str
    VERSION: str
    MANTICORE_SEARCH_URL: str
    DGEG_PRECO_COMB_API_URL: str
    NOMINATIM_USER_AGENT: str
    model_config = SettingsConfigDict(
        env_file=DOTENV,
        env_file_encoding='utf-8',
        extra='ignore'
    )
    
settings = Settings()