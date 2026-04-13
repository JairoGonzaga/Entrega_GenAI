"""Modelo de itens do pedido, relacionando produto e vendedor."""

from sqlalchemy import String, Float, Integer, ForeignKey, PrimaryKeyConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDeclarativa


class ItemPedido(BaseDeclarativa):
    __tablename__ = "itens_pedidos"

    id_pedido: Mapped[str] = mapped_column(
        String(32), ForeignKey("pedidos.id_pedido"), nullable=False
    )
    id_item: Mapped[int] = mapped_column(Integer, nullable=False)
    id_produto: Mapped[str] = mapped_column(
        String(32), ForeignKey("produtos.id_produto"), nullable=False
    )
    id_vendedor: Mapped[str] = mapped_column(
        String(32), ForeignKey("vendedores.id_vendedor"), nullable=False
    )
    preco_BRL: Mapped[float] = mapped_column(Float)
    preco_frete: Mapped[float] = mapped_column(Float)

    __table_args__ = (
        PrimaryKeyConstraint("id_pedido", "id_item"),
    )
