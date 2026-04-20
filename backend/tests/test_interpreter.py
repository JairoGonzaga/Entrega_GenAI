import asyncio

import pytest

from app.routers.agent.interpreter import interpret_stream, interpret_sync, suggest_followups


def test_interpret_sync_without_rows_returns_no_results_message():
    result = interpret_sync(
        question="Quais produtos venderam mais?",
        rows=[],
        category="sales",
        client=None,
    )

    assert "nao retornou resultados" in result.lower()


def test_interpret_sync_without_client_returns_fallback_with_count():
    result = interpret_sync(
        question="Quais produtos venderam mais?",
        rows=[{"produto": "A", "receita": 100.0}, {"produto": "B", "receita": 50.0}],
        category="sales",
        client=None,
    )

    assert "2 registro(s)" in result


def test_interpret_stream_without_client_yields_fallback_chunk():
    async def _collect() -> list[str]:
        chunks: list[str] = []
        async for chunk in interpret_stream(
            question="Qual o ticket medio por estado?",
            rows=[{"estado": "SP", "ticket_medio": 120.0}],
            category="customers",
            client=None,
        ):
            chunks.append(chunk)
        return chunks

    chunks = asyncio.run(_collect())

    assert len(chunks) == 1
    assert "1 registro(s)" in chunks[0]


def test_suggest_followups_without_data_returns_three_items():
    followups = suggest_followups(
        question="Qual foi a receita?",
        data=[],
        category="sales",
    )

    assert len(followups) == 3


def test_suggest_followups_sales_with_state_column_is_contextual():
    followups = suggest_followups(
        question="Quais os top produtos por receita?",
        data=[{"estado": "SP", "produto": "A", "receita": 100.0}],
        category="sales",
        interpretation="Produto A lidera a receita.",
    )

    assert len(followups) == 3
    combined = " ".join(followups).lower()
    assert "estado" in combined or "periodo" in combined or "top" in combined
