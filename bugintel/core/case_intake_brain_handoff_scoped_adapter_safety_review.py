"""
Brain handoff scoped adapter safety review.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_scoped_adapter_runtime_scope_review
artifact into a local adapter safety review artifact.

The review inspects the reviewed curl command for unsafe methods, redirects,
retry behavior, upload/write flags, shell control operators, and broad
automation patterns. It does not execute curl, Burp, browser, terminal, or any
tool.
"""

from __future__ import annotations

from dataclasses import dataclass
import shlex
from typing import Any


READ_ONLY_METHODS: tuple[str, ...] = ("GET", "HEAD", "OPTIONS")

BLOCKED_FLAGS: tuple[str, ...] = (
    "-d",
    "--data",
    "--data-raw",
    "--data-binary",
    "--data-urlencode",
    "--form",
    "-F",
    "--upload-file",
    "-T",
    "--request-target",
    "-o",
    "--output",
    "-O",
    "--remote-name",
    "--remote-header-name",
    "-L",
    "--location",
    "--location-trusted",
    "--retry",
    "--retry-all-errors",
    "--retry-connrefused",
    "--parallel",
    "--next",
)

REQUIRED_SAFE_FLAGS: tuple[str, ...] = (
    "--max-time",
    "--silent",
    "--show-error",
    "--fail-with-body",
)

SHELL_CONTROL_PATTERNS: tuple[str, ...] = (
    "\n",
    "\r",
    ";",
    "&&",
    "||",
    "`",
    "$(",
    "|",
    ">",
    "<",
)


@dataclass(frozen=True)
class CaseIntakeBrainScopedAdapterSafetyReview:
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
    allowed_scheme: str
    allowed_host: str
    allowed_method: str
    runtime_scope_review_status: str
    runtime_scope_validation_state: str
    runtime_adapter_execution_state: str
    adapter_safety_review_status: str
    adapter_safety_state: str
    adapter_execution_state: str
    parsed_command_tokens: tuple[str, ...]
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
    adapter_safety_review_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-scoped-adapter-safety-review"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_scoped_adapter_safety_review",
            "source": self.source,
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
            "allowed_scheme": self.allowed_scheme,
            "allowed_host": self.allowed_host,
            "allowed_method": self.allowed_method,
            "runtime_scope_review_status": self.runtime_scope_review_status,
            "runtime_scope_validation_state": self.runtime_scope_validation_state,
            "runtime_adapter_execution_state": self.runtime_adapter_execution_state,
            "adapter_safety_review_status": self.adapter_safety_review_status,
            "adapter_safety_state": self.adapter_safety_state,
            "adapter_execution_state": self.adapter_execution_state,
            "parsed_command_tokens": list(self.parsed_command_tokens),
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
            "adapter_safety_review_allows_execution": self.adapter_safety_review_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Scoped Adapter Safety Review") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
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
            f"- Adapter execution state: `{self.adapter_execution_state}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Adapter safety review allows execution: `{self.adapter_safety_review_allows_execution}`",
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
            self.reviewed_command or "# No reviewed command available because this adapter safety review is blocked.",
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


def export_case_intake_brain_handoff_scoped_adapter_safety_review(
    scoped_adapter_runtime_scope_review: dict[str, Any],
) -> CaseIntakeBrainScopedAdapterSafetyReview:
    review = scoped_adapter_runtime_scope_review if isinstance(scoped_adapter_runtime_scope_review, dict) else {}

    source_kind = str(review.get("kind") or "unknown")
    runtime_scope_review_id = str(review.get("review_id") or "RSR-UNKNOWN")
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

    command = str(review.get("reviewed_command") or "")
    parsed_tokens, parse_errors = _parse_command(command)
    reviewed_method = str(review.get("reviewed_method") or "").strip().upper()
    present_safe_flags = tuple(flag for flag in REQUIRED_SAFE_FLAGS if _flag_present(parsed_tokens, flag))
    missing_safe_flags = tuple(flag for flag in REQUIRED_SAFE_FLAGS if flag not in present_safe_flags)
    blocked_flags_seen = _blocked_flags_seen(parsed_tokens)
    shell_control_patterns_seen = _shell_control_patterns_seen(command)

    validation_errors = list(parse_errors)

    if source_kind != "case_intake_brain_handoff_scoped_adapter_runtime_scope_review":
        return _blocked_review(
            review=review,
            source_kind=source_kind,
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
            parsed_tokens=parsed_tokens,
            present_safe_flags=present_safe_flags,
            missing_safe_flags=missing_safe_flags,
            blocked_flags_seen=blocked_flags_seen,
            shell_control_patterns_seen=shell_control_patterns_seen,
            reason="Input is not a case_intake_brain_handoff_scoped_adapter_runtime_scope_review artifact.",
        )

    if _unsafe_review(review):
        return _blocked_review(
            review=review,
            source_kind=source_kind,
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
            parsed_tokens=parsed_tokens,
            present_safe_flags=present_safe_flags,
            missing_safe_flags=missing_safe_flags,
            blocked_flags_seen=blocked_flags_seen,
            shell_control_patterns_seen=shell_control_patterns_seen,
            reason="Source runtime scope review reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(review.get("blocked")):
        return _blocked_review(
            review=review,
            source_kind=source_kind,
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
            parsed_tokens=parsed_tokens,
            present_safe_flags=present_safe_flags,
            missing_safe_flags=missing_safe_flags,
            blocked_flags_seen=blocked_flags_seen,
            shell_control_patterns_seen=shell_control_patterns_seen,
            reason=str(review.get("block_reason") or "Source runtime scope review is blocked."),
        )

    if str(review.get("runtime_scope_review_status") or "") != "passed-local-runtime-scope-review-no-execution":
        validation_errors.append("Source runtime scope review has not passed.")

    if str(review.get("scope_validation_state") or "") != "reviewed_local_only":
        validation_errors.append("Source scope validation state must be reviewed_local_only.")

    if str(review.get("adapter_execution_state") or "") != "not_executed":
        validation_errors.append("Source adapter execution state must be not_executed.")

    if adapter_family != "curl" or command_family != "curl":
        validation_errors.append("Adapter safety review currently supports only curl.")

    if not parsed_tokens:
        validation_errors.append("Reviewed command could not be parsed.")

    if parsed_tokens and parsed_tokens[0] != "curl":
        validation_errors.append("Reviewed command must start with curl.")

    if reviewed_method not in READ_ONLY_METHODS:
        validation_errors.append("Reviewed command method must be read-only: GET, HEAD, or OPTIONS.")

    if missing_safe_flags:
        validation_errors.append("Reviewed command is missing required safe curl flags.")

    if blocked_flags_seen:
        validation_errors.append("Reviewed command contains blocked curl flags.")

    if shell_control_patterns_seen:
        validation_errors.append("Reviewed command contains shell control patterns.")

    if _strings(review.get("unresolved_placeholders")):
        validation_errors.append("Source runtime scope review still contains unresolved placeholders.")

    if validation_errors:
        return _blocked_review(
            review=review,
            source_kind=source_kind,
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
            parsed_tokens=parsed_tokens,
            present_safe_flags=present_safe_flags,
            missing_safe_flags=missing_safe_flags,
            blocked_flags_seen=blocked_flags_seen,
            shell_control_patterns_seen=shell_control_patterns_seen,
            reason=" ".join(validation_errors),
        )

    safe_findings = (
        "Reviewed command parses as a single curl invocation.",
        f"Reviewed method `{reviewed_method}` is read-only.",
        "No blocked mutation, upload, write, redirect, retry, parallel, or chained curl flags were found.",
        "No shell control operators were found.",
        "Required safe curl flags are present.",
        "Adapter safety review is local-only and did not execute the reviewed command.",
    )

    return CaseIntakeBrainScopedAdapterSafetyReview(
        safety_review_id=f"ASR-{runtime_scope_review_id}",
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
        reviewed_command=command,
        reviewed_method=reviewed_method,
        reviewed_scheme=str(review.get("reviewed_scheme") or ""),
        reviewed_host=str(review.get("reviewed_host") or ""),
        reviewed_path=str(review.get("reviewed_path") or ""),
        allowed_scheme=str(review.get("allowed_scheme") or ""),
        allowed_host=str(review.get("allowed_host") or ""),
        allowed_method=str(review.get("allowed_method") or ""),
        runtime_scope_review_status=str(review.get("runtime_scope_review_status") or ""),
        runtime_scope_validation_state=str(review.get("scope_validation_state") or ""),
        runtime_adapter_execution_state=str(review.get("adapter_execution_state") or ""),
        adapter_safety_review_status="passed-local-adapter-safety-review-no-execution",
        adapter_safety_state="reviewed_local_only",
        adapter_execution_state="not_executed",
        parsed_command_tokens=parsed_tokens,
        safe_command_findings=safe_findings,
        blocked_command_findings=(),
        required_safe_flags=REQUIRED_SAFE_FLAGS,
        present_safe_flags=present_safe_flags,
        missing_safe_flags=missing_safe_flags,
        blocked_flags_seen=blocked_flags_seen,
        shell_control_patterns_seen=shell_control_patterns_seen,
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
        adapter_safety_review_allows_execution=False,
    )


def _blocked_review(
    review: dict[str, Any],
    source_kind: str,
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
    parsed_tokens: tuple[str, ...],
    present_safe_flags: tuple[str, ...],
    missing_safe_flags: tuple[str, ...],
    blocked_flags_seen: tuple[str, ...],
    shell_control_patterns_seen: tuple[str, ...],
    reason: str,
) -> CaseIntakeBrainScopedAdapterSafetyReview:
    return CaseIntakeBrainScopedAdapterSafetyReview(
        safety_review_id=f"ASR-BLOCKED-{runtime_scope_review_id}",
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
        allowed_scheme=str(review.get("allowed_scheme") or ""),
        allowed_host=str(review.get("allowed_host") or ""),
        allowed_method=str(review.get("allowed_method") or ""),
        runtime_scope_review_status=str(review.get("runtime_scope_review_status") or "blocked"),
        runtime_scope_validation_state=str(review.get("scope_validation_state") or "blocked"),
        runtime_adapter_execution_state=str(review.get("adapter_execution_state") or "not_executed"),
        adapter_safety_review_status="blocked",
        adapter_safety_state="blocked",
        adapter_execution_state="not_executed",
        parsed_command_tokens=parsed_tokens,
        safe_command_findings=(),
        blocked_command_findings=(reason,),
        required_safe_flags=REQUIRED_SAFE_FLAGS,
        present_safe_flags=present_safe_flags,
        missing_safe_flags=missing_safe_flags,
        blocked_flags_seen=blocked_flags_seen,
        shell_control_patterns_seen=shell_control_patterns_seen,
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
        block_reason=reason,
        dry_run_only=True,
        can_execute_now=False,
        adapter_safety_review_allows_execution=False,
    )


def _parse_command(command: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not command.strip():
        return (), ("Reviewed command is required.",)

    try:
        return tuple(shlex.split(command)), ()
    except ValueError:
        return (), ("Reviewed command could not be parsed safely.",)


def _flag_present(tokens: tuple[str, ...], flag: str) -> bool:
    return flag in tokens or any(token.startswith(f"{flag}=") for token in tokens)


def _blocked_flags_seen(tokens: tuple[str, ...]) -> tuple[str, ...]:
    seen: list[str] = []
    for token in tokens:
        for flag in BLOCKED_FLAGS:
            if token == flag or token.startswith(f"{flag}="):
                seen.append(token)
    return tuple(seen)


def _shell_control_patterns_seen(command: str) -> tuple[str, ...]:
    return tuple(pattern for pattern in SHELL_CONTROL_PATTERNS if pattern in command)


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
            "runtime_scope_review_allows_execution",
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
