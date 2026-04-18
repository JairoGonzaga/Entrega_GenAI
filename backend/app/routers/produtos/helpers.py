"""Utilitários de validação, transformação e rounding de dados."""

from fastapi import HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.produto import Product
from app.schemas.produto import ProductListItem

ID_PATTERN = "^[0-9a-f]{32}$"


def round_2(value: float | None) -> float | None:
    """Arredonda valores numéricos para 2 casas decimais. Preserva None."""
    return round(value, 2) if value is not None else None


def normalized_name(column):
    """Normaliza nome removendo aspas e espaços duplicados para agrupamento."""
    return func.trim(func.replace(func.replace(column, '"', ""), "  ", " "))


def get_product_or_404(product_id: str, db: Session) -> Product:
    """Busca produto ou lança 404 se não existir."""
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Produto nao encontrado")
    return product


def product_to_list_item(product: Product) -> ProductListItem:
    """Converte modelo em item resumido para listagem."""
    return ProductListItem(
        id_produto=product.product_id,
        nome_produto=product.product_name,
        categoria_produto=product.product_category,
        descricao_produto=None,
        preco_base=None,
        media_avaliacoes=None,
        total_vendas=0,
    )


def payload_to_model_fields(data: dict[str, object]) -> dict[str, object]:
    """Mapeia campos do payload (PT) para atributos do model (EN)."""
    field_map = {
        "nome_produto": "product_name",
        "categoria_produto": "product_category",
        "peso_produto_gramas": "product_weight_grams",
        "comprimento_centimetros": "length_cm",
        "altura_centimetros": "height_cm",
        "largura_centimetros": "width_cm",
    }
    return {field_map[key]: value for key, value in data.items() if key in field_map}
