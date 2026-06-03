"""Application settings loaded from environment variables."""

from functools import lru_cache
from zoneinfo import ZoneInfo

from pydantic import PositiveInt
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Parse and validate application settings from `.env`."""

    AI_TOKEN: str

    TG_BOT_TOKEN: str
    OWNER_TG_ID: PositiveInt
    ADMIN_CHAT_ID: PositiveInt

    AI_MODEL: str = "openrouter/free"
    timezone: str = "UTC"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        extra="ignore",
    )

    @property
    def tz(self) -> ZoneInfo:
        """Return configured timezone as ZoneInfo."""
        return ZoneInfo(self.timezone)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached Settings instance."""
    return Settings()


settings = get_settings()
