"""
Brain chat session memory for Blackhole AI Workbench.

This module stores local deterministic brain-chat conversation turns. It does
not call LLM providers, send requests, execute shell commands, launch browsers,
use Kali tools, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
import json

from bugintel.core.brain_chat import BrainChatReply


@dataclass(frozen=True)
class BrainChatTurn:
    question: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    decision: str
    approval_status: str
    execution_gate: str
    execution_allowed: bool
    created_at: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainChatSession:
    turns: tuple[BrainChatTurn, ...] = field(default_factory=tuple)
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "turn_count": len(self.turns),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "turns": [turn.to_dict() for turn in self.turns],
        }


def load_brain_chat_session(path: Path) -> BrainChatSession:
    if not path.exists():
        return BrainChatSession()

    data = json.loads(path.read_text(encoding="utf-8"))
    turns = []

    for item in data.get("turns", []):
        turns.append(
            BrainChatTurn(
                question=str(item.get("question", "")),
                answer=str(item.get("answer", "")),
                target_name=str(item.get("target_name", "unknown-target")),
                focus_endpoint=item.get("focus_endpoint"),
                decision=str(item.get("decision", "unknown")),
                approval_status=str(item.get("approval_status", "unknown")),
                execution_gate=str(item.get("execution_gate", "unknown")),
                execution_allowed=bool(item.get("execution_allowed", False)),
                created_at=str(item.get("created_at", "")),
            )
        )

    return BrainChatSession(turns=tuple(turns))


def append_brain_chat_turn(session: BrainChatSession, reply: BrainChatReply) -> BrainChatSession:
    turn = BrainChatTurn(
        question=reply.question,
        answer=reply.answer,
        target_name=reply.target_name,
        focus_endpoint=reply.focus_endpoint,
        decision=reply.decision,
        approval_status=reply.approval_status,
        execution_gate=reply.execution_gate,
        execution_allowed=reply.execution_allowed,
        created_at=datetime.now(timezone.utc).isoformat(),
    )

    return BrainChatSession(turns=session.turns + (turn,))


def save_brain_chat_session(session: BrainChatSession, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def render_brain_chat_session_summary(session: BrainChatSession) -> str:
    lines = [
        "# Blackhole Brain Chat Session",
        "",
        f"- Turns: `{len(session.turns)}`",
        f"- Execution state: `{session.execution_state}`",
        "",
    ]

    for index, turn in enumerate(session.turns, start=1):
        lines.append(f"## Turn {index}")
        lines.append("")
        lines.append(f"- Question: `{turn.question}`")
        lines.append(f"- Target: `{turn.target_name}`")
        lines.append(f"- Focus endpoint: `{turn.focus_endpoint or 'none'}`")
        lines.append(f"- Decision: `{turn.decision}`")
        lines.append(f"- Approval status: `{turn.approval_status}`")
        lines.append(f"- Execution gate: `{turn.execution_gate}`")
        lines.append(f"- Execution allowed: `{turn.execution_allowed}`")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
