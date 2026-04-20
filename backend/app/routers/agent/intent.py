"""Categorias e palavras-chave para apoiar deteccao de intencao."""

CATEGORIES = {
    "sales": {
        "keywords": ["vendido", "receita", "produto", "top", "faturamento", "mais vendido", "venda", "sold", "revenue", "top-selling", "billing"],
        "context": "Foque em metricas de vendas e receita.",
    },
    "logistics": {
        "keywords": ["prazo", "atraso", "entrega", "status", "enviado", "entregue", "logistica", "deadline", "delay", "delivery", "shipped"],
        "context": "Foque em status de entrega e desempenho logistico.",
    },
    "reviews": {
        "keywords": ["avaliacao", "nota", "satisfacao", "negativa", "rating", "review", "comentario", "feedback", "rating", "satisfaction"],
        "context": "Foque em satisfacao do cliente e avaliacoes.",
    },
    "customers": {
        "keywords": ["consumidor", "cliente", "estado", "regiao", "ticket", "volume", "consumer", "customer", "region", "state"],
        "context": "Foque em comportamento de clientes e demografia.",
    },
    "sellers": {
        "keywords": ["vendedor", "seller", "loja", "store", "shop"],
        "context": "Foque em desempenho de vendedores.",
    },
}


def detect_category(question: str) -> str:
    """Detecta categoria da consulta a partir de palavras-chave."""
    lower = question.lower()
    for category, cfg in CATEGORIES.items():
        if any(keyword in lower for keyword in cfg["keywords"]):
            return category
    return "general"
