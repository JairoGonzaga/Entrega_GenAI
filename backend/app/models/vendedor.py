"""Modelo de vendedor com dados basicos de localizacao."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDeclarativa


class Vendedor(BaseDeclarativa):
    __tablename__ = "vendedores"

    id_vendedor: Mapped[str] = mapped_column(String(32), primary_key=True)
    nome_vendedor: Mapped[str] = mapped_column(String(255))
    prefixo_cep: Mapped[str] = mapped_column(String(10))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
