"""Modelo de consumidor com dados basicos de localizacao."""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Customer(Base):
    __tablename__ = "dim_consumidores"

    customer_id: Mapped[str] = mapped_column("id_consumidor", String(32), primary_key=True)
    zip_prefix: Mapped[str] = mapped_column("prefixo_cep", String(10))
    customer_name: Mapped[str] = mapped_column("nome_consumidor", String(255))
    cidade: Mapped[str] = mapped_column(String(100))
    estado: Mapped[str] = mapped_column(String(2))
