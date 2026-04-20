from fastapi import HTTPException

from app.routers.agent import llm


class _FakeResponse:
    def __init__(self, text: str):
        self.text = text


class _FakeModels:
    def __init__(self, text: str):
        self._text = text

    def generate_content(self, model: str, contents: str):  # noqa: ARG002
        return _FakeResponse(self._text)


class _FakeClient:
    def __init__(self, text: str):
        self.models = _FakeModels(text)


def test_generate_sql_plan_without_client_returns_fallback_plan():
    result = llm.generate_sql_plan(
        question="Top produtos",
        schema_context="schema",
        category_context="sales",
        history_context="",
        client=None,
    )

    assert result["objective"] == "Top produtos"
    assert result["ordering_limit"] == "LIMIT 100"
    assert result["tables"] == []


def test_generate_sql_plan_parses_json_payload_from_model():
    client = _FakeClient(
        '{"objective":"Receita por estado","tables":["fat_pedidos"],'
        '"joins":["fat_pedidos.id_consumidor = dim_consumidores.id_consumidor"],'
        '"filters":["status <> \'cancelado\'"],"aggregations":["SUM(valor_total)"],'
        '"ordering_limit":"ORDER BY receita DESC LIMIT 10"}'
    )

    result = llm.generate_sql_plan(
        question="Receita por estado",
        schema_context="schema",
        category_context="sales",
        history_context="",
        client=client,
    )

    assert result["objective"] == "Receita por estado"
    assert result["tables"] == ["fat_pedidos"]
    assert "LIMIT 10" in result["ordering_limit"]


def test_generate_sql_plan_returns_fallback_when_json_is_invalid():
    client = _FakeClient("not a json object")

    result = llm.generate_sql_plan(
        question="Pergunta",
        schema_context="schema",
        category_context="general",
        history_context="",
        client=client,
    )

    assert result["objective"] == "Pergunta"
    assert result["ordering_limit"] == "LIMIT 100"


def test_repair_sql_requires_client():
    try:
        llm.repair_sql(
            question="Pergunta",
            failed_sql="SELECT * FROM x",
            error_message="near FROM: syntax error",
            schema_context="schema",
            category_context="general",
            history_context="",
            client=None,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503


def test_repair_sql_extracts_sql_from_markdown_response():
    client = _FakeClient("```sql\nSELECT id_produto FROM dim_produtos LIMIT 10;\n```")

    repaired = llm.repair_sql(
        question="Top produtos",
        failed_sql="SELECT id_produto FROM dim_produtos",
        error_message="near LIMIT: syntax error",
        schema_context="schema",
        category_context="sales",
        history_context="",
        client=client,
    )

    assert repaired.upper().startswith("SELECT")
    assert "LIMIT 10" in repaired


def test_repair_sql_raises_when_model_returns_empty_sql():
    client = _FakeClient("   ")

    try:
        llm.repair_sql(
            question="Top produtos",
            failed_sql="SELECT * FROM dim_produtos",
            error_message="syntax error",
            schema_context="schema",
            category_context="sales",
            history_context="",
            client=client,
        )
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 502
