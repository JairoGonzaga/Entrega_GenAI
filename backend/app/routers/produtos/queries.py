"""Queries complexas: CTEs, subqueries para listagem e detalhes."""

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.avaliacao_pedido import OrderReview
from app.models.item_pedido import OrderItem
from app.models.pedido import Order
from app.models.produto import Product
from .helpers import normalized_name


def group_products_base():
    """CTE com produtos agrupados por nome e categoria com métricas."""
    normalized_name_col = normalized_name(Product.product_name)
    return (
        select(
            func.min(Product.product_id).label("id_produto"),
            normalized_name_col.label("nome_produto"),
            Product.product_category.label("categoria_produto"),
            func.max(Product.product_description).label("descricao_produto"),
            func.avg(Product.base_price).label("preco_base"),
            func.avg(Product.product_weight_grams).label("peso_produto_gramas"),
            func.avg(Product.length_cm).label("comprimento_centimetros"),
            func.avg(Product.height_cm).label("altura_centimetros"),
            func.avg(Product.width_cm).label("largura_centimetros"),
            func.count(Product.product_id).label("quantidade_registros"),
        )
        .select_from(Product)
        .group_by(normalized_name_col, Product.product_category)
        .cte("produtos_agrupados")
    )


def subquery_grouped_review_average():
    """Calcula média de avaliações por nome e categoria."""
    normalized_name_col = normalized_name(Product.product_name)
    return (
        select(
            normalized_name_col.label("nome_produto"),
            Product.product_category.label("categoria_produto"),
            func.avg(OrderReview.rating).label("media_avaliacoes"),
        )
        .select_from(OrderItem)
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .join(OrderReview, OrderReview.order_id == Order.order_id)
        .group_by(normalized_name_col, Product.product_category)
        .subquery()
    )


def subquery_grouped_total_sales():
    """Conta vendas por nome e categoria."""
    normalized_name_col = normalized_name(Product.product_name)
    return (
        select(
            normalized_name_col.label("nome_produto"),
            Product.product_category.label("categoria_produto"),
            func.count(OrderItem.item_id).label("total_vendas"),
        )
        .select_from(OrderItem)
        .join(Product, Product.product_id == OrderItem.product_id)
        .group_by(normalized_name_col, Product.product_category)
        .subquery()
    )


def product_group_by_id(product_id: str, db: Session):
    """Resolve nome e categoria normalizados a partir do id."""
    normalized_name_col = normalized_name(Product.product_name)
    return db.execute(
        select(
            normalized_name_col.label("nome_produto"),
            Product.product_category.label("categoria_produto"),
        ).where(Product.product_id == product_id)
    ).first()


def apply_product_filters(query, columns, search, category, min_price, max_price):
    """Aplica filtros de busca, categoria e preço à query."""
    if search:
        term = f"%{search.strip()}%"
        query = query.where(
            or_(
                columns.nome_produto.ilike(term),
                columns.categoria_produto.ilike(term),
                columns.descricao_produto.ilike(term),
            )
        )

    if category:
        normalized_categories = [v.strip() for v in category if v and v.strip()]
        if normalized_categories:
            query = query.where(columns.categoria_produto.in_(normalized_categories))

    if min_price is not None:
        query = query.where(columns.preco_base >= min_price)

    if max_price is not None:
        query = query.where(columns.preco_base <= max_price)

    return query
