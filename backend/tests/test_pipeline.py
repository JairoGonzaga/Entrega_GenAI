import sqlite3

import pytest
from fastapi import HTTPException

from app.routers.agent import pipeline


def test_build_generation_prompt_embeds_plan_json():
    base_prompt = "Question: top products\nSQL:"
    plan = {
        "objective": "Top produtos",
        "tables": ["fat_itens_pedidos"],
        "joins": [],
        "filters": [],
        "aggregations": ["SUM(quantidade * preco_unitario)"],
        "ordering_limit": "ORDER BY receita DESC LIMIT 10",
    }

    prompt = pipeline._build_generation_prompt(base_prompt, plan)

    assert "[PLANO_DE_EXECUCAO_JSON]" in prompt
    assert '"objective": "Top produtos"' in prompt
    assert "Use o plano acima apenas como guia" in prompt


def test_execute_with_auto_repair_returns_rows_when_first_execution_succeeds(monkeypatch):
    monkeypatch.setattr(pipeline, "execute_sql", lambda sql: [{"ok": 1}])

    sql, rows = pipeline._execute_with_auto_repair(
        question="Pergunta",
        history_context="",
        category_context="general",
        schema_context="schema",
        sql="SELECT 1 LIMIT 100",
        client=None,
    )

    assert sql == "SELECT 1 LIMIT 100"
    assert rows == [{"ok": 1}]


def test_execute_with_auto_repair_repairs_after_operational_error(monkeypatch):
    calls = {"count": 0}

    def _fake_execute(sql: str):
        calls["count"] += 1
        if calls["count"] == 1:
            raise sqlite3.OperationalError("near FROM: syntax error")
        return [{"fixed": 1}]

    monkeypatch.setattr(pipeline, "execute_sql", _fake_execute)
    monkeypatch.setattr(pipeline, "repair_sql", lambda **kwargs: "SELECT 1 LIMIT 100")
    monkeypatch.setattr(pipeline.guardrails, "validate_sql", lambda sql: sql)

    sql, rows = pipeline._execute_with_auto_repair(
        question="Pergunta",
        history_context="",
        category_context="general",
        schema_context="schema",
        sql="SELECT broken",
        client=None,
    )

    assert calls["count"] == 2
    assert sql == "SELECT 1 LIMIT 100"
    assert rows == [{"fixed": 1}]


def test_execute_with_auto_repair_raises_http_400_when_repair_still_fails(monkeypatch):
    monkeypatch.setattr(
        pipeline,
        "execute_sql",
        lambda sql: (_ for _ in ()).throw(sqlite3.OperationalError("syntax error")),
    )
    monkeypatch.setattr(pipeline, "repair_sql", lambda **kwargs: "SELECT still_broken LIMIT 100")
    monkeypatch.setattr(pipeline.guardrails, "validate_sql", lambda sql: sql)

    with pytest.raises(HTTPException) as exc_info:
        pipeline._execute_with_auto_repair(
            question="Pergunta",
            history_context="",
            category_context="general",
            schema_context="schema",
            sql="SELECT broken",
            client=None,
        )

    assert exc_info.value.status_code == 400
    assert "correcao automatica" in exc_info.value.detail


def test_run_query_pipeline_includes_planning_stage(monkeypatch):
    captured: dict = {}

    monkeypatch.setattr(pipeline, "detect_category", lambda question: "sales")
    monkeypatch.setattr(pipeline.memory, "format_for_prompt", lambda session_id: "history")
    monkeypatch.setattr(pipeline.prompts, "build_schema_context", lambda: "schema")
    monkeypatch.setattr(pipeline.prompts, "build_prompt", lambda question, history: "base prompt")
    monkeypatch.setattr(
        pipeline.prompts,
        "CATEGORIES",
        {"sales": {"context": "sales context"}},
        raising=False,
    )
    monkeypatch.setattr(
        pipeline,
        "generate_sql_plan",
        lambda **kwargs: {
            "objective": "Gerar top produtos",
            "tables": ["fat_itens_pedidos"],
            "joins": [],
            "filters": [],
            "aggregations": ["SUM(...)"],
            "ordering_limit": "LIMIT 10",
        },
    )

    def _fake_generate_sql(prompt: str, client):  # noqa: ARG001
        captured["prompt"] = prompt
        return "SELECT 1 LIMIT 100"

    monkeypatch.setattr(pipeline, "generate_sql", _fake_generate_sql)
    monkeypatch.setattr(
        pipeline,
        "_execute_with_auto_repair",
        lambda **kwargs: ("SELECT 1 LIMIT 100", [{"total": 1}]),
    )
    monkeypatch.setattr(pipeline, "interpret_sync", lambda question, rows, category, client: "ok")
    monkeypatch.setattr(pipeline, "suggest_followups", lambda *args, **kwargs: ["f1", "f2", "f3"])
    monkeypatch.setattr(pipeline.memory, "add_turn", lambda session_id, turn: None)
    monkeypatch.setattr(pipeline.guardrails, "validate_sql", lambda sql: sql)

    result = pipeline.run_query_pipeline("Top produtos", "sess-1", client=None)

    assert "[PLANO_DE_EXECUCAO_JSON]" in captured["prompt"]
    assert '"objective": "Gerar top produtos"' in captured["prompt"]
    assert result["sql"] == "SELECT 1 LIMIT 100"
    assert result["dados"] == [{"total": 1}]
