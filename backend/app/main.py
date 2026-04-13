"""Entrada da API: cria app, CORS, rotas e tarefas de startup."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401
from app.data_ingestion import popular_banco_a_partir_csv
from app.database import BaseDeclarativa, motor
from app.routers import roteador_produtos

app = FastAPI(
    title="Sistema de Compras Online",
    description="API para gerenciamento de pedidos, produtos, consumidores e vendedores.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(roteador_produtos, prefix="/api")


def _criar_indices() -> None:
    """
    Cria indices SQL para acelerar buscas comuns no catalogo.
    Garante idempotencia usando IF NOT EXISTS em cada indice.
    """
    comandos = [
        "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON produtos(categoria_produto)",
        "CREATE INDEX IF NOT EXISTS idx_produtos_nome ON produtos(nome_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto ON itens_pedidos(id_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto_pedido ON itens_pedidos(id_produto, id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON itens_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_avaliacoes_pedido ON avaliacoes_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_pedidos_data_compra ON pedidos(pedido_compra_timestamp)",
    ]

    with motor.begin() as conexao:
        for comando in comandos:
            conexao.execute(text(comando))


@app.on_event("startup")
def evento_startup() -> None:
    """
    Executa rotinas de inicializacao quando a API sobe.
    Cria tabelas, popula dados de exemplo e aplica indices.
    """
    BaseDeclarativa.metadata.create_all(bind=motor)
    popular_banco_a_partir_csv()
    _criar_indices()


@app.get("/", tags=["Health"])
def verificar_saude():
    """
    Endpoint simples de healthcheck para monitoramento.
    Retorna um payload minimo indicando que a API esta ativa.
    """
    return {"status": "ok", "message": "API rodando com sucesso!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
