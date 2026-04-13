"""Schemas Pydantic para entradas e respostas de produtos."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class ProdutoBase(BaseModel):
    nome_produto: str = Field(min_length=1, max_length=255)
    categoria_produto: str = Field(min_length=1, max_length=100)
    descricao_produto: Optional[str] = Field(default=None, max_length=1000)
    preco_base: Optional[float] = Field(default=None, ge=0)
    peso_produto_gramas: Optional[float] = Field(default=None, ge=0)
    comprimento_centimetros: Optional[float] = Field(default=None, ge=0)
    altura_centimetros: Optional[float] = Field(default=None, ge=0)
    largura_centimetros: Optional[float] = Field(default=None, ge=0)


class ProdutoCriacao(ProdutoBase):
    pass


class ProdutoAtualizacao(BaseModel):
    nome_produto: Optional[str] = Field(default=None, min_length=1, max_length=255)
    categoria_produto: Optional[str] = Field(default=None, min_length=1, max_length=100)
    descricao_produto: Optional[str] = Field(default=None, max_length=1000)
    preco_base: Optional[float] = Field(default=None, ge=0)
    peso_produto_gramas: Optional[float] = Field(default=None, ge=0)
    comprimento_centimetros: Optional[float] = Field(default=None, ge=0)
    altura_centimetros: Optional[float] = Field(default=None, ge=0)
    largura_centimetros: Optional[float] = Field(default=None, ge=0)


class ProdutoItemLista(BaseModel):
    id_produto: str
    nome_produto: str
    categoria_produto: str
    descricao_produto: Optional[str]
    preco_base: Optional[float]
    media_avaliacoes: Optional[float]
    total_vendas: int
    quantidade_registros: int = 1


class ProdutoRespostaLista(BaseModel):
    total: int
    itens: list[ProdutoItemLista]


class ItemHistoricoVenda(BaseModel):
    id_pedido: str
    data_pedido: Optional[datetime]
    quantidade_itens: int
    valor_total: float
    status: str


class ItemAvaliacao(BaseModel):
    id_avaliacao: str
    nota: int
    titulo: Optional[str]
    comentario: Optional[str]
    data_comentario: Optional[datetime]


class ProdutoRespostaDetalhe(BaseModel):
    id_produto: str
    nome_produto: str
    categoria_produto: str
    descricao_produto: Optional[str]
    preco_base: Optional[float]
    medidas: dict[str, Optional[float]]
    media_avaliacoes: Optional[float]
    total_vendas: int
    vendas_historico: list[ItemHistoricoVenda]
    avaliacoes: list[ItemAvaliacao]
