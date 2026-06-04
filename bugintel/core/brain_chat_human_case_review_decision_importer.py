"""
Brain chat human case review decision importer.

This module imports a local human case-review decision for a decision request.
It does not grant side-effectful approval, call LLM providers, execute tools,
collect evidence, send requests, mutate targets, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_human_case_review_decision_request import (
    BrainChatHumanCaseReviewDecisionRequest,
)


VALID_HUMAN_CASE_REVIEW_DECISIONS = frozenset(
    {
        "approved-for-next-local-planning-gate",
        "changes-requested",
        "rejected",
    }
)


@dataclass(frozen=True)
class BrainChatHumanCaseReviewDecisionImport:
    decision: str
    reviewer: str | None
    reason: str | None
    decision_request_status: str
    human_case_review_decision_ready: bool
    human_case_review_ready: bool
    effective_human_review_approval_granted: bool
    approval_granted: bool
    effective_next_local_planning_approval_granted: bool
    decision_effective: bool
    decision_import_status: str
    requested_human_decision_options: tuple[str, ...]
    reviewer_instructions: tuple[str, ...]
    required_human_checks: tuple[str, ...]
    packet_blockers: tuple[str, ...]
    decision_blockers: tuple[str, ...]
    missing_evidence_checklist: tuple[str, ...]
    blockers_checklist: tuple[str, ...]
    allowed_local_next_steps: tuple[str, ...]
    rejected_next_steps: tuple[str, ...]
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-human-case-review-decision-import"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_human_case_review_decision_import",
            "source": self.source,
            "decision": self.decision,
            "reviewer": self.reviewer,
            "reason": self.reason,
            "decision_request_status": self.decision_request_status,
            "human_case_review_decision_ready": self.human_case_review_decision_ready,
            "human_case_review_ready": self.human_case_review_ready,
            "effective_human_review_approval_granted": self.effective_human_review_approval_granted,
            "approval_granted": self.approval_granted,
            "effective_next_local_planning_approval_granted": self.effective_next_local_planning_approval_granted,
            "decision_effective": self.decision_effective,
            "decision_import_status": self.decision_import_status,
            "requested_human_decision_options": list(self.requested_human_decision_options),
            "reviewer_instructions": list(self.reviewer_instructions),
            "required_human_checks": list(self.required_human_checks),
            "packet_blockers": list(self.packet_blockers),
            "decision_blockers": list(self.decision_blockers),
            "missing_evidence_checklist": list(self.missing_evidence_checklist),
            "blockers_checklist": list(self.blockers_checklist),
            "allowed_local_next_steps": list(self.allowed_local_next_steps),
            "rejected_next_steps": list(self.rejected_next_steps),
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "deterministic": True,
                "planning_only": True,
                "decision_effective": self.decision_effective,
                "approval_granted": self.approval_granted,
                "effective_next_local_planning_approval_granted": self.effective_next_local_planning_approval_granted,
                "approval_side_effects": False,
                "human_approval_side_effects": False,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Human Case Review Decision Import") -> str:
        lines = [
            f"# {title}",
            "",
            "## Decision State",
            "",
            f"- Decision: `{self.decision}`",
            f"- Reviewer: `{self.reviewer or 'unknown'}`",
            f"- Reason: {self.reason or 'none'}",
            f"- Decision request status: `{self.decision_request_status}`",
            f"- Human case review decision ready: `{self.human_case_review_decision_ready}`",
            f"- Human case review ready: `{self.human_case_review_ready}`",
            f"- Effective human review approval granted: `{self.effective_human_review_approval_granted}`",
            f"- Approval granted: `{self.approval_granted}`",
            f"- Effective next local planning approval granted: `{self.effective_next_local_planning_approval_granted}`",
            f"- Decision effective: `{self.decision_effective}`",
            f"- Decision import status: `{self.decision_import_status}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Requested Human Decision Options",
            "",
        ]

        for item in self.requested_human_decision_options:
            lines.append(f"- `{item}`")

        lines.extend(["", "## Reviewer Instructions", ""])
        if self.reviewer_instructions:
            for item in self.reviewer_instructions:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Required Human Checks", ""])
        if self.required_human_checks:
            for item in self.required_human_checks:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Packet Blockers", ""])
        if self.packet_blockers:
            for item in self.packet_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Decision Blockers", ""])
        if self.decision_blockers:
            for item in self.decision_blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence Checklist", ""])
        if self.missing_evidence_checklist:
            for item in self.missing_evidence_checklist:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Blockers Checklist", ""])
        if self.blockers_checklist:
            for item in self.blockers_checklist:
                lines.append(f"- [ ] {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Allowed Local Next Steps", ""])
        if self.allowed_local_next_steps:
            for item in self.allowed_local_next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Rejected Next Steps", ""])
        if self.rejected_next_steps:
            for item in self.rejected_next_steps:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This decision import is local, deterministic, and planning-only.",
                "- It does not grant side-effectful approval.",
                "- It does not call providers, execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def import_human_case_review_decision_data(
    decision_request: BrainChatHumanCaseReviewDecisionRequest,
    decision_data: dict[str, Any],
    source: str = "brain-chat-human-case-review-decision-import",
) -> BrainChatHumanCaseReviewDecisionImport:
    decision = str(decision_data.get("decision") or "").strip()
    if decision not in VALID_HUMAN_CASE_REVIEW_DECISIONS:
        expected = ", ".join(sorted(VALID_HUMAN_CASE_REVIEW_DECISIONS))
        raise ValueError(f"Invalid human case review decision. Expected one of: {expected}")

    request_data = decision_request.to_dict()
    requested_options = tuple(_string_list(request_data.get("requested_human_decision_options")))
    if requested_options and decision not in requested_options:
        raise ValueError(
            "Invalid human case review decision for current request. "
            f"Allowed decisions: {', '.join(requested_options)}"
        )

    request_ready = bool(request_data.get("human_case_review_decision_ready", False))
    request_status = str(request_data.get("decision_request_status") or "unknown")
    safe = not _has_unsafe_flags(request_data)

    approved = decision == "approved-for-next-local-planning-gate"
    effective_approval = approved and request_ready and safe

    decision_import_status = _decision_import_status(
        decision=decision,
        request_ready=request_ready,
        request_status=request_status,
        effective_approval=effective_approval,
        safe=safe,
    )

    return BrainChatHumanCaseReviewDecisionImport(
        decision=decision,
        reviewer=_string_or_none(decision_data.get("reviewer")),
        reason=_string_or_none(decision_data.get("reason")),
        decision_request_status=request_status,
        human_case_review_decision_ready=request_ready and safe,
        human_case_review_ready=bool(request_data.get("human_case_review_ready", False)) and request_ready and safe,
        effective_human_review_approval_granted=bool(request_data.get("effective_human_review_approval_granted", False))
        and request_ready
        and safe,
        approval_granted=effective_approval,
        effective_next_local_planning_approval_granted=effective_approval,
        decision_effective=decision in {"changes-requested", "rejected"} or effective_approval,
        decision_import_status=decision_import_status,
        requested_human_decision_options=requested_options,
        reviewer_instructions=tuple(_string_list(request_data.get("reviewer_instructions"))),
        required_human_checks=tuple(_string_list(request_data.get("required_human_checks"))),
        packet_blockers=tuple(_string_list(request_data.get("packet_blockers"))),
        decision_blockers=tuple(_string_list(request_data.get("decision_blockers"))),
        missing_evidence_checklist=tuple(_string_list(request_data.get("missing_evidence_checklist"))),
        blockers_checklist=tuple(_string_list(request_data.get("blockers_checklist"))),
        allowed_local_next_steps=tuple(_allowed_next_steps(decision, decision_import_status)),
        rejected_next_steps=tuple(_rejected_next_steps(decision, decision_import_status)),
        validation_allowed=bool(request_data.get("validation_allowed", False)),
        runtime_execution_allowed=bool(request_data.get("runtime_execution_allowed", False)),
        report_submission_allowed=bool(request_data.get("report_submission_allowed", False)),
        vulnerability_confirmation_allowed=bool(request_data.get("vulnerability_confirmation_allowed", False)),
        source=source,
    )


def import_human_case_review_decision_file(
    decision_request: BrainChatHumanCaseReviewDecisionRequest,
    decision_file: Path,
    source: str = "brain-chat-human-case-review-decision-import",
) -> BrainChatHumanCaseReviewDecisionImport:
    data = json.loads(Path(decision_file).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Human case review decision JSON must be an object.")
    return import_human_case_review_decision_data(decision_request, data, source=source)


def _decision_import_status(
    decision: str,
    request_ready: bool,
    request_status: str,
    effective_approval: bool,
    safe: bool,
) -> str:
    if not safe:
        return "blocked-pending-safe-decision-request"

    if decision == "changes-requested":
        return "changes-requested"

    if decision == "rejected":
        return "rejected"

    if effective_approval:
        return "approved-for-next-local-planning-gate"

    return f"blocked-pending-ready-decision-request:{request_status}"


def _allowed_next_steps(decision: str, decision_import_status: str) -> list[str]:
    if decision_import_status == "approved-for-next-local-planning-gate":
        return [
            "Proceed to the next local planning gate only.",
            "Keep validation, execution, evidence collection, reporting, and vulnerability confirmation behind separate gates.",
        ]

    if decision == "changes-requested":
        return [
            "Apply requested local changes before rebuilding the decision request.",
        ]

    if decision == "rejected":
        return [
            "Stop this human case-review path unless a new local decision request is produced.",
        ]

    if decision_import_status == "blocked-pending-safe-decision-request":
        return [
            "Fix unsafe decision request state before treating approval as effective.",
        ]

    return [
        "Resolve decision request blockers before treating approval as effective.",
    ]


def _rejected_next_steps(decision: str, decision_import_status: str) -> list[str]:
    rejected = [
        "Do not execute network, browser, curl, Kali, shell, scanner, or target interaction steps from this imported decision.",
        "Do not collect new evidence from a target from this imported decision.",
        "Do not submit a report from imported human case-review decision state alone.",
        "Do not claim vulnerability confirmation from imported human case-review decision state alone.",
        "Do not treat this imported decision as validation or runtime execution approval.",
    ]

    if decision == "approved-for-next-local-planning-gate" and decision_import_status != "approved-for-next-local-planning-gate":
        rejected.insert(0, "Do not treat the approval decision as effective because the decision request is not ready.")

    return rejected


def _has_unsafe_flags(data: dict[str, Any]) -> bool:
    unsafe_keys = (
        "validation_allowed",
        "runtime_execution_allowed",
        "report_submission_allowed",
        "vulnerability_confirmation_allowed",
    )
    if any(bool(data.get(key)) for key in unsafe_keys):
        return True

    safety = data.get("safety")
    if isinstance(safety, dict):
        unsafe_safety = (
            "human_approval_side_effects",
            "tool_execution",
            "evidence_collection",
            "validation_execution",
            "report_submission",
            "vulnerability_confirmation",
        )
        return any(bool(safety.get(key)) for key in unsafe_safety)

    return False


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
