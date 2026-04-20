"""Historico de conversa em memoria por session_id.
Turno = pergunta do usuario + resposta do agente (sql, dados, interpretacao)."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
import threading


@dataclass
class Turn:
    question: str
    sql: str
    data: list[dict]
    interpretation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


_history: dict[str, list[Turn]] = defaultdict(list)
_locks: dict[str, threading.Lock] = defaultdict(threading.Lock)
MAX_TURNS = 10


def add_turn(session_id: str, turn: Turn) -> None:
    """Adiciona um turno ao historico mantendo o limite maximo de turnos."""
    turn.data = turn.data[:5]
    with _locks[session_id]:
        _history[session_id].append(turn)
        if len(_history[session_id]) > MAX_TURNS:
            _history[session_id].pop(0)


def get_history(session_id: str) -> list[Turn]:
    """Recupera o historico de conversa de uma sessao."""
    with _locks[session_id]:
        return list(_history.get(session_id, []))


def format_for_prompt(session_id: str) -> str:
    """Formata historico recente da conversa para inclusao no prompt."""
    turns = get_history(session_id)[-3:]
    if not turns:
        return ""

    lines = ["Historico recente da conversa:"]
    for t in turns:
        lines.append(f"  Usuario perguntou: {t.question}")
        lines.append(f"  SQL utilizado: {t.sql}")

    return "\n".join(lines)
