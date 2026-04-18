"""Modelo de pedido com status e datas de compra/entrega."""

from datetime import datetime, date
from typing import Optional

from sqlalchemy import String, Float, DateTime, Date, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "fat_pedidos"

    order_id: Mapped[str] = mapped_column("id_pedido", String(32), primary_key=True)
    customer_id: Mapped[str] = mapped_column(
        "id_consumidor", String(32), ForeignKey("dim_consumidores.id_consumidor"), nullable=False
    )
    status: Mapped[str] = mapped_column(String(50))
    purchase_timestamp: Mapped[Optional[datetime]] = mapped_column("pedido_compra_timestamp", DateTime, nullable=True)
    delivered_timestamp: Mapped[Optional[datetime]] = mapped_column("pedido_entregue_timestamp", DateTime, nullable=True)
    estimated_delivery_date: Mapped[Optional[date]] = mapped_column("data_estimada_entrega", Date, nullable=True)
    delivery_days: Mapped[Optional[float]] = mapped_column("tempo_entrega_dias", Float, nullable=True)
    estimated_delivery_days: Mapped[Optional[float]] = mapped_column("tempo_entrega_estimado_dias", Float, nullable=True)
    delivery_delay_days: Mapped[Optional[float]] = mapped_column("diferenca_entrega_dias", Float, nullable=True)
    on_time_delivery: Mapped[Optional[str]] = mapped_column("entrega_no_prazo", String(10), nullable=True)
