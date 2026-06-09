"""
Brain chat research hypothesis selection packet.

This module ranks and selects hypotheses from a local research hypothesis packet.
It does not browse, generate commands, execute tools, send requests, collect
evidence, validate findings, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from bugintel.core.brain_chat_research_hypothesis_packet import (
    BrainChatResearchHypothesisPacket,
)


@dataclass(frozen=True)
class SelectedResearchHypothesis:
    hypothesis_id: str
    title: str
    attack_surface: str
    hypothesis_type: str
    priority: str
    confidence: str
    selection_rank: int
    selection_score: int
    selection_reason: str
    evidence_needed: tuple[str, ...]
    allowed_local_checks: tuple[str, ...]
    tags: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "attack_surface": self.attack_surface,
            "hypothesis_type": self.hypothesis_type,
            "priority": self.priority,
            "confidence": self.confidence,
            "selection_rank": self.selection_rank,
            "selection_score": self.selection_score,
            "selection_reason": self.selection_reason,
            "evidence_needed": list(self.evidence_needed),
            "allowed_local_checks": list(self.allowed_local_checks),
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class BrainChatResearchHypothesisSelectionPacket:
    target_name: str
    packet_status: str
    hypothesis_packet_status: str
    selection_status: str
    selected_count: int
    selected_hypotheses: tuple[SelectedResearchHypothesis, ...]
    primary_hypothesis_id: str | None
    selection_gaps: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_actions: tuple[str, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-research-hypothesis-selection-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_research_hypothesis_selection_packet",
            "source": self.source,
            "target_name": self.target_name,
            "packet_status": self.packet_status,
            "hypothesis_packet_status": self.hypothesis_packet_status,
            "selection_status": self.selection_status,
            "selected_count": self.selected_count,
            "selected_hypotheses": [item.to_dict() for item in self.selected_hypotheses],
            "primary_hypothesis_id": self.primary_hypothesis_id,
            "selection_gaps": list(self.selection_gaps),
            "allowed_local_next_steps": list(self.allowed_local_next_steps),
            "rejected_actions": list(self.rejected_actions),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "web_browsing": False,
                "network_interaction": False,
                "target_mutation": False,
                "command_generation": False,
                "tool_execution": False,
                "browser_execution": False,
                "curl_execution": False,
                "kali_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Research Hypothesis Selection Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Packet State",
            "",
            f"- Target name: `{self.target_name}`",
            f"- Packet status: `{self.packet_status}`",
            f"- Hypothesis packet status: `{self.hypothesis_packet_status}`",
            f"- Selection status: `{self.selection_status}`",
            f"- Selected count: `{self.selected_count}`",
            f"- Primary hypothesis: `{self.primary_hypothesis_id or 'none'}`",
            "",
            "## Selected Hypotheses",
            "",
        ]

        if self.selected_hypotheses:
            for item in self.selected_hypotheses:
                lines.extend(
                    [
                        f"### Rank {item.selection_rank}: {item.hypothesis_id} - {item.title}",
                        "",
                        f"- Attack surface: `{item.attack_surface}`",
                        f"- Type: `{item.hypothesis_type}`",
                        f"- Priority: `{item.priority}`",
                        f"- Confidence: `{item.confidence}`",
                        f"- Selection score: `{item.selection_score}`",
                        f"- Selection reason: {item.selection_reason}",
                        "- Evidence needed:",
                    ]
                )
                for evidence in item.evidence_needed:
                    lines.append(f"  - {evidence}")

                lines.append("- Allowed local checks:")
                for check in item.allowed_local_checks:
                    lines.append(f"  - {check}")

                lines.append("- Tags:")
                for tag in item.tags:
                    lines.append(f"  - `{tag}`")

                lines.append("")
        else:
            lines.append("- none")
            lines.append("")

        lines.extend(["## Selection Gaps", ""])
        if self.selection_gaps:
            for item in self.selection_gaps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Local Next Steps", ""])
        for item in self.allowed_local_next_steps:
            lines.append(f"- {item}")

        lines.extend(["", "## Rejected Actions", ""])
        for item in self.rejected_actions:
            lines.append(f"- {item}")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This packet is local, deterministic, and planning-only.",
                "- It does not browse, generate commands, execute tools, collect evidence, validate, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_research_hypothesis_selection_packet(
    hypothesis_packet: BrainChatResearchHypothesisPacket,
    max_selected: int = 3,
    source: str = "brain-chat-research-hypothesis-selection-packet",
) -> BrainChatResearchHypothesisSelectionPacket:
    data = hypothesis_packet.to_dict()
    target_name = str(data.get("target_name") or "unknown-target")
    hypothesis_packet_status = str(data.get("packet_status") or "unknown")
    raw_hypotheses = data.get("hypotheses") if isinstance(data.get("hypotheses"), list) else []

    if hypothesis_packet_status != "ready-for-hypothesis-review":
        selected: tuple[SelectedResearchHypothesis, ...] = ()
        selection_gaps = (
            f"Hypothesis packet is not ready: {hypothesis_packet_status}.",
            "Resolve hypothesis packet blockers before selecting a research focus.",
        )
        selection_status = "blocked-pending-ready-hypothesis-packet"
    else:
        ranked = sorted(
            (item for item in raw_hypotheses if isinstance(item, dict)),
            key=_ranking_key,
            reverse=True,
        )
        limited = ranked[: max(1, max_selected)]
        selected = tuple(
            _selected_hypothesis(item, rank=index)
            for index, item in enumerate(limited, start=1)
        )
        selection_gaps = tuple(_selection_gaps(selected))
        selection_status = "ready-for-local-investigation-planning" if selected and not selection_gaps else "review-needed-selection-gaps"

    primary = selected[0].hypothesis_id if selected else None
    packet_status = selection_status

    return BrainChatResearchHypothesisSelectionPacket(
        target_name=target_name,
        packet_status=packet_status,
        hypothesis_packet_status=hypothesis_packet_status,
        selection_status=selection_status,
        selected_count=len(selected),
        selected_hypotheses=selected,
        primary_hypothesis_id=primary,
        selection_gaps=selection_gaps,
        allowed_local_next_steps=tuple(_allowed_local_next_steps(selection_status)),
        rejected_actions=tuple(_rejected_actions()),
        source=source,
    )


def _selected_hypothesis(raw: dict[str, Any], rank: int) -> SelectedResearchHypothesis:
    score = _selection_score(raw)
    return SelectedResearchHypothesis(
        hypothesis_id=str(raw.get("hypothesis_id") or f"HYP-{rank:03d}"),
        title=str(raw.get("title") or "Untitled hypothesis"),
        attack_surface=str(raw.get("attack_surface") or "unknown attack surface"),
        hypothesis_type=str(raw.get("hypothesis_type") or "unknown"),
        priority=str(raw.get("priority") or "low"),
        confidence=str(raw.get("confidence") or "low"),
        selection_rank=rank,
        selection_score=score,
        selection_reason=_selection_reason(raw, score),
        evidence_needed=tuple(_string_list(raw.get("evidence_needed"))),
        allowed_local_checks=tuple(_string_list(raw.get("allowed_local_checks"))),
        tags=tuple(_string_list(raw.get("tags"))),
    )


def _ranking_key(raw: dict[str, Any]) -> tuple[int, int, int, str]:
    return (
        _selection_score(raw),
        _priority_weight(str(raw.get("priority") or "")),
        _confidence_weight(str(raw.get("confidence") or "")),
        str(raw.get("hypothesis_id") or ""),
    )


def _selection_score(raw: dict[str, Any]) -> int:
    score = 0
    score += _priority_weight(str(raw.get("priority") or "")) * 100
    score += _confidence_weight(str(raw.get("confidence") or "")) * 10
    score += _type_weight(str(raw.get("hypothesis_type") or ""))
    score += min(len(_string_list(raw.get("evidence_needed"))), 5)
    score += min(len(_string_list(raw.get("allowed_local_checks"))), 5)
    return score


def _priority_weight(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(value.lower(), 0)


def _confidence_weight(value: str) -> int:
    return {"high": 3, "medium": 2, "low": 1}.get(value.lower(), 0)


def _type_weight(value: str) -> int:
    weights = {
        "worker-execution-trust-boundary": 50,
        "input-to-filesystem-trust-boundary": 45,
        "authorization-admin-boundary": 40,
        "api-authentication-authorization-boundary": 30,
        "authentication-session-trust-boundary": 25,
        "parser-template-serialization-boundary": 20,
        "general-trust-boundary": 10,
    }
    return weights.get(value.lower(), 0)


def _selection_reason(raw: dict[str, Any], score: int) -> str:
    return (
        f"Selected because it is {raw.get('priority', 'unknown')} priority, "
        f"{raw.get('confidence', 'unknown')} confidence, and classified as "
        f"{raw.get('hypothesis_type', 'unknown')} with local-only evidence planning value "
        f"(score {score})."
    )


def _selection_gaps(selected: tuple[SelectedResearchHypothesis, ...]) -> list[str]:
    gaps: list[str] = []
    if not selected:
        gaps.append("No hypotheses were selected.")
        return gaps

    if not any(item.priority == "high" for item in selected):
        gaps.append("No high-priority hypothesis was selected.")
    if not any(item.hypothesis_type in {"worker-execution-trust-boundary", "input-to-filesystem-trust-boundary", "authorization-admin-boundary"} for item in selected):
        gaps.append("No execution, filesystem, or authorization boundary hypothesis was selected.")

    return gaps


def _allowed_local_next_steps(selection_status: str) -> list[str]:
    if selection_status == "ready-for-local-investigation-planning":
        return [
            "Build a local-only investigation planning packet for the primary selected hypothesis.",
            "Keep command generation, validation, evidence collection, reporting, and vulnerability confirmation behind later gates.",
        ]

    if selection_status == "review-needed-selection-gaps":
        return [
            "Review selection gaps and adjust local source or hypothesis coverage before investigation planning.",
        ]

    return [
        "Resolve hypothesis packet readiness before selecting a research focus.",
    ]


def _rejected_actions() -> list[str]:
    return [
        "Do not browse the web from this selection packet.",
        "Do not generate curl, Kali, browser, scanner, shell, or target interaction commands from this selection packet.",
        "Do not execute tools or collect evidence from a target from this selection packet.",
        "Do not submit a report from research hypothesis selection state alone.",
        "Do not claim vulnerability confirmation from research hypothesis selection state alone.",
        "Do not treat this selection packet as validation or runtime execution approval.",
    ]


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
