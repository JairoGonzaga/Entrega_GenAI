"""Modelo de consumidor com dados basicos de localizacao."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDeclarativa


class Consumidor(BaseDeclarativa):
    __tablename__ = "consumidores"

    id_consumidor: Mapped[str] = mapped_column(String(32), primary_key=True)
    prefixo_cep: Mapped[str] = mapped_column(String(10))
    nome_consumidor: Mapped[str] = mapped_column(String(255))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
