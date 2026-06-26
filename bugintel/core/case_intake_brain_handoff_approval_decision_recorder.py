"""
Brain handoff approval decision recorder.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It records a human decision over a case_intake_brain_handoff_approval_packet
artifact and produces an auditable decision artifact.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_APPROVAL_DECISIONS: tuple[str, ...] = ("approved", "denied", "blocked")


@dataclass(frozen=True)
class CaseIntakeBrainApprovalDecision:
    decision_id: str
    approval_id: str
    target_name: str
    source_kind: str
    endpoint: str
    proposed_action: str
    packet_approval_status: str
    decision: str
    decision_status: str
    decided_by: str
    reason: str
    approved: bool
    denied: bool
    blocked: bool
    can_proceed_to_execution: bool
    human_approval_recorded: bool
    read_only_required: bool
    packet_human_approval_required: bool
    packet_blocked: bool
    packet_block_reason: str
    account_matrix: tuple[str, ...]
    validation_steps: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    tool_execution_allowed: bool = False
    browser_execution_allowed: bool = False
    evidence_collection_allowed: bool = False
    target_mutation_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-approval-decision-recorder"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_approval_decision",
            "source": self.source,
            "decision_id": self.decision_id,
            "approval_id": self.approval_id,
            "target_name": self.target_name,
            "source_kind": self.source_kind,
            "endpoint": self.endpoint,
            "proposed_action": self.proposed_action,
            "packet_approval_status": self.packet_approval_status,
            "decision": self.decision,
            "decision_status": self.decision_status,
            "decided_by": self.decided_by,
            "reason": self.reason,
            "approved": self.approved,
            "denied": self.denied,
            "blocked": self.blocked,
            "can_proceed_to_execution": self.can_proceed_to_execution,
            "human_approval_recorded": self.human_approval_recorded,
            "read_only_required": self.read_only_required,
            "packet_human_approval_required": self.packet_human_approval_required,
            "packet_blocked": self.packet_blocked,
            "packet_block_reason": self.packet_block_reason,
            "account_matrix": list(self.account_matrix),
            "validation_steps": list(self.validation_steps),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "redaction_requirements": list(self.redaction_requirements),
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "tool_execution_allowed": self.tool_execution_allowed,
            "browser_execution_allowed": self.browser_execution_allowed,
            "evidence_collection_allowed": self.evidence_collection_allowed,
            "target_mutation_allowed": self.target_mutation_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Approval Decision") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Decision ID: `{self.decision_id}`",
            f"- Approval ID: `{self.approval_id}`",
            f"- Target: `{self.target_name}`",
            f"- Source kind: `{self.source_kind}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Proposed action: `{self.proposed_action}`",
            f"- Packet approval status: `{self.packet_approval_status}`",
            f"- Decision: `{self.decision}`",
            f"- Decision status: `{self.decision_status}`",
            f"- Decided by: `{self.decided_by}`",
            f"- Approved: `{self.approved}`",
            f"- Denied: `{self.denied}`",
            f"- Blocked: `{self.blocked}`",
            f"- Can proceed to execution: `{self.can_proceed_to_execution}`",
            f"- Human approval recorded: `{self.human_approval_recorded}`",
            f"- Read-only required: `{self.read_only_required}`",
            f"- Packet blocked: `{self.packet_blocked}`",
            f"- Packet block reason: `{self.packet_block_reason or 'none'}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Reason",
            "",
            self.reason or "No reason supplied.",
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
            "## Account Matrix",
            "",
        ]

        lines.extend(_markdown_list(self.account_matrix))
        lines.extend(["", "## Approved/Reviewed Manual Steps", ""])
        lines.extend(f"{index}. {step}" for index, step in enumerate(self.validation_steps, start=1))
        lines.extend(["", "## Linked Checklist IDs", ""])
        lines.extend(_markdown_list(self.checklist_ids))
        lines.extend(["", "## Redaction Requirements", ""])
        lines.extend(_markdown_list(self.redaction_requirements))
        lines.extend(["", "## Stop Conditions", ""])
        lines.extend(_markdown_list(self.stop_conditions))

        return "\n".join(lines).rstrip() + "\n"


def record_case_intake_brain_handoff_approval_decision(
    approval_packet: dict[str, Any],
    decision: str,
    decided_by: str,
    reason: str,
) -> CaseIntakeBrainApprovalDecision:
    packet = approval_packet if isinstance(approval_packet, dict) else {}
    normalized_decision = _normalize_decision(decision)
    clean_decided_by = str(decided_by or "").strip() or "unknown"
    clean_reason = str(reason or "").strip()

    target_name = str(packet.get("target_name") or "bug-bounty-target")
    source_kind = str(packet.get("kind") or "unknown")
    approval_id = str(packet.get("approval_id") or "AP-UNKNOWN")
    endpoint = str(packet.get("endpoint") or "unknown-endpoint")

    if source_kind != "case_intake_brain_handoff_approval_packet":
        return _blocked_decision(
            target_name=target_name,
            source_kind=source_kind,
            approval_id=approval_id,
            endpoint=endpoint,
            decision=normalized_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Input is not a case_intake_brain_handoff_approval_packet artifact.",
        )

    if normalized_decision not in VALID_APPROVAL_DECISIONS:
        return _blocked_decision(
            target_name=target_name,
            source_kind=source_kind,
            approval_id=approval_id,
            endpoint=endpoint,
            decision=normalized_decision or "invalid",
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Decision must be one of: approved, denied, blocked.",
        )

    if _unsafe_packet(packet):
        return _blocked_decision(
            target_name=target_name,
            source_kind=source_kind,
            approval_id=approval_id,
            endpoint=endpoint,
            decision=normalized_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source approval packet reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(packet.get("blocked")):
        return _blocked_decision(
            target_name=target_name,
            source_kind=source_kind,
            approval_id=approval_id,
            endpoint=endpoint,
            decision=normalized_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason=str(packet.get("block_reason") or "Source approval packet is blocked."),
            packet=packet,
        )

    decision_status = _decision_status(normalized_decision)
    approved = normalized_decision == "approved"
    denied = normalized_decision == "denied"
    blocked = normalized_decision == "blocked"

    return CaseIntakeBrainApprovalDecision(
        decision_id=f"AD-{approval_id}",
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        proposed_action=str(packet.get("proposed_action") or "unknown"),
        packet_approval_status=str(packet.get("approval_status") or "unknown"),
        decision=normalized_decision,
        decision_status=decision_status,
        decided_by=clean_decided_by,
        reason=clean_reason,
        approved=approved,
        denied=denied,
        blocked=blocked,
        can_proceed_to_execution=False,
        human_approval_recorded=approved,
        read_only_required=bool(packet.get("read_only_required", True)),
        packet_human_approval_required=bool(packet.get("human_approval_required", True)),
        packet_blocked=False,
        packet_block_reason="",
        account_matrix=tuple(_strings(packet.get("account_matrix"))),
        validation_steps=tuple(_strings(packet.get("validation_steps"))),
        checklist_ids=tuple(_strings(packet.get("checklist_ids"))),
        stop_conditions=tuple(_strings(packet.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(packet.get("redaction_requirements"))),
    )


def _blocked_decision(
    target_name: str,
    source_kind: str,
    approval_id: str,
    endpoint: str,
    decision: str,
    decided_by: str,
    reason: str,
    block_reason: str,
    packet: dict[str, Any] | None = None,
) -> CaseIntakeBrainApprovalDecision:
    packet_data = packet or {}
    return CaseIntakeBrainApprovalDecision(
        decision_id=f"AD-BLOCKED-{approval_id}",
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        proposed_action=str(packet_data.get("proposed_action") or "blocked"),
        packet_approval_status=str(packet_data.get("approval_status") or "blocked"),
        decision=decision,
        decision_status="blocked",
        decided_by=decided_by,
        reason=reason,
        approved=False,
        denied=False,
        blocked=True,
        can_proceed_to_execution=False,
        human_approval_recorded=False,
        read_only_required=bool(packet_data.get("read_only_required", True)),
        packet_human_approval_required=bool(packet_data.get("human_approval_required", True)),
        packet_blocked=True,
        packet_block_reason=block_reason,
        account_matrix=tuple(_strings(packet_data.get("account_matrix"))),
        validation_steps=tuple(_strings(packet_data.get("validation_steps"))),
        checklist_ids=tuple(_strings(packet_data.get("checklist_ids"))),
        stop_conditions=tuple(_strings(packet_data.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(packet_data.get("redaction_requirements"))),
    )


def _decision_status(decision: str) -> str:
    if decision == "approved":
        return "approved-no-execution-authorized"
    if decision == "denied":
        return "denied-by-human"
    if decision == "blocked":
        return "blocked-by-human"
    return "blocked-invalid-decision"


def _normalize_decision(decision: str) -> str:
    return str(decision or "").strip().lower().replace("_", "-")


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_packet(packet: dict[str, Any]) -> bool:
    safety = packet.get("safety") if isinstance(packet.get("safety"), dict) else {}
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
    if any(bool(safety.get(key)) for key in unsafe_keys):
        return True

    return any(
        bool(packet.get(key))
        for key in (
            "validation_allowed",
            "runtime_execution_allowed",
            "tool_execution_allowed",
            "browser_execution_allowed",
            "evidence_collection_allowed",
            "target_mutation_allowed",
            "report_submission_allowed",
            "vulnerability_confirmation_allowed",
        )
    )


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
