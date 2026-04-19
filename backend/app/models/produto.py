"""Modelo de produto com categoria e medidas."""

from typing import Optional

from sqlalchemy import Float, String, func, select
from sqlalchemy.orm import Mapped, mapped_column, object_session

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

    @property
    def product_description(self) -> str:
        """Compatibilidade com o schema antigo usando a categoria do produto."""
        label = (self.product_category or "").replace("_", " ").strip()
        return f"Item da categoria {label}." if label else "Item da categoria desconhecida."

    @property
    def base_price(self) -> Optional[float]:
        """Compatibilidade com o schema antigo usando o preco medio dos itens do produto."""
        session = object_session(self)
        if session is None:
            return None

        from app.models.item_pedido import OrderItem

        average_price = session.scalar(
            select(func.avg(OrderItem.price_brl)).where(OrderItem.product_id == self.product_id)
        )
        return round(float(average_price), 2) if average_price is not None else None

