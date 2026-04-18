"""Modelo de produto com categoria, descricao, preco e medidas."""

from typing import Optional

from sqlalchemy import String, Float
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Product(Base):
    __tablename__ = "dim_produtos"

    product_id: Mapped[str] = mapped_column("id_produto", String(32), primary_key=True)
    product_name: Mapped[str] = mapped_column("nome_produto", String(255))
    product_category: Mapped[str] = mapped_column("categoria_produto", String(100))
    product_weight_grams: Mapped[Optional[float]] = mapped_column("peso_produto_gramas", Float, nullable=True)
    length_cm: Mapped[Optional[float]] = mapped_column("comprimento_centimetros", Float, nullable=True)
    height_cm: Mapped[Optional[float]] = mapped_column("altura_centimetros", Float, nullable=True)
    width_cm: Mapped[Optional[float]] = mapped_column("largura_centimetros", Float, nullable=True)

