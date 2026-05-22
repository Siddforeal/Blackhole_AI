"""
Brain chat evidence checklist tracker.

This module turns a brain-chat dashboard review packet into a deterministic
local evidence checklist. It does not collect evidence, execute tools, send
requests, call providers, mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from bugintel.core.brain_chat_case_dashboard_review_packet import (
    BrainChatCaseDashboardReviewPacket,
    build_brain_chat_case_dashboard_review_packet,
)
from bugintel.core.brain_chat_session import BrainChatSession


VALID_EVIDENCE_STATUSES = ("missing", "collected", "review-needed", "blocked")


@dataclass(frozen=True)
class EvidenceChecklistItem:
    label: str
    status: str = "missing"
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "label": self.label,
            "status": self.status,
            "notes": self.notes,
        }


@dataclass(frozen=True)
class BrainChatEvidenceChecklist:
    target_name: str
    focus_endpoint: str | None
    review_status: str
    reportable: bool
    execution_allowed: bool
    blockers: tuple[str, ...]
    items: tuple[EvidenceChecklistItem, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-evidence-checklist"

    @property
    def missing_count(self) -> int:
        return self._count("missing")

    @property
    def collected_count(self) -> int:
        return self._count("collected")

    @property
    def review_needed_count(self) -> int:
        return self._count("review-needed")

    @property
    def blocked_count(self) -> int:
        return self._count("blocked")

    @property
    def complete(self) -> bool:
        return bool(self.items) and all(item.status == "collected" for item in self.items)

    def _count(self, status: str) -> int:
        return sum(1 for item in self.items if item.status == status)

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_checklist",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "review_status": self.review_status,
            "reportable": self.reportable,
            "execution_allowed": self.execution_allowed,
            "blockers": list(self.blockers),
            "items": [item.to_dict() for item in self.items],
            "counts": {
                "total": len(self.items),
                "missing": self.missing_count,
                "collected": self.collected_count,
                "review_needed": self.review_needed_count,
                "blocked": self.blocked_count,
            },
            "complete": self.complete,
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
                "evidence_collection": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Evidence Checklist") -> str:
        lines = [
            f"# {title}",
            "",
            "## Case",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Review status: `{self.review_status}`",
            f"- Reportable: `{self.reportable}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Complete: `{self.complete}`",
            "",
            "## Counts",
            "",
            f"- Total: `{len(self.items)}`",
            f"- Missing: `{self.missing_count}`",
            f"- Collected: `{self.collected_count}`",
            f"- Review needed: `{self.review_needed_count}`",
            f"- Blocked: `{self.blocked_count}`",
            "",
            "## Evidence Items",
            "",
        ]

        for index, item in enumerate(self.items, start=1):
            lines.append(f"{index}. [{item.status}] {item.label}")
            if item.notes:
                lines.append(f"   - Notes: {item.notes}")

        lines.extend(["", "## Blockers", ""])
        if self.blockers:
            for blocker in self.blockers:
                lines.append(f"- {blocker}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This checklist is local and planning-only.",
                "- It does not collect evidence, execute tools, send requests, call providers, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_brain_chat_evidence_checklist(
    session: BrainChatSession,
    item_statuses: Mapping[str, str] | None = None,
    item_notes: Mapping[str, str] | None = None,
    source: str = "brain-chat-evidence-checklist",
) -> BrainChatEvidenceChecklist:
    packet = build_brain_chat_case_dashboard_review_packet(session)
    return build_evidence_checklist_from_review_packet(
        packet,
        item_statuses=item_statuses,
        item_notes=item_notes,
        source=source,
    )


def build_evidence_checklist_from_review_packet(
    packet: BrainChatCaseDashboardReviewPacket,
    item_statuses: Mapping[str, str] | None = None,
    item_notes: Mapping[str, str] | None = None,
    source: str = "brain-chat-evidence-checklist",
) -> BrainChatEvidenceChecklist:
    statuses = dict(item_statuses or {})
    notes = dict(item_notes or {})

    items = tuple(
        EvidenceChecklistItem(
            label=label,
            status=_normalize_status(statuses.get(label, "missing")),
            notes=notes.get(label, ""),
        )
        for label in packet.required_evidence
    )

    return BrainChatEvidenceChecklist(
        target_name=packet.target_name,
        focus_endpoint=packet.focus_endpoint,
        review_status=packet.review_status,
        reportable=packet.reportable,
        execution_allowed=packet.execution_allowed,
        blockers=packet.blockers,
        items=items,
        source=source,
    )


def _normalize_status(status: str) -> str:
    normalized = status.strip().lower().replace("_", "-")
    if normalized not in VALID_EVIDENCE_STATUSES:
        raise ValueError(
            f"Invalid evidence status: {status!r}. "
            f"Expected one of: {', '.join(VALID_EVIDENCE_STATUSES)}"
        )
    return normalized
