"""Utilitarios de LLM para geracao de SQL e interpretacao em stream."""

import asyncio
import json
import logging
import re
import threading
from typing import AsyncGenerator

from google import genai
from fastapi import HTTPException

from app.config import settings

MODEL_NAME = settings.gemini_model
logger = logging.getLogger("agent")


def _strip_code_fences(text: str) -> str:
    cleaned = (text or "").strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json|sql)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def _extract_json_object(text: str) -> dict | None:
    cleaned = _strip_code_fences(text)
    try:
        payload = json.loads(cleaned)
        if isinstance(payload, dict):
            return payload
    except Exception:  # noqa: BLE001
        pass

    start = cleaned.find("{")
    end = cleaned.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None

    snippet = cleaned[start : end + 1]
    try:
        payload = json.loads(snippet)
        return payload if isinstance(payload, dict) else None
    except Exception:  # noqa: BLE001
        return None


def generate_sql_plan(
    question: str,
    schema_context: str,
    category_context: str,
    history_context: str,
    client: genai.Client | None,
) -> dict:
    """Gera um plano estruturado de consulta sem expor cadeia de raciocinio."""
    if client is None:
        return {
            "objective": question,
            "tables": [],
            "joins": [],
            "filters": [],
            "aggregations": [],
            "ordering_limit": "LIMIT 100",
        }

    prompt = (
        "You are a SQL planning assistant for SQLite. "
        "Create a concise execution plan in JSON for the user question. "
        "Do not include chain-of-thought, hidden reasoning, or explanations outside JSON.\n\n"
        "Return exactly one JSON object with keys: "
        "objective, tables, joins, filters, aggregations, ordering_limit.\n\n"
        f"Schema context:\n{schema_context}\n\n"
        f"Category context:\n{category_context}\n\n"
        f"History context:\n{history_context}\n\n"
        f"Question: {question}"
    )

    try:
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        parsed = _extract_json_object(response.text or "")
    except Exception:  # noqa: BLE001
        parsed = None

    if parsed is None:
        return {
            "objective": question,
            "tables": [],
            "joins": [],
            "filters": [],
            "aggregations": [],
            "ordering_limit": "LIMIT 100",
        }

    return {
        "objective": str(parsed.get("objective", question)),
        "tables": parsed.get("tables", []),
        "joins": parsed.get("joins", []),
        "filters": parsed.get("filters", []),
        "aggregations": parsed.get("aggregations", []),
        "ordering_limit": str(parsed.get("ordering_limit", "LIMIT 100")),
    }


def extract_sql(text: str) -> str:
    """Extrai SQL da resposta do modelo, removendo markdown quando existir."""
    code_block = re.search(r"```(?:sql)?\s*(.*?)```", text, re.IGNORECASE | re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    select_match = re.search(r"(SELECT\b[\s\S]*?;)", text, re.IGNORECASE)
    if select_match:
        return select_match.group(1).strip()

    return text.strip()


def generate_sql(prompt: str, client: genai.Client | None) -> str:
    """Gera SQL de forma sincrona a partir do prompt."""
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY in backend/.env.",
        )

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    raw = (response.text or "").strip()
    sql = extract_sql(raw)
    if not sql:
        raise HTTPException(status_code=502, detail="Model returned empty SQL")

    return sql


def repair_sql(
    question: str,
    failed_sql: str,
    error_message: str,
    schema_context: str,
    category_context: str,
    history_context: str,
    client: genai.Client | None,
) -> str:
    """Tenta corrigir SQL invalido com base no erro retornado pelo SQLite."""
    if client is None:
        raise HTTPException(
            status_code=503,
            detail="Gemini API key not configured. Set GEMINI_API_KEY or GOOGLE_API_KEY in backend/.env.",
        )

    prompt = (
        "You are a SQLite SQL fixer. "
        "Given a failed SQL and execution error, return only one corrected SQL SELECT statement. "
        "No markdown, no comments, no explanation.\n\n"
        "Hard constraints:\n"
        "- SELECT only\n"
        "- exactly one statement\n"
        "- include LIMIT <= 100\n"
        "- use only tables/columns from provided schema\n\n"
        f"Schema context:\n{schema_context}\n\n"
        f"Category context:\n{category_context}\n\n"
        f"History context:\n{history_context}\n\n"
        f"Question: {question}\n"
        f"Failed SQL: {failed_sql}\n"
        f"SQLite error: {error_message}\n"
        "Corrected SQL:"
    )

    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    fixed = extract_sql((response.text or "").strip())
    if not fixed:
        raise HTTPException(status_code=502, detail="Model returned empty SQL during repair")

    return fixed


def build_interpretation(question: str, rows: list[dict], client: genai.Client | None) -> str:
    """Monta interpretacao textual dos resultados em PT-BR."""
    if not rows:
        return "A consulta nao retornou resultados para os filtros informados."

    if client is None:
        return f"A consulta retornou {len(rows)} registro(s)."

    prompt = (
        "Voce e um analista de dados de e-commerce. "
        "Resuma os resultados abaixo em PT-BR, em no maximo 5 linhas, com foco acionavel.\n\n"
        f"Pergunta original: {question}\n"
        f"Total de registros: {len(rows)}\n"
        f"Amostra JSON: {json.dumps(rows[:20], ensure_ascii=False)}"
    )
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    text = (response.text or "").strip()
    return text or f"A consulta retornou {len(rows)} registro(s)."


async def stream_interpretation_chunks(
    question: str,
    rows: list[dict],
    client: genai.Client | None,
) -> AsyncGenerator[str, None]:
    """Faz streaming real da interpretacao, emitindo chunks conforme chegam."""
    if not rows:
        yield "A consulta nao retornou resultados para os filtros informados."
        return

    if client is None:
        yield f"A consulta retornou {len(rows)} registro(s)."
        return

    prompt = (
        "Voce e um analista de dados de e-commerce. "
        "Resuma os resultados abaixo em PT-BR, em no maximo 5 linhas, com foco acionavel.\n\n"
        f"Pergunta original: {question}\n"
        f"Total de registros: {len(rows)}\n"
        f"Amostra JSON: {json.dumps(rows[:20], ensure_ascii=False)}"
    )

    queue: asyncio.Queue[tuple[str, str | None]] = asyncio.Queue()
    loop = asyncio.get_running_loop()

    def _producer() -> None:
        try:
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config={"response_modalities": ["TEXT"]},
                stream=True,
            )
            for chunk in response:
                text = getattr(chunk, "text", None)
                if text:
                    loop.call_soon_threadsafe(queue.put_nowait, ("text", text))
        except Exception as exc:  # noqa: BLE001
            loop.call_soon_threadsafe(queue.put_nowait, ("error", str(exc)))
        finally:
            loop.call_soon_threadsafe(queue.put_nowait, ("done", None))

    threading.Thread(target=_producer, daemon=True).start()

    while True:
        kind, payload = await queue.get()
        if kind == "done":
            break
        if kind == "error":
            logger.exception("Interpretation stream failed: %s", payload)
            yield "Nao foi possivel concluir a interpretacao em stream."
            break
        if payload:
            yield payload
