"""
Brain handoff read-only command proposal exporter.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts an approved case_intake_brain_handoff_approval_decision artifact
into a reviewable read-only command proposal. The proposed command uses
placeholders and is not executed by this module.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_COMMAND_FAMILIES: tuple[str, ...] = ("curl",)


@dataclass(frozen=True)
class CaseIntakeBrainReadOnlyCommandProposal:
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
    placeholder_requirements: tuple[str, ...]
    required_preconditions: tuple[str, ...]
    account_matrix: tuple[str, ...]
    validation_steps: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    redaction_requirements: tuple[str, ...]
    blocked: bool
    block_reason: str
    requires_separate_execution_approval: bool
    human_review_required: bool
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
    source: str = "case-intake-brain-handoff-read-only-command-proposal-exporter"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_read_only_command_proposal",
            "source": self.source,
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
            "placeholder_requirements": list(self.placeholder_requirements),
            "required_preconditions": list(self.required_preconditions),
            "account_matrix": list(self.account_matrix),
            "validation_steps": list(self.validation_steps),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "redaction_requirements": list(self.redaction_requirements),
            "blocked": self.blocked,
            "block_reason": self.block_reason,
            "requires_separate_execution_approval": self.requires_separate_execution_approval,
            "human_review_required": self.human_review_required,
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

    def to_markdown(self, title: str = "Case Intake Brain Read-Only Command Proposal") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Proposal ID: `{self.proposal_id}`",
            f"- Decision ID: `{self.decision_id}`",
            f"- Approval ID: `{self.approval_id}`",
            f"- Target: `{self.target_name}`",
            f"- Source kind: `{self.source_kind}`",
            f"- Endpoint: `{self.endpoint}`",
            f"- Command family: `{self.command_family}`",
            f"- Command purpose: `{self.command_purpose}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Human review required: `{self.human_review_required}`",
            f"- Separate execution approval required: `{self.requires_separate_execution_approval}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Proposed Command",
            "",
            "```bash",
            self.proposed_command or "# No command proposed because this artifact is blocked.",
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


def export_case_intake_brain_handoff_read_only_command_proposal(
    approval_decision: dict[str, Any],
    command_family: str,
) -> CaseIntakeBrainReadOnlyCommandProposal:
    decision = approval_decision if isinstance(approval_decision, dict) else {}
    family = str(command_family or "").strip().lower()
    target_name = str(decision.get("target_name") or "bug-bounty-target")
    source_kind = str(decision.get("kind") or "unknown")
    decision_id = str(decision.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(decision.get("approval_id") or "AP-UNKNOWN")
    endpoint = str(decision.get("endpoint") or "unknown-endpoint")

    if source_kind != "case_intake_brain_handoff_approval_decision":
        return _blocked_proposal(
            target_name=target_name,
            source_kind=source_kind,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=family or "unknown",
            reason="Input is not a case_intake_brain_handoff_approval_decision artifact.",
            decision=decision,
        )

    if family not in SUPPORTED_COMMAND_FAMILIES:
        return _blocked_proposal(
            target_name=target_name,
            source_kind=source_kind,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=family or "unknown",
            reason="Unsupported command family. Supported command families: curl.",
            decision=decision,
        )

    if _unsafe_decision(decision):
        return _blocked_proposal(
            target_name=target_name,
            source_kind=source_kind,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=family,
            reason="Source approval decision reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
            decision=decision,
        )

    if bool(decision.get("blocked")):
        return _blocked_proposal(
            target_name=target_name,
            source_kind=source_kind,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=family,
            reason=str(decision.get("packet_block_reason") or "Source approval decision is blocked."),
            decision=decision,
        )

    if str(decision.get("decision") or "") != "approved" or not bool(decision.get("human_approval_recorded")):
        return _blocked_proposal(
            target_name=target_name,
            source_kind=source_kind,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            command_family=family,
            reason="Approval decision must be approved and human_approval_recorded must be true before proposing a command.",
            decision=decision,
        )

    command_tokens = _curl_command_tokens(endpoint)

    return CaseIntakeBrainReadOnlyCommandProposal(
        proposal_id=f"CP-{decision_id}",
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        command_family=family,
        command_purpose="read-only-controlled-baseline-request-proposal",
        proposed_command=" ".join(command_tokens),
        proposed_command_tokens=command_tokens,
        placeholder_requirements=_placeholder_requirements(),
        required_preconditions=_required_preconditions(),
        account_matrix=tuple(_strings(decision.get("account_matrix"))),
        validation_steps=tuple(_strings(decision.get("validation_steps"))),
        checklist_ids=tuple(_strings(decision.get("checklist_ids"))),
        stop_conditions=tuple(_strings(decision.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(decision.get("redaction_requirements"))),
        blocked=False,
        block_reason="",
        requires_separate_execution_approval=True,
        human_review_required=True,
    )


def _blocked_proposal(
    target_name: str,
    source_kind: str,
    decision_id: str,
    approval_id: str,
    endpoint: str,
    command_family: str,
    reason: str,
    decision: dict[str, Any] | None = None,
) -> CaseIntakeBrainReadOnlyCommandProposal:
    decision_data = decision or {}
    return CaseIntakeBrainReadOnlyCommandProposal(
        proposal_id=f"CP-BLOCKED-{decision_id}",
        decision_id=decision_id,
        approval_id=approval_id,
        target_name=target_name,
        source_kind=source_kind,
        endpoint=endpoint,
        command_family=command_family,
        command_purpose="blocked",
        proposed_command="",
        proposed_command_tokens=(),
        placeholder_requirements=_placeholder_requirements(),
        required_preconditions=("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(decision_data.get("account_matrix"))),
        validation_steps=tuple(_strings(decision_data.get("validation_steps"))),
        checklist_ids=tuple(_strings(decision_data.get("checklist_ids"))),
        stop_conditions=tuple(_strings(decision_data.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(decision_data.get("redaction_requirements"))),
        blocked=True,
        block_reason=reason,
        requires_separate_execution_approval=True,
        human_review_required=True,
    )


def _curl_command_tokens(endpoint: str) -> tuple[str, ...]:
    safe_endpoint = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    return (
        "curl",
        "--request",
        "GET",
        "--url",
        f"'{{{{TARGET_BASE_URL}}}}{safe_endpoint}'",
        "--header",
        "'Authorization: Bearer {{CONTROLLED_ACCOUNT_TOKEN}}'",
        "--header",
        "'Accept: application/json'",
        "--max-time",
        "10",
        "--silent",
        "--show-error",
        "--fail-with-body",
    )


def _placeholder_requirements() -> tuple[str, ...]:
    return (
        "`{{TARGET_BASE_URL}}` must be an in-scope target base URL confirmed by the program rules.",
        "`{{CONTROLLED_ACCOUNT_TOKEN}}` must belong only to a controlled test account.",
        "Object identifiers in the endpoint must be replaced only with synthetic controlled-account identifiers.",
        "No production user data, real payment data, real invoice data, or real files may be used.",
    )


def _required_preconditions() -> tuple[str, ...]:
    return (
        "Human must review this proposal before any command is copied or run.",
        "A separate execution approval artifact is required before any terminal, browser, Burp, curl, or tool execution.",
        "The request must remain read-only and must not mutate target state.",
        "All tokens, cookies, identifiers, personal data, and secrets must be redacted from any notes or later evidence.",
        "Stop conditions from the approval packet remain binding.",
    )


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_decision(decision: dict[str, Any]) -> bool:
    safety = decision.get("safety") if isinstance(decision.get("safety"), dict) else {}
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
        bool(decision.get(key))
        for key in (
            "can_proceed_to_execution",
            "validation_allowed",
            "runtime_execution_allowed",
            "tool_execution_allowed",
            "browser_execution_allowed",
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
