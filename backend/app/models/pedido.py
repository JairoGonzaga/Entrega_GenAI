"""Modelo de pedido com status e datas de compra/entrega."""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDeclarativa


class Pedido(BaseDeclarativa):
    __tablename__ = "pedidos"

    id_pedido: Mapped[str] = mapped_column(String(32), primary_key=True)
    id_consumidor: Mapped[str] = mapped_column(
        String(32), ForeignKey("consumidores.id_consumidor"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50))
    pedido_compra_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    pedido_entregue_timestamp: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_estimada_entrega: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    tempo_entrega_dias: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    tempo_entrega_estimado_dias: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diferenca_entrega_dias: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    entrega_no_prazo: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
