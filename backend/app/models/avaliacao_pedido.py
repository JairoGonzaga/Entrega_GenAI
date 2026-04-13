"""
Modelo de Avaliação de Pedido para armazenar avaliações e comentários dos clientes sobre seus pedidos.
Cada avaliação está associada a um pedido específico e pode incluir uma nota, um título de comentário,
o comentário em si, e as datas de quando o comentário foi feito e quando uma resposta foi dada (se aplicável).
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import BaseDeclarativa


class AvaliacaoPedido(BaseDeclarativa):
    __tablename__ = "avaliacoes_pedidos"

    id_avaliacao: Mapped[str] = mapped_column(String(32), primary_key=True)
    id_pedido: Mapped[str] = mapped_column(
        String(32), ForeignKey("pedidos.id_pedido"), nullable=False
    )
    avaliacao: Mapped[int] = mapped_column(Integer)
    titulo_comentario: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    comentario: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    data_comentario: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    data_resposta: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
