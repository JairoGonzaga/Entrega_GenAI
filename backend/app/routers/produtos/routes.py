"""Endpoints para produtos: listagem, detalhes, categorias e CRUD."""

from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.avaliacao_pedido import OrderReview
from app.models.item_pedido import OrderItem
from app.models.pedido import Order
from app.models.produto import Product
from app.schemas.produto import (
    ReviewItem,
    OrderHistoryItem,
    ProductUpdate,
    ProductCreate,
    ProductListItem,
    ProductDetailResponse,
    ProductListResponse,
)
from .helpers import (
    ID_PATTERN,
    get_product_or_404,
    normalized_name,
    payload_to_model_fields,
    product_to_list_item,
    round_2,
)
from .queries import (
    apply_product_filters,
    group_products_base,
    product_group_by_id,
    subquery_grouped_review_average,
    subquery_grouped_total_sales,
)

router = APIRouter(prefix="/produtos", tags=["Produtos"])


@router.get("", response_model=ProductListResponse)
def list_products(
    busca: str | None = Query(default=None),
    categoria: list[str] | None = Query(default=None),
    preco_min: float | None = Query(default=None, ge=0),
    preco_max: float | None = Query(default=None, ge=0),
    nota_min: float | None = Query(default=None, ge=0, le=5),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Lista produtos com paginação, filtros e métricas agregadas."""
    products_cte = group_products_base()
    review_avg_subq = subquery_grouped_review_average()
    sales_subq = subquery_grouped_total_sales()

    filters = dict(search=busca, category=categoria, min_price=preco_min, max_price=preco_max)

    base_query = (
        select(
            products_cte.c.id_produto,
            products_cte.c.nome_produto,
            products_cte.c.categoria_produto,
            products_cte.c.descricao_produto,
            products_cte.c.preco_base,
            review_avg_subq.c.media_avaliacoes,
            func.coalesce(sales_subq.c.total_vendas, 0).label("total_vendas"),
            products_cte.c.quantidade_registros,
        )
        .select_from(products_cte)
        .outerjoin(
            review_avg_subq,
            (review_avg_subq.c.nome_produto == products_cte.c.nome_produto)
            & (review_avg_subq.c.categoria_produto == products_cte.c.categoria_produto),
        )
        .outerjoin(
            sales_subq,
            (sales_subq.c.nome_produto == products_cte.c.nome_produto)
            & (sales_subq.c.categoria_produto == products_cte.c.categoria_produto),
        )
    )

    base_query = apply_product_filters(base_query, products_cte.c, **filters)

    if nota_min is not None:
        base_query = base_query.where(review_avg_subq.c.media_avaliacoes >= nota_min)
        total = db.scalar(select(func.count()).select_from(base_query.subquery()))
    else:
        total = db.scalar(
            apply_product_filters(
                select(func.count()).select_from(products_cte), products_cte.c, **filters
            )
        )

    rows = db.execute(
        base_query
        .order_by(products_cte.c.nome_produto, products_cte.c.categoria_produto)
        .offset(skip)
        .limit(limit)
    ).all()

    items = [
        ProductListItem(
            id_produto=row.id_produto,
            nome_produto=row.nome_produto,
            categoria_produto=row.categoria_produto,
            descricao_produto=row.descricao_produto,
            preco_base=row.preco_base,
            media_avaliacoes=round_2(float(row.media_avaliacoes)) if row.media_avaliacoes is not None else None,
            total_vendas=row.total_vendas,
            quantidade_registros=row.quantidade_registros,
        )
        for row in rows
    ]

    return ProductListResponse(total=total or 0, itens=items)


@router.get("/categorias")
def list_categories(db: Session = Depends(get_db)):
    """Retorna categorias únicas ordenadas do catálogo."""
    category_col = func.trim(Product.product_category)
    rows = db.execute(
        select(category_col.label("categoria_produto"))
        .distinct()
        .where(category_col.is_not(None))
        .where(category_col != "")
        .order_by(category_col)
    ).all()
    return [row.categoria_produto for row in rows]


@router.get("/{id_produto}", response_model=ProductDetailResponse)
def get_product_detail(
    id_produto: str = PathParam(..., pattern=ID_PATTERN),
    db: Session = Depends(get_db),
):
    """Retorna detalhes agregados de um produto com histórico e avaliações."""
    product = get_product_or_404(product_id=id_produto, db=db)

    group = product_group_by_id(product_id=id_produto, db=db)
    if not group:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")

    group_name, group_category = group.nome_produto, group.categoria_produto
    group_filter = (
        normalized_name(Product.product_name) == group_name,
        Product.product_category == group_category,
    )

    history_rows = db.execute(
        select(
            Order.order_id.label("id_pedido"),
            Order.purchase_timestamp.label("pedido_compra_timestamp"),
            Order.status,
            func.count(OrderItem.item_id).label("quantidade_itens"),
            func.sum(OrderItem.price_brl + OrderItem.freight_price).label("valor_total"),
        )
        .select_from(OrderItem)
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .where(*group_filter)
        .group_by(Order.order_id, Order.purchase_timestamp, Order.status)
        .order_by(Order.purchase_timestamp.desc())
    ).all()

    review_rows = db.execute(
        select(
            OrderReview.review_id.label("id_avaliacao"),
            OrderReview.rating.label("avaliacao"),
            OrderReview.comment_title.label("titulo_comentario"),
            OrderReview.comment.label("comentario"),
            OrderReview.comment_date.label("data_comentario"),
        )
        .select_from(OrderItem)
        .join(Product, Product.product_id == OrderItem.product_id)
        .join(Order, Order.order_id == OrderItem.order_id)
        .join(OrderReview, OrderReview.order_id == Order.order_id)
        .where(*group_filter)
        .order_by(OrderReview.comment_date.desc())
    ).all()

    measure_rows = db.execute(
        select(
            func.avg(Product.product_weight_grams).label("peso_produto_gramas"),
            func.avg(Product.length_cm).label("comprimento_centimetros"),
            func.avg(Product.height_cm).label("altura_centimetros"),
            func.avg(Product.width_cm).label("largura_centimetros"),
            func.avg(OrderItem.price_brl).label("preco_base"),
        )
        .select_from(Product)
        .outerjoin(OrderItem, OrderItem.product_id == Product.product_id)
        .where(*group_filter)
    ).first()

    def measure(field: str, fallback_field: str):
        """Calcula média com fallback ao valor individual."""
        value = getattr(measure_rows, field, None) if measure_rows else None
        fallback_value = getattr(product, fallback_field, None)
        return round_2(float(value) if value is not None else fallback_value)

    review_average = (
        sum(row.avaliacao for row in review_rows) / len(review_rows)
        if review_rows else None
    )

    return ProductDetailResponse(
        id_produto=product.product_id,
        nome_produto=group_name,
        categoria_produto=group_category,
        descricao_produto=None,
        preco_base=round_2(float(measure_rows.preco_base)) if measure_rows and measure_rows.preco_base is not None else None,
        medidas={
            "peso_produto_gramas": measure("peso_produto_gramas", "product_weight_grams"),
            "comprimento_centimetros": measure("comprimento_centimetros", "length_cm"),
            "altura_centimetros": measure("altura_centimetros", "height_cm"),
            "largura_centimetros": measure("largura_centimetros", "width_cm"),
        },
        media_avaliacoes=round_2(review_average),
        total_vendas=len(history_rows),
        vendas_historico=[
            OrderHistoryItem(
                id_pedido=row.id_pedido,
                data_pedido=row.pedido_compra_timestamp,
                quantidade_itens=row.quantidade_itens,
                valor_total=float(row.valor_total or 0),
                status=row.status,
            )
            for row in history_rows
        ],
        avaliacoes=[
            ReviewItem(
                id_avaliacao=row.id_avaliacao,
                nota=row.avaliacao,
                titulo=row.titulo_comentario,
                comentario=row.comentario,
                data_comentario=row.data_comentario,
            )
            for row in review_rows
        ],
    )


@router.post("", status_code=status.HTTP_201_CREATED, response_model=ProductListItem)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    """Cria um novo produto e retorna item resumido."""
    product_data = payload_to_model_fields(payload.model_dump())
    product = Product(product_id=uuid4().hex, **product_data)
    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_list_item(product)


@router.put("/{id_produto}", response_model=ProductListItem)
def update_product(
    id_produto: str = PathParam(..., pattern=ID_PATTERN),
    payload: ProductUpdate = ...,
    db: Session = Depends(get_db),
):
    """Atualiza campos permitidos de um produto existente."""
    product = get_product_or_404(product_id=id_produto, db=db)

    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="Nenhum campo para atualizar")

    model_update_data = payload_to_model_fields(update_data)
    if not model_update_data:
        raise HTTPException(status_code=400, detail="Campos enviados nao existem no schema atual do banco")

    for field, value in model_update_data.items():
        setattr(product, field, value)

    db.add(product)
    db.commit()
    db.refresh(product)
    return product_to_list_item(product)


@router.delete("/{id_produto}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    id_produto: str = PathParam(..., pattern=ID_PATTERN),
    db: Session = Depends(get_db),
):
    """Remove um produto se não houver histórico de vendas."""
    product = get_product_or_404(product_id=id_produto, db=db)

    has_items = db.scalar(
        select(func.count())
        .select_from(OrderItem)
        .where(OrderItem.product_id == id_produto)
    )

    if has_items:
        raise HTTPException(
            status_code=409,
            detail="Produto possui historico de vendas e nao pode ser removido",
        )

    db.delete(product)
    db.commit()
