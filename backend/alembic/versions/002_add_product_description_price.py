"""adiciona descricao e preco base

Revision ID: 002
Revises: 001
Create Date: 2026-04-10
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Adiciona descricao e preco base na tabela de produtos.
    Permite enriquecer o catalogo sem perder dados existentes.
    """
    op.add_column("produtos", sa.Column("descricao_produto", sa.String(length=1000), nullable=True))
    op.add_column("produtos", sa.Column("preco_base", sa.Float(), nullable=True))


def downgrade() -> None:
    """
    Reverte a migracao removendo as colunas adicionadas.
    Mantem a tabela de produtos no formato anterior.
    """
    op.drop_column("produtos", "preco_base")
    op.drop_column("produtos", "descricao_produto")
