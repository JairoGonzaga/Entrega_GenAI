"""Security guardrails for agent input and SQL validation."""

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
    """Validate user input for prompt injection attacks."""
    if len(question) > 500:
        raise HTTPException(status_code=400, detail="Question too long (max 500 chars)")

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, question, re.IGNORECASE):
            raise HTTPException(status_code=400, detail="Invalid input detected")

    return question.strip()


def validate_sql(sql: str) -> str:
    """Validate SQL query for dangerous operations and multi-statement execution."""
    sql_upper = sql.upper()

    for keyword in BLOCKED_SQL_KEYWORDS:
        if re.search(r"\b" + keyword + r"\b", sql_upper):
            raise HTTPException(status_code=400, detail=f"Invalid SQL: {keyword} not allowed")

    if sql.count(";") > 1:
        raise HTTPException(status_code=400, detail="Multiple queries not allowed")

    if "LIMIT" not in sql_upper:
        sql = sql.rstrip(";") + " LIMIT 100"

    return sql
