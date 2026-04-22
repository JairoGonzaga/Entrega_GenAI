"""Prompts e contexto de dominio para o agente Text-to-SQL."""

import json
import sqlite3
from functools import lru_cache
from pathlib import Path

from app.config import settings

from .intent import CATEGORIES, detect_category

SQL_RULES = """
Mandatory SQL rules:
- Output only one SQL query text (no markdown, no comments, no explanation).
- SQLite dialect only.
- Read-only query: SELECT only. Never use DELETE, DROP, UPDATE, INSERT, ALTER, CREATE, TRUNCATE, PRAGMA.
- Return exactly one statement. Do not chain statements.
- Always include LIMIT and keep it <= 100.
- Use only tables/columns that exist in the provided schema context.
- Prefer explicit JOIN clauses with clear ON conditions.
- Prefer explicit column list; avoid SELECT * unless user explicitly asks for all columns.
- Use deterministic output ordering when ranking/top-k is requested (include ORDER BY).
- Use meaningful aliases in snake_case (example: COUNT(*) AS total_orders).
- Handle aggregates carefully:
    - Include GROUP BY for all non-aggregated selected columns.
    - Use COALESCE for nullable numeric fields when appropriate.
- For ratio/percentage metrics, avoid integer division (cast when needed).
- For date/time filters, use SQLite-compatible expressions only.
- For textual categorical columns, compare using exact string values from sample_values (never invent boolean True/False).
"""


def _quote_identifier(name: str) -> str:
    """Coloca identificadores do SQLite com seguranca."""
    return '"' + name.replace('"', '""') + '"'


def _resolve_sqlite_path(database_url: str) -> Path:
    """Resolve o caminho do banco SQLite a partir da URL do SQLAlchemy."""
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite DATABASE_URL is supported for schema extraction")

    db_path = database_url[len(prefix):]
    return Path(db_path)


def _is_textual_column(column_type: str) -> bool:
    normalized = (column_type or "").upper()
    return any(token in normalized for token in ("TEXT", "CHAR", "CLOB", "VARCHAR"))


def _distinct_count_with_limit(
    conn: sqlite3.Connection,
    table: str,
    col_name: str,
    limit: int,
) -> int:
    """Conta distintos ate um limite para estimar cardinalidade sem custo alto."""
    query = (
        "SELECT COUNT(*) FROM ("
        f"SELECT DISTINCT {_quote_identifier(col_name)} "
        f"FROM {_quote_identifier(table)} "
        f"WHERE {_quote_identifier(col_name)} IS NOT NULL "
        f"LIMIT {max(1, limit)}"
        ")"
    )
    return int(conn.execute(query).fetchone()[0])


def _select_textual_columns_for_sampling(
    conn: sqlite3.Connection,
    table: str,
    columns: list[tuple],
    max_columns: int,
    max_categorical_distinct: int = 20,
) -> list[tuple]:
    """Seleciona colunas textuais por verificacao SQL de cardinalidade (categoricas)."""
    textual_columns = [c for c in columns if _is_textual_column(c[2])]
    if not textual_columns:
        return []

    scored: list[tuple[int, str, tuple]] = []
    overflow_limit = max_categorical_distinct + 1
    for col in textual_columns:
        col_name = str(col[1])
        distinct_count = _distinct_count_with_limit(conn, table, col_name, overflow_limit)
        if 2 <= distinct_count <= max_categorical_distinct:
            scored.append((distinct_count, col_name, col))

    if not scored:
        for col in textual_columns:
            col_name = str(col[1])
            distinct_count = _distinct_count_with_limit(conn, table, col_name, max_categorical_distinct)
            if distinct_count > 0:
                scored.append((distinct_count, col_name, col))

    scored.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in scored[:max_columns]]


def _get_sample_values(
    conn: sqlite3.Connection,
    table: str,
    columns: list[tuple],
    max_columns: int = 2,
    max_values: int = 3,
) -> list[str]:
    """Coleta pequenas amostras de valores para colunas textuais."""
    lines: list[str] = []
    textual_columns = _select_textual_columns_for_sampling(conn, table, columns, max_columns=max_columns)

    for _, col_name, _, _, _, _ in textual_columns:
        query = (
            f"SELECT DISTINCT {_quote_identifier(col_name)} "
            f"FROM {_quote_identifier(table)} "
            f"WHERE {_quote_identifier(col_name)} IS NOT NULL "
            f"LIMIT {max_values}"
        )
        rows = conn.execute(query).fetchall()
        values = [r[0] for r in rows]
        if values:
            lines.append(f"- {col_name}: {json.dumps(values, ensure_ascii=False)}")

    return lines


@lru_cache(maxsize=1)
def build_schema_context() -> str:
    """Monta o contexto completo de schema dinamicamente a partir do metadata do SQLite."""
    db_path = _resolve_sqlite_path(settings.database_url)
    if not db_path.exists():
        return "[DATABASE]\ndialect: sqlite\nstatus: unavailable (database file not found)"

    conn = sqlite3.connect(str(db_path))
    try:
        table_rows = conn.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
            ORDER BY name
            """
        ).fetchall()
        tables = [row[0] for row in table_rows]

        output: list[str] = [
            "[DATABASE]",
            "dialect: sqlite",
            f"tables_count: {len(tables)}",
        ]
        relationships: list[str] = []

        for table in tables:
            output.append("")
            output.append(f"[TABLE] {table}")
            output.append("columns:")

            table_info = conn.execute(f"PRAGMA table_info({_quote_identifier(table)})").fetchall()
            fk_rows = conn.execute(f"PRAGMA foreign_key_list({_quote_identifier(table)})").fetchall()
            fk_by_column = {fk[3]: (fk[2], fk[4]) for fk in fk_rows}

            for _, col_name, col_type, not_null, _, pk in table_info:
                pieces = [f"- {col_name} {(col_type or 'TEXT').upper()}"]
                if pk:
                    pieces.append("PK")
                if not_null:
                    pieces.append("NOT NULL")
                if col_name in fk_by_column:
                    ref_table, ref_col = fk_by_column[col_name]
                    pieces.append(f"FK->{ref_table}.{ref_col}")
                    relationships.append(f"- {table}.{col_name} -> {ref_table}.{ref_col}")

                output.append(" ".join(pieces))

            sample_lines = _get_sample_values(conn, table, table_info)
            if sample_lines:
                output.append("sample_values:")
                output.extend(sample_lines)

        output.append("")
        output.append("[RELATIONSHIPS]")
        output.extend(sorted(set(relationships)) or ["- none detected"])

        output.append("")
        output.append("[BUSINESS_RULES]")
        output.append("- Only SELECT queries")
        output.append("- Always include LIMIT <= 100")
        output.append("- Exclude canceled orders when user asks for revenue (default)")

        return "\n".join(output)
    finally:
        conn.close()


def refresh_schema_context_cache() -> None:
    """Limpa o cache do schema (use apos migracoes ou atualizacoes de schema)."""
    build_schema_context.cache_clear()


def build_prompt(question: str, history_context: str = "") -> str:
    """Monta o prompt do agente com base na pergunta e na categoria."""
    category = detect_category(question)
    category_context = CATEGORIES.get(category, {}).get("context", "")
    schema_context = build_schema_context()

    return f"""You are an expert SQL developer for e-commerce systems.

{SQL_RULES}

{schema_context}
{category_context}
{history_context}

Question: {question}
SQL:"""
