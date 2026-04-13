"""Faz ingestao de CSVs em lote para popular o banco de dados."""

from __future__ import annotations

import csv
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

from sqlalchemy import func, insert, select
from sqlalchemy.orm import Session

from app.database import SessaoLocal
from app.models.avaliacao_pedido import AvaliacaoPedido
from app.models.consumidor import Consumidor
from app.models.item_pedido import ItemPedido
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.models.vendedor import Vendedor

TAMANHO_LOTE = 5000


def _parsear_float(value: str | None) -> float | None:
    """
    Converte string para float respeitando valores vazios.
    Retorna None quando a entrada e nula ou so tem espacos.
    """
    if value is None:
        return None

    normalizado = value.strip()
    if not normalizado:
        return None

    return float(normalizado)


def _parsear_int(value: str | None) -> int | None:
    """
    Converte string para int respeitando valores vazios.
    Retorna None quando a entrada e nula ou so tem espacos.
    """
    if value is None:
        return None

    normalizado = value.strip()
    if not normalizado:
        return None

    return int(normalizado)


def _parsear_data_hora(value: str | None) -> datetime | None:
    """
    Converte string ISO para datetime quando possivel.
    Retorna None para valores vazios ou ausentes.
    """
    if value is None:
        return None

    normalizado = value.strip()
    if not normalizado:
        return None

    return datetime.fromisoformat(normalizado)


def _parsear_data(value: str | None) -> date | None:
    """
    Converte string ISO para date quando possivel.
    Retorna None para valores vazios ou ausentes.
    """
    if value is None:
        return None

    normalizado = value.strip()
    if not normalizado:
        return None

    return date.fromisoformat(normalizado)


def _linhas_csv(file_path: Path) -> Iterable[dict[str, str]]:
    """
    Itera um CSV e entrega cada linha como dicionario.
    Usa encoding utf-8-sig para lidar com BOM.
    """
    with file_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            yield row


def _inserir_em_lotes(
    db: Session,
    model: type,
    linhas: Iterable[dict],
    tamanho_lote: int = TAMANHO_LOTE,
) -> int:
    """
    Insere registros em lotes para reduzir custo de transacao.
    Usa OR IGNORE para evitar falhas quando ja existem dados.
    """
    lote: list[dict] = []
    inseridos = 0

    for linha in linhas:
        lote.append(linha)
        if len(lote) >= tamanho_lote:
            db.execute(insert(model).prefix_with("OR IGNORE"), lote)
            inseridos += len(lote)
            lote.clear()

    if lote:
        db.execute(insert(model).prefix_with("OR IGNORE"), lote)
        inseridos += len(lote)

    return inseridos


def _montar_estatisticas_preco(itens_csv: Path) -> dict[str, tuple[float, int]]:
    """
    Calcula estatisticas de preco por id_produto.
    Retorna soma e contagem para derivar preco medio.
    """
    estatisticas: dict[str, tuple[float, int]] = {}

    for row in _linhas_csv(itens_csv):
        id_produto = row["id_produto"].strip()
        preco = _parsear_float(row.get("preco_BRL"))
        if preco is None:
            continue

        total, quantidade = estatisticas.get(id_produto, (0.0, 0))
        estatisticas[id_produto] = (total + preco, quantidade + 1)

    return estatisticas


def _descricao_padrao(categoria: str) -> str:
    """
    Gera uma descricao padrao legivel a partir da categoria.
    Substitui underscores por espacos e normaliza o texto.
    """
    label = categoria.replace("_", " ").strip()
    return f"Item da categoria {label}."


def _diretorio_dados_repo() -> Path:
    """
    Resolve o caminho da pasta raiz de dados de ingestao.
    Assume a estrutura padrao do repositorio do projeto.
    """
    repo_root = Path(__file__).resolve().parents[2]
    return repo_root / "data_ingestao"


def popular_banco_a_partir_csv() -> bool:
    """
    Popula tabelas a partir dos CSVs se ainda estiverem vazias.
    Retorna False quando arquivos faltam ou quando ja ha dados.
    """
    diretorio_dados = _diretorio_dados_repo()
    if not diretorio_dados.exists():
        return False

    produtos_csv = diretorio_dados / "dim_produtos.csv"
    consumidores_csv = diretorio_dados / "dim_consumidores.csv"
    vendedores_csv = diretorio_dados / "dim_vendedores.csv"
    pedidos_csv = diretorio_dados / "fat_pedidos.csv"
    itens_csv = diretorio_dados / "fat_itens_pedidos.csv"
    avaliacoes_csv = diretorio_dados / "fat_avaliacoes_pedidos.csv"

    arquivos_necessarios = [
        produtos_csv,
        consumidores_csv,
        vendedores_csv,
        pedidos_csv,
        itens_csv,
        avaliacoes_csv,
    ]

    if any(not file_path.exists() for file_path in arquivos_necessarios):
        return False

    with SessaoLocal() as db:
        contagem_tabelas = {
            "consumidores": db.scalar(select(func.count()).select_from(Consumidor)) or 0,
            "vendedores": db.scalar(select(func.count()).select_from(Vendedor)) or 0,
            "produtos": db.scalar(select(func.count()).select_from(Produto)) or 0,
            "pedidos": db.scalar(select(func.count()).select_from(Pedido)) or 0,
            "itens": db.scalar(select(func.count()).select_from(ItemPedido)) or 0,
            "avaliacoes": db.scalar(select(func.count()).select_from(AvaliacaoPedido)) or 0,
        }
        if all(contagem > 0 for contagem in contagem_tabelas.values()):
            return False

        estatisticas_preco = _montar_estatisticas_preco(itens_csv)

        _inserir_em_lotes(
            db,
            Consumidor,
            (
                {
                    "id_consumidor": row["id_consumidor"],
                    "prefixo_cep": row["prefixo_cep"],
                    "nome_consumidor": row["nome_consumidor"],
                    "cidade": row["cidade"],
                    "estado": row["estado"],
                }
                for row in _linhas_csv(consumidores_csv)
            ),
        )
        db.commit()

        _inserir_em_lotes(
            db,
            Vendedor,
            (
                {
                    "id_vendedor": row["id_vendedor"],
                    "nome_vendedor": row["nome_vendedor"],
                    "prefixo_cep": row["prefixo_cep"],
                    "cidade": row["cidade"],
                    "estado": row["estado"],
                }
                for row in _linhas_csv(vendedores_csv)
            ),
        )
        db.commit()

        _inserir_em_lotes(
            db,
            Produto,
            (
                {
                    "id_produto": row["id_produto"],
                    "nome_produto": row["nome_produto"],
                    "categoria_produto": row["categoria_produto"],
                    "descricao_produto": _descricao_padrao(row["categoria_produto"]),
                    "preco_base": (
                        round(
                            estatisticas_preco[row["id_produto"]][0]
                            / estatisticas_preco[row["id_produto"]][1],
                            2,
                        )
                        if row["id_produto"] in estatisticas_preco
                        else None
                    ),
                    "peso_produto_gramas": _parsear_float(row.get("peso_produto_gramas")),
                    "comprimento_centimetros": _parsear_float(row.get("comprimento_centimetros")),
                    "altura_centimetros": _parsear_float(row.get("altura_centimetros")),
                    "largura_centimetros": _parsear_float(row.get("largura_centimetros")),
                }
                for row in _linhas_csv(produtos_csv)
            ),
        )
        db.commit()

        _inserir_em_lotes(
            db,
            Pedido,
            (
                {
                    "id_pedido": row["id_pedido"],
                    "id_consumidor": row["id_consumidor"],
                    "status": row["status"],
                    "pedido_compra_timestamp": _parsear_data_hora(row.get("pedido_compra_timestamp")),
                    "pedido_entregue_timestamp": _parsear_data_hora(row.get("pedido_entregue_timestamp")),
                    "data_estimada_entrega": _parsear_data(row.get("data_estimada_entrega")),
                    "tempo_entrega_dias": _parsear_float(row.get("tempo_entrega_dias")),
                    "tempo_entrega_estimado_dias": _parsear_float(row.get("tempo_entrega_estimado_dias")),
                    "diferenca_entrega_dias": _parsear_float(row.get("diferenca_entrega_dias")),
                    "entrega_no_prazo": row["entrega_no_prazo"],
                }
                for row in _linhas_csv(pedidos_csv)
            ),
        )
        db.commit()

        _inserir_em_lotes(
            db,
            ItemPedido,
            (
                {
                    "id_pedido": row["id_pedido"],
                    "id_item": _parsear_int(row.get("id_item")),
                    "id_produto": row["id_produto"],
                    "id_vendedor": row["id_vendedor"],
                    "preco_BRL": _parsear_float(row.get("preco_BRL")),
                    "preco_frete": _parsear_float(row.get("preco_frete")),
                }
                for row in _linhas_csv(itens_csv)
            ),
        )
        db.commit()

        _inserir_em_lotes(
            db,
            AvaliacaoPedido,
            (
                {
                    "id_avaliacao": row["id_avaliacao"],
                    "id_pedido": row["id_pedido"],
                    "avaliacao": _parsear_int(row.get("avaliacao")),
                    "titulo_comentario": row["titulo_comentario"],
                    "comentario": row["comentario"],
                    "data_comentario": _parsear_data_hora(row.get("data_comentario")),
                    "data_resposta": _parsear_data_hora(row.get("data_resposta")),
                }
                for row in _linhas_csv(avaliacoes_csv)
            ),
        )
        db.commit()

    return True
