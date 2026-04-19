"""Camada HTTP do agent Text-to-SQL.

Este arquivo concentra apenas endpoints e validacoes de entrada.
A logica de negocio fica em modulos dedicados para facilitar manutencao e testes.
"""

import asyncio

from google import genai
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from . import guardrails
from .intent import CATEGORIES
from .pipeline import run_query_pipeline, stream_response

router = APIRouter(prefix="/agent", tags=["agent"])


class QueryRequest(BaseModel):
    """Payload de consulta em linguagem natural."""

    question: str


def _run_query_pipeline(question: str, session_id: str, client: genai.Client | None) -> dict:
    """Wrapper para manter compatibilidade com testes existentes."""
    return run_query_pipeline(question, session_id, client)


async def _stream_response(question: str, session_id: str, client: genai.Client | None):
    """Wrapper para manter compatibilidade com testes existentes."""
    async for event in stream_response(question, session_id, client):
        yield event


@router.post("/query")
async def query(
    req: QueryRequest,
    request: Request,
    x_session_id: str = Header(default="default", alias="X-Session-ID"),
):
    """Endpoint principal com resposta JSON."""
    session_id = (x_session_id or "default").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    question = guardrails.validate_user_input(req.question)
    client = getattr(request.app.state, "gemini_client", None)
    return await asyncio.to_thread(_run_query_pipeline, question, session_id, client)


@router.post("/query/stream")
async def query_stream(
    req: QueryRequest,
    request: Request,
    x_session_id: str = Header(default="default", alias="X-Session-ID"),
):
    """Endpoint SSE para envio incremental de resposta."""
    session_id = (x_session_id or "default").strip()
    if not session_id:
        raise HTTPException(status_code=400, detail="Invalid session_id")

    question = guardrails.validate_user_input(req.question)
    client = getattr(request.app.state, "gemini_client", None)
    return StreamingResponse(
        _stream_response(question, session_id, client),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get("/suggestions")
def suggestions():
    """Retorna perguntas sugeridas agrupadas por categoria de negocio."""
    return {
        "sales": [
            "Top 10 produtos mais vendidos",
            "Receita total por categoria",
            "Ticket medio por estado",
        ],
        "logistics": [
            "Percentual de pedidos entregues no prazo",
            "Tempo medio de entrega por estado",
            "Status de pedidos por mes",
        ],
        "reviews": [
            "Media de avaliacao por categoria",
            "Top vendedores por nota media",
            "Taxa de avaliacao negativa por estado",
        ],
        "customers": [
            "Estados com maior volume de pedidos",
            "Clientes com maior receita acumulada",
            "Distribuicao de ticket medio por regiao",
        ],
        "sellers": [
            "Top 10 vendedores por faturamento",
            "Vendedores com maior taxa de entrega no prazo",
            "Comparativo de avaliacao entre vendedores",
        ],
        "general": [
            "Quais sao os 10 produtos com maior receita?",
            "Qual o faturamento total no periodo?",
            "Qual categoria tem maior ticket medio?",
        ],
        "available_categories": sorted(list(CATEGORIES.keys()) + ["general"]),
    }
