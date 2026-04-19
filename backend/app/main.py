"""API entry point: creates app, CORS, routes and startup tasks."""

from contextlib import asynccontextmanager

from google import genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app import models  # noqa: F401
from app.config import settings
from app.database import Base, engine
from app.routers import agent_router, products_router


def _run_startup_tasks() -> None:
    """
    Run initialization routines when the application starts.
    Ensures schema and indexes for operation with existing database.
    """
    Base.metadata.create_all(bind=engine)
    _create_indexes()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _run_startup_tasks()

    api_key = settings.resolved_gemini_api_key
    app.state.gemini_client = genai.Client(api_key=api_key) if api_key else None
    yield


app = FastAPI(
    title="Online Shopping System",
    description="API for managing orders, products, customers and sellers.",
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
app.include_router(agent_router, prefix="/api")


def _create_indexes() -> None:
    """
    Create SQL indexes to speed up common catalog searches.
    Ensures idempotency using IF NOT EXISTS for each index.
    """
    commands = [
        "CREATE INDEX IF NOT EXISTS idx_produtos_categoria ON dim_produtos(categoria_produto)",
        "CREATE INDEX IF NOT EXISTS idx_produtos_nome ON dim_produtos(nome_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto ON fat_itens_pedidos(id_produto)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto_pedido ON fat_itens_pedidos(id_produto, id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON fat_itens_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_avaliacoes_pedido ON fat_avaliacoes_pedidos(id_pedido)",
        "CREATE INDEX IF NOT EXISTS idx_pedidos_data_compra ON fat_pedidos(pedido_compra_timestamp)",
    ]

    with engine.begin() as connection:
        for command in commands:
            connection.execute(text(command))

@app.get("/", tags=["Health"])
def healthcheck():
    """
    Simple health check endpoint for monitoring.
    Returns a minimal payload indicating the API is active.
    """
    return {"status": "ok", "message": "API running successfully!"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
