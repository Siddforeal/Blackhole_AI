"""
Brain handoff adapter dry-run preview.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts a case_intake_brain_handoff_runtime_safety_manifest artifact into
a resolved dry-run preview for a future adapter.

The preview may resolve placeholders into a command preview string. It does not
execute curl, Burp, browser, terminal, or any tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from ipaddress import ip_address
import re
from typing import Any
from urllib.parse import urlparse


SUPPORTED_DRY_RUN_ADAPTER_FAMILIES: tuple[str, ...] = ("curl",)


@dataclass(frozen=True)
class CaseIntakeBrainAdapterDryRunPreview:
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
    command_purpose: str
    target_base_url: str
    resolved_endpoint: str
    resolved_target_url: str
    controlled_account_token_placeholder: str
    path_parameters: tuple[str, ...]
    proposed_command: str
    resolved_command_preview: str
    unresolved_placeholders: tuple[str, ...]
    runtime_manifest_status: str
    dry_run_preview_status: str
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
    dry_run_only: bool
    preview_ready: bool
    can_execute_now: bool
    preview_allows_execution: bool
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
    source: str = "case-intake-brain-handoff-adapter-dry-run-preview"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_adapter_dry_run_preview",
            "source": self.source,
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
            "command_purpose": self.command_purpose,
            "target_base_url": self.target_base_url,
            "resolved_endpoint": self.resolved_endpoint,
            "resolved_target_url": self.resolved_target_url,
            "controlled_account_token_placeholder": self.controlled_account_token_placeholder,
            "path_parameters": list(self.path_parameters),
            "proposed_command": self.proposed_command,
            "resolved_command_preview": self.resolved_command_preview,
            "unresolved_placeholders": list(self.unresolved_placeholders),
            "runtime_manifest_status": self.runtime_manifest_status,
            "dry_run_preview_status": self.dry_run_preview_status,
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
            "dry_run_only": self.dry_run_only,
            "preview_ready": self.preview_ready,
            "can_execute_now": self.can_execute_now,
            "preview_allows_execution": self.preview_allows_execution,
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

    def to_markdown(self, title: str = "Case Intake Brain Adapter Dry-Run Preview") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
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
            f"- Runtime manifest status: `{self.runtime_manifest_status}`",
            f"- Dry-run preview status: `{self.dry_run_preview_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Block reason: `{self.block_reason or 'none'}`",
            f"- Dry-run only: `{self.dry_run_only}`",
            f"- Preview ready: `{self.preview_ready}`",
            f"- Can execute now: `{self.can_execute_now}`",
            f"- Preview allows execution: `{self.preview_allows_execution}`",
            f"- Execution allowed: `{self.execution_allowed}`",
            f"- Tool execution allowed: `{self.tool_execution_allowed}`",
            f"- Network requests allowed: `{self.network_requests_allowed}`",
            f"- Evidence collection allowed: `{self.evidence_collection_allowed}`",
            f"- Target mutation allowed: `{self.target_mutation_allowed}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Resolved Dry-Run Command Preview",
            "",
            "```bash",
            self.resolved_command_preview or "# No command preview available because this dry-run preview is blocked.",
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
            "## Path Parameters",
            "",
        ]

        lines.extend(_markdown_list(self.path_parameters))
        lines.extend(["", "## Unresolved Placeholders", ""])
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


def export_case_intake_brain_handoff_adapter_dry_run_preview(
    runtime_safety_manifest: dict[str, Any],
    target_base_url: str,
    controlled_account_token_placeholder: str,
    path_parameters: list[str] | tuple[str, ...] | None = None,
) -> CaseIntakeBrainAdapterDryRunPreview:
    manifest = runtime_safety_manifest if isinstance(runtime_safety_manifest, dict) else {}

    source_kind = str(manifest.get("kind") or "unknown")
    manifest_id = str(manifest.get("manifest_id") or "RSM-UNKNOWN")
    gate_id = str(manifest.get("gate_id") or "EG-UNKNOWN")
    proposal_id = str(manifest.get("proposal_id") or "CP-UNKNOWN")
    decision_id = str(manifest.get("decision_id") or "AD-UNKNOWN")
    approval_id = str(manifest.get("approval_id") or "AP-UNKNOWN")
    target_name = str(manifest.get("target_name") or "bug-bounty-target")
    endpoint = str(manifest.get("endpoint") or "unknown-endpoint")
    adapter_family = str(manifest.get("adapter_family") or "unknown").strip().lower()
    command_family = str(manifest.get("command_family") or "unknown").strip().lower()

    if source_kind != "case_intake_brain_handoff_runtime_safety_manifest":
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason="Input is not a case_intake_brain_handoff_runtime_safety_manifest artifact.",
        )

    if adapter_family not in SUPPORTED_DRY_RUN_ADAPTER_FAMILIES:
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason="Unsupported adapter family. Supported adapter families: curl.",
        )

    if _unsafe_manifest(manifest):
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason="Source runtime safety manifest reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    if bool(manifest.get("blocked")):
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason=str(manifest.get("block_reason") or "Source runtime safety manifest is blocked."),
        )

    if bool(manifest.get("manifest_allows_execution")) or bool(manifest.get("can_execute_now")):
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason="Runtime safety manifest must not allow execution before dry-run preview.",
        )

    normalized_base_url, base_url_errors = _validate_target_base_url(target_base_url)
    token_placeholder, token_errors = _validate_token_placeholder(controlled_account_token_placeholder)
    path_parameter_map, parameter_errors = _parse_path_parameters(path_parameters or ())

    endpoint_placeholders = _path_placeholder_names(endpoint)
    missing_path_parameters = tuple(
        name for name in endpoint_placeholders if name not in path_parameter_map
    )

    validation_errors = tuple(base_url_errors) + tuple(token_errors) + tuple(parameter_errors)
    if missing_path_parameters:
        validation_errors = validation_errors + (
            "Missing path parameter replacement(s): " + ", ".join(missing_path_parameters) + ".",
        )

    proposed_command = str(manifest.get("proposed_command") or "")
    if not proposed_command.strip():
        validation_errors = validation_errors + ("Runtime safety manifest does not contain a proposed command.",)

    resolved_endpoint = _resolve_endpoint(endpoint, path_parameter_map)
    resolved_target_url = f"{normalized_base_url}{resolved_endpoint}" if normalized_base_url else ""

    resolved_command_preview = _resolve_command(
        proposed_command=proposed_command,
        target_base_url=normalized_base_url,
        token_placeholder=token_placeholder,
        path_parameter_map=path_parameter_map,
    )
    unresolved_placeholders = _unresolved_placeholders(resolved_command_preview)

    if unresolved_placeholders:
        validation_errors = validation_errors + (
            "Unresolved placeholder(s) remain: " + ", ".join(unresolved_placeholders) + ".",
        )

    if validation_errors:
        return _blocked_preview(
            manifest=manifest,
            target_name=target_name,
            source_kind=source_kind,
            manifest_id=manifest_id,
            gate_id=gate_id,
            proposal_id=proposal_id,
            decision_id=decision_id,
            approval_id=approval_id,
            endpoint=endpoint,
            adapter_family=adapter_family,
            command_family=command_family,
            reason=" ".join(validation_errors),
            target_base_url=normalized_base_url,
            resolved_endpoint=resolved_endpoint,
            resolved_target_url=resolved_target_url,
            token_placeholder=token_placeholder,
            path_parameters=_path_parameter_strings(path_parameter_map),
            resolved_command_preview=resolved_command_preview,
            unresolved_placeholders=unresolved_placeholders,
        )

    return CaseIntakeBrainAdapterDryRunPreview(
        preview_id=f"ADP-{manifest_id}",
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
        command_purpose=str(manifest.get("command_purpose") or "unknown"),
        target_base_url=normalized_base_url,
        resolved_endpoint=resolved_endpoint,
        resolved_target_url=resolved_target_url,
        controlled_account_token_placeholder=token_placeholder,
        path_parameters=_path_parameter_strings(path_parameter_map),
        proposed_command=proposed_command,
        resolved_command_preview=resolved_command_preview,
        unresolved_placeholders=(),
        runtime_manifest_status=str(manifest.get("runtime_manifest_status") or "unknown"),
        dry_run_preview_status="ready-for-human-review-no-execution",
        scope_check_requirements=tuple(_strings(manifest.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(manifest.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(manifest.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(manifest.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(manifest.get("required_preconditions"))),
        account_matrix=tuple(_strings(manifest.get("account_matrix"))),
        validation_steps=tuple(_strings(manifest.get("validation_steps"))),
        checklist_ids=tuple(_strings(manifest.get("checklist_ids"))),
        stop_conditions=tuple(_strings(manifest.get("stop_conditions"))),
        redaction_requirements=tuple(_strings(manifest.get("redaction_requirements"))),
        blocked=False,
        block_reason="",
        dry_run_only=True,
        preview_ready=True,
        can_execute_now=False,
        preview_allows_execution=False,
    )


def _blocked_preview(
    manifest: dict[str, Any],
    target_name: str,
    source_kind: str,
    manifest_id: str,
    gate_id: str,
    proposal_id: str,
    decision_id: str,
    approval_id: str,
    endpoint: str,
    adapter_family: str,
    command_family: str,
    reason: str,
    target_base_url: str = "",
    resolved_endpoint: str = "",
    resolved_target_url: str = "",
    token_placeholder: str = "",
    path_parameters: tuple[str, ...] = (),
    resolved_command_preview: str = "",
    unresolved_placeholders: tuple[str, ...] = (),
) -> CaseIntakeBrainAdapterDryRunPreview:
    return CaseIntakeBrainAdapterDryRunPreview(
        preview_id=f"ADP-BLOCKED-{manifest_id}",
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
        command_purpose=str(manifest.get("command_purpose") or "blocked"),
        target_base_url=target_base_url,
        resolved_endpoint=resolved_endpoint,
        resolved_target_url=resolved_target_url,
        controlled_account_token_placeholder=token_placeholder,
        path_parameters=path_parameters,
        proposed_command=str(manifest.get("proposed_command") or ""),
        resolved_command_preview=resolved_command_preview,
        unresolved_placeholders=unresolved_placeholders,
        runtime_manifest_status=str(manifest.get("runtime_manifest_status") or "blocked"),
        dry_run_preview_status="blocked",
        scope_check_requirements=tuple(_strings(manifest.get("scope_check_requirements"))),
        placeholder_check_requirements=tuple(_strings(manifest.get("placeholder_check_requirements"))),
        adapter_safety_requirements=tuple(_strings(manifest.get("adapter_safety_requirements"))),
        final_human_confirmation_requirements=tuple(_strings(manifest.get("final_human_confirmation_requirements"))),
        required_preconditions=tuple(_strings(manifest.get("required_preconditions"))) or ("Do not proceed until the block reason is resolved.",),
        account_matrix=tuple(_strings(manifest.get("account_matrix"))),
        validation_steps=tuple(_strings(manifest.get("validation_steps"))),
        checklist_ids=tuple(_strings(manifest.get("checklist_ids"))),
        stop_conditions=tuple(_strings(manifest.get("stop_conditions"))) or ("Do not proceed until the block reason is resolved.",),
        redaction_requirements=tuple(_strings(manifest.get("redaction_requirements"))),
        blocked=True,
        block_reason=reason,
        dry_run_only=True,
        preview_ready=False,
        can_execute_now=False,
        preview_allows_execution=False,
    )


def _validate_target_base_url(value: str) -> tuple[str, tuple[str, ...]]:
    raw = str(value or "").strip().rstrip("/")
    if not raw:
        return "", ("Target base URL is required.",)

    parsed = urlparse(raw)
    errors: list[str] = []

    if parsed.scheme != "https":
        errors.append("Target base URL must use https.")

    if not parsed.hostname:
        errors.append("Target base URL must include a hostname.")

    if parsed.query or parsed.fragment:
        errors.append("Target base URL must not include query string or fragment.")

    host = (parsed.hostname or "").lower().strip("[]")
    if host in {"localhost", "metadata.google.internal"} or host.endswith(".localhost"):
        errors.append("Target base URL host is not allowed for dry-run preview.")

    try:
        ip = ip_address(host)
    except ValueError:
        ip = None

    if ip is not None and (
        ip.is_loopback
        or ip.is_private
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    ):
        errors.append("Target base URL IP address is not allowed for dry-run preview.")

    return raw, tuple(errors)


def _validate_token_placeholder(value: str) -> tuple[str, tuple[str, ...]]:
    token = str(value or "").strip()
    if not token:
        return "", ("Controlled account token placeholder is required.",)

    errors: list[str] = []
    if token.lower().startswith("bearer "):
        errors.append("Controlled account token placeholder must not include the Bearer prefix.")

    if any(character.isspace() for character in token):
        errors.append("Controlled account token placeholder must not contain whitespace.")

    if len(token) > 128:
        errors.append("Controlled account token placeholder is too long for a safe dry-run label.")

    return token, tuple(errors)


def _parse_path_parameters(items: list[str] | tuple[str, ...]) -> tuple[dict[str, str], tuple[str, ...]]:
    parsed: dict[str, str] = {}
    errors: list[str] = []

    for item in items:
        text = str(item or "").strip()
        if not text:
            continue

        if "=" not in text:
            errors.append(f"Path parameter replacement must use key=value form: {text}.")
            continue

        key, value = text.split("=", 1)
        key = key.strip()
        value = value.strip()

        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key):
            errors.append(f"Invalid path parameter name: {key}.")
            continue

        if not value:
            errors.append(f"Path parameter value is empty for: {key}.")
            continue

        if any(character in value for character in "\r\n"):
            errors.append(f"Path parameter value contains a newline for: {key}.")
            continue

        parsed[key] = value

    return parsed, tuple(errors)


def _path_placeholder_names(endpoint: str) -> tuple[str, ...]:
    return tuple(re.findall(r"\{([A-Za-z_][A-Za-z0-9_-]*)\}", endpoint or ""))


def _resolve_endpoint(endpoint: str, path_parameter_map: dict[str, str]) -> str:
    resolved = endpoint if endpoint.startswith("/") else f"/{endpoint}"
    for key, value in path_parameter_map.items():
        resolved = resolved.replace(f"{{{key}}}", value)
    return resolved


def _resolve_command(
    proposed_command: str,
    target_base_url: str,
    token_placeholder: str,
    path_parameter_map: dict[str, str],
) -> str:
    resolved = proposed_command
    resolved = resolved.replace("{{TARGET_BASE_URL}}", target_base_url)
    resolved = resolved.replace("{{CONTROLLED_ACCOUNT_TOKEN}}", token_placeholder)
    for key, value in path_parameter_map.items():
        resolved = resolved.replace(f"{{{key}}}", value)
    return resolved


def _unresolved_placeholders(value: str) -> tuple[str, ...]:
    matches = re.findall(r"\{\{[^{}]+\}\}|\{[A-Za-z_][A-Za-z0-9_-]*\}", value or "")
    return tuple(dict.fromkeys(matches))


def _path_parameter_strings(path_parameter_map: dict[str, str]) -> tuple[str, ...]:
    return tuple(f"{key}={value}" for key, value in sorted(path_parameter_map.items()))


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_manifest(manifest: dict[str, Any]) -> bool:
    safety = manifest.get("safety") if isinstance(manifest.get("safety"), dict) else {}
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
        bool(manifest.get(key))
        for key in (
            "can_execute_now",
            "manifest_allows_execution",
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
