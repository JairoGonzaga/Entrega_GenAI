"""Exporta routers para registro no aplicativo FastAPI."""

from app.routers.agent import router as agent_router
from app.routers.produtos import router as products_router

__all__ = ["products_router", "agent_router"]
