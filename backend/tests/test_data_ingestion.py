"""Smoke tests for the repository SQLite database.

The current workflow uses only the committed `backend/Banco/banco.db` file.
"""

from pathlib import Path
import sqlite3

from app.config import DEFAULT_DB_PATH, settings


def test_database_url_points_to_repo_db_file():
    db_path = Path(DEFAULT_DB_PATH)

    assert settings.database_url == f"sqlite:///{db_path.as_posix()}"
    assert db_path.name == "banco.db"
    assert db_path.exists()


def test_repository_database_contains_expected_tables():
    db_path = Path(DEFAULT_DB_PATH)

    with sqlite3.connect(db_path) as connection:
        tables = {
            row[0]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
            )
        }

    expected_tables = {
        "dim_produtos",
        "dim_consumidores",
        "dim_vendedores",
        "fat_pedidos",
        "fat_itens_pedidos",
        "fat_avaliacoes_pedidos",
    }

    assert expected_tables.issubset(tables)
