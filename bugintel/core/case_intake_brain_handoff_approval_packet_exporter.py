"""
Brain handoff approval packet exporter.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts one endpoint from a case_intake_brain_handoff_manual_validation_plan
artifact into a reviewable human approval packet.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainApprovalPacket:
    approval_id: str
    target_name: str
    source_kind: str
    endpoint: str
    lane: str
    priority_score: int
    priority_band: str
    proposed_action: str
    approval_question: str
    human_approval_required: bool
    approved: bool
    approval_status: str
    read_only_required: bool
    account_matrix: tuple[str, ...]
    validation_steps: tuple[str, ...]
    evidence_targets: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    blocked: bool
    block_reason: str
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
    source: str = "case-intake-brain-handoff-approval-packet-exporter"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_approval_packet",
            "source": self.source,
            "approval_id": self.approval_id,
            "target_name": self.target_name,
            "source_kind": self.source_kind,
            "endpoint": self.endpoint,
            "lane": self.lane,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "proposed_action": self.proposed_action,
            "approval_question": self.approval_question,
            "human_approval_required": self.human_approval_required,
            "approved": self.approved,
            "approval_status": self.approval_status,
            "read_only_required": self.read_only_required,
            "account_matrix": list(self.account_matrix),
            "validation_steps": list(self.validation_steps),
            "evidence_targets": list(self.evidence_targets),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "redaction_requirements": list(self.redaction_requirements),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
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

    def to_markdown(self, title: str = "Case Intake Brain Approval Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Approval ID: `{self.approval_id}`",
            f"- Target: `{self.target_name}`",
            f"- Source kind: `{self.source_kind}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Lane: `{self.lane}`",
            f"- Score: `{self.priority_score}`",
            f"- Band: `{self.priority_band}`",
            f"- Proposed action: `{self.proposed_action}`",
            f"- Human approval required: `{self.human_approval_required}`",
            f"- Approved: `{self.approved}`",
            f"- Approval status: `{self.approval_status}`",
            f"- Read-only required: `{self.read_only_required}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Approval Checkbox",
            "",
            f"- [ ] {self.approval_question}",
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
        lines.extend(["", "## Proposed Read-Only Manual Steps", ""])
        lines.extend(f"{index}. {step}" for index, step in enumerate(self.validation_steps, start=1))
        lines.extend(["", "## Evidence Targets", ""])
        lines.extend(_markdown_list(self.evidence_targets))
        lines.extend(["", "## Linked Checklist IDs", ""])
        lines.extend(_markdown_list(self.checklist_ids))
        lines.extend(["", "## Redaction Requirements", ""])
        lines.extend(_markdown_list(self.redaction_requirements))
        lines.extend(["", "## Stop Conditions", ""])
        lines.extend(_markdown_list(self.stop_conditions))

        return "\n".join(lines).rstrip() + "\n"


def export_case_intake_brain_handoff_approval_packet(
    manual_validation_plan: dict[str, Any],
    endpoint: str | None = None,
) -> CaseIntakeBrainApprovalPacket:
    plan = manual_validation_plan if isinstance(manual_validation_plan, dict) else {}
    target_name = str(plan.get("target_name") or "bug-bounty-target")
    source_kind = str(plan.get("kind") or "unknown")
    selected_endpoint = str(endpoint or "")

    if source_kind != "case_intake_brain_handoff_manual_validation_plan":
        return _blocked_packet(
            target_name=target_name,
            source_kind=source_kind,
            endpoint=selected_endpoint or "unknown-endpoint",
            reason="Input is not a case_intake_brain_handoff_manual_validation_plan artifact.",
        )

    if _unsafe_plan(plan):
        return _blocked_packet(
            target_name=target_name,
            source_kind=source_kind,
            endpoint=selected_endpoint or "unknown-endpoint",
            reason="Source manual validation plan reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    plan_endpoints = _objects(plan.get("plan_endpoints"))
    selected = _select_endpoint(plan_endpoints, selected_endpoint)

    if selected is None:
        return _blocked_packet(
            target_name=target_name,
            source_kind=source_kind,
            endpoint=selected_endpoint or "unknown-endpoint",
            reason="Requested endpoint was not found in the manual validation plan.",
        )

    endpoint_value = str(selected.get("endpoint") or "unknown-endpoint")
    approval_id = _approval_id(plan_endpoints, endpoint_value)

    return CaseIntakeBrainApprovalPacket(
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint_value,
        lane=str(selected.get("lane") or "unknown"),
        priority_score=_int(selected.get("priority_score")),
        priority_band=str(selected.get("priority_band") or "unknown"),
        proposed_action="manual-read-only-validation-review",
        approval_question=(
            f"Approve planning the next read-only manual validation review for `{endpoint_value}` "
            "using only controlled accounts and the listed stop conditions?"
        ),
        human_approval_required=True,
        approved=False,
        approval_status="pending-human-approval",
        read_only_required=True,
        account_matrix=tuple(_strings(selected.get("controlled_account_matrix"))),
        validation_steps=tuple(_strings(selected.get("validation_steps"))),
        evidence_targets=tuple(_strings(selected.get("evidence_targets"))),
        checklist_ids=tuple(_strings(selected.get("checklist_ids"))),
        stop_conditions=tuple(_strings(selected.get("stop_conditions"))),
        redaction_requirements=_redaction_requirements(),
        blocked=False,
        block_reason="",
    )


def _blocked_packet(
    target_name: str,
    source_kind: str,
    endpoint: str,
    reason: str,
) -> CaseIntakeBrainApprovalPacket:
    return CaseIntakeBrainApprovalPacket(
        approval_id="AP-BLOCKED",
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        lane="unknown",
        priority_score=0,
        priority_band="unknown",
        proposed_action="blocked",
        approval_question="No approval can be requested because this packet is blocked.",
        human_approval_required=True,
        approved=False,
        approval_status="blocked",
        read_only_required=True,
        account_matrix=(),
        validation_steps=(),
        evidence_targets=(),
        checklist_ids=(),
        stop_conditions=("Do not proceed until the block reason is resolved.",),
        redaction_requirements=_redaction_requirements(),
        blocked=True,
        block_reason=reason,
    )


def _select_endpoint(plan_endpoints: list[dict[str, Any]], endpoint: str) -> dict[str, Any] | None:
    if endpoint:
        for item in plan_endpoints:
            if str(item.get("endpoint") or "") == endpoint:
                return item
        return None

    return plan_endpoints[0] if plan_endpoints else None


def _approval_id(plan_endpoints: list[dict[str, Any]], endpoint: str) -> str:
    for index, item in enumerate(plan_endpoints, start=1):
        if str(item.get("endpoint") or "") == endpoint:
            return f"AP-{index:03d}"
    return "AP-001"


def _redaction_requirements() -> tuple[str, ...]:
    return (
        "Redact cookies and session tokens.",
        "Redact authorization headers and API keys.",
        "Redact CSRF tokens, reset tokens, OTPs, and one-time links.",
        "Redact account IDs, object IDs, invoice IDs, file IDs, and internal identifiers unless synthetic.",
        "Redact personal data, emails, names, addresses, phone numbers, and payment data.",
        "Redact secrets from request bodies, response bodies, logs, screenshots, and filenames.",
    )


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_plan(plan: dict[str, Any]) -> bool:
    safety = plan.get("safety") if isinstance(plan.get("safety"), dict) else {}
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
        bool(plan.get(key))
        for key in (
            "validation_allowed",
            "runtime_execution_allowed",
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
