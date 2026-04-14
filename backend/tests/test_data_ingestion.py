from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import sessionmaker

from app import data_ingestion
from app.database import Base
from app.models.avaliacao_pedido import OrderReview
from app.models.consumidor import Customer
from app.models.item_pedido import OrderItem
from app.models.pedido import Order
from app.models.produto import Product
from app.models.vendedor import Seller


def _write_csv(path: Path, header: list[str], rows: list[list[str]]) -> None:
    lines = [",".join(header)] + [",".join(row) for row in rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_parse_helpers_and_default_description():
    assert data_ingestion._parse_float(None) is None
    assert data_ingestion._parse_float(" ") is None
    assert data_ingestion._parse_float("10.5") == 10.5

    assert data_ingestion._parse_int(None) is None
    assert data_ingestion._parse_int(" ") is None
    assert data_ingestion._parse_int("7") == 7

    assert data_ingestion._parse_datetime(None) is None
    assert data_ingestion._parse_datetime(" ") is None
    assert data_ingestion._parse_datetime("2026-01-10T12:30:00").isoformat() == "2026-01-10T12:30:00"

    assert data_ingestion._parse_date(None) is None
    assert data_ingestion._parse_date(" ") is None
    assert data_ingestion._parse_date("2026-01-15").isoformat() == "2026-01-15"

    assert data_ingestion._default_description("casa_conforto") == "Item da categoria casa conforto."


def test_data_dir_points_to_repo_data_folder():
    data_dir = data_ingestion._data_dir()

    assert data_dir.name == "data_ingestao"
    assert data_dir.parent.exists()
    assert (data_dir.parent / "backend").exists()
    assert (data_dir / "dim_produtos.csv").exists()


def test_build_price_stats_and_insert_in_batches(tmp_path, test_engine):
    order_items_csv = tmp_path / "fat_itens_pedidos.csv"
    _write_csv(
        order_items_csv,
        ["id_pedido", "id_item", "id_produto", "id_vendedor", "preco_BRL", "preco_frete"],
        [
            ["o1", "1", "p1", "s1", "10.0", "1.5"],
            ["o2", "1", "p1", "s1", "14.0", "1.5"],
            ["o3", "1", "p2", "s2", "", "2.0"],
        ],
    )

    stats = data_ingestion._build_price_stats(order_items_csv)
    assert stats["p1"] == (24.0, 2)
    assert "p2" not in stats

    Base.metadata.create_all(bind=test_engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    with SessionLocal() as db:
        inserted = data_ingestion._insert_in_batches(
            db,
            Customer,
            [
                {
                    "customer_id": "a" * 32,
                    "zip_prefix": "00000-000",
                    "customer_name": "A",
                    "cidade": "SP",
                    "estado": "SP",
                },
                {
                    "customer_id": "b" * 32,
                    "zip_prefix": "11111-111",
                    "customer_name": "B",
                    "cidade": "SP",
                    "estado": "SP",
                },
                {
                    "customer_id": "a" * 32,
                    "zip_prefix": "00000-000",
                    "customer_name": "A",
                    "cidade": "SP",
                    "estado": "SP",
                },
            ],
            batch_size=2,
        )
        db.commit()

        assert inserted == 3
        assert db.scalar(select(func.count()).select_from(Customer)) == 2


def test_populate_db_from_csv_returns_false_for_missing_paths(monkeypatch, tmp_path):
    missing_dir = tmp_path / "nao-existe"
    monkeypatch.setattr(data_ingestion, "_data_dir", lambda: missing_dir)

    assert data_ingestion.populate_db_from_csv() is False

    partial_dir = tmp_path / "parcial"
    partial_dir.mkdir()
    _write_csv(partial_dir / "dim_produtos.csv", ["id_produto"], [["p1"]])
    monkeypatch.setattr(data_ingestion, "_data_dir", lambda: partial_dir)

    assert data_ingestion.populate_db_from_csv() is False


def test_populate_db_from_csv_full_flow(monkeypatch, tmp_path, test_engine):
    data_dir = tmp_path / "data_ingestao"
    data_dir.mkdir()

    product_id = "1" * 32
    customer_id = "2" * 32
    seller_id = "3" * 32
    order_id = "4" * 32
    review_id = "5" * 32

    _write_csv(
        data_dir / "dim_produtos.csv",
        [
            "id_produto",
            "nome_produto",
            "categoria_produto",
            "peso_produto_gramas",
            "comprimento_centimetros",
            "altura_centimetros",
            "largura_centimetros",
        ],
        [[product_id, "Produto Teste", "casa_conforto", "100", "10", "5", "3"]],
    )

    _write_csv(
        data_dir / "dim_consumidores.csv",
        ["id_consumidor", "prefixo_cep", "nome_consumidor", "cidade", "estado"],
        [[customer_id, "01000-000", "Cliente Teste", "Sao Paulo", "SP"]],
    )

    _write_csv(
        data_dir / "dim_vendedores.csv",
        ["id_vendedor", "nome_vendedor", "prefixo_cep", "cidade", "estado"],
        [[seller_id, "Vendedor Teste", "02000-000", "Sao Paulo", "SP"]],
    )

    _write_csv(
        data_dir / "fat_pedidos.csv",
        [
            "id_pedido",
            "id_consumidor",
            "status",
            "pedido_compra_timestamp",
            "pedido_entregue_timestamp",
            "data_estimada_entrega",
            "tempo_entrega_dias",
            "tempo_entrega_estimado_dias",
            "diferenca_entrega_dias",
            "entrega_no_prazo",
        ],
        [
            [
                order_id,
                customer_id,
                "delivered",
                "2026-01-01T10:00:00",
                "2026-01-03T12:00:00",
                "2026-01-04",
                "2",
                "3",
                "-1",
                "yes",
            ]
        ],
    )

    _write_csv(
        data_dir / "fat_itens_pedidos.csv",
        ["id_pedido", "id_item", "id_produto", "id_vendedor", "preco_BRL", "preco_frete"],
        [[order_id, "1", product_id, seller_id, "20", "5"]],
    )

    _write_csv(
        data_dir / "fat_avaliacoes_pedidos.csv",
        [
            "id_avaliacao",
            "id_pedido",
            "avaliacao",
            "titulo_comentario",
            "comentario",
            "data_comentario",
            "data_resposta",
        ],
        [[review_id, order_id, "5", "Otimo", "Muito bom", "2026-01-04T10:00:00", ""]],
    )

    Base.metadata.create_all(bind=test_engine)
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

    monkeypatch.setattr(data_ingestion, "_data_dir", lambda: data_dir)
    monkeypatch.setattr(data_ingestion, "SessionLocal", TestSessionLocal)

    assert data_ingestion.populate_db_from_csv() is True

    with TestSessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(Customer)) == 1
        assert db.scalar(select(func.count()).select_from(Seller)) == 1
        assert db.scalar(select(func.count()).select_from(Product)) == 1
        assert db.scalar(select(func.count()).select_from(Order)) == 1
        assert db.scalar(select(func.count()).select_from(OrderItem)) == 1
        assert db.scalar(select(func.count()).select_from(OrderReview)) == 1

        product = db.scalar(select(Product).where(Product.product_id == product_id))
        assert product is not None
        assert product.base_price == 20.0
        assert product.product_description == "Item da categoria casa conforto."

    # Segunda execucao deve ser no-op porque todas as tabelas ja tem dados.
    assert data_ingestion.populate_db_from_csv() is False
