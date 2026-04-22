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


class _FakeClientError(Exception):
    """Simula google.genai.errors.ClientError com atributo 'code'."""
    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
        self.message = message
        # Simula a string format do ClientError real: "CODE STATUS. JSON"
        self.args = (f"{code} {message}",)


class _FailingModels:
    def __init__(self, exc: Exception):
        self._exc = exc

    def generate_content(self, model: str, contents: str):  # noqa: ARG002
        raise self._exc


class _FailingClient:
    def __init__(self, exc: Exception):
        self.models = _FailingModels(exc)


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


def test_generate_sql_maps_quota_error_to_http_429():
    client = _FailingClient(
        _FakeClientError(
            code=429,
            message="429 RESOURCE_EXHAUSTED. Please retry in 30.7s.",
        )
    )

    try:
        llm.generate_sql("SELECT ...", client)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 429
        assert "Cota da Gemini API excedida" in exc.detail


def test_generate_sql_maps_auth_error_to_http_503():
    client = _FailingClient(_FakeClientError(code=403, message="PERMISSION_DENIED"))

    try:
        llm.generate_sql("SELECT ...", client)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503


def test_generate_sql_maps_unavailable_error_to_user_friendly_503():
    client = _FailingClient(
        _FakeClientError(
            code=503,
            message=(
                "503 UNAVAILABLE. This model is currently experiencing high demand. "
                "Spikes in demand are usually temporary. Please try again later."
            ),
        )
    )

    try:
        llm.generate_sql("SELECT ...", client)
        assert False, "Expected HTTPException"
    except HTTPException as exc:
        assert exc.status_code == 503
        assert "temporariamente indisponivel" in exc.detail.lower()
