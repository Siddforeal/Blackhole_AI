"""
Brain chat case dashboard.

This module combines a brain-chat session summary and next-step plan into a
single local case dashboard. It does not call providers, execute tools, send
requests, launch browsers, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_session import BrainChatSession, summarize_brain_chat_session
from bugintel.core.brain_chat_session_next_step import build_brain_chat_session_next_step_plan


@dataclass(frozen=True)
class BrainChatCaseDashboard:
    target_name: str
    focus_endpoint: str | None
    latest_question: str | None
    turn_count: int
    decision: str
    approval_status: str
    execution_gate: str
    execution_allowed: bool
    reportable: bool
    current_blocker: str
    next_question: str
    next_evidence: tuple[str, ...]
    repeated_questions: tuple[str, ...]
    recommendation: str
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-dashboard"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_dashboard",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "latest_question": self.latest_question,
            "turn_count": self.turn_count,
            "decision": self.decision,
            "approval_status": self.approval_status,
            "execution_gate": self.execution_gate,
            "execution_allowed": self.execution_allowed,
            "reportable": self.reportable,
            "current_blocker": self.current_blocker,
            "next_question": self.next_question,
            "next_evidence": list(self.next_evidence),
            "repeated_questions": list(self.repeated_questions),
            "recommendation": self.recommendation,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Case Dashboard") -> str:
        lines = [
            f"# {title}",
            "",
            "## Current Case",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Turns: `{self.turn_count}`",
            f"- Latest question: `{self.latest_question or 'none'}`",
            "",
            "## Gate State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Approval status: `{self.approval_status}`",
            f"- Execution gate: `{self.execution_gate}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Reportable: `{self.reportable}`",
            "",
            "## Next Step",
            "",
            f"- Recommendation: `{self.recommendation}`",
            f"- Current blocker: {self.current_blocker}",
            f"- Next question: `{self.next_question}`",
            "",
            "## Next Evidence",
            "",
        ]

        for item in self.next_evidence:
            lines.append(f"- {item}")

        lines.extend(["", "## Repeated Questions", ""])
        if self.repeated_questions:
            for item in self.repeated_questions:
                lines.append(f"- `{item}`")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This dashboard is local and planning-only.",
                "- It does not execute tools, send requests, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_chat_case_dashboard(
    session: BrainChatSession,
    source: str = "brain-chat-case-dashboard",
) -> BrainChatCaseDashboard:
    summary = summarize_brain_chat_session(session)
    next_step = build_brain_chat_session_next_step_plan(session)
    latest = session.turns[-1] if session.turns else None

    return BrainChatCaseDashboard(
        target_name=latest.target_name if latest else "unknown-target",
        focus_endpoint=summary.latest_focus_endpoint,
        latest_question=summary.latest_question,
        turn_count=summary.turn_count,
        decision=summary.latest_decision,
        approval_status=summary.latest_approval_status,
        execution_gate=summary.latest_execution_gate,
        execution_allowed=summary.latest_execution_allowed,
        reportable=False,
        current_blocker=next_step.current_blocker,
        next_question=next_step.next_question,
        next_evidence=next_step.next_evidence,
        repeated_questions=summary.repeated_questions,
        recommendation=next_step.recommendation,
        source=source,
    )
