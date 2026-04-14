from datetime import date, datetime


CUSTOMER_ID = "4" * 32
SELLER_ID = "5" * 32
SALE_PRODUCT_ID = "1" * 32
FREE_PRODUCT_ID = "2" * 32
ORDER_ID = "3" * 32
REVIEW_ID = "6" * 32
MISSING_PRODUCT_ID = "7" * 32


def seed_catalog(session):
    from app.models.avaliacao_pedido import OrderReview
    from app.models.consumidor import Customer
    from app.models.item_pedido import OrderItem
    from app.models.pedido import Order
    from app.models.produto import Product
    from app.models.vendedor import Seller

    session.add_all(
        [
            Customer(
                customer_id=CUSTOMER_ID,
                zip_prefix="01000-000",
                customer_name="Cliente Teste",
                cidade="Sao Paulo",
                estado="SP",
            ),
            Seller(
                seller_id=SELLER_ID,
                seller_name="Vendedor Teste",
                zip_prefix="02000-000",
                cidade="Sao Paulo",
                estado="SP",
            ),
            Product(
                product_id=SALE_PRODUCT_ID,
                product_name="Cafeteira",
                product_category="Casa",
                product_description="Cafeteira eletrica",
                base_price=100.0,
                product_weight_grams=1200.0,
                length_cm=30.0,
                height_cm=25.0,
                width_cm=20.0,
            ),
            Product(
                product_id=FREE_PRODUCT_ID,
                product_name="Livro",
                product_category="Leitura",
                product_description="Livro de teste",
                base_price=50.0,
                product_weight_grams=300.0,
                length_cm=21.0,
                height_cm=3.0,
                width_cm=14.0,
            ),
            Order(
                order_id=ORDER_ID,
                customer_id=CUSTOMER_ID,
                status="delivered",
                purchase_timestamp=datetime(2026, 1, 15, 10, 30),
                delivered_timestamp=datetime(2026, 1, 18, 12, 0),
                estimated_delivery_date=date(2026, 1, 20),
                delivery_days=3.0,
                estimated_delivery_days=5.0,
                delivery_delay_days=0.0,
                on_time_delivery="yes",
            ),
            OrderItem(
                order_id=ORDER_ID,
                item_id=1,
                product_id=SALE_PRODUCT_ID,
                seller_id=SELLER_ID,
                price_brl=100.0,
                freight_price=10.0,
            ),
            OrderReview(
                review_id=REVIEW_ID,
                order_id=ORDER_ID,
                rating=5,
                comment_title="Otimo",
                comment="Produto muito bom",
                comment_date=datetime(2026, 1, 19, 9, 0),
                response_date=None,
            ),
        ]
    )
    session.commit()


def test_healthcheck(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "API rodando com sucesso!"}


def test_list_categories_and_products(client, db_session):
    seed_catalog(db_session)

    categories_response = client.get("/api/produtos/categorias")
    products_response = client.get("/api/produtos")

    assert categories_response.status_code == 200
    assert categories_response.json() == ["Casa", "Leitura"]

    assert products_response.status_code == 200
    payload = products_response.json()
    assert payload["total"] == 2
    assert len(payload["itens"]) == 2

    cafeteira = next(item for item in payload["itens"] if item["id_produto"] == SALE_PRODUCT_ID)
    assert cafeteira["nome_produto"] == "Cafeteira"
    assert cafeteira["media_avaliacoes"] == 5.0
    assert cafeteira["total_vendas"] == 1
    assert cafeteira["quantidade_registros"] == 1


def test_product_detail_returns_history_and_reviews(client, db_session):
    seed_catalog(db_session)

    response = client.get(f"/api/produtos/{SALE_PRODUCT_ID}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id_produto"] == SALE_PRODUCT_ID
    assert payload["nome_produto"] == "Cafeteira"
    assert payload["media_avaliacoes"] == 5.0
    assert payload["total_vendas"] == 1
    assert payload["medidas"]["peso_produto_gramas"] == 1200.0
    assert len(payload["vendas_historico"]) == 1
    assert len(payload["avaliacoes"]) == 1


def test_create_update_and_delete_product(client, db_session):
    seed_catalog(db_session)

    create_response = client.post(
        "/api/produtos",
        json={
            "nome_produto": "Fone de ouvido",
            "categoria_produto": "Eletronicos",
            "descricao_produto": "Modelo sem fio",
            "preco_base": 199.9,
            "peso_produto_gramas": 120.0,
            "comprimento_centimetros": 18.0,
            "altura_centimetros": 6.0,
            "largura_centimetros": 15.0,
        },
    )

    assert create_response.status_code == 201
    created = create_response.json()
    created_id = created["id_produto"]
    assert created["nome_produto"] == "Fone de ouvido"
    assert created["categoria_produto"] == "Eletronicos"

    update_response = client.put(
        f"/api/produtos/{FREE_PRODUCT_ID}",
        json={
            "nome_produto": "Livro Atualizado",
            "preco_base": 59.9,
        },
    )

    assert update_response.status_code == 200
    updated = update_response.json()
    assert updated["id_produto"] == FREE_PRODUCT_ID
    assert updated["nome_produto"] == "Livro Atualizado"

    delete_created_response = client.delete(f"/api/produtos/{created_id}")
    assert delete_created_response.status_code == 204

    conflict_response = client.delete(f"/api/produtos/{SALE_PRODUCT_ID}")
    assert conflict_response.status_code == 409
    assert conflict_response.json()["detail"] == "Produto possui historico de vendas e nao pode ser removido"


def test_list_products_with_filters(client, db_session):
    seed_catalog(db_session)

    by_search = client.get("/api/produtos", params={"busca": "Cafe"})
    by_category = client.get("/api/produtos", params={"categoria": "Leitura"})
    by_min_price = client.get("/api/produtos", params={"preco_min": 60})
    by_max_price = client.get("/api/produtos", params={"preco_max": 60})
    by_min_rating = client.get("/api/produtos", params={"nota_min": 4.5})

    assert by_search.status_code == 200
    assert by_search.json()["total"] == 1
    assert by_search.json()["itens"][0]["id_produto"] == SALE_PRODUCT_ID

    assert by_category.status_code == 200
    assert by_category.json()["total"] == 1
    assert by_category.json()["itens"][0]["id_produto"] == FREE_PRODUCT_ID

    assert by_min_price.status_code == 200
    assert by_min_price.json()["total"] == 1
    assert by_min_price.json()["itens"][0]["id_produto"] == SALE_PRODUCT_ID

    assert by_max_price.status_code == 200
    assert by_max_price.json()["total"] == 1
    assert by_max_price.json()["itens"][0]["id_produto"] == FREE_PRODUCT_ID

    assert by_min_rating.status_code == 200
    assert by_min_rating.json()["total"] == 1
    assert by_min_rating.json()["itens"][0]["id_produto"] == SALE_PRODUCT_ID


def test_validation_and_not_found_paths(client, db_session):
    seed_catalog(db_session)

    invalid_filter = client.get("/api/produtos", params={"preco_min": -1})
    invalid_id_shape = client.get("/api/produtos/id-invalido")

    assert invalid_filter.status_code == 422
    assert invalid_id_shape.status_code == 422

    detail_missing = client.get(f"/api/produtos/{MISSING_PRODUCT_ID}")
    update_missing = client.put(
        f"/api/produtos/{MISSING_PRODUCT_ID}",
        json={"nome_produto": "Nao existe"},
    )
    delete_missing = client.delete(f"/api/produtos/{MISSING_PRODUCT_ID}")

    assert detail_missing.status_code == 404
    assert update_missing.status_code == 404
    assert delete_missing.status_code == 404
    assert detail_missing.json()["detail"] == "Produto nao encontrado"


def test_update_without_fields_returns_400(client, db_session):
    seed_catalog(db_session)

    response = client.put(f"/api/produtos/{FREE_PRODUCT_ID}", json={})

    assert response.status_code == 400
    assert response.json()["detail"] == "Nenhum campo para atualizar"


def test_category_images_endpoint(client, monkeypatch):
    from pathlib import Path

    from app.routers.produtos import cache

    monkeypatch.setattr(cache, "repo_data_dir", lambda: Path("./missing-test-dir"))
    cache.category_images.cache_clear()

    response = client.get("/api/produtos/categorias-imagens")

    assert response.status_code == 200
    assert response.json() == {}
