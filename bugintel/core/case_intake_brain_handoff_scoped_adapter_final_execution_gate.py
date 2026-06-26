"""
Brain handoff scoped adapter final execution gate.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_scoped_adapter_safety_review artifact
into a final execution gate artifact.

The gate records an explicit human go/no-go decision for a future adapter path.
It does not execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


VALID_FINAL_EXECUTION_GATE_DECISIONS: tuple[str, ...] = ("approved", "denied", "blocked")


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterFinalExecutionGate:
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
    resolved_target_url: str
    reviewed_command: str
    reviewed_method: str
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    adapter_safety_review_status: str
    adapter_safety_state: str
    source_adapter_execution_state: str
    final_execution_gate_decision: str
    final_execution_gate_status: str
    decided_by: str
    decision_reason: str
    human_final_execution_gate_recorded: bool
    final_go_no_go: str
    adapter_execution_state: str
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
    final_execution_gate_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-final-execution-gate"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_final_execution_gate",
            "source": self.source,
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
            "resolved_target_url": self.resolved_target_url,
            "reviewed_command": self.reviewed_command,
            "reviewed_method": self.reviewed_method,
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "adapter_safety_review_status": self.adapter_safety_review_status,
            "adapter_safety_state": self.adapter_safety_state,
            "source_adapter_execution_state": self.source_adapter_execution_state,
            "final_execution_gate_decision": self.final_execution_gate_decision,
            "final_execution_gate_status": self.final_execution_gate_status,
            "decided_by": self.decided_by,
            "decision_reason": self.decision_reason,
            "human_final_execution_gate_recorded": self.human_final_execution_gate_recorded,
            "final_go_no_go": self.final_go_no_go,
            "adapter_execution_state": self.adapter_execution_state,
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
            "final_execution_gate_allows_execution": self.final_execution_gate_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Final Execution Gate") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
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
            f"- Resolved target URL: `{self.resolved_target_url}`",
            f"- Reviewed method: `{self.reviewed_method}`",
            f"- Reviewed scheme: `{self.reviewed_scheme}`",
            f"- Reviewed host: `{self.reviewed_host}`",
            f"- Reviewed path: `{self.reviewed_path}`",
            f"- Adapter safety review status: `{self.adapter_safety_review_status}`",
            f"- Adapter safety state: `{self.adapter_safety_state}`",
            f"- Source adapter execution state: `{self.source_adapter_execution_state}`",
            f"- Final execution gate decision: `{self.final_execution_gate_decision}`",
            f"- Final execution gate status: `{self.final_execution_gate_status}`",
            f"- Decided by: `{self.decided_by}`",
            f"- Human final execution gate recorded: `{self.human_final_execution_gate_recorded}`",
            f"- Final go/no-go: `{self.final_go_no_go}`",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Final execution gate allows execution: `{self.final_execution_gate_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Decision Reason",
            "",
            self.decision_reason or "No reason supplied.",
            "",
            "## Reviewed Command",
            "",
            "```bash",
            self.reviewed_command or "# No reviewed command available because this final execution gate is blocked.",
            "```",
            "",
            "## Safe Command Findings",
            "",
        ]

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


def record_case_intake_brain_handoff_scoped_adapter_final_execution_gate(
    scoped_adapter_safety_review: dict[str, Any],
    decision: str,
    decided_by: str,
    reason: str,
) -> CaseIntakeBrainScopedAdapterFinalExecutionGate:
    review = scoped_adapter_safety_review if isinstance(scoped_adapter_safety_review, dict) else {}

    source_kind = str(review.get("kind") or "unknown")
    safety_review_id = str(review.get("safety_review_id") or "ASR-UNKNOWN")
    runtime_scope_review_id = str(review.get("runtime_scope_review_id") or "RSR-UNKNOWN")
    request_id = str(review.get("request_id") or "SAER-UNKNOWN")
    confirmation_id = str(review.get("confirmation_id") or "AFC-UNKNOWN")
    preview_id = str(review.get("preview_id") or "ADP-UNKNOWN")
    manifest_id = str(review.get("manifest_id") or "RSM-UNKNOWN")
    gate_id = str(review.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(review.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(review.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(review.get("approval_id") or "AP-UNKNOWN")
    target_name = str(review.get("target_name") or "bug-bounty-target")
    endpoint = str(review.get("endpoint") or "unknown-endpoint")
    adapter_family = str(review.get("adapter_family") or "unknown").strip().lower()
    command_family = str(review.get("command_family") or "unknown").strip().lower()
    clean_decision = str(decision or "").strip().lower()
    clean_decided_by = str(decided_by or "").strip() or "human-reviewer"
    clean_reason = str(reason or "").strip()

    if source_kind != "case_intake_brain_handoff_scoped_adapter_safety_review":
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision or "blocked",
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Input is not a case_intake_brain_handoff_scoped_adapter_safety_review artifact.",
        )

    if clean_decision not in VALID_FINAL_EXECUTION_GATE_DECISIONS:
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision or "blocked",
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Invalid final execution gate decision. Valid decisions: approved, denied, blocked.",
        )

    if not clean_reason:
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Final execution gate reason is required.",
        )

    if _unsafe_review(review):
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source adapter safety review reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(review.get("blocked")):
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason=str(review.get("block_reason") or "Source adapter safety review is blocked."),
        )

    if str(review.get("adapter_safety_review_status") or "") != "passed-local-adapter-safety-review-no-execution":
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source adapter safety review has not passed.",
        )

    if str(review.get("adapter_safety_state") or "") != "reviewed_local_only":
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source adapter safety state must be reviewed_local_only.",
        )

    if str(review.get("adapter_execution_state") or "") != "not_executed":
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source adapter execution state must be not_executed.",
        )

    if _strings(review.get("missing_safe_flags")) or _strings(review.get("blocked_flags_seen")) or _strings(review.get("shell_control_patterns_seen")):
        return _blocked_gate(
            review=review,
            source_kind=source_kind,
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
            decision=clean_decision,
            decided_by=clean_decided_by,
            reason=clean_reason,
            block_reason="Source adapter safety review still has missing safe flags, blocked flags, or shell control patterns.",
        )

    status_by_decision = {
        "approved": "approved-for-future-adapter-path-no-execution",
        "denied": "denied-by-human-no-execution",
        "blocked": "blocked-by-human-no-execution",
    }
    go_no_go_by_decision = {
        "approved": "go-recorded-for-future-adapter-path-only",
        "denied": "no-go-denied-by-human",
        "blocked": "no-go-blocked-by-human",
    }

    blocked = clean_decision in {"denied", "blocked"}
    return CaseIntakeBrainScopedAdapterFinalExecutionGate(
        final_gate_id=f"FEG-{safety_review_id}",
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
        request_purpose=str(review.get("request_purpose") or ""),
        requested_action=str(review.get("requested_action") or ""),
        resolved_target_url=str(review.get("resolved_target_url") or ""),
        reviewed_command=str(review.get("reviewed_command") or ""),
        reviewed_method=str(review.get("reviewed_method") or ""),
        reviewed_scheme=str(review.get("reviewed_scheme") or ""),
        reviewed_host=str(review.get("reviewed_host") or ""),
        reviewed_path=str(review.get("reviewed_path") or ""),
        adapter_safety_review_status=str(review.get("adapter_safety_review_status") or ""),
        adapter_safety_state=str(review.get("adapter_safety_state") or ""),
        source_adapter_execution_state=str(review.get("adapter_execution_state") or ""),
        final_execution_gate_decision=clean_decision,
        final_execution_gate_status=status_by_decision[clean_decision],
        decided_by=clean_decided_by,
        decision_reason=clean_reason,
        human_final_execution_gate_recorded=True,
        final_go_no_go=go_no_go_by_decision[clean_decision],
        adapter_execution_state="not_executed",
        safe_command_findings=tuple(_strings(review.get("safe_command_findings"))),
        blocked_command_findings=tuple(_strings(review.get("blocked_command_findings"))),
        required_safe_flags=tuple(_strings(review.get("required_safe_flags"))),
        present_safe_flags=tuple(_strings(review.get("present_safe_flags"))),
        missing_safe_flags=tuple(_strings(review.get("missing_safe_flags"))),
        blocked_flags_seen=tuple(_strings(review.get("blocked_flags_seen"))),
        shell_control_patterns_seen=tuple(_strings(review.get("shell_control_patterns_seen"))),
        required_runtime_checks=tuple(_strings(review.get("required_runtime_checks"))),
        scope_check_requirements=tuple(_strings(review.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(review.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(review.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(review.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(review.get("required_preconditions"))),
        account_matrix=tuple(_strings(review.get("account_matrix"))),
        validation_steps=tuple(_strings(review.get("validation_steps"))),
        checklist_ids=tuple(_strings(review.get("checklist_ids"))),
        stop_conditions=tuple(_strings(review.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(review.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(review.get("unresolved_placeholders"))),
        blocked=blocked,
        block_reason="Human final execution gate decision is not approved." if blocked else "",
        dry_run_only=True,
        can_execute_now=False,
        final_execution_gate_allows_execution=False,
    )


def _blocked_gate(
    review: dict[str, Any],
    source_kind: str,
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
    decision: str,
    decided_by: str,
    reason: str,
    block_reason: str,
) -> CaseIntakeBrainScopedAdapterFinalExecutionGate:
    return CaseIntakeBrainScopedAdapterFinalExecutionGate(
        final_gate_id=f"FEG-BLOCKED-{safety_review_id}",
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
        request_purpose=str(review.get("request_purpose") or ""),
        requested_action=str(review.get("requested_action") or ""),
        resolved_target_url=str(review.get("resolved_target_url") or ""),
        reviewed_command=str(review.get("reviewed_command") or ""),
        reviewed_method=str(review.get("reviewed_method") or ""),
        reviewed_scheme=str(review.get("reviewed_scheme") or ""),
        reviewed_host=str(review.get("reviewed_host") or ""),
        reviewed_path=str(review.get("reviewed_path") or ""),
        adapter_safety_review_status=str(review.get("adapter_safety_review_status") or "blocked"),
        adapter_safety_state=str(review.get("adapter_safety_state") or "blocked"),
        source_adapter_execution_state=str(review.get("adapter_execution_state") or "not_executed"),
        final_execution_gate_decision=decision,
        final_execution_gate_status="blocked",
        decided_by=decided_by,
        decision_reason=reason,
        human_final_execution_gate_recorded=False,
        final_go_no_go="no-go-blocked",
        adapter_execution_state="not_executed",
        safe_command_findings=tuple(_strings(review.get("safe_command_findings"))),
        blocked_command_findings=tuple(_strings(review.get("blocked_command_findings"))) or (block_reason,),
        required_safe_flags=tuple(_strings(review.get("required_safe_flags"))),
        present_safe_flags=tuple(_strings(review.get("present_safe_flags"))),
        missing_safe_flags=tuple(_strings(review.get("missing_safe_flags"))),
        blocked_flags_seen=tuple(_strings(review.get("blocked_flags_seen"))),
        shell_control_patterns_seen=tuple(_strings(review.get("shell_control_patterns_seen"))),
        required_runtime_checks=tuple(_strings(review.get("required_runtime_checks"))),
        scope_check_requirements=tuple(_strings(review.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(review.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(review.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(review.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(review.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(review.get("account_matrix"))),
        validation_steps=tuple(_strings(review.get("validation_steps"))),
        checklist_ids=tuple(_strings(review.get("checklist_ids"))),
        stop_conditions=tuple(_strings(review.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(review.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(review.get("unresolved_placeholders"))),
        blocked=True,
        block_reason=block_reason,
        dry_run_only=True,
        can_execute_now=False,
        final_execution_gate_allows_execution=False,
    )


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_review(review: dict[str, Any]) -> bool:
    safety = review.get("safety") if isinstance(review.get("safety"), dict) else {}
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
        bool(review.get(key))
        for key in (
            "can_execute_now",
            "adapter_safety_review_allows_execution",
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
