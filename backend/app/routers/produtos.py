"""Endpoints de produtos: filtros, detalhes, categorias e CRUD."""

from uuid import uuid4
import csv
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.database import obter_db
from app.models.avaliacao_pedido import AvaliacaoPedido
from app.models.item_pedido import ItemPedido
from app.models.pedido import Pedido
from app.models.produto import Produto
from app.schemas.produto import (
    ItemAvaliacao,
    ItemHistoricoVenda,
    ProdutoAtualizacao,
    ProdutoCriacao,
    ProdutoItemLista,
    ProdutoRespostaDetalhe,
    ProdutoRespostaLista,
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])

_PADRAO_ID = "^[0-9a-f]{32}$"


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _arredondar_2(value: float | None) -> float | None:
    """
    Arredonda valores numericos para 2 casas decimais.
    Preserva None quando nao ha valor calculado.
    """
    return round(value, 2) if value is not None else None


def _nome_normalizado(coluna):
    """
    Normaliza o nome do produto removendo aspas e espacos duplicados.
    Ajuda a agrupar produtos semelhantes com grafias inconsistentes.
    """
    return func.trim(func.replace(func.replace(coluna, '"', ""), "  ", " "))


def _obter_produto_ou_404(id_produto: str, db: Session) -> Produto:
    """
    Busca um produto pelo id, garantindo resposta 404 se nao existir.
    Evita repeticao de logica de validacao nas rotas.
    """
    produto = db.get(Produto, id_produto)
    if not produto:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    return produto


def _produto_para_item_lista(produto: Produto) -> ProdutoItemLista:
    """
    Converte um Produto em um item resumido do catalogo.
    Mantem valores essenciais para listagens e respostas de CRUD.
    """
    return ProdutoItemLista(
        id_produto=produto.id_produto,
        nome_produto=produto.nome_produto,
        categoria_produto=produto.categoria_produto,
        descricao_produto=produto.descricao_produto,
        preco_base=produto.preco_base,
        media_avaliacoes=None,
        total_vendas=0,
    )


# ---------------------------------------------------------------------------
# Subqueries / CTEs
# ---------------------------------------------------------------------------


def _agrupar_produtos_base():
    """
    Monta um CTE com produtos agrupados por nome e categoria.
    Calcula medias e contagens para suportar listagens agregadas.
    """
    nome_normalizado = _nome_normalizado(Produto.nome_produto)
    return (
        select(
            func.min(Produto.id_produto).label("id_produto"),
            nome_normalizado.label("nome_produto"),
            Produto.categoria_produto.label("categoria_produto"),
            func.max(Produto.descricao_produto).label("descricao_produto"),
            func.avg(Produto.preco_base).label("preco_base"),
            func.avg(Produto.peso_produto_gramas).label("peso_produto_gramas"),
            func.avg(Produto.comprimento_centimetros).label("comprimento_centimetros"),
            func.avg(Produto.altura_centimetros).label("altura_centimetros"),
            func.avg(Produto.largura_centimetros).label("largura_centimetros"),
            func.count(Produto.id_produto).label("quantidade_registros"),
        )
        .select_from(Produto)
        .group_by(nome_normalizado, Produto.categoria_produto)
        .cte("produtos_agrupados")
    )


def _subquery_media_avaliacao_agrupada():
    """
    Calcula a media de avaliacoes por nome normalizado e categoria.
    Usa joins entre itens, pedidos e avaliacoes.
    """
    nome_normalizado = _nome_normalizado(Produto.nome_produto)
    return (
        select(
            nome_normalizado.label("nome_produto"),
            Produto.categoria_produto.label("categoria_produto"),
            func.avg(AvaliacaoPedido.avaliacao).label("media_avaliacoes"),
        )
        .select_from(ItemPedido)
        .join(Produto, Produto.id_produto == ItemPedido.id_produto)
        .join(Pedido, Pedido.id_pedido == ItemPedido.id_pedido)
        .join(AvaliacaoPedido, AvaliacaoPedido.id_pedido == Pedido.id_pedido)
        .group_by(nome_normalizado, Produto.categoria_produto)
        .subquery()
    )


def _subquery_total_vendas_agrupadas():
    """
    Conta a quantidade de vendas por nome normalizado e categoria.
    A contagem considera itens de pedido registrados.
    """
    nome_normalizado = _nome_normalizado(Produto.nome_produto)
    return (
        select(
            nome_normalizado.label("nome_produto"),
            Produto.categoria_produto.label("categoria_produto"),
            func.count(ItemPedido.id_item).label("total_vendas"),
        )
        .select_from(ItemPedido)
        .join(Produto, Produto.id_produto == ItemPedido.id_produto)
        .group_by(nome_normalizado, Produto.categoria_produto)
        .subquery()
    )


def _produto_grupo_por_id(id_produto: str, db: Session):
    """
    Resolve nome e categoria normalizados a partir de um id.
    Permite reutilizar os agrupamentos para detalhes do produto.
    """
    nome_normalizado = _nome_normalizado(Produto.nome_produto)
    return db.execute(
        select(nome_normalizado.label("nome_produto"), Produto.categoria_produto)
        .where(Produto.id_produto == id_produto)
    ).first()


def _aplicar_filtros_produto(consulta, colunas, busca, categoria, preco_min, preco_max):
    """
    Aplica filtros de busca textual, categorias e faixa de preco.
    Reaproveitado em consultas de listagem e contagem.
    """
    if busca:
        termo = f"%{busca.strip()}%"
        consulta = consulta.where(
            or_(
                colunas.nome_produto.ilike(termo),
                colunas.categoria_produto.ilike(termo),
                colunas.descricao_produto.ilike(termo),
            )
        )

    if categoria:
        categorias_normalizadas = [v.strip() for v in categoria if v and v.strip()]
        if categorias_normalizadas:
            consulta = consulta.where(colunas.categoria_produto.in_(categorias_normalizadas))

    if preco_min is not None:
        consulta = consulta.where(colunas.preco_base >= preco_min)

    if preco_max is not None:
        consulta = consulta.where(colunas.preco_base <= preco_max)

    return consulta


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("", response_model=ProdutoRespostaLista)
def listar_produtos(
    busca: str | None = Query(default=None),
    categoria: list[str] | None = Query(default=None),
    preco_min: float | None = Query(default=None, ge=0),
    preco_max: float | None = Query(default=None, ge=0),
    nota_min: float | None = Query(default=None, ge=0, le=5),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(obter_db),
):
    """
    Lista produtos com paginacao, filtros e metricas agregadas.
    Combina CTE e subqueries para media de avaliacao e vendas.
    """
    produtos_cte = _agrupar_produtos_base()
    media_subq = _subquery_media_avaliacao_agrupada()
    vendas_subq = _subquery_total_vendas_agrupadas()

    filtros = dict(busca=busca, categoria=categoria, preco_min=preco_min, preco_max=preco_max)

    consulta_base = (
        select(
            produtos_cte.c.id_produto,
            produtos_cte.c.nome_produto,
            produtos_cte.c.categoria_produto,
            produtos_cte.c.descricao_produto,
            produtos_cte.c.preco_base,
            media_subq.c.media_avaliacoes,
            func.coalesce(vendas_subq.c.total_vendas, 0).label("total_vendas"),
            produtos_cte.c.quantidade_registros,
        )
        .select_from(produtos_cte)
        .outerjoin(
            media_subq,
            (media_subq.c.nome_produto == produtos_cte.c.nome_produto)
            & (media_subq.c.categoria_produto == produtos_cte.c.categoria_produto),
        )
        .outerjoin(
            vendas_subq,
            (vendas_subq.c.nome_produto == produtos_cte.c.nome_produto)
            & (vendas_subq.c.categoria_produto == produtos_cte.c.categoria_produto),
        )
    )

    consulta_base = _aplicar_filtros_produto(consulta_base, produtos_cte.c, **filtros)

    if nota_min is not None:
        consulta_base = consulta_base.where(media_subq.c.media_avaliacoes >= nota_min)
        total = db.scalar(select(func.count()).select_from(consulta_base.subquery()))
    else:
        total = db.scalar(
            _aplicar_filtros_produto(
                select(func.count()).select_from(produtos_cte), produtos_cte.c, **filtros
            )
        )

    linhas = db.execute(
        consulta_base
        .order_by(produtos_cte.c.nome_produto, produtos_cte.c.categoria_produto)
        .offset(skip)
        .limit(limit)
    ).all()

    itens = [
        ProdutoItemLista(
            id_produto=linha.id_produto,
            nome_produto=linha.nome_produto,
            categoria_produto=linha.categoria_produto,
            descricao_produto=linha.descricao_produto,
            preco_base=linha.preco_base,
            media_avaliacoes=_arredondar_2(float(linha.media_avaliacoes)) if linha.media_avaliacoes is not None else None,
            total_vendas=linha.total_vendas,
            quantidade_registros=linha.quantidade_registros,
        )
        for linha in linhas
    ]

    return ProdutoRespostaLista(total=total or 0, itens=itens)


@router.get("/categorias")
def listar_categorias(db: Session = Depends(obter_db)):
    """
    Retorna categorias unicas ordenadas do catalogo.
    Filtra valores nulos e strings vazias.
    """
    categoria = func.trim(Produto.categoria_produto)
    rows = db.execute(
        select(categoria.label("categoria_produto"))
        .distinct()
        .where(categoria.is_not(None))
        .where(categoria != "")
        .order_by(categoria)
    ).all()
    return [row.categoria_produto for row in rows]


def _diretorio_dados_repo() -> Path:
    """
    Resolve o diretorio base do repositorio para arquivos auxiliares.
    Usado para localizar CSVs de imagens por categoria.
    """
    return Path(__file__).resolve().parents[3] / "data_ingestao"


@lru_cache(maxsize=1)
def _categoria_imagens() -> dict[str, str]:
    """
    Carrega o mapeamento categoria -> imagem a partir do CSV.
    Aplica aliases para categorias com nomes alternativos.
    """
    caminho_csv = _diretorio_dados_repo() / "dim_categoria_imagens.csv"
    if not caminho_csv.exists():
        return {}

    with caminho_csv.open("r", encoding="utf-8-sig", newline="") as handle:
        leitor = csv.DictReader(handle)
        mapeamento: dict[str, str] = {}
        for linha in leitor:
            categoria = (linha.get("Categoria") or linha.get("categoria") or "").strip()
            link = (linha.get("Link") or linha.get("link") or "").strip()
            if categoria and link:
                mapeamento[categoria] = link

        apelidos = {
            "casa_conforto_2": "casa_conforto",
            "construcao_ferramentas_construcao": "construcao_ferramentas",
            "construcao_ferramentas_ferramentas": "construcao_ferramentas",
            "construcao_ferramentas_iluminacao": "construcao_iluminacao",
            "construcao_ferramentas_jardim": "ferramentas_jardim",
            "construcao_ferramentas_seguranca": "construcao_seguranca",
            "moveis_cozinha_area_de_servico_jantar_e_jardim": "moveis_cozinha_jantar_jardim",
            "portateis_cozinha_e_preparadores_de_alimentos": "portateis_cozinha",
        }

        for apelido, destino in apelidos.items():
            if destino in mapeamento and apelido not in mapeamento:
                mapeamento[apelido] = mapeamento[destino]

        return mapeamento


@router.get("/categorias-imagens")
def listar_categorias_imagens():
    """
    Retorna o dicionario de imagens usadas no frontend.
    Os dados sao cacheados para evitar leituras repetidas.
    A logica de imagens fica separada para permitir cache via lru_cache.
    Isso foi feito por boas praticas do fastapi mesmo que nao seja necessario para o volume atual de dados.
    """
    return _categoria_imagens()


@router.get("/{id_produto}", response_model=ProdutoRespostaDetalhe)
def detalhar_produto(
    id_produto: str = PathParam(..., pattern=_PADRAO_ID),
    db: Session = Depends(obter_db),
):
    """
    Retorna detalhes de um produto agregado por nome e categoria.
    Inclui historico de vendas, avaliacoes e medidas medias.
    """
    produto = _obter_produto_ou_404(id_produto, db)

    grupo = _produto_grupo_por_id(id_produto, db)
    if not grupo:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    nome_grupo, categoria_grupo = grupo.nome_produto, grupo.categoria_produto
    filtro_grupo = (
        _nome_normalizado(Produto.nome_produto) == nome_grupo,
        Produto.categoria_produto == categoria_grupo,
    )

    linhas_historico = db.execute(
        select(
            Pedido.id_pedido,
            Pedido.pedido_compra_timestamp,
            Pedido.status,
            func.count(ItemPedido.id_item).label("quantidade_itens"),
            func.sum(ItemPedido.preco_BRL + ItemPedido.preco_frete).label("valor_total"),
        )
        .select_from(ItemPedido)
        .join(Produto, Produto.id_produto == ItemPedido.id_produto)
        .join(Pedido, Pedido.id_pedido == ItemPedido.id_pedido)
        .where(*filtro_grupo)
        .group_by(Pedido.id_pedido, Pedido.pedido_compra_timestamp, Pedido.status)
        .order_by(Pedido.pedido_compra_timestamp.desc())
    ).all()

    linhas_avaliacoes = db.execute(
        select(
            AvaliacaoPedido.id_avaliacao,
            AvaliacaoPedido.avaliacao,
            AvaliacaoPedido.titulo_comentario,
            AvaliacaoPedido.comentario,
            AvaliacaoPedido.data_comentario,
        )
        .select_from(ItemPedido)
        .join(Produto, Produto.id_produto == ItemPedido.id_produto)
        .join(Pedido, Pedido.id_pedido == ItemPedido.id_pedido)
        .join(AvaliacaoPedido, AvaliacaoPedido.id_pedido == Pedido.id_pedido)
        .where(*filtro_grupo)
        .order_by(AvaliacaoPedido.data_comentario.desc())
    ).all()

    linhas_medidas = db.execute(
        select(
            func.avg(Produto.peso_produto_gramas).label("peso_produto_gramas"),
            func.avg(Produto.comprimento_centimetros).label("comprimento_centimetros"),
            func.avg(Produto.altura_centimetros).label("altura_centimetros"),
            func.avg(Produto.largura_centimetros).label("largura_centimetros"),
            func.avg(Produto.preco_base).label("preco_base"),
            func.max(Produto.descricao_produto).label("descricao_produto"),
        )
        .select_from(Produto)
        .where(*filtro_grupo)
    ).first()

    def _medida(campo: str):
        """
        Calcula media de uma medida quando houver dados agregados.
        Usa o valor individual do produto como fallback.
        """
        valor = getattr(linhas_medidas, campo, None) if linhas_medidas else None
        valor_padrao = getattr(produto, campo, None)
        return _arredondar_2(float(valor) if valor is not None else valor_padrao)

    media_avaliacoes = (
        sum(linha.avaliacao for linha in linhas_avaliacoes) / len(linhas_avaliacoes)
        if linhas_avaliacoes else None
    )

    return ProdutoRespostaDetalhe(
        id_produto=produto.id_produto,
        nome_produto=nome_grupo,
        categoria_produto=categoria_grupo,
        descricao_produto=linhas_medidas.descricao_produto if linhas_medidas else produto.descricao_produto,
        preco_base=_medida("preco_base"),
        medidas={
            "peso_produto_gramas": _medida("peso_produto_gramas"),
            "comprimento_centimetros": _medida("comprimento_centimetros"),
            "altura_centimetros": _medida("altura_centimetros"),
            "largura_centimetros": _medida("largura_centimetros"),
        },
        media_avaliacoes=_arredondar_2(media_avaliacoes),
        total_vendas=len(linhas_historico),
        vendas_historico=[
            ItemHistoricoVenda(
                id_pedido=linha.id_pedido,
                data_pedido=linha.pedido_compra_timestamp,
                quantidade_itens=linha.quantidade_itens,
                valor_total=float(linha.valor_total or 0),
                status=linha.status,
            )
            for linha in linhas_historico
        ],
        avaliacoes=[
            ItemAvaliacao(
                id_avaliacao=linha.id_avaliacao,
                nota=linha.avaliacao,
                titulo=linha.titulo_comentario,
                comentario=linha.comentario,
                data_comentario=linha.data_comentario,
            )
            for linha in linhas_avaliacoes
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProdutoItemLista)
def criar_produto(payload: ProdutoCriacao, db: Session = Depends(obter_db)):
    """
    Cria um novo produto a partir do payload validado.
    Retorna o item resumido para atualizar o catalogo.
    """
    produto = Produto(id_produto=uuid4().hex, **payload.model_dump())
    db.add(produto)
    db.commit()
    db.refresh(produto)
    return _produto_para_item_lista(produto)


@router.put("/{id_produto}", response_model=ProdutoItemLista)
def atualizar_produto(
    id_produto: str = PathParam(..., pattern=_PADRAO_ID),
    payload: ProdutoAtualizacao = ...,
    db: Session = Depends(obter_db),
):
    """
    Atualiza campos permitidos de um produto existente.
    Rejeita requisicoes sem dados para atualizar.
    """
    produto = _obter_produto_ou_404(id_produto, db)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    for field, value in update_data.items():
        setattr(produto, field, value)

    db.add(produto)
    db.commit()
    db.refresh(produto)
    return _produto_para_item_lista(produto)


@router.delete("/{id_produto}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(
    id_produto: str = PathParam(..., pattern=_PADRAO_ID),
    db: Session = Depends(obter_db),
):
    """
    Remove um produto se nao houver historico de vendas.
    Bloqueia a exclusao quando ha itens associados.
    """
    produto = _obter_produto_ou_404(id_produto, db)

    tem_itens = db.scalar(
        select(func.count())
        .select_from(ItemPedido)
        .where(ItemPedido.id_produto == id_produto)
    )

    if tem_itens:
        raise HTTPException(
            status_code=409,
            detail="Produto possui historico de vendas e nao pode ser removido",
        )

    db.delete(produto)
    db.commit()