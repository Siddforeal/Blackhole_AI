"""
Brain handoff scoped adapter execution plan packet.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet
artifact into a strict future adapter execution plan packet.

The packet describes ordered execution-plan steps for a future scoped adapter
runtime path. It does not execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterExecutionPlanPacket:
    execution_plan_id: str
    runtime_confirmation_id: str
    final_gate_id: str
    safety_review_id: str
    runtime_scope_review_id: str
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
    plan_purpose: str
    planned_by: str
    resolved_target_url: str
    reviewed_command: str
    reviewed_method: str
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    runtime_confirmation_status: str
    runtime_confirmation_state: str
    runtime_confirmed_by: str
    runtime_confirmation_text: str
    human_runtime_confirmation_recorded: bool
    exact_context_confirmed: bool
    source_adapter_execution_state: str
    execution_plan_status: str
    execution_plan_state: str
    adapter_execution_state: str
    execution_plan_steps: tuple[str, ...]
    execution_preflight_checks: tuple[str, ...]
    execution_stop_conditions: tuple[str, ...]
    safe_command_findings: tuple[str, ...]
    blocked_command_findings: tuple[str, ...]
    required_safe_flags: tuple[str, ...]
    present_safe_flags: tuple[str, ...]
    missing_safe_flags: tuple[str, ...]
    blocked_flags_seen: tuple[str, ...]
    shell_control_patterns_seen: tuple[str, ...]
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
    execution_plan_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-execution-plan-packet"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_execution_plan_packet",
            "source": self.source,
            "execution_plan_id": self.execution_plan_id,
            "runtime_confirmation_id": self.runtime_confirmation_id,
            "final_gate_id": self.final_gate_id,
            "safety_review_id": self.safety_review_id,
            "runtime_scope_review_id": self.runtime_scope_review_id,
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
            "plan_purpose": self.plan_purpose,
            "planned_by": self.planned_by,
            "resolved_target_url": self.resolved_target_url,
            "reviewed_command": self.reviewed_command,
            "reviewed_method": self.reviewed_method,
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "runtime_confirmation_status": self.runtime_confirmation_status,
            "runtime_confirmation_state": self.runtime_confirmation_state,
            "runtime_confirmed_by": self.runtime_confirmed_by,
            "runtime_confirmation_text": self.runtime_confirmation_text,
            "human_runtime_confirmation_recorded": self.human_runtime_confirmation_recorded,
            "exact_context_confirmed": self.exact_context_confirmed,
            "source_adapter_execution_state": self.source_adapter_execution_state,
            "execution_plan_status": self.execution_plan_status,
            "execution_plan_state": self.execution_plan_state,
            "adapter_execution_state": self.adapter_execution_state,
            "execution_plan_steps": list(self.execution_plan_steps),
            "execution_preflight_checks": list(self.execution_preflight_checks),
            "execution_stop_conditions": list(self.execution_stop_conditions),
            "safe_command_findings": list(self.safe_command_findings),
            "blocked_command_findings": list(self.blocked_command_findings),
            "required_safe_flags": list(self.required_safe_flags),
            "present_safe_flags": list(self.present_safe_flags),
            "missing_safe_flags": list(self.missing_safe_flags),
            "blocked_flags_seen": list(self.blocked_flags_seen),
            "shell_control_patterns_seen": list(self.shell_control_patterns_seen),
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
            "execution_plan_allows_execution": self.execution_plan_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Execution Plan Packet") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Execution plan ID: `{self.execution_plan_id}`",
            f"- Runtime confirmation ID: `{self.runtime_confirmation_id}`",
            f"- Final gate ID: `{self.final_gate_id}`",
            f"- Safety review ID: `{self.safety_review_id}`",
            f"- Runtime scope review ID: `{self.runtime_scope_review_id}`",
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
            f"- Planned by: `{self.planned_by}`",
            f"- Plan purpose: `{self.plan_purpose}`",
            f"- Resolved target URL: `{self.resolved_target_url}`",
            f"- Reviewed method: `{self.reviewed_method}`",
            f"- Reviewed scheme: `{self.reviewed_scheme}`",
            f"- Reviewed host: `{self.reviewed_host}`",
            f"- Reviewed path: `{self.reviewed_path}`",
            f"- Runtime confirmation status: `{self.runtime_confirmation_status}`",
            f"- Runtime confirmation state: `{self.runtime_confirmation_state}`",
            f"- Runtime confirmed by: `{self.runtime_confirmed_by}`",
            f"- Human runtime confirmation recorded: `{self.human_runtime_confirmation_recorded}`",
            f"- Exact context confirmed: `{self.exact_context_confirmed}`",
            f"- Source adapter execution state: `{self.source_adapter_execution_state}`",
            f"- Execution plan status: `{self.execution_plan_status}`",
            f"- Execution plan state: `{self.execution_plan_state}`",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Execution plan allows execution: `{self.execution_plan_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Runtime Confirmation Text",
            "",
            self.runtime_confirmation_text or "No runtime confirmation text supplied.",
            "",
            "## Reviewed Command",
            "",
            "```bash",
            self.reviewed_command or "# No reviewed command available because this execution plan packet is blocked.",
            "```",
            "",
            "## Execution Plan Steps",
            "",
        ]

        lines.extend(f"{index}. {step}" for index, step in enumerate(self.execution_plan_steps, start=1))
        lines.extend(["", "## Execution Preflight Checks", ""])
        lines.extend(_markdown_list(self.execution_preflight_checks))
        lines.extend(["", "## Execution Stop Conditions", ""])
        lines.extend(_markdown_list(self.execution_stop_conditions))
        lines.extend(["", "## Safe Command Findings", ""])
        lines.extend(_markdown_list(self.safe_command_findings))
        lines.extend(["", "## Blocked Command Findings", ""])
        lines.extend(_markdown_list(self.blocked_command_findings))
        lines.extend(["", "## Required Safe Flags", ""])
        lines.extend(_markdown_list(self.required_safe_flags))
        lines.extend(["", "## Present Safe Flags", ""])
        lines.extend(_markdown_list(self.present_safe_flags))
        lines.extend(["", "## Missing Safe Flags", ""])
        lines.extend(_markdown_list(self.missing_safe_flags))
        lines.extend(["", "## Blocked Flags Seen", ""])
        lines.extend(_markdown_list(self.blocked_flags_seen))
        lines.extend(["", "## Shell Control Patterns Seen", ""])
        lines.extend(_markdown_list(self.shell_control_patterns_seen))
        lines.extend(
            [
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
        )
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


def export_case_intake_brain_handoff_scoped_adapter_execution_plan_packet(
    scoped_adapter_runtime_confirmation_packet: dict[str, Any],
    planned_by: str,
    plan_purpose: str,
) -> CaseIntakeBrainScopedAdapterExecutionPlanPacket:
    packet = (
        scoped_adapter_runtime_confirmation_packet
        if isinstance(scoped_adapter_runtime_confirmation_packet, dict)
        else {}
    )

    source_kind = str(packet.get("kind") or "unknown")
    runtime_confirmation_id = str(packet.get("runtime_confirmation_id") or "RCP-UNKNOWN")
    final_gate_id = str(packet.get("final_gate_id") or "FEG-UNKNOWN")
    safety_review_id = str(packet.get("safety_review_id") or "ASR-UNKNOWN")
    runtime_scope_review_id = str(packet.get("runtime_scope_review_id") or "RSR-UNKNOWN")
    request_id = str(packet.get("request_id") or "SAER-UNKNOWN")
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
    clean_planned_by = str(planned_by or "").strip() or "human-reviewer"
    clean_plan_purpose = str(plan_purpose or "").strip()

    if source_kind != "case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet":
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Input is not a case_intake_brain_handoff_scoped_adapter_runtime_confirmation_packet artifact.",
        )

    if not clean_plan_purpose:
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Execution plan purpose is required.",
        )

    if _unsafe_packet(packet):
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation packet reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(packet.get("blocked")):
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason=str(packet.get("block_reason") or "Source runtime confirmation packet is blocked."),
        )

    if str(packet.get("runtime_confirmation_status") or "") != "confirmed-runtime-context-for-future-adapter-path-no-execution":
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation status has not passed.",
        )

    if str(packet.get("runtime_confirmation_state") or "") != "confirmed_local_only":
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation state must be confirmed_local_only.",
        )

    if not bool(packet.get("human_runtime_confirmation_recorded")):
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation must record human confirmation.",
        )

    if not bool(packet.get("exact_context_confirmed")):
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation must confirm the exact context.",
        )

    if str(packet.get("adapter_execution_state") or "") != "not_executed":
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source adapter execution state must be not_executed.",
        )

    if _strings(packet.get("missing_safe_flags")) or _strings(packet.get("blocked_flags_seen")) or _strings(packet.get("shell_control_patterns_seen")):
        return _blocked_plan(
            packet=packet,
            source_kind=source_kind,
            runtime_confirmation_id=runtime_confirmation_id,
            final_gate_id=final_gate_id,
            safety_review_id=safety_review_id,
            runtime_scope_review_id=runtime_scope_review_id,
            request_id=request_id,
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
            planned_by=clean_planned_by,
            plan_purpose=clean_plan_purpose,
            block_reason="Source runtime confirmation still has missing safe flags, blocked flags, or shell control patterns.",
        )

    execution_plan_steps = (
        "Load the scoped adapter runtime confirmation packet.",
        "Verify the final gate, safety review, runtime scope review, request, confirmation, preview, manifest, gate, proposal, decision, and approval IDs match the packet chain.",
        "Verify the reviewed scheme, host, method, path, resolved URL, and command exactly match the confirmed local artifact.",
        "Verify controlled-account-only requirements, placeholder requirements, redaction rules, and stop conditions before any future adapter implementation.",
        "Prepare the future adapter invocation as a dry-run-only plan object without sending a request.",
        "Require a separate execution implementation and a separate explicit runtime execution confirmation before any command can be run.",
        "Stop immediately if scope, method, host, command, token, placeholder, account, redirect, retry, mutation, or shell-control checks differ from the confirmed packet.",
    )

    execution_preflight_checks = (
        "Confirm no unresolved placeholders remain.",
        "Confirm reviewed method is read-only.",
        "Confirm reviewed host and scheme match the scoped runtime review.",
        "Confirm blocked flags and shell control patterns are absent.",
        "Confirm no execution, validation, network, tool, browser, provider, evidence, mutation, report, or vulnerability-confirmation flag is enabled.",
    )

    execution_stop_conditions = tuple(_strings(packet.get("stop_conditions"))) + (
        "Stop if any future adapter would execute without a separate explicit runtime execution confirmation.",
        "Stop if any future adapter would collect evidence, mutate targets, submit reports, or confirm vulnerabilities automatically.",
    )

    return CaseIntakeBrainScopedAdapterExecutionPlanPacket(
        execution_plan_id=f"SEP-{runtime_confirmation_id}",
        runtime_confirmation_id=runtime_confirmation_id,
        final_gate_id=final_gate_id,
        safety_review_id=safety_review_id,
        runtime_scope_review_id=runtime_scope_review_id,
        request_id=request_id,
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
        request_purpose=str(packet.get("request_purpose") or ""),
        requested_action=str(packet.get("requested_action") or ""),
        plan_purpose=clean_plan_purpose,
        planned_by=clean_planned_by,
        resolved_target_url=str(packet.get("resolved_target_url") or ""),
        reviewed_command=str(packet.get("reviewed_command") or ""),
        reviewed_method=str(packet.get("reviewed_method") or ""),
        reviewed_scheme=str(packet.get("reviewed_scheme") or ""),
        reviewed_host=str(packet.get("reviewed_host") or ""),
        reviewed_path=str(packet.get("reviewed_path") or ""),
        runtime_confirmation_status=str(packet.get("runtime_confirmation_status") or ""),
        runtime_confirmation_state=str(packet.get("runtime_confirmation_state") or ""),
        runtime_confirmed_by=str(packet.get("confirmed_by") or "human-reviewer"),
        runtime_confirmation_text=str(packet.get("confirmation_text") or ""),
        human_runtime_confirmation_recorded=bool(packet.get("human_runtime_confirmation_recorded")),
        exact_context_confirmed=bool(packet.get("exact_context_confirmed")),
        source_adapter_execution_state=str(packet.get("adapter_execution_state") or ""),
        execution_plan_status="planned-for-future-scoped-adapter-execution-no-execution",
        execution_plan_state="planned_local_only",
        adapter_execution_state="not_executed",
        execution_plan_steps=execution_plan_steps,
        execution_preflight_checks=execution_preflight_checks,
        execution_stop_conditions=execution_stop_conditions,
        safe_command_findings=tuple(_strings(packet.get("safe_command_findings"))),
        blocked_command_findings=tuple(_strings(packet.get("blocked_command_findings"))),
        required_safe_flags=tuple(_strings(packet.get("required_safe_flags"))),
        present_safe_flags=tuple(_strings(packet.get("present_safe_flags"))),
        missing_safe_flags=tuple(_strings(packet.get("missing_safe_flags"))),
        blocked_flags_seen=tuple(_strings(packet.get("blocked_flags_seen"))),
        shell_control_patterns_seen=tuple(_strings(packet.get("shell_control_patterns_seen"))),
        required_runtime_checks=tuple(_strings(packet.get("required_runtime_checks"))),
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
        execution_plan_allows_execution=False,
    )


def _blocked_plan(
    packet: dict[str, Any],
    source_kind: str,
    runtime_confirmation_id: str,
    final_gate_id: str,
    safety_review_id: str,
    runtime_scope_review_id: str,
    request_id: str,
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
    planned_by: str,
    plan_purpose: str,
    block_reason: str,
) -> CaseIntakeBrainScopedAdapterExecutionPlanPacket:
    return CaseIntakeBrainScopedAdapterExecutionPlanPacket(
        execution_plan_id=f"SEP-BLOCKED-{runtime_confirmation_id}",
        runtime_confirmation_id=runtime_confirmation_id,
        final_gate_id=final_gate_id,
        safety_review_id=safety_review_id,
        runtime_scope_review_id=runtime_scope_review_id,
        request_id=request_id,
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
        request_purpose=str(packet.get("request_purpose") or ""),
        requested_action=str(packet.get("requested_action") or ""),
        plan_purpose=plan_purpose,
        planned_by=planned_by,
        resolved_target_url=str(packet.get("resolved_target_url") or ""),
        reviewed_command=str(packet.get("reviewed_command") or ""),
        reviewed_method=str(packet.get("reviewed_method") or ""),
        reviewed_scheme=str(packet.get("reviewed_scheme") or ""),
        reviewed_host=str(packet.get("reviewed_host") or ""),
        reviewed_path=str(packet.get("reviewed_path") or ""),
        runtime_confirmation_status=str(packet.get("runtime_confirmation_status") or "blocked"),
        runtime_confirmation_state=str(packet.get("runtime_confirmation_state") or "blocked"),
        runtime_confirmed_by=str(packet.get("confirmed_by") or "human-reviewer"),
        runtime_confirmation_text=str(packet.get("confirmation_text") or ""),
        human_runtime_confirmation_recorded=bool(packet.get("human_runtime_confirmation_recorded")),
        exact_context_confirmed=bool(packet.get("exact_context_confirmed")),
        source_adapter_execution_state=str(packet.get("adapter_execution_state") or "not_executed"),
        execution_plan_status="blocked",
        execution_plan_state="blocked",
        adapter_execution_state="not_executed",
        execution_plan_steps=(),
        execution_preflight_checks=(),
        execution_stop_conditions=("Do not proceed until the block reason is resolved.",),
        safe_command_findings=tuple(_strings(packet.get("safe_command_findings"))),
        blocked_command_findings=tuple(_strings(packet.get("blocked_command_findings"))) or (block_reason,),
        required_safe_flags=tuple(_strings(packet.get("required_safe_flags"))),
        present_safe_flags=tuple(_strings(packet.get("present_safe_flags"))),
        missing_safe_flags=tuple(_strings(packet.get("missing_safe_flags"))),
        blocked_flags_seen=tuple(_strings(packet.get("blocked_flags_seen"))),
        shell_control_patterns_seen=tuple(_strings(packet.get("shell_control_patterns_seen"))),
        required_runtime_checks=tuple(_strings(packet.get("required_runtime_checks"))),
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
        block_reason=block_reason,
        dry_run_only=True,
        can_execute_now=False,
        execution_plan_allows_execution=False,
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
            "runtime_confirmation_allows_execution",
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
