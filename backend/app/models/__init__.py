"""Importa modelos para registro no SQLAlchemy e Alembic."""

# Importa todos os models para que o SQLAlchemy e o Alembic os registrem
from app.models.consumidor import Consumidor
from app.models.produto import Produto
from app.models.vendedor import Vendedor
from app.models.pedido import Pedido
from app.models.item_pedido import ItemPedido
from app.models.avaliacao_pedido import AvaliacaoPedido

__all__ = [
    "Consumidor",
    "Produto",
    "Vendedor",
    "Pedido",
    "ItemPedido",
    "AvaliacaoPedido",
]
