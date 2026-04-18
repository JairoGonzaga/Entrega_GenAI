"""Modelo de vendedor com dados basicos de localizacao."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Seller(Base):
    __tablename__ = "dim_vendedores"

    seller_id: Mapped[str] = mapped_column("id_vendedor", String(32), primary_key=True)
    seller_name: Mapped[str] = mapped_column("nome_vendedor", String(255))
    zip_prefix: Mapped[str] = mapped_column("prefixo_cep", String(10))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
