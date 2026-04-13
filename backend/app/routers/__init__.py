"""Exporta routers para registro no aplicativo FastAPI."""

from app.routers.produtos import router as roteador_produtos

__all__ = ["roteador_produtos"]
