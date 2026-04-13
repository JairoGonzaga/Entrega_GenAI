"""Configura motor, sessoes e base declarativa do SQLAlchemy."""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import configuracoes

motor = create_engine(
    configuracoes.url_banco,
    connect_args={"check_same_thread": False},
)

SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=motor)


class BaseDeclarativa(DeclarativeBase):
    pass


def obter_db():
    """
    Fornece uma sessao do banco via dependencia do FastAPI.
    Fecha a sessao ao final do request, mesmo em erro.
    """
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()
