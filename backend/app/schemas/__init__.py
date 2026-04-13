"""Reexporta schemas Pydantic usados nas rotas da API."""

from app.schemas.produto import (
    ItemAvaliacao,
    ProdutoAtualizacao,
    ProdutoCriacao,
    ProdutoItemLista,
    ProdutoRespostaDetalhe,
    ProdutoRespostaLista,
    ItemHistoricoVenda,
)

__all__ = [
    "ItemAvaliacao",
    "ProdutoAtualizacao",
    "ProdutoCriacao",
    "ProdutoItemLista",
    "ProdutoRespostaDetalhe",
    "ProdutoRespostaLista",
    "ItemHistoricoVenda",
]
