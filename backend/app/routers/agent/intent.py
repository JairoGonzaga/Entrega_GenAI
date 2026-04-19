"""Simple category detection by keywords."""

CATEGORIES = {
    "sales": {
        "keywords": ["vendido", "receita", "produto", "top", "faturamento", "mais vendido", "venda", "sold", "revenue", "top-selling", "billing"],
        "context": "Focus on sales and revenue metrics.",
    },
    "logistics": {
        "keywords": ["prazo", "atraso", "entrega", "status", "enviado", "entregue", "logistica", "deadline", "delay", "delivery", "shipped"],
        "context": "Focus on delivery status and performance.",
    },
    "reviews": {
        "keywords": ["avaliacao", "nota", "satisfacao", "negativa", "rating", "review", "comentario", "feedback", "rating", "satisfaction"],
        "context": "Focus on customer satisfaction and ratings.",
    },
    "customers": {
        "keywords": ["consumidor", "cliente", "estado", "regiao", "ticket", "volume", "consumer", "customer", "region", "state"],
        "context": "Focus on customer behavior and demographics.",
    },
    "sellers": {
        "keywords": ["vendedor", "seller", "loja", "store", "shop"],
        "context": "Focus on seller performance.",
    },
}


def detect_category(question: str) -> str:
    """Detect query category by keywords."""
    lower = question.lower()
    for category, cfg in CATEGORIES.items():
        if any(keyword in lower for keyword in cfg["keywords"]):
            return category
    return "general"
