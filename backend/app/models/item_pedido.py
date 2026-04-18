"""Modelo de itens do pedido, relacionando produto e vendedor."""

from sqlalchemy import String, Float, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderItem(Base):
    __tablename__ = "fat_itens_pedidos"

    order_id: Mapped[str] = mapped_column(
        "id_pedido", String(32), ForeignKey("fat_pedidos.id_pedido"), nullable=False
    )
    item_id: Mapped[int] = mapped_column("id_item", Integer, nullable=False)
    product_id: Mapped[str] = mapped_column(
        "id_produto", String(32), ForeignKey("dim_produtos.id_produto"), nullable=False
    )
    seller_id: Mapped[str] = mapped_column(
        "id_vendedor", String(32), ForeignKey("dim_vendedores.id_vendedor"), nullable=False
    )
    price_brl: Mapped[float] = mapped_column("preco_BRL", Float)
    freight_price: Mapped[float] = mapped_column("preco_frete", Float)

    __table_args__ = (
        PrimaryKeyConstraint("id_pedido", "id_item"),
    )
