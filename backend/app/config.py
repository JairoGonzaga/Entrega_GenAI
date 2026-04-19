"""Define configuracoes e carrega variaveis de ambiente do backend."""

from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "Banco" / "banco.db").as_posix()


class Settings(BaseSettings):
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH}", alias="DATABASE_URL")
    gemini_model: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    google_api_key: Optional[str] = Field(default=None, alias="GOOGLE_API_KEY")

    @property
    def resolved_gemini_api_key(self) -> Optional[str]:
        """Resolve API key with backward-compatible fallback."""
        return self.gemini_api_key or self.google_api_key

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
