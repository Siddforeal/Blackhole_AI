"""
Brain handoff scoped adapter runtime scope review.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_scoped_adapter_execution_request
artifact into a local runtime scope review artifact.

The review checks scheme, host, method, endpoint path, and safety flags for a
future adapter. It does not execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import shlex
from typing import Any
from urllib.parse import urlparse


READ_ONLY_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterRuntimeScopeReview:
    review_id: str
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
    reviewed_scheme: str
    reviewed_host: str
    reviewed_path: str
    reviewed_method: str
    allowed_scheme: str
    allowed_host: str
    allowed_method: str
    final_confirmation_decision: str
    final_confirmation_status: str
    human_final_confirmation_recorded: bool
    confirmed_by: str
    request_status: str
    request_scope_validation_state: str
    request_adapter_execution_state: str
    runtime_scope_review_status: str
    scope_validation_state: str
    adapter_execution_state: str
    review_findings: tuple[str, ...]
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
    runtime_scope_review_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-runtime-scope-review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_runtime_scope_review",
            "source": self.source,
            "review_id": self.review_id,
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
            "reviewed_scheme": self.reviewed_scheme,
            "reviewed_host": self.reviewed_host,
            "reviewed_path": self.reviewed_path,
            "reviewed_method": self.reviewed_method,
            "allowed_scheme": self.allowed_scheme,
            "allowed_host": self.allowed_host,
            "allowed_method": self.allowed_method,
            "final_confirmation_decision": self.final_confirmation_decision,
            "final_confirmation_status": self.final_confirmation_status,
            "human_final_confirmation_recorded": self.human_final_confirmation_recorded,
            "confirmed_by": self.confirmed_by,
            "request_status": self.request_status,
            "request_scope_validation_state": self.request_scope_validation_state,
            "request_adapter_execution_state": self.request_adapter_execution_state,
            "runtime_scope_review_status": self.runtime_scope_review_status,
            "scope_validation_state": self.scope_validation_state,
            "adapter_execution_state": self.adapter_execution_state,
            "review_findings": list(self.review_findings),
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
            "runtime_scope_review_allows_execution": self.runtime_scope_review_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Runtime Scope Review") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Review ID: `{self.review_id}`",
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
            f"- Reviewed scheme: `{self.reviewed_scheme}`",
            f"- Reviewed host: `{self.reviewed_host}`",
            f"- Reviewed path: `{self.reviewed_path}`",
            f"- Reviewed method: `{self.reviewed_method}`",
            f"- Allowed scheme: `{self.allowed_scheme}`",
            f"- Allowed host: `{self.allowed_host}`",
            f"- Allowed method: `{self.allowed_method}`",
            f"- Final confirmation decision: `{self.final_confirmation_decision}`",
            f"- Final confirmation status: `{self.final_confirmation_status}`",
            f"- Human final confirmation recorded: `{self.human_final_confirmation_recorded}`",
            f"- Confirmed by: `{self.confirmed_by}`",
            f"- Runtime scope review status: `{self.runtime_scope_review_status}`",
            f"- Scope validation state: `{self.scope_validation_state}`",
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Runtime scope review allows execution: `{self.runtime_scope_review_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Reviewed Command",
            "",
            "```bash",
            self.reviewed_command or "# No reviewed command available because this runtime scope review is blocked.",
            "```",
            "",
            "## Review Findings",
            "",
        ]

        lines.extend(_markdown_list(self.review_findings))
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


def export_case_intake_brain_handoff_scoped_adapter_runtime_scope_review(
    scoped_adapter_execution_request: dict[str, Any],
    allowed_host: str,
    allowed_scheme: str,
    allowed_method: str,
) -> CaseIntakeBrainScopedAdapterRuntimeScopeReview:
    request = scoped_adapter_execution_request if isinstance(scoped_adapter_execution_request, dict) else {}

    source_kind = str(request.get("kind") or "unknown")
    request_id = str(request.get("request_id") or "SAER-UNKNOWN")
    confirmation_id = str(request.get("confirmation_id") or "AFC-UNKNOWN")
    preview_id = str(request.get("preview_id") or "ADP-UNKNOWN")
    manifest_id = str(request.get("manifest_id") or "RSM-UNKNOWN")
    gate_id = str(request.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(request.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(request.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(request.get("approval_id") or "AP-UNKNOWN")
    target_name = str(request.get("target_name") or "bug-bounty-target")
    endpoint = str(request.get("endpoint") or "unknown-endpoint")
    adapter_family = str(request.get("adapter_family") or "unknown").strip().lower()
    command_family = str(request.get("command_family") or "unknown").strip().lower()

    allowed_scheme_clean, allowed_scheme_errors = _validate_allowed_scheme(allowed_scheme)
    allowed_host_clean, allowed_host_errors = _validate_allowed_host(allowed_host)
    allowed_method_clean, allowed_method_errors = _validate_allowed_method(allowed_method)

    resolved_target_url = str(request.get("resolved_target_url") or "")
    parsed = urlparse(resolved_target_url)
    reviewed_scheme = parsed.scheme.lower()
    reviewed_host = (parsed.hostname or "").lower()
    reviewed_path = parsed.path or ""
    reviewed_method = _extract_reviewed_method(str(request.get("reviewed_command") or ""))

    validation_errors = (
        tuple(allowed_scheme_errors)
        + tuple(allowed_host_errors)
        + tuple(allowed_method_errors)
    )

    if source_kind != "case_intake_brain_handoff_scoped_adapter_execution_request":
        return _blocked_review(
            request=request,
            source_kind=source_kind,
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
            allowed_scheme=allowed_scheme_clean,
            allowed_host=allowed_host_clean,
            allowed_method=allowed_method_clean,
            reviewed_scheme=reviewed_scheme,
            reviewed_host=reviewed_host,
            reviewed_path=reviewed_path,
            reviewed_method=reviewed_method,
            reason="Input is not a case_intake_brain_handoff_scoped_adapter_execution_request artifact.",
        )

    if _unsafe_request(request):
        return _blocked_review(
            request=request,
            source_kind=source_kind,
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
            allowed_scheme=allowed_scheme_clean,
            allowed_host=allowed_host_clean,
            allowed_method=allowed_method_clean,
            reviewed_scheme=reviewed_scheme,
            reviewed_host=reviewed_host,
            reviewed_path=reviewed_path,
            reviewed_method=reviewed_method,
            reason="Source scoped adapter execution request reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(request.get("blocked")):
        return _blocked_review(
            request=request,
            source_kind=source_kind,
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
            allowed_scheme=allowed_scheme_clean,
            allowed_host=allowed_host_clean,
            allowed_method=allowed_method_clean,
            reviewed_scheme=reviewed_scheme,
            reviewed_host=reviewed_host,
            reviewed_path=reviewed_path,
            reviewed_method=reviewed_method,
            reason=str(request.get("block_reason") or "Source scoped adapter execution request is blocked."),
        )

    if str(request.get("request_status") or "") != "ready-for-future-scoped-adapter-review-no-execution":
        validation_errors = validation_errors + ("Source request is not ready for future scoped adapter review.",)

    if str(request.get("scope_validation_state") or "") != "not_performed":
        validation_errors = validation_errors + ("Source request scope validation state must be not_performed before runtime scope review.",)

    if str(request.get("adapter_execution_state") or "") != "not_executed":
        validation_errors = validation_errors + ("Source request adapter execution state must be not_executed.",)

    if _strings(request.get("unresolved_placeholders")):
        validation_errors = validation_errors + ("Source request still contains unresolved placeholders.",)

    if not resolved_target_url.strip():
        validation_errors = validation_errors + ("Resolved target URL is required.",)

    if not reviewed_scheme:
        validation_errors = validation_errors + ("Resolved target URL scheme is missing.",)
    elif allowed_scheme_clean and reviewed_scheme != allowed_scheme_clean:
        validation_errors = validation_errors + (
            f"Resolved target URL scheme `{reviewed_scheme}` does not match allowed scheme `{allowed_scheme_clean}`.",
        )

    if not reviewed_host:
        validation_errors = validation_errors + ("Resolved target URL host is missing.",)
    elif allowed_host_clean and reviewed_host != allowed_host_clean:
        validation_errors = validation_errors + (
            f"Resolved target URL host `{reviewed_host}` does not match allowed host `{allowed_host_clean}`.",
        )

    if not reviewed_path:
        validation_errors = validation_errors + ("Resolved target URL path is missing.",)
    elif str(request.get("resolved_endpoint") or "") and reviewed_path != str(request.get("resolved_endpoint")):
        validation_errors = validation_errors + ("Resolved target URL path does not match resolved endpoint.",)

    if not reviewed_method:
        validation_errors = validation_errors + ("Reviewed command method could not be extracted.",)
    elif allowed_method_clean and reviewed_method != allowed_method_clean:
        validation_errors = validation_errors + (
            f"Reviewed command method `{reviewed_method}` does not match allowed method `{allowed_method_clean}`.",
        )

    if reviewed_method and reviewed_method not in READ_ONLY_METHODS:
        validation_errors = validation_errors + ("Reviewed command method is not read-only.",)

    if validation_errors:
        return _blocked_review(
            request=request,
            source_kind=source_kind,
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
            allowed_scheme=allowed_scheme_clean,
            allowed_host=allowed_host_clean,
            allowed_method=allowed_method_clean,
            reviewed_scheme=reviewed_scheme,
            reviewed_host=reviewed_host,
            reviewed_path=reviewed_path,
            reviewed_method=reviewed_method,
            reason=" ".join(validation_errors),
        )

    findings = (
        f"Allowed scheme `{allowed_scheme_clean}` matches reviewed scheme `{reviewed_scheme}`.",
        f"Allowed host `{allowed_host_clean}` matches reviewed host `{reviewed_host}`.",
        f"Allowed method `{allowed_method_clean}` matches reviewed method `{reviewed_method}`.",
        "Reviewed method is read-only.",
        "Resolved target URL path matches the resolved endpoint.",
        "Runtime scope review is local-only and did not execute the reviewed command.",
    )

    return CaseIntakeBrainScopedAdapterRuntimeScopeReview(
        review_id=f"RSR-{request_id}",
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
        request_purpose=str(request.get("request_purpose") or ""),
        requested_action=str(request.get("requested_action") or ""),
        target_base_url=str(request.get("target_base_url") or ""),
        resolved_endpoint=str(request.get("resolved_endpoint") or ""),
        resolved_target_url=resolved_target_url,
        reviewed_command=str(request.get("reviewed_command") or ""),
        reviewed_scheme=reviewed_scheme,
        reviewed_host=reviewed_host,
        reviewed_path=reviewed_path,
        reviewed_method=reviewed_method,
        allowed_scheme=allowed_scheme_clean,
        allowed_host=allowed_host_clean,
        allowed_method=allowed_method_clean,
        final_confirmation_decision=str(request.get("final_confirmation_decision") or "unknown"),
        final_confirmation_status=str(request.get("final_confirmation_status") or "unknown"),
        human_final_confirmation_recorded=bool(request.get("human_final_confirmation_recorded")),
        confirmed_by=str(request.get("confirmed_by") or "human-reviewer"),
        request_status=str(request.get("request_status") or "unknown"),
        request_scope_validation_state=str(request.get("scope_validation_state") or "unknown"),
        request_adapter_execution_state=str(request.get("adapter_execution_state") or "unknown"),
        runtime_scope_review_status="passed-local-runtime-scope-review-no-execution",
        scope_validation_state="reviewed_local_only",
        adapter_execution_state="not_executed",
        review_findings=findings,
        required_runtime_checks=tuple(_strings(request.get("required_runtime_checks"))),
        scope_check_requirements=tuple(_strings(request.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(request.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(request.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(request.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(request.get("required_preconditions"))),
        account_matrix=tuple(_strings(request.get("account_matrix"))),
        validation_steps=tuple(_strings(request.get("validation_steps"))),
        checklist_ids=tuple(_strings(request.get("checklist_ids"))),
        stop_conditions=tuple(_strings(request.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(request.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(request.get("unresolved_placeholders"))),
        blocked=False,
        block_reason="",
        dry_run_only=True,
        can_execute_now=False,
        runtime_scope_review_allows_execution=False,
    )


def _blocked_review(
    request: dict[str, Any],
    source_kind: str,
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
    allowed_scheme: str,
    allowed_host: str,
    allowed_method: str,
    reviewed_scheme: str,
    reviewed_host: str,
    reviewed_path: str,
    reviewed_method: str,
    reason: str,
) -> CaseIntakeBrainScopedAdapterRuntimeScopeReview:
    return CaseIntakeBrainScopedAdapterRuntimeScopeReview(
        review_id=f"RSR-BLOCKED-{request_id}",
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
        request_purpose=str(request.get("request_purpose") or ""),
        requested_action=str(request.get("requested_action") or "blocked"),
        target_base_url=str(request.get("target_base_url") or ""),
        resolved_endpoint=str(request.get("resolved_endpoint") or ""),
        resolved_target_url=str(request.get("resolved_target_url") or ""),
        reviewed_command=str(request.get("reviewed_command") or ""),
        reviewed_scheme=reviewed_scheme,
        reviewed_host=reviewed_host,
        reviewed_path=reviewed_path,
        reviewed_method=reviewed_method,
        allowed_scheme=allowed_scheme,
        allowed_host=allowed_host,
        allowed_method=allowed_method,
        final_confirmation_decision=str(request.get("final_confirmation_decision") or "unknown"),
        final_confirmation_status=str(request.get("final_confirmation_status") or "blocked"),
        human_final_confirmation_recorded=bool(request.get("human_final_confirmation_recorded")),
        confirmed_by=str(request.get("confirmed_by") or "human-reviewer"),
        request_status=str(request.get("request_status") or "blocked"),
        request_scope_validation_state=str(request.get("scope_validation_state") or "unknown"),
        request_adapter_execution_state=str(request.get("adapter_execution_state") or "unknown"),
        runtime_scope_review_status="blocked",
        scope_validation_state="blocked",
        adapter_execution_state="not_executed",
        review_findings=(reason,),
        required_runtime_checks=tuple(_strings(request.get("required_runtime_checks"))),
        scope_check_requirements=tuple(_strings(request.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(request.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(request.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(request.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(request.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(request.get("account_matrix"))),
        validation_steps=tuple(_strings(request.get("validation_steps"))),
        checklist_ids=tuple(_strings(request.get("checklist_ids"))),
        stop_conditions=tuple(_strings(request.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(request.get("redaction_requirements"))),
        unresolved_placeholders=tuple(_strings(request.get("unresolved_placeholders"))),
        blocked=True,
        block_reason=reason,
        dry_run_only=True,
        can_execute_now=False,
        runtime_scope_review_allows_execution=False,
    )


def _validate_allowed_scheme(value: str) -> tuple[str, tuple[str, ...]]:
    scheme = str(value or "").strip().lower()
    if not scheme:
        return "", ("Allowed scheme is required.",)
    if scheme != "https":
        return scheme, ("Allowed scheme must be https.",)
    return scheme, ()


def _validate_allowed_method(value: str) -> tuple[str, tuple[str, ...]]:
    method = str(value or "").strip().upper()
    if not method:
        return "", ("Allowed method is required.",)
    if method not in READ_ONLY_METHODS:
        return method, ("Allowed method must be read-only: GET, HEAD, or OPTIONS.",)
    return method, ()


def _validate_allowed_host(value: str) -> tuple[str, tuple[str, ...]]:
    host = str(value or "").strip().lower()
    if not host:
        return "", ("Allowed host is required.",)
    if "://" in host or "/" in host or "?" in host or "#" in host:
        return host, ("Allowed host must be a hostname only, not a URL.",)
    if host in {"localhost", "metadata.google.internal"} or host.endswith(".localhost"):
        return host, ("Allowed host is not allowed.",)

    try:
        parsed_ip = ip_address(host)
    except ValueError:
        return host, ()

    if (
        parsed_ip.is_loopback
        or parsed_ip.is_private
        or parsed_ip.is_link_local
        or parsed_ip.is_multicast
        or parsed_ip.is_reserved
        or parsed_ip.is_unspecified
    ):
        return host, ("Allowed host IP address is not allowed.",)

    return host, ()


def _extract_reviewed_method(command: str) -> str:
    if not command.strip():
        return ""

    try:
        parts = shlex.split(command)
    except ValueError:
        return ""

    for index, part in enumerate(parts):
        normalized = part.strip().lower()
        if normalized in {"--request", "-X"} and index + 1 < len(parts):
            return parts[index + 1].strip().upper()
        if normalized.startswith("--request="):
            return normalized.split("=", 1)[1].strip().upper()

    return "GET" if parts and parts[0] == "curl" else ""


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_request(request: dict[str, Any]) -> bool:
    safety = request.get("safety") if isinstance(request.get("safety"), dict) else {}
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
        bool(request.get(key))
        for key in (
            "can_execute_now",
            "execution_request_allows_execution",
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
