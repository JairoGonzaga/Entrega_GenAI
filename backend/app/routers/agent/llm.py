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
