"""Entrada da API: cria app, CORS, rotas e tarefas de startup."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401
from app.database import Base, engine
from app.routers import products_router


def _run_startup_tasks() -> None:
    """
    Executa rotinas de inicializacao ao subir a aplicacao.
    Garante schema e indices para operar com banco existente.
    """
    Base.metadata.create_all(bind=engine)
    _create_indexes()


@asynccontextmanager
async def lifespan(_: FastAPI):
    _run_startup_tasks()
    yield


app = FastAPI(
    title="Sistema de Compras Online",
    description="API para gerenciamento de pedidos, produtos, consumidores e vendedores.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(products_router, prefix="/api")


def _create_indexes() -> None:
    """
    Cria indices SQL para acelerar buscas comuns no catalogo.
    Garante idempotencia usando IF NOT EXISTS em cada indice.
    """
    comandos = [
        "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON dim_produtos(categoria_produto)",
        "CREATE INDEX IF NOT EXISTS idx_produtos_nome ON dim_produtos(nome_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto ON fat_itens_pedidos(id_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto_pedido ON fat_itens_pedidos(id_produto, id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON fat_itens_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_avaliacoes_pedido ON fat_avaliacoes_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_pedidos_data_compra ON fat_pedidos(pedido_compra_timestamp)",
    ]

    with engine.begin() as conexao:
        for comando in comandos:
            conexao.execute(text(comando))

@app.get("/", tags=["Health"])
def healthcheck():
    """
    Endpoint simples de healthcheck para monitoramento.
    Retorna um payload minimo indicando que a API esta ativa.
    """
    return {"status": "ok", "message": "API rodando com sucesso!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
