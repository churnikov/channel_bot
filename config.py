from pydantic import BaseSettings, Field


class Settings(BaseSettings):
    tg_api_id: str = Field(..., env="TG_API_ID")
    tg_api_hash: str = Field(..., env="TG_API_HASH")
    """get it from my.telegram.com"""

    tg_bot_token: str = Field(..., env="TG_BOT_TOKEN")
    """get it from @botfather"""

    class Config:
        env_file = '.env'
        env_file_encoding = 'utf-8'


settings = Settings()
