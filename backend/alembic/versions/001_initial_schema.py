"""Criacao inicial do schema

Revision ID: 001
Revises:
Create Date: 2026-04-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Cria todas as tabelas iniciais do schema da aplicacao.
    Define chaves primarias e relacionamentos basicos.
    """
    op.create_table(
        "consumidores",
        sa.Column("id_consumidor", sa.String(32), primary_key=True),
        sa.Column("prefixo_cep", sa.String(10), nullable=False),
        sa.Column("nome_consumidor", sa.String(255), nullable=False),
        sa.Column("cidade", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(2), nullable=False),
    )

    op.create_table(
        "produtos",
        sa.Column("id_produto", sa.String(32), primary_key=True),
        sa.Column("nome_produto", sa.String(255), nullable=False),
        sa.Column("categoria_produto", sa.String(100), nullable=False),
        sa.Column("peso_produto_gramas", sa.Float(), nullable=True),
        sa.Column("comprimento_centimetros", sa.Float(), nullable=True),
        sa.Column("altura_centimetros", sa.Float(), nullable=True),
        sa.Column("largura_centimetros", sa.Float(), nullable=True),
    )

    op.create_table(
        "vendedores",
        sa.Column("id_vendedor", sa.String(32), primary_key=True),
        sa.Column("nome_vendedor", sa.String(255), nullable=False),
        sa.Column("prefixo_cep", sa.String(10), nullable=False),
        sa.Column("cidade", sa.String(100), nullable=False),
        sa.Column("estado", sa.String(2), nullable=False),
    )

    op.create_table(
        "pedidos",
        sa.Column("id_pedido", sa.String(32), primary_key=True),
        sa.Column("id_consumidor", sa.String(32), sa.ForeignKey("consumidores.id_consumidor"), nullable=False),
        sa.Column("status", sa.String(50), nullable=False),
        sa.Column("pedido_compra_timestamp", sa.DateTime(), nullable=True),
        sa.Column("pedido_entregue_timestamp", sa.DateTime(), nullable=True),
        sa.Column("data_estimada_entrega", sa.Date(), nullable=True),
        sa.Column("tempo_entrega_dias", sa.Float(), nullable=True),
        sa.Column("tempo_entrega_estimado_dias", sa.Float(), nullable=True),
        sa.Column("diferenca_entrega_dias", sa.Float(), nullable=True),
        sa.Column("entrega_no_prazo", sa.String(10), nullable=True),
    )

    op.create_table(
        "itens_pedidos",
        sa.Column("id_pedido", sa.String(32), sa.ForeignKey("pedidos.id_pedido"), nullable=False),
        sa.Column("id_item", sa.Integer(), nullable=False),
        sa.Column("id_produto", sa.String(32), sa.ForeignKey("produtos.id_produto"), nullable=False),
        sa.Column("id_vendedor", sa.String(32), sa.ForeignKey("vendedores.id_vendedor"), nullable=False),
        sa.Column("preco_BRL", sa.Float(), nullable=False),
        sa.Column("preco_frete", sa.Float(), nullable=False),
        sa.PrimaryKeyConstraint("id_pedido", "id_item"),
    )

    op.create_table(
        "avaliacoes_pedidos",
        sa.Column("id_avaliacao", sa.String(32), primary_key=True),
        sa.Column("id_pedido", sa.String(32), sa.ForeignKey("pedidos.id_pedido"), nullable=False),
        sa.Column("avaliacao", sa.Integer(), nullable=False),
        sa.Column("titulo_comentario", sa.String(255), nullable=True),
        sa.Column("comentario", sa.String(1000), nullable=True),
        sa.Column("data_comentario", sa.DateTime(), nullable=True),
        sa.Column("data_resposta", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    """
    Remove as tabelas criadas nesta migracao inicial.
    O drop segue a ordem inversa das dependencias.
    """
    op.drop_table("avaliacoes_pedidos")
    op.drop_table("itens_pedidos")
    op.drop_table("pedidos")
    op.drop_table("vendedores")
    op.drop_table("produtos")
    op.drop_table("consumidores")
