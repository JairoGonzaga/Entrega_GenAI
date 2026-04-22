import sqlite3

from app.routers.agent import prompts


def test_select_textual_columns_for_sampling_prefers_low_cardinality_categories():
    columns = [
        (0, "id_pedido", "TEXT", 0, None, 0),
        (1, "id_consumidor", "TEXT", 0, None, 0),
        (2, "status", "TEXT", 0, None, 0),
        (3, "entrega_no_prazo", "TEXT", 0, None, 0),
        (4, "tempo_entrega_dias", "REAL", 0, None, 0),
    ]

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE TABLE fat_pedidos (
                id_pedido TEXT,
                id_consumidor TEXT,
                status TEXT,
                entrega_no_prazo TEXT,
                tempo_entrega_dias REAL
            )
            """
        )
        conn.executemany(
            "INSERT INTO fat_pedidos (id_pedido, id_consumidor, status, entrega_no_prazo, tempo_entrega_dias) VALUES (?, ?, ?, ?, ?)",
            [
                ("pid-001", "cid-001", "entregue", "sim", 1.0),
                ("pid-002", "cid-002", "entregue", "nao", 2.0),
                ("pid-003", "cid-003", "cancelado", "nao entregue", 3.0),
            ],
        )

        selected = prompts._select_textual_columns_for_sampling(conn, "fat_pedidos", columns, max_columns=2)
        selected_names = [col[1] for col in selected]

        assert "status" in selected_names
        assert "entrega_no_prazo" in selected_names
        assert "id_pedido" not in selected_names
        assert "id_consumidor" not in selected_names
    finally:
        conn.close()


def test_get_sample_values_prefers_semantic_textual_columns():
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute(
            """
            CREATE TABLE fat_pedidos (
                id_pedido TEXT,
                id_consumidor TEXT,
                status TEXT,
                entrega_no_prazo TEXT
            )
            """
        )
        conn.executemany(
            "INSERT INTO fat_pedidos (id_pedido, id_consumidor, status, entrega_no_prazo) VALUES (?, ?, ?, ?)",
            [
                ("p1", "c1", "entregue", "sim"),
                ("p2", "c2", "entregue", "nao"),
                ("p3", "c3", "cancelado", "nao entregue"),
            ],
        )
        columns = conn.execute("PRAGMA table_info(\"fat_pedidos\")").fetchall()

        lines = prompts._get_sample_values(conn, "fat_pedidos", columns, max_columns=2, max_values=3)

        assert any(line.startswith("- status:") for line in lines)
        assert any(line.startswith("- entrega_no_prazo:") for line in lines)
        assert all(not line.startswith("- id_pedido:") for line in lines)
        assert all(not line.startswith("- id_consumidor:") for line in lines)
    finally:
        conn.close()
