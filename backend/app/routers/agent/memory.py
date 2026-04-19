"""In-memory conversation history per session_id."""

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Turn:
    question: str
    sql: str
    data: list[dict]
    interpretation: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


_history: dict[str, list[Turn]] = defaultdict(list)
MAX_TURNS = 10


def add_turn(session_id: str, turn: Turn) -> None:
    """Add a turn to conversation history, maintaining max turns limit."""
    _history[session_id].append(turn)
    if len(_history[session_id]) > MAX_TURNS:
        _history[session_id].pop(0)


def get_history(session_id: str) -> list[Turn]:
    """Retrieve conversation history for a session."""
    return _history.get(session_id, [])


def format_for_prompt(session_id: str) -> str:
    """Format recent conversation history for inclusion in prompt."""
    turns = get_history(session_id)[-3:]
    if not turns:
        return ""

    lines = ["Recent conversation history:"]
    for t in turns:
        lines.append(f"  User asked: {t.question}")
        lines.append(f"  SQL used: {t.sql}")

    return "\n".join(lines)
