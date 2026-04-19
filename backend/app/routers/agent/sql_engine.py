"""Camada de execucao SQL com protecao de timeout no SQLite."""

import sqlite3
from pathlib import Path
from time import perf_counter

from fastapi import HTTPException

from app.config import settings

SQLITE_BUSY_TIMEOUT_SECONDS = 5.0
SQLITE_QUERY_TIMEOUT_SECONDS = 10.0


def resolve_sqlite_path(database_url: str) -> Path:
    """Resolve caminho do arquivo SQLite a partir da DATABASE_URL."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise HTTPException(status_code=500, detail="Unsupported DATABASE_URL for sqlite execution")

    return Path(database_url[len(prefix):])


def execute_sql(sql: str) -> list[dict]:
    """Executa SQL em modo seguro com timeout de lock e de execucao."""
    db_path = resolve_sqlite_path(settings.database_url)
    if not db_path.exists():
        raise HTTPException(status_code=500, detail="Database file not found")

    conn = sqlite3.connect(str(db_path), timeout=SQLITE_BUSY_TIMEOUT_SECONDS)
    conn.row_factory = sqlite3.Row
    start = perf_counter()

    def _progress_abort() -> int:
        elapsed = perf_counter() - start
        # Interrompe queries longas para preservar disponibilidade da API.
        return 1 if elapsed > SQLITE_QUERY_TIMEOUT_SECONDS else 0

    conn.set_progress_handler(_progress_abort, 10000)
    conn.execute(f"PRAGMA busy_timeout={int(SQLITE_BUSY_TIMEOUT_SECONDS * 1000)}")
    try:
        rows = conn.execute(sql).fetchall()
        return [dict(row) for row in rows]
    except sqlite3.OperationalError as exc:
        msg = str(exc).lower()
        if "interrupted" in msg or "busy" in msg or "locked" in msg:
            raise HTTPException(
                status_code=408,
                detail="SQL query timed out or database is busy. Refine filters and try again.",
            ) from exc
        raise
    finally:
        conn.set_progress_handler(None, 0)
        conn.close()
