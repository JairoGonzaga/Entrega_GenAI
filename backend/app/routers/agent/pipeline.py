"""Orquestracao do pipeline de consulta e do fluxo SSE do agent."""

import asyncio
import json
import logging
from time import perf_counter
from typing import AsyncGenerator

from google import genai
from fastapi import HTTPException

from . import guardrails, memory, prompts
from .intent import detect_category
from .interpreter import suggest_followups
from .llm import build_interpretation, generate_sql, stream_interpretation_chunks
from .sql_engine import execute_sql

logger = logging.getLogger("agent")


def run_query_pipeline(question: str, session_id: str, client: genai.Client | None) -> dict:
    """Executa pipeline completo sincrono para resposta JSON."""
    start = perf_counter()
    category = detect_category(question)
    history_context = memory.format_for_prompt(session_id)
    prompt = prompts.build_prompt(question, history_context)

    sql = generate_sql(prompt, client)
    sql = guardrails.validate_sql(sql)
    rows = execute_sql(sql)
    interpretation = build_interpretation(question, rows, client)
    try:
        followups = suggest_followups(question, rows)
    except Exception:  # noqa: BLE001
        followups = []

    memory.add_turn(
        session_id,
        memory.Turn(
            question=question,
            sql=sql,
            data=rows,
            interpretation=interpretation,
        ),
    )

    elapsed_ms = round((perf_counter() - start) * 1000)
    logger.info(
        json.dumps(
            {
                "question": question,
                "category": category,
                "sql": sql,
                "rows": len(rows),
                "elapsed_ms": elapsed_ms,
            },
            ensure_ascii=False,
        )
    )

    return {
        "answer": interpretation,
        "interpretacao": interpretation,
        "sql": sql,
        "dados": rows,
        "category": category,
        "followups": followups,
    }


async def stream_response(
    question: str,
    session_id: str,
    client: genai.Client | None,
) -> AsyncGenerator[str, None]:
    """Executa fluxo SSE com envio incremental de texto."""
    try:
        validated_question = guardrails.validate_user_input(question)
        category = detect_category(validated_question)
        history_context = memory.format_for_prompt(session_id)
        prompt = prompts.build_prompt(validated_question, history_context)
        sql = await asyncio.to_thread(generate_sql, prompt, client)
        sql = guardrails.validate_sql(sql)
        rows = await asyncio.to_thread(execute_sql, sql)
        try:
            followups = await asyncio.to_thread(suggest_followups, validated_question, rows)
        except Exception:  # noqa: BLE001
            followups = []
    except HTTPException as exc:
        payload = json.dumps({"type": "error", "msg": exc.detail}, ensure_ascii=False)
        yield f"data: {payload}\n\n"
        return
    except Exception:
        payload = json.dumps({"type": "error", "msg": "Erro interno ao processar a consulta."}, ensure_ascii=False)
        yield f"data: {payload}\n\n"
        return

    meta_payload = json.dumps(
        {
            "type": "meta",
            "sql": sql,
            "dados": rows,
            "categoria": category,
        },
        ensure_ascii=False,
    )
    yield f"data: {meta_payload}\n\n"

    interpretation_parts: list[str] = []
    async for chunk_text in stream_interpretation_chunks(validated_question, rows, client):
        interpretation_parts.append(chunk_text)
        text_payload = json.dumps({"type": "text", "content": chunk_text}, ensure_ascii=False)
        yield f"data: {text_payload}\n\n"

    interpretation = "".join(interpretation_parts).strip() or f"A consulta retornou {len(rows)} registro(s)."
    memory.add_turn(
        session_id,
        memory.Turn(
            question=validated_question,
            sql=sql,
            data=rows,
            interpretation=interpretation,
        ),
    )

    done_payload = json.dumps({"type": "done", "followups": followups}, ensure_ascii=False)
    yield f"data: {done_payload}\n\n"
