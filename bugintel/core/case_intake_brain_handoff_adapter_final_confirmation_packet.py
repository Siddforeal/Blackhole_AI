"""
Brain handoff adapter final confirmation packet.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It records final human confirmation over a
case_intake_brain_handoff_adapter_dry_run_preview artifact.

Even when confirmed, this module does not execute curl, Burp, browser,
terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_FINAL_CONFIRMATION_DECISIONS: tuple[str, ...] = ("confirmed", "denied", "blocked")


@dataclass(frozen=True)
class CaseIntakeBrainAdapterFinalConfirmationPacket:
    confirmation_id: str
    preview_id: str
    manifest_id: str
    gate_id: str
    proposal_id: str
    decision_id: str
    approval_id: str
    target_name: str
    source_kind: str
    endpoint: str
    adapter_family: str
    command_family: str
    target_base_url: str
    resolved_endpoint: str
    resolved_target_url: str
    resolved_command_preview: str
    dry_run_preview_status: str
    final_confirmation_decision: str
    final_confirmation_status: str
    confirmed_by: str
    reason: str
    confirmed: bool
    denied: bool
    blocked: bool
    human_final_confirmation_recorded: bool
    dry_run_only: bool
    source_preview_ready: bool
    source_preview_blocked: bool
    source_preview_block_reason: str
    unresolved_placeholders: tuple[str, ...]
    scope_check_requirements: tuple[str, ...]
    placeholder_check_requirements: tuple[str, ...]
    adapter_safety_requirements: tuple[str, ...]
    final_human_confirmation_requirements: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    account_matrix: tuple[str, ...]
    validation_steps: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    can_execute_now: bool
    final_confirmation_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-adapter-final-confirmation-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_adapter_final_confirmation_packet",
            "source": self.source,
            "confirmation_id": self.confirmation_id,
            "preview_id": self.preview_id,
            "manifest_id": self.manifest_id,
            "gate_id": self.gate_id,
            "proposal_id": self.proposal_id,
            "decision_id": self.decision_id,
            "approval_id": self.approval_id,
            "target_name": self.target_name,
            "source_kind": self.source_kind,
            "endpoint": self.endpoint,
            "adapter_family": self.adapter_family,
            "command_family": self.command_family,
            "target_base_url": self.target_base_url,
            "resolved_endpoint": self.resolved_endpoint,
            "resolved_target_url": self.resolved_target_url,
            "resolved_command_preview": self.resolved_command_preview,
            "dry_run_preview_status": self.dry_run_preview_status,
            "final_confirmation_decision": self.final_confirmation_decision,
            "final_confirmation_status": self.final_confirmation_status,
            "confirmed_by": self.confirmed_by,
            "reason": self.reason,
            "confirmed": self.confirmed,
            "denied": self.denied,
            "blocked": self.blocked,
            "human_final_confirmation_recorded": self.human_final_confirmation_recorded,
            "dry_run_only": self.dry_run_only,
            "source_preview_ready": self.source_preview_ready,
            "source_preview_blocked": self.source_preview_blocked,
            "source_preview_block_reason": self.source_preview_block_reason,
            "unresolved_placeholders": list(self.unresolved_placeholders),
            "scope_check_requirements": list(self.scope_check_requirements),
            "placeholder_check_requirements": list(self.placeholder_check_requirements),
            "adapter_safety_requirements": list(self.adapter_safety_requirements),
            "final_human_confirmation_requirements": list(self.final_human_confirmation_requirements),
            "required_preconditions": list(self.required_preconditions),
            "account_matrix": list(self.account_matrix),
            "validation_steps": list(self.validation_steps),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "redaction_requirements": list(self.redaction_requirements),
            "can_execute_now": self.can_execute_now,
            "final_confirmation_allows_execution": self.final_confirmation_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Adapter Final Confirmation Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Confirmation ID: `{self.confirmation_id}`",
            f"- Preview ID: `{self.preview_id}`",
            f"- Manifest ID: `{self.manifest_id}`",
            f"- Gate ID: `{self.gate_id}`",
            f"- Proposal ID: `{self.proposal_id}`",
            f"- Decision ID: `{self.decision_id}`",
            f"- Approval ID: `{self.approval_id}`",
            f"- Target: `{self.target_name}`",
            f"- Source kind: `{self.source_kind}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Adapter family: `{self.adapter_family}`",
            f"- Command family: `{self.command_family}`",
            f"- Target base URL: `{self.target_base_url}`",
            f"- Resolved endpoint: `{self.resolved_endpoint}`",
            f"- Resolved target URL: `{self.resolved_target_url}`",
            f"- Dry-run preview status: `{self.dry_run_preview_status}`",
            f"- Final confirmation decision: `{self.final_confirmation_decision}`",
            f"- Final confirmation status: `{self.final_confirmation_status}`",
            f"- Confirmed by: `{self.confirmed_by}`",
            f"- Confirmed: `{self.confirmed}`",
            f"- Denied: `{self.denied}`",
            f"- Blocked: `{self.blocked}`",
            f"- Human final confirmation recorded: `{self.human_final_confirmation_recorded}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Source preview ready: `{self.source_preview_ready}`",
            f"- Source preview blocked: `{self.source_preview_blocked}`",
            f"- Source preview block reason: `{self.source_preview_block_reason or 'none'}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Final confirmation allows execution: `{self.final_confirmation_allows_execution}`",
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
            "## Resolved Dry-Run Command Reviewed",
            "",
            "```bash",
            self.resolved_command_preview or "# No resolved dry-run preview available because this packet is blocked.",
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
            "## Unresolved Placeholders",
            "",
        ]

        lines.extend(_markdown_list(self.unresolved_placeholders))
        lines.extend(["", "## Runtime Scope Check Requirements", ""])
        lines.extend(_markdown_list(self.scope_check_requirements))
        lines.extend(["", "## Placeholder Check Requirements", ""])
        lines.extend(_markdown_list(self.placeholder_check_requirements))
        lines.extend(["", "## Adapter Safety Requirements", ""])
        lines.extend(_markdown_list(self.adapter_safety_requirements))
        lines.extend(["", "## Final Human Confirmation Requirements", ""])
        lines.extend(_markdown_list(self.final_human_confirmation_requirements))
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


def record_case_intake_brain_handoff_adapter_final_confirmation(
    adapter_dry_run_preview: dict[str, Any],
    decision: str,
    confirmed_by: str,
    reason: str,
) -> CaseIntakeBrainAdapterFinalConfirmationPacket:
    preview = adapter_dry_run_preview if isinstance(adapter_dry_run_preview, dict) else {}
    normalized_decision = _normalize_decision(decision)
    clean_confirmed_by = str(confirmed_by or "").strip() or "human-reviewer"
    clean_reason = str(reason or "").strip()

    source_kind = str(preview.get("kind") or "unknown")
    preview_id = str(preview.get("preview_id") or "ADP-UNKNOWN")
    manifest_id = str(preview.get("manifest_id") or "RSM-UNKNOWN")
    gate_id = str(preview.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(preview.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(preview.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(preview.get("approval_id") or "AP-UNKNOWN")
    target_name = str(preview.get("target_name") or "bug-bounty-target")
    endpoint = str(preview.get("endpoint") or "unknown-endpoint")
    adapter_family = str(preview.get("adapter_family") or "unknown")
    command_family = str(preview.get("command_family") or "unknown")

    if source_kind != "case_intake_brain_handoff_adapter_dry_run_preview":
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision or "invalid",
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason="Input is not a case_intake_brain_handoff_adapter_dry_run_preview artifact.",
        )

    if normalized_decision not in VALID_FINAL_CONFIRMATION_DECISIONS:
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision or "invalid",
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason="Final confirmation decision must be one of: confirmed, denied, blocked.",
        )

    if _unsafe_preview(preview):
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision,
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason="Source dry-run preview reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(preview.get("blocked")):
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision,
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason=str(preview.get("block_reason") or "Source dry-run preview is blocked."),
        )

    if not bool(preview.get("dry_run_only")) or not bool(preview.get("preview_ready")):
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision,
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason="Source dry-run preview must be dry_run_only and preview_ready before final confirmation.",
        )

    if _strings(preview.get("unresolved_placeholders")):
        return _blocked_packet(
            preview=preview,
            source_kind=source_kind,
            preview_id=preview_id,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            target_name=target_name,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            decision=normalized_decision,
            confirmed_by=clean_confirmed_by,
            reason=clean_reason,
            block_reason="Source dry-run preview still contains unresolved placeholders.",
        )

    confirmed = normalized_decision == "confirmed"
    denied = normalized_decision == "denied"
    blocked = normalized_decision == "blocked"

    return CaseIntakeBrainAdapterFinalConfirmationPacket(
        confirmation_id=f"AFC-{preview_id}",
        preview_id=preview_id,
        manifest_id=manifest_id,
        gate_id=gate_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        adapter_family=adapter_family,
        command_family=command_family,
        target_base_url=str(preview.get("target_base_url") or ""),
        resolved_endpoint=str(preview.get("resolved_endpoint") or ""),
        resolved_target_url=str(preview.get("resolved_target_url") or ""),
        resolved_command_preview=str(preview.get("resolved_command_preview") or ""),
        dry_run_preview_status=str(preview.get("dry_run_preview_status") or "unknown"),
        final_confirmation_decision=normalized_decision,
        final_confirmation_status=_final_confirmation_status(normalized_decision),
        confirmed_by=clean_confirmed_by,
        reason=clean_reason,
        confirmed=confirmed,
        denied=denied,
        blocked=blocked,
        human_final_confirmation_recorded=confirmed,
        dry_run_only=True,
        source_preview_ready=True,
        source_preview_blocked=False,
        source_preview_block_reason="",
        unresolved_placeholders=tuple(_strings(preview.get("unresolved_placeholders"))),
        scope_check_requirements=tuple(_strings(preview.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(preview.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(preview.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(preview.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(preview.get("required_preconditions"))),
        account_matrix=tuple(_strings(preview.get("account_matrix"))),
        validation_steps=tuple(_strings(preview.get("validation_steps"))),
        checklist_ids=tuple(_strings(preview.get("checklist_ids"))),
        stop_conditions=tuple(_strings(preview.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(preview.get("redaction_requirements"))),
        can_execute_now=False,
        final_confirmation_allows_execution=False,
    )


def _blocked_packet(
    preview: dict[str, Any],
    source_kind: str,
    preview_id: str,
    manifest_id: str,
    gate_id: str,
    proposal_id: str,
    decision_id: str,
    approval_id: str,
    target_name: str,
    endpoint: str,
    adapter_family: str,
    command_family: str,
    decision: str,
    confirmed_by: str,
    reason: str,
    block_reason: str,
) -> CaseIntakeBrainAdapterFinalConfirmationPacket:
    return CaseIntakeBrainAdapterFinalConfirmationPacket(
        confirmation_id=f"AFC-BLOCKED-{preview_id}",
        preview_id=preview_id,
        manifest_id=manifest_id,
        gate_id=gate_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        adapter_family=adapter_family,
        command_family=command_family,
        target_base_url=str(preview.get("target_base_url") or ""),
        resolved_endpoint=str(preview.get("resolved_endpoint") or ""),
        resolved_target_url=str(preview.get("resolved_target_url") or ""),
        resolved_command_preview=str(preview.get("resolved_command_preview") or ""),
        dry_run_preview_status=str(preview.get("dry_run_preview_status") or "blocked"),
        final_confirmation_decision=decision,
        final_confirmation_status="blocked",
        confirmed_by=confirmed_by,
        reason=reason,
        confirmed=False,
        denied=False,
        blocked=True,
        human_final_confirmation_recorded=False,
        dry_run_only=True,
        source_preview_ready=bool(preview.get("preview_ready")),
        source_preview_blocked=True,
        source_preview_block_reason=block_reason,
        unresolved_placeholders=tuple(_strings(preview.get("unresolved_placeholders"))),
        scope_check_requirements=tuple(_strings(preview.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(preview.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(preview.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(preview.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(preview.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(preview.get("account_matrix"))),
        validation_steps=tuple(_strings(preview.get("validation_steps"))),
        checklist_ids=tuple(_strings(preview.get("checklist_ids"))),
        stop_conditions=tuple(_strings(preview.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(preview.get("redaction_requirements"))),
        can_execute_now=False,
        final_confirmation_allows_execution=False,
    )


def _final_confirmation_status(decision: str) -> str:
    if decision == "confirmed":
        return "confirmed-no-execution-authorized"
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


def _unsafe_preview(preview: dict[str, Any]) -> bool:
    safety = preview.get("safety") if isinstance(preview.get("safety"), dict) else {}
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
        bool(preview.get(key))
        for key in (
            "can_execute_now",
            "preview_allows_execution",
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
        "dry_run_only": True,
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
