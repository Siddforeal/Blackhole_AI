"""
Brain handoff evidence checklist exporter.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts evidence gaps from a case_intake_brain_handoff artifact into a
manual checklist grouped by endpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainEvidenceChecklistItem:
    checklist_id: str
    endpoint: str
    gap_type: str
    description: str
    required_before_report: bool
    checked: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "checklist_id": self.checklist_id,
            "endpoint": self.endpoint,
            "gap_type": self.gap_type,
            "description": self.description,
            "required_before_report": self.required_before_report,
            "checked": self.checked,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class CaseIntakeBrainEvidenceChecklist:
    target_name: str
    handoff_status: str
    checklist_items: tuple[CaseIntakeBrainEvidenceChecklistItem, ...]
    endpoint_count: int
    evidence_gap_count: int
    required_before_report_count: int
    blocked: bool
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-evidence-checklist-exporter"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_evidence_checklist",
            "source": self.source,
            "target_name": self.target_name,
            "handoff_status": self.handoff_status,
            "checklist_items": [item.to_dict() for item in self.checklist_items],
            "endpoint_count": self.endpoint_count,
            "evidence_gap_count": self.evidence_gap_count,
            "required_before_report_count": self.required_before_report_count,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Evidence Checklist") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Target: `{self.target_name}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Endpoints with gaps: `{self.endpoint_count}`",
            f"- Evidence gaps: `{self.evidence_gap_count}`",
            f"- Required before report: `{self.required_before_report_count}`",
            f"- Blocked: `{self.blocked}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Safety",
            "",
            "- No network requests",
            "- No tool execution",
            "- No browser execution",
            "- No provider calls",
            "- No evidence collection",
            "- No target mutation",
            "- No report submission",
            "- No vulnerability confirmation",
            "",
            "## Checklist",
            "",
        ]

        if not self.checklist_items:
            lines.extend(
                [
                    "No evidence gaps are recorded in this handoff.",
                    "",
                    "Manual review is still required before validation or report drafting.",
                    "",
                ]
            )
            return "\n".join(lines).rstrip() + "\n"

        grouped: dict[str, list[CaseIntakeBrainEvidenceChecklistItem]] = {}
        for item in self.checklist_items:
            grouped.setdefault(item.endpoint or "unknown-endpoint", []).append(item)

        for endpoint, items in grouped.items():
            lines.extend([f"### `{endpoint}`", ""])
            for item in items:
                required = "required before report" if item.required_before_report else "optional"
                lines.extend(
                    [
                        f"- [ ] `{item.checklist_id}` `{item.gap_type}` — {item.description}",
                        f"  - Status: unchecked",
                        f"  - Requirement: {required}",
                        f"  - Execution state: `{item.execution_state}`",
                    ]
                )
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def export_case_intake_brain_handoff_evidence_checklist(
    handoff: dict[str, Any],
) -> CaseIntakeBrainEvidenceChecklist:
    handoff_data = handoff if isinstance(handoff, dict) else {}
    target_name = str(handoff_data.get("target_name") or "bug-bounty-target")
    handoff_status = str(handoff_data.get("status") or "unknown")

    if str(handoff_data.get("kind") or "") != "case_intake_brain_handoff":
        return CaseIntakeBrainEvidenceChecklist(
            target_name=target_name,
            handoff_status="blocked-invalid-case-intake-brain-handoff",
            checklist_items=(),
            endpoint_count=0,
            evidence_gap_count=0,
            required_before_report_count=0,
            blocked=True,
        )

    if _unsafe_handoff(handoff_data):
        return CaseIntakeBrainEvidenceChecklist(
            target_name=target_name,
            handoff_status="blocked-unsafe-case-intake-brain-handoff",
            checklist_items=(),
            endpoint_count=0,
            evidence_gap_count=0,
            required_before_report_count=0,
            blocked=True,
        )

    gaps = _objects(handoff_data.get("evidence_gaps"))
    checklist_items = tuple(_checklist_item(index, gap) for index, gap in enumerate(gaps, start=1))
    endpoints = {item.endpoint for item in checklist_items if item.endpoint}
    required_count = sum(1 for item in checklist_items if item.required_before_report)

    return CaseIntakeBrainEvidenceChecklist(
        target_name=target_name,
        handoff_status=handoff_status,
        checklist_items=checklist_items,
        endpoint_count=len(endpoints),
        evidence_gap_count=len(checklist_items),
        required_before_report_count=required_count,
        blocked=handoff_status.startswith("blocked-"),
    )


def _checklist_item(index: int, gap: dict[str, Any]) -> CaseIntakeBrainEvidenceChecklistItem:
    return CaseIntakeBrainEvidenceChecklistItem(
        checklist_id=f"EC-{index:03d}",
        endpoint=str(gap.get("endpoint") or "unknown-endpoint"),
        gap_type=str(gap.get("gap_type") or "unknown-gap"),
        description=str(gap.get("description") or "Evidence gap requires manual review."),
        required_before_report=bool(gap.get("required_before_report")),
    )


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _unsafe_handoff(handoff: dict[str, Any]) -> bool:
    safety = handoff.get("safety") if isinstance(handoff.get("safety"), dict) else {}
    unsafe_keys = (
        "network_requests",
        "tool_execution",
        "browser_execution",
        "llm_provider_calls",
        "provider_execution",
        "target_mutation",
        "evidence_collection",
        "validation_execution",
        "report_submission",
        "vulnerability_confirmation",
    )
    return any(bool(safety.get(key)) for key in unsafe_keys)


def _safety_metadata() -> dict[str, bool]:
    return {
        "local_only": True,
        "deterministic": True,
        "planning_only": True,
        "network_requests": False,
        "tool_execution": False,
        "browser_execution": False,
        "llm_provider_calls": False,
        "provider_execution": False,
        "target_mutation": False,
        "evidence_collection": False,
        "validation_execution": False,
        "report_submission": False,
        "vulnerability_confirmation": False,
        "requires_human_authorization_before_testing": True,
    }
