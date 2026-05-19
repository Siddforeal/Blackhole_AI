"""
Brain chat case dashboard review packet.

This module turns a brain-chat case dashboard into a deterministic local
review packet. It does not call providers, execute tools, send requests,
launch browsers, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_case_dashboard import (
    BrainChatCaseDashboard,
    build_brain_chat_case_dashboard,
)
from bugintel.core.brain_chat_session import BrainChatSession


@dataclass(frozen=True)
class BrainChatCaseDashboardReviewPacket:
    target_name: str
    focus_endpoint: str | None
    reportable: bool
    execution_allowed: bool
    review_status: str
    blockers: tuple[str, ...]
    required_evidence: tuple[str, ...]
    safe_next_action: str
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-dashboard-review-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_dashboard_review_packet",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "reportable": self.reportable,
            "execution_allowed": self.execution_allowed,
            "review_status": self.review_status,
            "blockers": list(self.blockers),
            "required_evidence": list(self.required_evidence),
            "safe_next_action": self.safe_next_action,
            "rejected_actions": list(self.rejected_actions),
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

    def to_markdown(self, title: str = "Brain Chat Case Dashboard Review Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Review Status",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Review status: `{self.review_status}`",
            f"- Reportable: `{self.reportable}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            "- Planning-only: true",
            "",
            "## Blockers",
            "",
        ]

        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Evidence", ""])
        for item in self.required_evidence:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safe Next Action",
                "",
                f"- {self.safe_next_action}",
                "",
                "## Rejected Actions",
                "",
            ]
        )

        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This review packet is local and planning-only.",
                "- It does not execute tools, send requests, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_chat_case_dashboard_review_packet(
    session: BrainChatSession,
    source: str = "brain-chat-case-dashboard-review-packet",
) -> BrainChatCaseDashboardReviewPacket:
    dashboard = build_brain_chat_case_dashboard(session)
    return build_review_packet_from_dashboard(dashboard, source=source)


def build_review_packet_from_dashboard(
    dashboard: BrainChatCaseDashboard,
    source: str = "brain-chat-case-dashboard-review-packet",
) -> BrainChatCaseDashboardReviewPacket:
    blockers = _blockers(dashboard)
    review_status = "blocked-review" if blockers else "ready-for-local-evidence-review"

    return BrainChatCaseDashboardReviewPacket(
        target_name=dashboard.target_name,
        focus_endpoint=dashboard.focus_endpoint,
        reportable=False,
        execution_allowed=dashboard.execution_allowed,
        review_status=review_status,
        blockers=tuple(blockers),
        required_evidence=dashboard.next_evidence,
        safe_next_action=_safe_next_action(dashboard, blockers),
        rejected_actions=(
            "Do not run network, browser, curl, Kali, or shell actions from this review packet.",
            "Do not submit a report from dashboard state alone.",
            "Do not claim vulnerability confirmation without local validation evidence.",
        ),
        source=source,
    )


def _blockers(dashboard: BrainChatCaseDashboard) -> list[str]:
    blockers: list[str] = []

    if not dashboard.execution_allowed:
        blockers.append("Execution is still blocked by the latest gate state.")

    if not dashboard.focus_endpoint:
        blockers.append("No focus endpoint is set for the current case.")

    if not dashboard.next_evidence:
        blockers.append("No required evidence list is available.")

    if not dashboard.reportable:
        blockers.append("Dashboard state is not reportable by itself.")

    return blockers


def _safe_next_action(dashboard: BrainChatCaseDashboard, blockers: list[str]) -> str:
    if blockers:
        return "Resolve the listed blockers and collect local evidence before validation."
    return "Review required evidence locally and prepare a human approval request."
