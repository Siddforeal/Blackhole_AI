"""
Brain handoff runtime safety manifest.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_execution_approval_gate artifact into
a runtime safety manifest for a future adapter.

The manifest describes what a future adapter must verify before execution.
It does not execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_ADAPTER_FAMILIES: tuple[str, ...] = ("curl",)


@dataclass(frozen=True)
class CaseIntakeBrainRuntimeSafetyManifest:
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
    command_purpose: str
    proposed_command: str
    proposed_command_tokens: tuple[str, ...]
    execution_decision: str
    execution_gate_status: str
    human_execution_approval_recorded: bool
    runtime_manifest_status: str
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
    blocked: bool
    block_reason: str
    can_execute_now: bool
    manifest_allows_execution: bool
    requires_runtime_scope_check: bool
    requires_final_human_confirmation: bool
    requires_adapter_safety_check: bool
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
    source: str = "case-intake-brain-handoff-runtime-safety-manifest"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_runtime_safety_manifest",
            "source": self.source,
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
            "command_purpose": self.command_purpose,
            "proposed_command": self.proposed_command,
            "proposed_command_tokens": list(self.proposed_command_tokens),
            "execution_decision": self.execution_decision,
            "execution_gate_status": self.execution_gate_status,
            "human_execution_approval_recorded": self.human_execution_approval_recorded,
            "runtime_manifest_status": self.runtime_manifest_status,
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
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "can_execute_now": self.can_execute_now,
            "manifest_allows_execution": self.manifest_allows_execution,
            "requires_runtime_scope_check": self.requires_runtime_scope_check,
            "requires_final_human_confirmation": self.requires_final_human_confirmation,
            "requires_adapter_safety_check": self.requires_adapter_safety_check,
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

    def to_markdown(self, title: str = "Case Intake Brain Runtime Safety Manifest") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
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
            f"- Execution decision: `{self.execution_decision}`",
            f"- Execution gate status: `{self.execution_gate_status}`",
            f"- Runtime manifest status: `{self.runtime_manifest_status}`",
            f"- Human execution approval recorded: `{self.human_execution_approval_recorded}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Manifest allows execution: `{self.manifest_allows_execution}`",
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
            "## Proposed Command Under Manifest",
            "",
            "```bash",
            self.proposed_command or "# No command available because this manifest is blocked.",
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
            "## Runtime Scope Check Requirements",
            "",
        ]

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


def export_case_intake_brain_handoff_runtime_safety_manifest(
    execution_approval_gate: dict[str, Any],
    adapter_family: str,
) -> CaseIntakeBrainRuntimeSafetyManifest:
    gate = execution_approval_gate if isinstance(execution_approval_gate, dict) else {}
    family = str(adapter_family or "").strip().lower()

    target_name = str(gate.get("target_name") or "bug-bounty-target")
    source_kind = str(gate.get("kind") or "unknown")
    gate_id = str(gate.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(gate.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(gate.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(gate.get("approval_id") or "AP-UNKNOWN")
    endpoint = str(gate.get("endpoint") or "unknown-endpoint")
    command_family = str(gate.get("command_family") or "unknown")

    if source_kind != "case_intake_brain_handoff_execution_approval_gate":
        return _blocked_manifest(
            target_name=target_name,
            source_kind=source_kind,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=family or "unknown",
            command_family=command_family,
            reason="Input is not a case_intake_brain_handoff_execution_approval_gate artifact.",
            gate=gate,
        )

    if family not in SUPPORTED_ADAPTER_FAMILIES:
        return _blocked_manifest(
            target_name=target_name,
            source_kind=source_kind,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=family or "unknown",
            command_family=command_family,
            reason="Unsupported adapter family. Supported adapter families: curl.",
            gate=gate,
        )

    if _unsafe_gate(gate):
        return _blocked_manifest(
            target_name=target_name,
            source_kind=source_kind,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=family,
            command_family=command_family,
            reason="Source execution approval gate reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
            gate=gate,
        )

    if bool(gate.get("blocked")):
        return _blocked_manifest(
            target_name=target_name,
            source_kind=source_kind,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=family,
            command_family=command_family,
            reason=str(gate.get("original_proposal_block_reason") or "Source execution approval gate is blocked."),
            gate=gate,
        )

    if str(gate.get("execution_decision") or "") != "approved" or not bool(gate.get("human_execution_approval_recorded")):
        return _blocked_manifest(
            target_name=target_name,
            source_kind=source_kind,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=family,
            command_family=command_family,
            reason="Execution approval gate must be approved and human_execution_approval_recorded must be true before exporting a runtime safety manifest.",
            gate=gate,
        )

    return CaseIntakeBrainRuntimeSafetyManifest(
        manifest_id=f"RSM-{gate_id}",
        gate_id=gate_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        adapter_family=family,
        command_family=command_family,
        command_purpose=str(gate.get("command_purpose") or "unknown"),
        proposed_command=str(gate.get("proposed_command") or ""),
        proposed_command_tokens=tuple(_strings(gate.get("proposed_command_tokens"))),
        execution_decision=str(gate.get("execution_decision") or "unknown"),
        execution_gate_status=str(gate.get("execution_gate_status") or "unknown"),
        human_execution_approval_recorded=bool(gate.get("human_execution_approval_recorded")),
        runtime_manifest_status="ready-for-future-adapter-review-no-execution",
        scope_check_requirements=_scope_check_requirements(),
        placeholder_check_requirements=_placeholder_check_requirements(),
        adapter_safety_requirements=_adapter_safety_requirements(),
        final_human_confirmation_requirements=_final_human_confirmation_requirements(),
        required_preconditions=tuple(_strings(gate.get("required_preconditions"))),
        account_matrix=tuple(_strings(gate.get("account_matrix"))),
        validation_steps=tuple(_strings(gate.get("validation_steps"))),
        checklist_ids=tuple(_strings(gate.get("checklist_ids"))),
        stop_conditions=tuple(_strings(gate.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(gate.get("redaction_requirements"))),
        blocked=False,
        block_reason="",
        can_execute_now=False,
        manifest_allows_execution=False,
        requires_runtime_scope_check=True,
        requires_final_human_confirmation=True,
        requires_adapter_safety_check=True,
    )


def _blocked_manifest(
    target_name: str,
    source_kind: str,
    gate_id: str,
    proposal_id: str,
    decision_id: str,
    approval_id: str,
    endpoint: str,
    adapter_family: str,
    command_family: str,
    reason: str,
    gate: dict[str, Any] | None = None,
) -> CaseIntakeBrainRuntimeSafetyManifest:
    gate_data = gate or {}
    return CaseIntakeBrainRuntimeSafetyManifest(
        manifest_id=f"RSM-BLOCKED-{gate_id}",
        gate_id=gate_id,
        proposal_id=proposal_id,
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        adapter_family=adapter_family,
        command_family=command_family,
        command_purpose=str(gate_data.get("command_purpose") or "blocked"),
        proposed_command=str(gate_data.get("proposed_command") or ""),
        proposed_command_tokens=tuple(_strings(gate_data.get("proposed_command_tokens"))),
        execution_decision=str(gate_data.get("execution_decision") or "unknown"),
        execution_gate_status=str(gate_data.get("execution_gate_status") or "blocked"),
        human_execution_approval_recorded=False,
        runtime_manifest_status="blocked",
        scope_check_requirements=_scope_check_requirements(),
        placeholder_check_requirements=_placeholder_check_requirements(),
        adapter_safety_requirements=_adapter_safety_requirements(),
        final_human_confirmation_requirements=_final_human_confirmation_requirements(),
        required_preconditions=tuple(_strings(gate_data.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(gate_data.get("account_matrix"))),
        validation_steps=tuple(_strings(gate_data.get("validation_steps"))),
        checklist_ids=tuple(_strings(gate_data.get("checklist_ids"))),
        stop_conditions=tuple(_strings(gate_data.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(gate_data.get("redaction_requirements"))),
        blocked=True,
        block_reason=reason,
        can_execute_now=False,
        manifest_allows_execution=False,
        requires_runtime_scope_check=True,
        requires_final_human_confirmation=True,
        requires_adapter_safety_check=True,
    )


def _scope_check_requirements() -> tuple[str, ...]:
    return (
        "Adapter must verify the target base URL is explicitly in scope before any request can be prepared.",
        "Adapter must reject private, loopback, link-local, metadata, and non-program-owned hosts unless explicitly allowed by scope.",
        "Adapter must verify the endpoint path still matches the approved command proposal.",
        "Adapter must verify the HTTP method is read-only for the selected adapter family.",
        "Adapter must block execution if scope, method, host, or endpoint cannot be proven safe.",
    )


def _placeholder_check_requirements() -> tuple[str, ...]:
    return (
        "`{{TARGET_BASE_URL}}` must be replaced only with a confirmed in-scope HTTPS base URL.",
        "`{{CONTROLLED_ACCOUNT_TOKEN}}` must be supplied only from a controlled test account.",
        "Path parameters such as `{id}` must be replaced only with synthetic controlled-account identifiers.",
        "No production personal data, payment data, invoice data, or real user file identifiers may be used.",
        "Execution must be blocked if any placeholder remains unresolved.",
    )


def _adapter_safety_requirements() -> tuple[str, ...]:
    return (
        "Adapter must run in read-only mode for this manifest.",
        "Adapter must not add mutation methods such as POST, PUT, PATCH, or DELETE.",
        "Adapter must not follow redirects to out-of-scope hosts.",
        "Adapter must not retry aggressively, fuzz, brute force, scan, crawl, or enumerate.",
        "Adapter must not write files, submit reports, confirm vulnerabilities, or collect evidence automatically.",
        "Adapter must preserve a dry-run preview before any future execution path.",
    )


def _final_human_confirmation_requirements() -> tuple[str, ...]:
    return (
        "Human must review the resolved target URL before any future adapter execution.",
        "Human must review the resolved headers and confirm no secret will be stored in logs.",
        "Human must confirm controlled-account-only data is being used.",
        "Human must confirm stop conditions are understood.",
        "Human must provide a final explicit execution confirmation in a future adapter-specific flow.",
    )


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_gate(gate: dict[str, Any]) -> bool:
    safety = gate.get("safety") if isinstance(gate.get("safety"), dict) else {}
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
        bool(gate.get(key))
        for key in (
            "can_execute_now",
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
