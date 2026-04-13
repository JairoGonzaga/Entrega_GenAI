"""Define configuracoes e carrega variaveis de ambiente do backend."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


DIRETORIO_BASE = Path(__file__).resolve().parent.parent
CAMINHO_PADRAO_BANCO = (DIRETORIO_BASE / "database.db").as_posix()


class Configuracoes(BaseSettings):
    url_banco: str = Field(default=f"sqlite:///{CAMINHO_PADRAO_BANCO}", alias="DATABASE_URL")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


configuracoes = Configuracoes()
