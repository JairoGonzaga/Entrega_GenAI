"""Orquestracao do pipeline de consulta e do fluxo SSE do agent."""

import asyncio
import json
import logging
import sqlite3
from time import perf_counter
from typing import AsyncGenerator

from google import genai
from fastapi import HTTPException

from . import guardrails, memory, prompts
from .intent import detect_category
from .interpreter import interpret_stream, interpret_sync, suggest_followups
from .llm import generate_sql, generate_sql_plan, repair_sql
from .sql_engine import execute_sql

logger = logging.getLogger("agent")


def _build_generation_prompt(base_prompt: str, plan: dict) -> str:
    """Anexa plano estruturado ao prompt final de geracao SQL."""
    return (
        f"{base_prompt}\n\n"
        "[PLANO_DE_EXECUCAO_JSON]\n"
        f"{json.dumps(plan, ensure_ascii=False)}\n"
        "[/PLANO_DE_EXECUCAO_JSON]\n"
        "Use o plano acima apenas como guia e retorne somente SQL valido."
    )


def _execute_with_auto_repair(
    question: str,
    history_context: str,
    category_context: str,
    schema_context: str,
    sql: str,
    client: genai.Client | None,
) -> tuple[str, list[dict]]:
    """Executa SQL e tenta uma correcao automatica caso o SQLite retorne erro operacional."""
    try:
        rows = execute_sql(sql)
        return sql, rows
    except sqlite3.OperationalError as exc:
        error_message = str(exc)

    try:
        fixed_sql = repair_sql(
            question=question,
            failed_sql=sql,
            error_message=error_message,
            schema_context=schema_context,
            category_context=category_context,
            history_context=history_context,
            client=client,
        )
        fixed_sql = guardrails.validate_sql(fixed_sql)
        rows = execute_sql(fixed_sql)
        return fixed_sql, rows
    except HTTPException:
        raise
    except sqlite3.OperationalError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"SQL invalido apos tentativa de correcao automatica: {exc}",
        ) from exc


def run_query_pipeline(question: str, session_id: str, client: genai.Client | None) -> dict:
    """Executa pipeline completo sincrono para resposta JSON."""
    start = perf_counter()
    category = detect_category(question)
    history_context = memory.format_for_prompt(session_id)
    schema_context = prompts.build_schema_context()
    category_context = prompts.CATEGORIES.get(category, {}).get("context", "")
    plan = generate_sql_plan(
        question=question,
        schema_context=schema_context,
        category_context=category_context,
        history_context=history_context,
        client=client,
    )
    base_prompt = prompts.build_prompt(question, history_context)
    prompt = _build_generation_prompt(base_prompt, plan)

    sql = generate_sql(prompt, client)
    sql = guardrails.validate_sql(sql)
    sql, rows = _execute_with_auto_repair(
        question=question,
        history_context=history_context,
        category_context=category_context,
        schema_context=schema_context,
        sql=sql,
        client=client,
    )
    interpretation = interpret_sync(question, rows, category, client)
    try:
        followups = suggest_followups(question, rows, category=category, interpretation=interpretation)
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
                "plan": plan,
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
        schema_context = prompts.build_schema_context()
        category_context = prompts.CATEGORIES.get(category, {}).get("context", "")
        plan = await asyncio.to_thread(
            generate_sql_plan,
            validated_question,
            schema_context,
            category_context,
            history_context,
            client,
        )
        base_prompt = prompts.build_prompt(validated_question, history_context)
        prompt = _build_generation_prompt(base_prompt, plan)
        sql = await asyncio.to_thread(generate_sql, prompt, client)
        sql = guardrails.validate_sql(sql)
        sql, rows = await asyncio.to_thread(
            _execute_with_auto_repair,
            validated_question,
            history_context,
            category_context,
            schema_context,
            sql,
            client,
        )
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
    async for chunk_text in interpret_stream(validated_question, rows, category, client):
        interpretation_parts.append(chunk_text)
        text_payload = json.dumps({"type": "text", "content": chunk_text}, ensure_ascii=False)
        yield f"data: {text_payload}\n\n"

    interpretation = "".join(interpretation_parts).strip() or f"A consulta retornou {len(rows)} registro(s)."
    try:
        followups = await asyncio.to_thread(
            suggest_followups,
            validated_question,
            rows,
            category,
            interpretation,
        )
    except Exception:  # noqa: BLE001
        followups = []

    followups_payload = json.dumps({"type": "followups", "items": followups}, ensure_ascii=False)
    yield f"data: {followups_payload}\n\n"

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
