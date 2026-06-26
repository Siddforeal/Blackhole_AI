"""
Brain handoff execution approval gate.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It records a separate human execution approval decision over a
case_intake_brain_handoff_read_only_command_proposal artifact.

Even when approved, this module does not execute the proposed command.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_EXECUTION_APPROVAL_DECISIONS: tuple[str, ...] = ("approved", "denied", "blocked")


@dataclass(frozen=True)
class CaseIntakeBrainExecutionApprovalGate:
    gate_id: str
    proposal_id: str
    decision_id: str
    approval_id: str
    target_name: str
    source_kind: str
    endpoint: str
    command_family: str
    command_purpose: str
    proposed_command: str
    proposed_command_tokens: tuple[str, ...]
    execution_decision: str
    execution_gate_status: str
    decided_by: str
    reason: str
    approved: bool
    denied: bool
    blocked: bool
    human_execution_approval_recorded: bool
    can_execute_now: bool
    requires_runtime_scope_check: bool
    requires_final_human_confirmation: bool
    requires_adapter_safety_check: bool
    original_proposal_blocked: bool
    original_proposal_block_reason: str
    placeholder_requirements: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    account_matrix: tuple[str, ...]
    validation_steps: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    execution_allowed: bool = False
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    tool_execution_allowed: bool = False
    browser_execution_allowed: bool = False
    network_requests_allowed: bool = False
    evidence_collection_allowed: bool = False
    target_mutation_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-execution-approval-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_execution_approval_gate",
            "source": self.source,
            "gate_id": self.gate_id,
            "proposal_id": self.proposal_id,
            "decision_id": self.decision_id,
            "approval_id": self.approval_id,
            "target_name": self.target_name,
            "source_kind": self.source_kind,
            "endpoint": self.endpoint,
            "command_family": self.command_family,
            "command_purpose": self.command_purpose,
            "proposed_command": self.proposed_command,
            "proposed_command_tokens": list(self.proposed_command_tokens),
            "execution_decision": self.execution_decision,
            "execution_gate_status": self.execution_gate_status,
            "decided_by": self.decided_by,
            "reason": self.reason,
            "approved": self.approved,
            "denied": self.denied,
            "blocked": self.blocked,
            "human_execution_approval_recorded": self.human_execution_approval_recorded,
            "can_execute_now": self.can_execute_now,
            "requires_runtime_scope_check": self.requires_runtime_scope_check,
            "requires_final_human_confirmation": self.requires_final_human_confirmation,
            "requires_adapter_safety_check": self.requires_adapter_safety_check,
            "original_proposal_blocked": self.original_proposal_blocked,
            "original_proposal_block_reason": self.original_proposal_block_reason,
            "placeholder_requirements": list(self.placeholder_requirements),
            "required_preconditions": list(self.required_preconditions),
            "account_matrix": list(self.account_matrix),
            "validation_steps": list(self.validation_steps),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "redaction_requirements": list(self.redaction_requirements),
            "execution_allowed": self.execution_allowed,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "tool_execution_allowed": self.tool_execution_allowed,
            "browser_execution_allowed": self.browser_execution_allowed,
            "network_requests_allowed": self.network_requests_allowed,
            "evidence_collection_allowed": self.evidence_collection_allowed,
            "target_mutation_allowed": self.target_mutation_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Execution Approval Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Gate ID: `{self.gate_id}`",
            f"- Proposal ID: `{self.proposal_id}`",
            f"- Decision ID: `{self.decision_id}`",
            f"- Approval ID: `{self.approval_id}`",
            f"- Target: `{self.target_name}`",
            f"- Source kind: `{self.source_kind}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Command family: `{self.command_family}`",
            f"- Execution decision: `{self.execution_decision}`",
            f"- Execution gate status: `{self.execution_gate_status}`",
            f"- Decided by: `{self.decided_by}`",
            f"- Approved: `{self.approved}`",
            f"- Denied: `{self.denied}`",
            f"- Blocked: `{self.blocked}`",
            f"- Human execution approval recorded: `{self.human_execution_approval_recorded}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Requires runtime scope check: `{self.requires_runtime_scope_check}`",
            f"- Requires final human confirmation: `{self.requires_final_human_confirmation}`",
            f"- Requires adapter safety check: `{self.requires_adapter_safety_check}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Reason",
            "",
            self.reason or "No reason supplied.",
            "",
            "## Proposed Command Under Review",
            "",
            "```bash",
            self.proposed_command or "# No command available because this gate is blocked.",
            "```",
            "",
            "## Safety",
            "",
            "- No command execution",
            "- No network requests",
            "- No tool execution",
            "- No browser execution",
            "- No provider calls",
            "- No evidence collection",
            "- No target mutation",
            "- No report submission",
            "- No vulnerability confirmation",
            "",
            "## Placeholder Requirements",
            "",
        ]

        lines.extend(_markdown_list(self.placeholder_requirements))
        lines.extend(["", "## Required Preconditions", ""])
        lines.extend(_markdown_list(self.required_preconditions))
        lines.extend(["", "## Account Matrix", ""])
        lines.extend(_markdown_list(self.account_matrix))
        lines.extend(["", "## Reviewed Manual Steps", ""])
        lines.extend(f"{index}. {step}" for index, step in enumerate(self.validation_steps, start=1))
        lines.extend(["", "## Linked Checklist IDs", ""])
        lines.extend(_markdown_list(self.checklist_ids))
        lines.extend(["", "## Redaction Requirements", ""])
        lines.extend(_markdown_list(self.redaction_requirements))
        lines.extend(["", "## Stop Conditions", ""])
        lines.extend(_markdown_list(self.stop_conditions))

        return "\n".join(lines).rstrip() + "\n"


def record_case_intake_brain_handoff_execution_approval_gate(
    command_proposal: dict[str, Any],
    decision: str,
    decided_by: str,
    reason: str,
) -> CaseIntakeBrainExecutionApprovalGate:
    proposal = command_proposal if isinstance(command_proposal, dict) else {}
    normalized_decision = _normalize_decision(decision)
    clean_decided_by = str(decided_by or "").strip() or "unknown"
    clean_reason = str(reason or "").strip()

    target_name = str(proposal.get("target_name") or "bug-bounty-target")
    source_kind = str(proposal.get("kind") or "unknown")
    proposal_id = str(proposal.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(proposal.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(proposal.get("approval_id") or "AP-UNKNOWN")
    endpoint = str(proposal.get("endpoint") or "unknown-endpoint")
    command_family = str(proposal.get("command_family") or "unknown")

    if source_kind != "case_intake_brain_handoff_read_only_command_proposal":
        return _blocked_gate(
            target_name=target_name,
            source_kind=source_kind,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=command_family,
            execution_decision=normalized_decision or "invalid",
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Input is not a case_intake_brain_handoff_read_only_command_proposal artifact.",
            proposal=proposal,
        )

    if normalized_decision not in VALID_EXECUTION_APPROVAL_DECISIONS:
        return _blocked_gate(
            target_name=target_name,
            source_kind=source_kind,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=command_family,
            execution_decision=normalized_decision or "invalid",
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Execution approval decision must be one of: approved, denied, blocked.",
            proposal=proposal,
        )

    if _unsafe_proposal(proposal):
        return _blocked_gate(
            target_name=target_name,
            source_kind=source_kind,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=command_family,
            execution_decision=normalized_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source command proposal reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
            proposal=proposal,
        )

    if bool(proposal.get("blocked")):
        return _blocked_gate(
            target_name=target_name,
            source_kind=source_kind,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=command_family,
            execution_decision=normalized_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason=str(proposal.get("block_reason") or "Source command proposal is blocked."),
            proposal=proposal,
        )

    approved = normalized_decision == "approved"
    denied = normalized_decision == "denied"
    blocked = normalized_decision == "blocked"

    return CaseIntakeBrainExecutionApprovalGate(
        gate_id=f"EG-{proposal_id}",
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        command_family=command_family,
        command_purpose=str(proposal.get("command_purpose") or "unknown"),
        proposed_command=str(proposal.get("proposed_command") or ""),
        proposed_command_tokens=tuple(_strings(proposal.get("proposed_command_tokens"))),
        execution_decision=normalized_decision,
        execution_gate_status=_execution_gate_status(normalized_decision),
        decided_by=clean_decided_by,
        reason=clean_reason,
        approved=approved,
        denied=denied,
        blocked=blocked,
        human_execution_approval_recorded=approved,
        can_execute_now=False,
        requires_runtime_scope_check=True,
        requires_final_human_confirmation=True,
        requires_adapter_safety_check=True,
        original_proposal_blocked=False,
        original_proposal_block_reason="",
        placeholder_requirements=tuple(_strings(proposal.get("placeholder_requirements"))),
        required_preconditions=tuple(_strings(proposal.get("required_preconditions"))),
        account_matrix=tuple(_strings(proposal.get("account_matrix"))),
        validation_steps=tuple(_strings(proposal.get("validation_steps"))),
        checklist_ids=tuple(_strings(proposal.get("checklist_ids"))),
        stop_conditions=tuple(_strings(proposal.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(proposal.get("redaction_requirements"))),
    )


def _blocked_gate(
    target_name: str,
    source_kind: str,
    proposal_id: str,
    decision_id: str,
    approval_id: str,
    endpoint: str,
    command_family: str,
    execution_decision: str,
    decided_by: str,
    reason: str,
    block_reason: str,
    proposal: dict[str, Any] | None = None,
) -> CaseIntakeBrainExecutionApprovalGate:
    proposal_data = proposal or {}
    return CaseIntakeBrainExecutionApprovalGate(
        gate_id=f"EG-BLOCKED-{proposal_id}",
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        command_family=command_family,
        command_purpose=str(proposal_data.get("command_purpose") or "blocked"),
        proposed_command=str(proposal_data.get("proposed_command") or ""),
        proposed_command_tokens=tuple(_strings(proposal_data.get("proposed_command_tokens"))),
        execution_decision=execution_decision,
        execution_gate_status="blocked",
        decided_by=decided_by,
        reason=reason,
        approved=False,
        denied=False,
        blocked=True,
        human_execution_approval_recorded=False,
        can_execute_now=False,
        requires_runtime_scope_check=True,
        requires_final_human_confirmation=True,
        requires_adapter_safety_check=True,
        original_proposal_blocked=True,
        original_proposal_block_reason=block_reason,
        placeholder_requirements=tuple(_strings(proposal_data.get("placeholder_requirements"))),
        required_preconditions=tuple(_strings(proposal_data.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(proposal_data.get("account_matrix"))),
        validation_steps=tuple(_strings(proposal_data.get("validation_steps"))),
        checklist_ids=tuple(_strings(proposal_data.get("checklist_ids"))),
        stop_conditions=tuple(_strings(proposal_data.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(proposal_data.get("redaction_requirements"))),
    )


def _execution_gate_status(decision: str) -> str:
    if decision == "approved":
        return "approved-no-execution-performed"
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


def _unsafe_proposal(proposal: dict[str, Any]) -> bool:
    safety = proposal.get("safety") if isinstance(proposal.get("safety"), dict) else {}
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
        bool(proposal.get(key))
        for key in (
            "execution_allowed",
            "validation_allowed",
            "runtime_execution_allowed",
            "tool_execution_allowed",
            "browser_execution_allowed",
            "network_requests_allowed",
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
