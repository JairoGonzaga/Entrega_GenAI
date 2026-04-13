"""Configura o Alembic para executar migracoes com o motor da app."""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from alembic import context
from app.database import BaseDeclarativa, motor
import app.models 

target_metadata = BaseDeclarativa.metadata


def executar_migracoes():
    """
    Executa as migracoes do Alembic usando o motor da aplicacao.
    Roda em transacao unica e aponta para o metadata do SQLAlchemy.
    """
    with motor.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


executar_migracoes()
