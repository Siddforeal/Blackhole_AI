"""
Brain handoff scoped adapter implementation blueprint.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_scoped_adapter_execution_readiness_review
artifact into an implementation blueprint artifact.

The blueprint defines future adapter module files, interfaces, dataclasses,
validation responsibilities, and safety guard requirements. It does not execute
curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterImplementationBlueprint:
    implementation_blueprint_id: str
    readiness_review_id: str
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
    reviewed_by: str
    blueprinted_by: str
    readiness_note: str
    blueprint_note: str
    resolved_target_url: str
    reviewed_command: str
    reviewed_method: str
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    readiness_review_status: str
    readiness_review_state: str
    implementation_readiness: str
    source_adapter_execution_state: str
    implementation_blueprint_status: str
    implementation_blueprint_state: str
    adapter_execution_state: str
    proposed_module_files: tuple[str, ...]
    proposed_interfaces: tuple[str, ...]
    proposed_dataclasses: tuple[str, ...]
    proposed_validation_guards: tuple[str, ...]
    proposed_test_files: tuple[str, ...]
    blueprint_findings: tuple[str, ...]
    blocking_findings: tuple[str, ...]
    execution_plan_steps: tuple[str, ...]
    execution_preflight_checks: tuple[str, ...]
    execution_stop_conditions: tuple[str, ...]
    readiness_findings: tuple[str, ...]
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
    implementation_blueprint_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-implementation-blueprint"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_implementation_blueprint",
            "source": self.source,
            "implementation_blueprint_id": self.implementation_blueprint_id,
            "readiness_review_id": self.readiness_review_id,
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
            "reviewed_by": self.reviewed_by,
            "blueprinted_by": self.blueprinted_by,
            "readiness_note": self.readiness_note,
            "blueprint_note": self.blueprint_note,
            "resolved_target_url": self.resolved_target_url,
            "reviewed_command": self.reviewed_command,
            "reviewed_method": self.reviewed_method,
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "readiness_review_status": self.readiness_review_status,
            "readiness_review_state": self.readiness_review_state,
            "implementation_readiness": self.implementation_readiness,
            "source_adapter_execution_state": self.source_adapter_execution_state,
            "implementation_blueprint_status": self.implementation_blueprint_status,
            "implementation_blueprint_state": self.implementation_blueprint_state,
            "adapter_execution_state": self.adapter_execution_state,
            "proposed_module_files": list(self.proposed_module_files),
            "proposed_interfaces": list(self.proposed_interfaces),
            "proposed_dataclasses": list(self.proposed_dataclasses),
            "proposed_validation_guards": list(self.proposed_validation_guards),
            "proposed_test_files": list(self.proposed_test_files),
            "blueprint_findings": list(self.blueprint_findings),
            "blocking_findings": list(self.blocking_findings),
            "execution_plan_steps": list(self.execution_plan_steps),
            "execution_preflight_checks": list(self.execution_preflight_checks),
            "execution_stop_conditions": list(self.execution_stop_conditions),
            "readiness_findings": list(self.readiness_findings),
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
            "implementation_blueprint_allows_execution": self.implementation_blueprint_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Implementation Blueprint") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Implementation blueprint ID: `{self.implementation_blueprint_id}`",
            f"- Readiness review ID: `{self.readiness_review_id}`",
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
            f"- Reviewed by: `{self.reviewed_by}`",
            f"- Blueprinted by: `{self.blueprinted_by}`",
            f"- Readiness review status: `{self.readiness_review_status}`",
            f"- Readiness review state: `{self.readiness_review_state}`",
            f"- Implementation readiness: `{self.implementation_readiness}`",
            f"- Implementation blueprint status: `{self.implementation_blueprint_status}`",
            f"- Implementation blueprint state: `{self.implementation_blueprint_state}`",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Implementation blueprint allows execution: `{self.implementation_blueprint_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Blueprint Note",
            "",
            self.blueprint_note or "No blueprint note supplied.",
            "",
            "## Reviewed Command",
            "",
            "```bash",
            self.reviewed_command or "# No reviewed command available because this blueprint is blocked.",
            "```",
            "",
            "## Proposed Module Files",
            "",
        ]

        lines.extend(_markdown_list(self.proposed_module_files))
        lines.extend(["", "## Proposed Interfaces", ""])
        lines.extend(_markdown_list(self.proposed_interfaces))
        lines.extend(["", "## Proposed Dataclasses", ""])
        lines.extend(_markdown_list(self.proposed_dataclasses))
        lines.extend(["", "## Proposed Validation Guards", ""])
        lines.extend(_markdown_list(self.proposed_validation_guards))
        lines.extend(["", "## Proposed Test Files", ""])
        lines.extend(_markdown_list(self.proposed_test_files))
        lines.extend(["", "## Blueprint Findings", ""])
        lines.extend(_markdown_list(self.blueprint_findings))
        lines.extend(["", "## Blocking Findings", ""])
        lines.extend(_markdown_list(self.blocking_findings))
        lines.extend(["", "## Execution Plan Steps", ""])
        lines.extend(f"{index}. {step}" for index, step in enumerate(self.execution_plan_steps, start=1))
        lines.extend(["", "## Execution Preflight Checks", ""])
        lines.extend(_markdown_list(self.execution_preflight_checks))
        lines.extend(["", "## Execution Stop Conditions", ""])
        lines.extend(_markdown_list(self.execution_stop_conditions))
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
                "## Runtime Scope Check Requirements",
                "",
            ]
        )
        lines.extend(_markdown_list(self.scope_check_requirements))
        lines.extend(["", "## Placeholder Check Requirements", ""])
        lines.extend(_markdown_list(self.placeholder_check_requirements))
        lines.extend(["", "## Adapter Safety Requirements", ""])
        lines.extend(_markdown_list(self.adapter_safety_requirements))
        lines.extend(["", "## Required Preconditions", ""])
        lines.extend(_markdown_list(self.required_preconditions))
        lines.extend(["", "## Account Matrix", ""])
        lines.extend(_markdown_list(self.account_matrix))
        lines.extend(["", "## Redaction Requirements", ""])
        lines.extend(_markdown_list(self.redaction_requirements))
        lines.extend(["", "## Stop Conditions", ""])
        lines.extend(_markdown_list(self.stop_conditions))
        lines.extend(["", "## Unresolved Placeholders", ""])
        lines.extend(_markdown_list(self.unresolved_placeholders))

        return "\n".join(lines).rstrip() + "\n"


def export_case_intake_brain_handoff_scoped_adapter_implementation_blueprint(
    scoped_adapter_execution_readiness_review: dict[str, Any],
    blueprinted_by: str,
    blueprint_note: str,
) -> CaseIntakeBrainScopedAdapterImplementationBlueprint:
    review = scoped_adapter_execution_readiness_review if isinstance(scoped_adapter_execution_readiness_review, dict) else {}

    source_kind = str(review.get("kind") or "unknown")
    readiness_review_id = str(review.get("readiness_review_id") or "ERR-UNKNOWN")
    execution_plan_id = str(review.get("execution_plan_id") or "SEP-UNKNOWN")
    runtime_confirmation_id = str(review.get("runtime_confirmation_id") or "RCP-UNKNOWN")
    final_gate_id = str(review.get("final_gate_id") or "FEG-UNKNOWN")
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
    clean_blueprinted_by = str(blueprinted_by or "").strip() or "human-reviewer"
    clean_blueprint_note = str(blueprint_note or "").strip()

    if source_kind != "case_intake_brain_handoff_scoped_adapter_execution_readiness_review":
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Input is not a case_intake_brain_handoff_scoped_adapter_execution_readiness_review artifact.",
        )

    if not clean_blueprint_note:
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Implementation blueprint note is required.",
        )

    if _unsafe_review(review):
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness review reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(review.get("blocked")):
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            str(review.get("block_reason") or "Source readiness review is blocked."),
        )

    if str(review.get("readiness_review_status") or "") != "ready-for-future-scoped-adapter-implementation-no-execution":
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness review status has not passed.",
        )

    if str(review.get("readiness_review_state") or "") != "reviewed_local_only":
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness review state must be reviewed_local_only.",
        )

    if str(review.get("implementation_readiness") or "") != "ready-for-future-implementation-only":
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source implementation readiness must be ready-for-future-implementation-only.",
        )

    if str(review.get("adapter_execution_state") or "") != "not_executed":
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source adapter execution state must be not_executed.",
        )

    if not _strings(review.get("readiness_findings")):
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness findings are required.",
        )

    if _strings(review.get("blocking_findings")):
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness review contains blocking findings.",
        )

    if _strings(review.get("missing_safe_flags")) or _strings(review.get("blocked_flags_seen")) or _strings(review.get("shell_control_patterns_seen")):
        return _blocked_blueprint(
            review, source_kind, readiness_review_id, execution_plan_id, runtime_confirmation_id,
            final_gate_id, safety_review_id, runtime_scope_review_id, request_id, confirmation_id,
            preview_id, manifest_id, gate_id, proposal_id, decision_id, approval_id, target_name,
            endpoint, adapter_family, command_family, clean_blueprinted_by, clean_blueprint_note,
            "Source readiness review still has missing safe flags, blocked flags, or shell control patterns.",
        )

    proposed_module_files = (
        "bugintel/adapters/scoped_runtime/__init__.py",
        "bugintel/adapters/scoped_runtime/contracts.py",
        "bugintel/adapters/scoped_runtime/curl_adapter.py",
        "bugintel/adapters/scoped_runtime/scope_guard.py",
        "bugintel/adapters/scoped_runtime/result_types.py",
    )

    proposed_interfaces = (
        "ScopedAdapterRequest.from_blueprint_artifact(...)",
        "ScopedAdapterScopeGuard.validate_request(...)",
        "ScopedCurlAdapter.prepare_request(...)",
        "ScopedCurlAdapter.render_preview(...)",
        "ScopedAdapterResult.to_dict(...)",
    )

    proposed_dataclasses = (
        "ScopedAdapterRequest",
        "ScopedAdapterScopeGuardResult",
        "ScopedAdapterPreparedCommand",
        "ScopedAdapterResult",
    )

    proposed_validation_guards = (
        "Reject execution unless a later explicit runtime execution confirmation artifact exists.",
        "Reject if host, scheme, method, path, command family, or adapter family differs from the blueprint.",
        "Reject unresolved placeholders before any future implementation can prepare a request.",
        "Reject redirects, retries, shell controls, mutation methods, provider calls, evidence collection, report submission, and vulnerability confirmation.",
        "Require controlled-account-only token handling and redaction before any future implementation can produce output.",
    )

    proposed_test_files = (
        "tests/test_scoped_runtime_contracts.py",
        "tests/test_scoped_runtime_scope_guard.py",
        "tests/test_scoped_runtime_curl_adapter.py",
    )

    blueprint_findings = (
        "Readiness review is valid and ready for future implementation only.",
        "Blueprint defines module boundaries without adding runtime execution.",
        "Blueprint defines interfaces and guards that must block execution by default.",
        "Blueprint preserves not_executed adapter state and does not authorize network or tool use.",
    )

    return CaseIntakeBrainScopedAdapterImplementationBlueprint(
        implementation_blueprint_id=f"SIB-{readiness_review_id}",
        readiness_review_id=readiness_review_id,
        execution_plan_id=execution_plan_id,
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
        request_purpose=str(review.get("request_purpose") or ""),
        requested_action=str(review.get("requested_action") or ""),
        plan_purpose=str(review.get("plan_purpose") or ""),
        planned_by=str(review.get("planned_by") or "human-reviewer"),
        reviewed_by=str(review.get("reviewed_by") or "human-reviewer"),
        blueprinted_by=clean_blueprinted_by,
        readiness_note=str(review.get("readiness_note") or ""),
        blueprint_note=clean_blueprint_note,
        resolved_target_url=str(review.get("resolved_target_url") or ""),
        reviewed_command=str(review.get("reviewed_command") or ""),
        reviewed_method=str(review.get("reviewed_method") or ""),
        reviewed_scheme=str(review.get("reviewed_scheme") or ""),
        reviewed_host=str(review.get("reviewed_host") or ""),
        reviewed_path=str(review.get("reviewed_path") or ""),
        readiness_review_status=str(review.get("readiness_review_status") or ""),
        readiness_review_state=str(review.get("readiness_review_state") or ""),
        implementation_readiness=str(review.get("implementation_readiness") or ""),
        source_adapter_execution_state=str(review.get("adapter_execution_state") or ""),
        implementation_blueprint_status="blueprinted-for-future-scoped-adapter-implementation-no-execution",
        implementation_blueprint_state="blueprinted_local_only",
        adapter_execution_state="not_executed",
        proposed_module_files=proposed_module_files,
        proposed_interfaces=proposed_interfaces,
        proposed_dataclasses=proposed_dataclasses,
        proposed_validation_guards=proposed_validation_guards,
        proposed_test_files=proposed_test_files,
        blueprint_findings=blueprint_findings,
        blocking_findings=(),
        execution_plan_steps=tuple(_strings(review.get("execution_plan_steps"))),
        execution_preflight_checks=tuple(_strings(review.get("execution_preflight_checks"))),
        execution_stop_conditions=tuple(_strings(review.get("execution_stop_conditions"))),
        readiness_findings=tuple(_strings(review.get("readiness_findings"))),
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
        blocked=False,
        block_reason="",
        dry_run_only=True,
        can_execute_now=False,
        implementation_blueprint_allows_execution=False,
    )


def _blocked_blueprint(
    review: dict[str, Any],
    source_kind: str,
    readiness_review_id: str,
    execution_plan_id: str,
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
    blueprinted_by: str,
    blueprint_note: str,
    block_reason: str,
) -> CaseIntakeBrainScopedAdapterImplementationBlueprint:
    return CaseIntakeBrainScopedAdapterImplementationBlueprint(
        implementation_blueprint_id=f"SIB-BLOCKED-{readiness_review_id}",
        readiness_review_id=readiness_review_id,
        execution_plan_id=execution_plan_id,
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
        request_purpose=str(review.get("request_purpose") or ""),
        requested_action=str(review.get("requested_action") or ""),
        plan_purpose=str(review.get("plan_purpose") or ""),
        planned_by=str(review.get("planned_by") or "human-reviewer"),
        reviewed_by=str(review.get("reviewed_by") or "human-reviewer"),
        blueprinted_by=blueprinted_by,
        readiness_note=str(review.get("readiness_note") or ""),
        blueprint_note=blueprint_note,
        resolved_target_url=str(review.get("resolved_target_url") or ""),
        reviewed_command=str(review.get("reviewed_command") or ""),
        reviewed_method=str(review.get("reviewed_method") or ""),
        reviewed_scheme=str(review.get("reviewed_scheme") or ""),
        reviewed_host=str(review.get("reviewed_host") or ""),
        reviewed_path=str(review.get("reviewed_path") or ""),
        readiness_review_status=str(review.get("readiness_review_status") or "blocked"),
        readiness_review_state=str(review.get("readiness_review_state") or "blocked"),
        implementation_readiness=str(review.get("implementation_readiness") or "not_ready"),
        source_adapter_execution_state=str(review.get("adapter_execution_state") or "not_executed"),
        implementation_blueprint_status="blocked",
        implementation_blueprint_state="blocked",
        adapter_execution_state="not_executed",
        proposed_module_files=(),
        proposed_interfaces=(),
        proposed_dataclasses=(),
        proposed_validation_guards=(),
        proposed_test_files=(),
        blueprint_findings=(),
        blocking_findings=(block_reason,),
        execution_plan_steps=tuple(_strings(review.get("execution_plan_steps"))),
        execution_preflight_checks=tuple(_strings(review.get("execution_preflight_checks"))),
        execution_stop_conditions=tuple(_strings(review.get("execution_stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        readiness_findings=tuple(_strings(review.get("readiness_findings"))),
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
        implementation_blueprint_allows_execution=False,
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
            "readiness_review_allows_execution",
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
