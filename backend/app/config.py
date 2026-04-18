"""Define configuracoes e carrega variaveis de ambiente do backend."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_DB_PATH = (BASE_DIR / "Banco" / "banco.db").as_posix()


class Settings(BaseSettings):
    database_url: str = Field(default=f"sqlite:///{DEFAULT_DB_PATH}", alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
