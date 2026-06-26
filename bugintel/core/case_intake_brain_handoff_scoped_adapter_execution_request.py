"""
Brain handoff scoped adapter execution request.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_adapter_final_confirmation_packet
artifact into a scoped adapter execution request artifact for future review.

The request packages the reviewed command for a future adapter. It does not
execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_REQUEST_ADAPTER_FAMILIES: tuple[str, ...] = ("curl",)


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterExecutionRequest:
    request_id: str
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
    request_purpose: str
    requested_action: str
    target_base_url: str
    resolved_endpoint: str
    resolved_target_url: str
    reviewed_command: str
    final_confirmation_decision: str
    final_confirmation_status: str
    human_final_confirmation_recorded: bool
    confirmed_by: str
    confirmation_reason: str
    request_status: str
    scope_validation_state: str
    adapter_execution_state: str
    required_runtime_checks: tuple[str, ...]
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
    unresolved_placeholders: tuple[str, ...]
    blocked: bool
    block_reason: str
    dry_run_only: bool
    can_execute_now: bool
    execution_request_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-execution-request"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_execution_request",
            "source": self.source,
            "request_id": self.request_id,
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
            "request_purpose": self.request_purpose,
            "requested_action": self.requested_action,
            "target_base_url": self.target_base_url,
            "resolved_endpoint": self.resolved_endpoint,
            "resolved_target_url": self.resolved_target_url,
            "reviewed_command": self.reviewed_command,
            "final_confirmation_decision": self.final_confirmation_decision,
            "final_confirmation_status": self.final_confirmation_status,
            "human_final_confirmation_recorded": self.human_final_confirmation_recorded,
            "confirmed_by": self.confirmed_by,
            "confirmation_reason": self.confirmation_reason,
            "request_status": self.request_status,
            "scope_validation_state": self.scope_validation_state,
            "adapter_execution_state": self.adapter_execution_state,
            "required_runtime_checks": list(self.required_runtime_checks),
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
            "unresolved_placeholders": list(self.unresolved_placeholders),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "dry_run_only": self.dry_run_only,
            "can_execute_now": self.can_execute_now,
            "execution_request_allows_execution": self.execution_request_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Execution Request") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Request ID: `{self.request_id}`",
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
            f"- Request purpose: `{self.request_purpose}`",
            f"- Requested action: `{self.requested_action}`",
            f"- Target base URL: `{self.target_base_url}`",
            f"- Resolved endpoint: `{self.resolved_endpoint}`",
            f"- Resolved target URL: `{self.resolved_target_url}`",
            f"- Final confirmation decision: `{self.final_confirmation_decision}`",
            f"- Final confirmation status: `{self.final_confirmation_status}`",
            f"- Human final confirmation recorded: `{self.human_final_confirmation_recorded}`",
            f"- Confirmed by: `{self.confirmed_by}`",
            f"- Request status: `{self.request_status}`",
            f"- Scope validation state: `{self.scope_validation_state}`",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Execution request allows execution: `{self.execution_request_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Confirmation Reason",
            "",
            self.confirmation_reason or "No reason supplied.",
            "",
            "## Reviewed Command Packaged for Future Adapter",
            "",
            "```bash",
            self.reviewed_command or "# No reviewed command available because this request is blocked.",
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
            "## Required Runtime Checks",
            "",
        ]

        lines.extend(_markdown_list(self.required_runtime_checks))
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
        lines.extend(["", "## Unresolved Placeholders", ""])
        lines.extend(_markdown_list(self.unresolved_placeholders))

        return "\n".join(lines).rstrip() + "\n"


def export_case_intake_brain_handoff_scoped_adapter_execution_request(
    adapter_final_confirmation_packet: dict[str, Any],
    request_purpose: str,
) -> CaseIntakeBrainScopedAdapterExecutionRequest:
    packet = adapter_final_confirmation_packet if isinstance(adapter_final_confirmation_packet, dict) else {}
    clean_purpose, purpose_errors = _validate_request_purpose(request_purpose)

    source_kind = str(packet.get("kind") or "unknown")
    confirmation_id = str(packet.get("confirmation_id") or "AFC-UNKNOWN")
    preview_id = str(packet.get("preview_id") or "ADP-UNKNOWN")
    manifest_id = str(packet.get("manifest_id") or "RSM-UNKNOWN")
    gate_id = str(packet.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(packet.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(packet.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(packet.get("approval_id") or "AP-UNKNOWN")
    target_name = str(packet.get("target_name") or "bug-bounty-target")
    endpoint = str(packet.get("endpoint") or "unknown-endpoint")
    adapter_family = str(packet.get("adapter_family") or "unknown").strip().lower()
    command_family = str(packet.get("command_family") or "unknown").strip().lower()

    if source_kind != "case_intake_brain_handoff_adapter_final_confirmation_packet":
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Input is not a case_intake_brain_handoff_adapter_final_confirmation_packet artifact.",
        )

    if purpose_errors:
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason=" ".join(purpose_errors),
        )

    if adapter_family not in SUPPORTED_REQUEST_ADAPTER_FAMILIES:
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Unsupported adapter family. Supported adapter families: curl.",
        )

    if _unsafe_packet(packet):
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Source final confirmation packet reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(packet.get("blocked")):
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason=str(packet.get("source_preview_block_reason") or "Source final confirmation packet is blocked."),
        )

    if str(packet.get("final_confirmation_decision") or "") != "confirmed" or not bool(packet.get("human_final_confirmation_recorded")):
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Final confirmation packet must be confirmed and human_final_confirmation_recorded must be true before exporting a scoped adapter execution request.",
        )

    if _strings(packet.get("unresolved_placeholders")):
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Final confirmation packet still contains unresolved placeholders.",
        )

    if not str(packet.get("resolved_command_preview") or "").strip():
        return _blocked_request(
            packet=packet,
            source_kind=source_kind,
            confirmation_id=confirmation_id,
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
            request_purpose=clean_purpose,
            reason="Final confirmation packet does not contain a resolved command preview.",
        )

    return CaseIntakeBrainScopedAdapterExecutionRequest(
        request_id=f"SAER-{confirmation_id}",
        confirmation_id=confirmation_id,
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
        request_purpose=clean_purpose,
        requested_action="future-scoped-adapter-execution-review",
        target_base_url=str(packet.get("target_base_url") or ""),
        resolved_endpoint=str(packet.get("resolved_endpoint") or ""),
        resolved_target_url=str(packet.get("resolved_target_url") or ""),
        reviewed_command=str(packet.get("resolved_command_preview") or ""),
        final_confirmation_decision=str(packet.get("final_confirmation_decision") or "unknown"),
        final_confirmation_status=str(packet.get("final_confirmation_status") or "unknown"),
        human_final_confirmation_recorded=bool(packet.get("human_final_confirmation_recorded")),
        confirmed_by=str(packet.get("confirmed_by") or "human-reviewer"),
        confirmation_reason=str(packet.get("reason") or ""),
        request_status="ready-for-future-scoped-adapter-review-no-execution",
        scope_validation_state="not_performed",
        adapter_execution_state="not_executed",
        required_runtime_checks=_required_runtime_checks(),
        scope_check_requirements=tuple(_strings(packet.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(packet.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(packet.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(packet.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(packet.get("required_preconditions"))),
        account_matrix=tuple(_strings(packet.get("account_matrix"))),
        validation_steps=tuple(_strings(packet.get("validation_steps"))),
        checklist_ids=tuple(_strings(packet.get("checklist_ids"))),
        stop_conditions=tuple(_strings(packet.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(packet.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(packet.get("unresolved_placeholders"))),
        blocked=False,
        block_reason="",
        dry_run_only=True,
        can_execute_now=False,
        execution_request_allows_execution=False,
    )


def _blocked_request(
    packet: dict[str, Any],
    source_kind: str,
    confirmation_id: str,
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
    request_purpose: str,
    reason: str,
) -> CaseIntakeBrainScopedAdapterExecutionRequest:
    return CaseIntakeBrainScopedAdapterExecutionRequest(
        request_id=f"SAER-BLOCKED-{confirmation_id}",
        confirmation_id=confirmation_id,
        preview_id=preview_id,
        manifest_id=manifest_id,
        gate_id=gate_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        adapter_family=adapter_family or "unknown",
        command_family=command_family or "unknown",
        request_purpose=request_purpose,
        requested_action="blocked",
        target_base_url=str(packet.get("target_base_url") or ""),
        resolved_endpoint=str(packet.get("resolved_endpoint") or ""),
        resolved_target_url=str(packet.get("resolved_target_url") or ""),
        reviewed_command=str(packet.get("resolved_command_preview") or ""),
        final_confirmation_decision=str(packet.get("final_confirmation_decision") or "unknown"),
        final_confirmation_status=str(packet.get("final_confirmation_status") or "blocked"),
        human_final_confirmation_recorded=bool(packet.get("human_final_confirmation_recorded")),
        confirmed_by=str(packet.get("confirmed_by") or "human-reviewer"),
        confirmation_reason=str(packet.get("reason") or ""),
        request_status="blocked",
        scope_validation_state="not_performed",
        adapter_execution_state="not_executed",
        required_runtime_checks=_required_runtime_checks(),
        scope_check_requirements=tuple(_strings(packet.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(packet.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(packet.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(packet.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(packet.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(packet.get("account_matrix"))),
        validation_steps=tuple(_strings(packet.get("validation_steps"))),
        checklist_ids=tuple(_strings(packet.get("checklist_ids"))),
        stop_conditions=tuple(_strings(packet.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(packet.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(packet.get("unresolved_placeholders"))),
        blocked=True,
        block_reason=reason,
        dry_run_only=True,
        can_execute_now=False,
        execution_request_allows_execution=False,
    )


def _validate_request_purpose(value: str) -> tuple[str, tuple[str, ...]]:
    purpose = str(value or "").strip()
    if not purpose:
        return "", ("Request purpose is required.",)

    errors: list[str] = []
    if "\n" in purpose or "\r" in purpose:
        errors.append("Request purpose must not contain newlines.")
    if len(purpose) > 160:
        errors.append("Request purpose is too long.")
    return purpose, tuple(errors)


def _required_runtime_checks() -> tuple[str, ...]:
    return (
        "Re-verify target base URL is explicitly in scope at execution time.",
        "Re-verify resolved target URL host, scheme, endpoint path, and method before any request.",
        "Re-verify controlled-account-only token and synthetic identifiers.",
        "Re-verify the command remains read-only and contains no mutation method.",
        "Re-verify redirects, retries, scanning, crawling, fuzzing, and enumeration remain disabled.",
        "Show a final adapter preview immediately before any future execution.",
        "Require explicit human execution confirmation in a separate adapter-specific flow.",
        "Block if any runtime check cannot be proven safe.",
    )


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
            "can_execute_now",
            "final_confirmation_allows_execution",
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
