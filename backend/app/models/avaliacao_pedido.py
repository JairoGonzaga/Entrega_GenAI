"""
Modelo de Avaliação de Pedido para armazenar avaliações e comentários dos clientes sobre seus pedidos.
Cada avaliação está associada a um pedido específico e pode incluir uma nota, um título de comentário,
o comentário em si, e as datas de quando o comentário foi feito e quando uma resposta foi dada (se aplicável).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class OrderReview(Base):
    __tablename__ = "fat_avaliacoes_pedidos"

    review_id: Mapped[str] = mapped_column("id_avaliacao", String(32), primary_key=True)
    order_id: Mapped[str] = mapped_column(
        "id_pedido", String(32), ForeignKey("fat_pedidos.id_pedido"), nullable=False
    )
    rating: Mapped[int] = mapped_column("avaliacao", Integer)
    comment_title: Mapped[Optional[str]] = mapped_column("titulo_comentario", String(255), nullable=True)
    comment: Mapped[Optional[str]] = mapped_column("comentario", String(1000), nullable=True)
    comment_date: Mapped[Optional[datetime]] = mapped_column("data_comentario", DateTime, nullable=True)
    response_date: Mapped[Optional[datetime]] = mapped_column("data_resposta", DateTime, nullable=True)
