"""Codigo responsavel por interpretar os resultados das consultas e
gerar insights acionaveis para o usuario, alem de sugerir perguntas
de follow-up baseadas no contexto."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from typing import AsyncGenerator

from google import genai

from app.config import settings

logger = logging.getLogger("agent")
MODEL_NAME = settings.gemini_model


def _fallback_interpretation(question: str, rows: list[dict]) -> str:
    # Interpretacao simples quando o cliente Gemini nao esta disponivel, ou quando a consulta nao retorna dados.
    if not rows:
        return "A consulta nao retornou resultados para os filtros informados."

    columns = list(rows[0].keys()) if rows else []
    if columns:
        return (
            f"A consulta retornou {len(rows)} registro(s) para a pergunta '{question}'. "
            f"Colunas principais: {', '.join(columns[:5])}."
        )

    return f"A consulta retornou {len(rows)} registro(s)."


def _build_interpretation_prompt(question: str, rows: list[dict], category: str) -> str:
    # Prompt para interpretacao dos resultados, com dicas de foco baseadas na categoria detectada.
    category_hint = {
        "sales": "Foque em receita, volume e itens de maior impacto.",
        "logistics": "Foque em prazos, atrasos e desempenho de entrega.",
        "reviews": "Foque em satisfacao, notas e sinais de problema.",
        "customers": "Foque em comportamento, ticket e distribuicao geográfica.",
        "sellers": "Foque em performance e comparativo entre vendedores.",
    }.get(category, "Foque em insights acionaveis para negocio.")

    return (
        "Voce e um analista de dados de e-commerce. "
        "Resuma os resultados em PT-BR, em no maximo 5 linhas, com linguagem objetiva e acionavel.\n\n"
        f"Categoria: {category}\n"
        f"Contexto: {category_hint}\n"
        f"Pergunta original: {question}\n"
        f"Total de registros: {len(rows)}\n"
        f"Amostra JSON: {json.dumps(rows[:20], ensure_ascii=False)}"
    )


def interpret_sync(question: str, rows: list[dict], category: str, client: genai.Client | None) -> str:
    """Constrói a interpretação textual dos resultados de forma sincrona."""
    if client is None:
        return _fallback_interpretation(question, rows)

    prompt = _build_interpretation_prompt(question, rows, category)
    response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
    text = (response.text or "").strip()
    return text or _fallback_interpretation(question, rows)


async def interpret_stream(
    question: str,
    rows: list[dict],
    category: str,
    client: genai.Client | None,
) -> AsyncGenerator[str, None]:
    """Interpreta os resultados de forma incremental,
      emitindo chunks de texto conforme chegam do modelo."""
    if client is None:
        yield _fallback_interpretation(question, rows)
        return

    prompt = _build_interpretation_prompt(question, rows, category)
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
            yield _fallback_interpretation(question, rows)
            break
        if payload:
            yield payload


def suggest_followups(
    question: str,
    data: list[dict],
    category: str = "general",
    interpretation: str | None = None,
) -> list[str]:
    """Gera sugestões de perguntas de follow-up baseadas na pergunta original,
      nos dados retornados, na categoria detectada e na interpretação gerada. 
      As sugestões são focadas em aprofundar a análise ou explorar novas perspectivas relevantes para o usuário."""
    if not data:
        return [
            "Quer testar a mesma pergunta com outro periodo?",
            "Quer aplicar um filtro por categoria de produto?",
            "Quer ver esse indicador segmentado por estado?",
        ]

    columns = {str(col).lower() for col in data[0].keys()}
    followups: list[str] = []

    by_category = {
        "sales": [
            "Quer quebrar esse resultado por categoria de produto?",
            "Quer comparar essa metrica com o periodo anterior?",
            "Quer ver os itens que mais contribuem para a receita?",
        ],
        "logistics": [
            "Quer segmentar os prazos por estado do cliente?",
            "Quer analisar apenas pedidos com atraso?",
            "Quer comparar desempenho entre vendedores?",
        ],
        "reviews": [
            "Quer focar apenas em avaliacoes negativas?",
            "Quer ver a evolucao das notas por periodo?",
            "Quer comparar satisfacao por categoria de produto?",
        ],
        "customers": [
            "Quer detalhar esse comportamento por estado?",
            "Quer listar os clientes com maior ticket medio?",
            "Quer comparar recorrencia entre regioes?",
        ],
        "sellers": [
            "Quer ranquear vendedores por faturamento?",
            "Quer cruzar performance de vendedor com nota media?",
            "Quer analisar atraso por vendedor?",
        ],
    }

    followups.extend(by_category.get(category, []))

    if "estado" in columns and all("estado" not in f.lower() for f in followups):
        followups.append("Quer ver esse resultado segmentado por estado?")

    has_date_column = any(token in col for col in columns for token in ["data", "timestamp", "date"])
    if has_date_column and all("periodo" not in f.lower() for f in followups):
        followups.append("Quer comparar esse indicador com o periodo anterior?")

    if interpretation and "top" in question.lower() and all("top" not in f.lower() for f in followups):
        followups.append("Quer detalhar os TOP 10 elementos desse resultado?")

    # Remove duplicados mantendo ordem e devolve no maximo 3 sugestoes.
    seen: set[str] = set()
    unique = []
    for item in followups:
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            unique.append(item.strip())

    if len(unique) < 3:
        unique.extend(
            [
                "Quer aplicar filtros adicionais para refinar a analise?",
                "Quer transformar isso em um ranking dos principais resultados?",
                "Quer exportar uma visao resumida para tomada de decisao?",
            ]
        )

    return unique[:3]
