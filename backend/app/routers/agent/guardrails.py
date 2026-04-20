"""Guardrails de seguranca para entrada do agente e validacao de SQL."""

import re

from fastapi import HTTPException

BLOCKED_SQL_KEYWORDS = [
    "DELETE",
    "DROP",
    "UPDATE",
    "INSERT",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "REPLACE",
    "MERGE",
    "ATTACH",
    "DETACH",
    "PRAGMA",
]

INJECTION_PATTERNS = [
    r"ignore (previous|above|all) instructions",
    r"forget (your|the) (system|previous)",
    r"you are now",
    r"ignore (as|todas) (instruções|instrucoes) (anteriores|acima|todas)",
    r"esqueça (as|as) (instruções|instrucoes) (do|da) (sistema|anterior)",
    r"você é agora",
    r"voce e agora",
    r"agora você é",
    r"agora voce e",
    r"--",
    r";.*SELECT",
]


def validate_user_input(question: str) -> str:
    """Valida entrada do usuario contra tentativas de prompt injection."""
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Pergunta longa demais, limite de 500 caracteres")

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="Input invalido detectado")

    return question.strip()


def validate_sql(sql: str) -> str:
    """Valida SQL contra operacoes perigosas e execucao de multiplas consultas."""
    sql_upper = sql.upper()

    for keyword in BLOCKED_SQL_KEYWORDS:
        if re.search(r"\b" + keyword + r"\b", sql_upper):
            raise HTTPException(status_code=400, detail=f"SQL invalido: {keyword} nao permitido")

    if sql.count(";") > 1:
        raise HTTPException(status_code=400, detail="Multiplas consultas nao permitidas")

    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + " LIMIT 100"

    return sql
