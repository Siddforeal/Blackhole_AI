"""
Deterministic brain chat for Blackhole AI Workbench.

This module reads existing planning artifacts from a state directory and creates
a local, non-provider chat reply. It does not call LLM providers, send requests,
execute shell commands, launch browsers, use Kali tools, mutate targets, or
bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
import json


@dataclass(frozen=True)
class BrainChatReply:
    question: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    decision: str
    approval_status: str
    execution_gate: str
    execution_allowed: bool
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_brain_chat_reply(question: str, state_dir: Path) -> BrainChatReply:
    brain = _read_json(state_dir / "03-ai-brain.json")
    decision = _read_json(state_dir / "06-brain-decision.json")
    approval = _read_json(state_dir / "07-brain-approval.json")
    gate = _read_json(state_dir / "09-tool-execution-gate.json")

    focus = _first_focus_item(brain)

    target_name = str(
        brain.get("target_name")
        or decision.get("target_name")
        or approval.get("target_name")
        or gate.get("target_name")
        or "unknown-target"
    )

    focus_endpoint = (
        focus.get("endpoint")
        or decision.get("focus_endpoint")
        or approval.get("focus_endpoint")
        or gate.get("focus_endpoint")
    )
    focus_endpoint = str(focus_endpoint) if focus_endpoint else None

    decision_value = str(decision.get("decision") or "unknown")
    approval_status = str(approval.get("approval_status") or "unknown")
    execution_gate = str(gate.get("gate_decision") or "unknown")
    execution_allowed = bool(gate.get("execution_allowed", False))

    answer = _answer_question(
        question=question,
        target_name=target_name,
        focus=focus,
        decision=decision_value,
        approval_status=approval_status,
        execution_gate=execution_gate,
        execution_allowed=execution_allowed,
    )

    return BrainChatReply(
        question=question,
        answer=answer,
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        decision=decision_value,
        approval_status=approval_status,
        execution_gate=execution_gate,
        execution_allowed=execution_allowed,
    )


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def _first_focus_item(brain: dict[str, Any]) -> dict[str, Any]:
    queue = brain.get("focus_queue") or []
    if queue and isinstance(queue[0], dict):
        return queue[0]
    return {}


def _answer_question(
    question: str,
    target_name: str,
    focus: dict[str, Any],
    decision: str,
    approval_status: str,
    execution_gate: str,
    execution_allowed: bool,
) -> str:
    q = question.strip().lower()
    endpoint = str(focus.get("endpoint") or "none")
    band = str(focus.get("priority_band") or "unknown")
    score = str(focus.get("priority_score") or 0)
    reason = str(focus.get("reason") or "No focus reason is available.")

    if q in {"hello", "hi", "hey", "yo"}:
        return "\n".join(
            [
                "Hello Sidd. I am Blackhole AI Workbench.",
                "",
                "Current mode: planning-only, human-in-the-loop, scope-safe.",
                f"Target: {target_name}",
                f"Recommended focus endpoint: {endpoint}",
                f"Priority: {band} / {score}",
                f"Current decision: {decision}",
                f"Approval status: {approval_status}",
                f"Execution gate: {execution_gate}",
                f"Execution allowed: {execution_allowed}",
                "",
                "I can help plan the next safe validation step, but I will not execute curl, browser, Kali, network, shell, or LLM-provider actions.",
            ]
        )

    if "status" in q or "where" in q:
        return "\n".join(
            [
                f"Target `{target_name}` is loaded.",
                f"Current focus endpoint is `{endpoint}` with priority `{band}/{score}`.",
                f"Decision is `{decision}`.",
                f"Approval status is `{approval_status}`.",
                f"Execution gate is `{execution_gate}`.",
                f"Execution allowed is `{execution_allowed}`.",
            ]
        )

    if "next" in q or "do" in q:
        return "\n".join(
            [
                "Next safe step:",
                "",
                "1. Confirm scope and authorization.",
                "2. Confirm controlled accounts, objects, tenants, projects, or files.",
                "3. Confirm redaction plan.",
                "4. Confirm non-destructive validation.",
                "5. Keep execution disabled until a future explicit human-approved execution layer exists.",
            ]
        )

    if "why" in q or "focus" in q:
        return "\n".join(
            [
                f"Blackhole is focusing on `{endpoint}`.",
                f"Reason: {reason}",
                f"Priority: `{band}/{score}`.",
                "This is not a confirmed vulnerability. It is only a planning signal.",
            ]
        )

    if "execute" in q or "run" in q or "curl" in q or "browser" in q or "kali" in q:
        return "\n".join(
            [
                "Execution is not allowed from brain-chat.",
                f"Execution gate: `{execution_gate}`.",
                f"Execution allowed: `{execution_allowed}`.",
                "Blackhole can only provide planning guidance until a future explicit human-approved execution layer exists.",
            ]
        )

    return "\n".join(
        [
            "I can answer planning-only questions from the current brain state.",
            "",
            "Try:",
            "- hello",
            "- status",
            "- what should we do next?",
            "- why this endpoint?",
            "- can we execute?",
        ]
    )
