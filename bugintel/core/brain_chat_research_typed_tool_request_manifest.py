"""Typed research tool-request manifest.

This module converts a validated research approved-action packet into a
deterministic, planning-only typed tool-request manifest.

The manifest preserves action identity, tool and adapter families, risk
classification, scope requirements, controlled-asset requirements, expected
artifacts, observation requirements, and fail-closed blockers.

It also produces a compatibility view for the existing ToolExecutionGate and
a conservative execution-gate preview.

It does not generate commands or payloads, install packages, execute tools,
launch browsers, interact with Burp Suite, use Kali tools, send requests,
collect evidence, mutate state, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_research_approved_action_packet import (
    ACTION_PROFILES,
)
from bugintel.core.tool_execution_gate import (
    build_tool_execution_gate,
)


EXPECTED_APPROVED_PACKET_KIND = (
    "brain_chat_research_approved_action_packet"
)
EXPECTED_APPROVED_PACKET_STATUS = (
    "ready-for-typed-tool-request-manifest"
)

REQUIRED_APPROVED_ACTION_FIELDS: tuple[str, ...] = (
    "action_id",
    "hypothesis_id",
    "hypothesis_type",
    "action_type",
    "title",
    "purpose",
    "manual_order",
    "decision_reason",
    "expected_artifact",
    "tool_family",
    "adapter_family",
    "request_kind",
    "risk_level",
    "risk_reasons",
    "requires_human_approval",
    "requires_scope_confirmation",
    "requires_controlled_assets",
    "requires_runtime_gate",
    "requires_redaction_review",
    "requires_observation_capture",
    "manifest_eligible",
    "command_generated",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
    "blocked_by",
)

PACKET_FALSE_FLAGS: tuple[str, ...] = (
    "execution_gate_ready",
    "runtime_execution_allowed",
    "command_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

ACTION_FALSE_FLAGS: tuple[str, ...] = (
    "command_generated",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
)

SAFETY_TRUE_FLAGS: tuple[str, ...] = (
    "local_only",
    "planning_only",
    "human_approval_recorded",
    "typed_normalization_only",
)

SAFETY_FALSE_FLAGS: tuple[str, ...] = (
    "network_interaction",
    "target_mutation",
    "command_generation",
    "tool_execution",
    "browser_execution",
    "curl_execution",
    "kali_execution",
    "burp_execution",
    "provider_execution",
    "package_installation",
    "target_interaction",
    "evidence_collection",
    "validation_execution",
    "runtime_execution_allowed",
    "state_mutation",
    "report_submission",
    "vulnerability_confirmation",
)

MANIFEST_SAFETY: dict[str, bool] = {
    "local_only": True,
    "planning_only": True,
    "typed_requests_only": True,
    "source_human_approval_required": True,
    "execution_gate_required": True,
    "network_interaction": False,
    "target_mutation": False,
    "command_generation": False,
    "payload_generation": False,
    "tool_execution": False,
    "browser_execution": False,
    "curl_execution": False,
    "kali_execution": False,
    "burp_execution": False,
    "provider_execution": False,
    "package_installation": False,
    "target_interaction": False,
    "evidence_collection": False,
    "validation_execution": False,
    "runtime_execution_allowed": False,
    "state_mutation": False,
    "report_submission": False,
    "vulnerability_confirmation": False,
}

ADAPTER_CONTRACTS: dict[str, dict[str, tuple[str, ...]]] = {
    "local-file": {
        "allowed_inputs": (
            "approved local paths",
            "approved source-file identifiers",
            "local search patterns",
            "local parser options",
        ),
        "required_outputs": (
            "local source-inspection notes",
            "referenced file paths",
            "redacted observations",
        ),
        "prohibited_operations": (
            "network access",
            "shell execution",
            "package installation",
            "target interaction",
            "file mutation",
        ),
    },
    "local-artifact": {
        "allowed_inputs": (
            "approved HAR files",
            "approved HTTP artifacts",
            "approved browser artifacts",
            "approved mobile artifacts",
            "approved evidence files",
        ),
        "required_outputs": (
            "artifact-inspection notes",
            "artifact references",
            "redacted observations",
        ),
        "prohibited_operations": (
            "network replay",
            "browser execution",
            "target interaction",
            "artifact mutation",
            "evidence fabrication",
        ),
    },
    "scope-review": {
        "allowed_inputs": (
            "program scope text",
            "target identifiers",
            "hostname lists",
            "authorization notes",
        ),
        "required_outputs": (
            "scope-confirmation record",
            "authorized-target summary",
            "scope blockers",
        ),
        "prohibited_operations": (
            "network probing",
            "target validation",
            "scope expansion",
            "authorization inference",
        ),
    },
    "controlled-assets": {
        "allowed_inputs": (
            "controlled account references",
            "controlled object references",
            "controlled tenant references",
            "controlled project references",
            "controlled file references",
        ),
        "required_outputs": (
            "controlled-assets matrix",
            "ownership notes",
            "role and isolation notes",
        ),
        "prohibited_operations": (
            "account creation",
            "credential use",
            "authentication attempts",
            "target mutation",
            "private-data access",
        ),
    },
    "browser": {
        "allowed_inputs": (
            "approved target URL",
            "approved browser profile reference",
            "approved controlled-session reference",
            "observation plan",
            "abort conditions",
        ),
        "required_outputs": (
            "browser observation artifact",
            "network observation artifact",
            "console observation artifact",
            "redaction report",
        ),
        "prohibited_operations": (
            "automatic navigation",
            "form submission",
            "credential entry",
            "state-changing actions",
            "out-of-scope navigation",
            "runtime execution without a separate gate",
        ),
    },
    "burp": {
        "allowed_inputs": (
            "approved local Burp export",
            "approved request artifact",
            "approved response artifact",
            "request-review checklist",
        ),
        "required_outputs": (
            "request-review notes",
            "response-review notes",
            "redaction report",
            "replay-risk assessment",
        ),
        "prohibited_operations": (
            "request replay",
            "intruder execution",
            "active scanning",
            "target interaction",
            "extension installation",
            "runtime execution without a separate gate",
        ),
    },
    "shell-review": {
        "allowed_inputs": (
            "tool-family identifier",
            "command intent",
            "expected local artifact",
            "scope constraints",
            "runtime guard requirements",
        ),
        "required_outputs": (
            "command-review requirements",
            "tool-selection rationale",
            "risk assessment",
            "required runtime confirmations",
        ),
        "prohibited_operations": (
            "command generation",
            "shell execution",
            "package installation",
            "network access",
            "process creation",
            "runtime execution without a separate gate",
        ),
    },
    "evidence": {
        "allowed_inputs": (
            "evidence requirements",
            "redaction requirements",
            "expected artifact type",
            "storage requirements",
            "review requirements",
        ),
        "required_outputs": (
            "evidence plan",
            "artifact naming plan",
            "redaction plan",
            "review checklist",
        ),
        "prohibited_operations": (
            "evidence collection",
            "target interaction",
            "screenshot capture",
            "traffic capture",
            "evidence mutation",
            "runtime execution without a separate gate",
        ),
    },
}

REJECTED_NEXT_STEPS: tuple[str, ...] = (
    "Do not execute typed requests from this manifest.",
    "Do not generate shell, curl, browser, Burp, Kali, scanner, or exploitation commands.",
    "Do not install packages or modify the runtime environment.",
    "Do not send requests or interact with a target.",
    "Do not collect evidence or validate exploitability.",
    "Do not mutate case state from manifest data.",
    "Do not submit reports or confirm vulnerabilities.",
)


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load one JSON object."""
    source = Path(path)

    with source.open("r", encoding="utf-8") as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(f"Expected JSON object in {source}")

    return value


def write_json(
    path: str | Path,
    value: dict[str, Any],
) -> None:
    """Write deterministic JSON."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_markdown(path: str | Path, text: str) -> None:
    """Write Markdown."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def build_research_typed_tool_request_manifest(
    approved_action_packet: dict[str, Any],
    source: str = (
        "brain-chat-research-typed-tool-request-manifest"
    ),
) -> dict[str, Any]:
    """Build a typed planning-only tool-request manifest."""

    source_packet = copy.deepcopy(approved_action_packet)
    approved_actions = _object_list(
        source_packet.get("approved_actions")
    )

    source_findings = _source_findings(
        source_packet,
        approved_actions,
    )
    request_findings = _request_findings(
        approved_actions
    )

    manifest_status = _manifest_status(
        approved_actions=approved_actions,
        source_findings=source_findings,
        request_findings=request_findings,
    )

    manifest_ready = (
        manifest_status
        == "ready-for-tool-execution-gate-review"
    )

    typed_requests = [
        _build_typed_request(
            action,
            request_index=index,
            manifest_eligible=manifest_ready,
        )
        for index, action in enumerate(
            sorted(
                approved_actions,
                key=lambda item: (
                    _int(item.get("manual_order")),
                    _text(item.get("action_id")),
                ),
            ),
            start=1,
        )
    ]

    focus_endpoint = _optional_text(
        source_packet.get("focus_endpoint")
    )

    execution_gate_input = _execution_gate_input(
        target_name=_text(
            source_packet.get("target_name"),
            "unknown-target",
        ),
        focus_endpoint=focus_endpoint,
        requests=typed_requests,
    )

    gate_preview = build_tool_execution_gate(
        execution_gate_input
    ).to_dict()
    gate_preview.pop("markdown", None)

    tool_family_counts = _count_by(
        typed_requests,
        "tool_family",
    )
    adapter_family_counts = _count_by(
        typed_requests,
        "adapter_family",
    )
    request_kind_counts = _count_by(
        typed_requests,
        "request_kind",
    )
    risk_level_counts = _count_by(
        typed_requests,
        "risk_level",
    )

    runtime_gated_count = sum(
        bool(item.get("requires_runtime_gate"))
        for item in typed_requests
    )
    scope_required_count = sum(
        bool(item.get("requires_scope_confirmation"))
        for item in typed_requests
    )
    controlled_assets_count = sum(
        bool(item.get("requires_controlled_assets"))
        for item in typed_requests
    )
    observation_capture_count = sum(
        bool(item.get("requires_observation_capture"))
        for item in typed_requests
    )

    source_digest = _sha256(source_packet)

    digest_material = {
        "target_name": source_packet.get("target_name"),
        "focus_endpoint": focus_endpoint,
        "typed_requests": typed_requests,
        "source_digest": source_digest,
    }
    manifest_digest = _sha256(digest_material)

    high_findings = [
        item
        for item in (
            source_findings + request_findings
        )
        if item.get("severity") == "high"
    ]
    medium_findings = [
        item
        for item in (
            source_findings + request_findings
        )
        if item.get("severity") == "medium"
    ]

    requires_focus_endpoint = (
        any(
            bool(
                item.get(
                    "requires_focus_endpoint"
                )
            )
            for item in typed_requests
        )
        and not focus_endpoint
    )

    return {
        "kind": (
            "brain_chat_research_typed_tool_request_manifest"
        ),
        "source": source,
        "target_name": _text(
            source_packet.get("target_name"),
            "unknown-target",
        ),
        "focus_endpoint": focus_endpoint,
        "manifest_status": manifest_status,
        "summary": _summary(
            manifest_status,
            len(typed_requests),
        ),
        "manifest_ready": manifest_ready,
        "execution_gate_input_ready": manifest_ready,
        "execution_gate_review_ready": manifest_ready,
        "existing_tool_execution_gate_compatible": True,
        "requires_focus_endpoint_before_runtime_review": (
            requires_focus_endpoint
        ),
        "source_packet_kind": _text(
            source_packet.get("kind"),
            "unknown",
        ),
        "source_packet_status": _text(
            source_packet.get("packet_status"),
            "unknown",
        ),
        "source_packet_ready": bool(
            source_packet.get("packet_ready")
        ),
        "source_manifest_ready": bool(
            source_packet.get(
                "typed_tool_request_manifest_ready"
            )
        ),
        "source_approved_action_count": _int(
            source_packet.get("approved_action_count")
        ),
        "typed_request_count": len(typed_requests),
        "typed_requests": typed_requests,
        "tool_family_counts": tool_family_counts,
        "adapter_family_counts": adapter_family_counts,
        "request_kind_counts": request_kind_counts,
        "risk_level_counts": risk_level_counts,
        "runtime_gated_request_count": (
            runtime_gated_count
        ),
        "scope_required_request_count": (
            scope_required_count
        ),
        "controlled_assets_request_count": (
            controlled_assets_count
        ),
        "observation_capture_request_count": (
            observation_capture_count
        ),
        "approved_action_packet_digest": source_digest,
        "manifest_digest": manifest_digest,
        "execution_gate_input": execution_gate_input,
        "execution_gate_preview": gate_preview,
        "execution_gate_preview_decision": _text(
            gate_preview.get("gate_decision"),
            "unknown",
        ),
        "execution_gate_preview_execution_allowed": bool(
            gate_preview.get("execution_allowed")
        ),
        "source_findings": source_findings,
        "request_findings": request_findings,
        "counts": {
            "typed_requests": len(typed_requests),
            "source_findings": len(source_findings),
            "request_findings": len(request_findings),
            "high_findings": len(high_findings),
            "medium_findings": len(medium_findings),
            "tool_families": len(tool_family_counts),
            "adapter_families": len(
                adapter_family_counts
            ),
            "request_kinds": len(request_kind_counts),
            "risk_levels": len(risk_level_counts),
            "runtime_gated_requests": (
                runtime_gated_count
            ),
            "scope_required_requests": (
                scope_required_count
            ),
            "controlled_assets_requests": (
                controlled_assets_count
            ),
            "observation_capture_requests": (
                observation_capture_count
            ),
        },
        "allowed_next_steps": _allowed_next_steps(
            manifest_status,
            len(typed_requests),
            requires_focus_endpoint,
        ),
        "rejected_next_steps": list(
            REJECTED_NEXT_STEPS
        ),
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": dict(MANIFEST_SAFETY),
    }


def render_research_typed_tool_request_manifest_markdown(
    manifest: dict[str, Any],
) -> str:
    """Render typed manifest Markdown."""

    lines = [
        "# Research Typed Tool Request Manifest",
        "",
        "## Manifest Status",
        "",
        (
            "- target_name: "
            f"`{manifest.get('target_name', '')}`"
        ),
        (
            "- focus_endpoint: "
            f"`{manifest.get('focus_endpoint') or 'none'}`"
        ),
        (
            "- manifest_status: "
            f"`{manifest.get('manifest_status', '')}`"
        ),
        (
            "- manifest_ready: "
            f"`{_bool_text(manifest.get('manifest_ready'))}`"
        ),
        (
            "- execution_gate_input_ready: "
            f"`{_bool_text(manifest.get('execution_gate_input_ready'))}`"
        ),
        (
            "- runtime_execution_allowed: "
            f"`{_bool_text(manifest.get('runtime_execution_allowed'))}`"
        ),
        (
            "- execution_gate_preview_decision: "
            f"`{manifest.get('execution_gate_preview_decision', '')}`"
        ),
        (
            "- approved_action_packet_digest: "
            f"`{manifest.get('approved_action_packet_digest', '')}`"
        ),
        (
            "- manifest_digest: "
            f"`{manifest.get('manifest_digest', '')}`"
        ),
        f"- summary: {manifest.get('summary', '')}",
        "",
        "## Typed Requests",
        "",
        (
            "| Order | Request ID | Action ID | Request Kind | "
            "Tool Family | Adapter | Risk | Scope | Assets | "
            "Runtime Gate | Eligible |"
        ),
        (
            "|---:|---|---|---|---|---|---|---|---|---|---|"
        ),
    ]

    for request in _object_list(
        manifest.get("typed_requests")
    ):
        lines.append(
            "| "
            f"{request.get('manual_order', 0)} | "
            f"`{request.get('request_id', '')}` | "
            f"`{request.get('action_id', '')}` | "
            f"`{request.get('request_kind', '')}` | "
            f"`{request.get('tool_family', '')}` | "
            f"`{request.get('adapter_family', '')}` | "
            f"`{request.get('risk_level', '')}` | "
            f"`{_bool_text(request.get('requires_scope_confirmation'))}` | "
            f"`{_bool_text(request.get('requires_controlled_assets'))}` | "
            f"`{_bool_text(request.get('requires_runtime_gate'))}` | "
            f"`{_bool_text(request.get('manifest_eligible'))}` |"
        )

    lines.extend(["", "## Adapter Contracts", ""])

    for request in _object_list(
        manifest.get("typed_requests")
    ):
        lines.extend(
            [
                (
                    "### "
                    f"{request.get('request_id', 'unknown')} — "
                    f"{request.get('adapter_family', 'unknown')}"
                ),
                "",
                "Allowed inputs:",
                *[
                    f"- {item}"
                    for item in _list_of_text(
                        request.get("allowed_inputs")
                    )
                ],
                "",
                "Required outputs:",
                *[
                    f"- {item}"
                    for item in _list_of_text(
                        request.get("required_outputs")
                    )
                ],
                "",
                "Prohibited operations:",
                *[
                    f"- {item}"
                    for item in _list_of_text(
                        request.get(
                            "prohibited_operations"
                        )
                    )
                ],
                "",
            ]
        )

    lines.extend(
        ["## Execution Gate Compatibility", ""]
    )
    lines.extend(
        [
            (
                "- Existing gate compatible: "
                f"`{_bool_text(manifest.get('existing_tool_execution_gate_compatible'))}`"
            ),
            (
                "- Gate preview decision: "
                f"`{manifest.get('execution_gate_preview_decision', '')}`"
            ),
            (
                "- Gate preview execution allowed: "
                f"`{_bool_text(manifest.get('execution_gate_preview_execution_allowed'))}`"
            ),
            (
                "- Focus endpoint required before runtime review: "
                f"`{_bool_text(manifest.get('requires_focus_endpoint_before_runtime_review'))}`"
            ),
        ]
    )

    lines.extend(["", "## Source Findings", ""])
    lines.extend(
        _render_findings(manifest.get("source_findings"))
    )

    lines.extend(["", "## Request Findings", ""])
    lines.extend(
        _render_findings(
            manifest.get("request_findings")
        )
    )

    lines.extend(["", "## Allowed Next Steps", ""])
    allowed = _list_of_text(
        manifest.get("allowed_next_steps")
    )
    lines.extend(
        [f"- {item}" for item in allowed]
        or ["- none"]
    )

    lines.extend(["", "## Rejected Next Steps", ""])
    rejected = _list_of_text(
        manifest.get("rejected_next_steps")
    )
    lines.extend(
        [f"- {item}" for item in rejected]
        or ["- none"]
    )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- This is a planning-only typed manifest.",
            "- Command generation allowed: `false`",
            "- Payload generation allowed: `false`",
            "- Package installation allowed: `false`",
            "- Tool execution allowed: `false`",
            "- Runtime execution allowed: `false`",
            "- Network interaction allowed: `false`",
            "- Target interaction allowed: `false`",
            "- Evidence collection allowed: `false`",
            "- Validation allowed: `false`",
            (
                "- The execution-gate preview is advisory and "
                "remains fail-closed."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def build_typed_manifest_from_file(
    approved_action_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
    focus_endpoint: str | None = None,
) -> dict[str, Any]:
    """Load approved actions and optionally write outputs."""

    approved_action_packet = load_json_object(
        approved_action_file
    )

    if focus_endpoint is not None:
        approved_action_packet["focus_endpoint"] = (
            _optional_text(focus_endpoint)
        )

    manifest = (
        build_research_typed_tool_request_manifest(
            approved_action_packet
        )
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_typed_tool_request_manifest_markdown(
                manifest
            ),
        )

    if json_output is not None:
        write_json(json_output, manifest)

    return manifest


def _source_findings(
    packet: dict[str, Any],
    approved_actions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if (
        packet.get("kind")
        != EXPECTED_APPROVED_PACKET_KIND
    ):
        findings.append(
            _finding(
                "source-schema",
                "high",
                (
                    "Approved-action packet kind must be "
                    f"{EXPECTED_APPROVED_PACKET_KIND}."
                ),
                "kind",
                "Provide a valid approved-action packet.",
            )
        )

    if not _text(packet.get("target_name")):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "target_name must not be empty.",
                "target_name",
                "Regenerate the approved-action packet.",
            )
        )

    if (
        _text(packet.get("packet_status"))
        != EXPECTED_APPROVED_PACKET_STATUS
    ):
        findings.append(
            _finding(
                "source-readiness",
                "high",
                (
                    "Approved-action status must be "
                    f"{EXPECTED_APPROVED_PACKET_STATUS}."
                ),
                "packet_status",
                "Resolve approved-action packet blockers.",
            )
        )

    for field in (
        "packet_ready",
        "typed_tool_request_manifest_ready",
    ):
        if not bool(packet.get(field)):
            findings.append(
                _finding(
                    "source-readiness",
                    "high",
                    f"{field} must be true.",
                    field,
                    "Use a manifest-ready approved-action packet.",
                )
            )

    if not isinstance(
        packet.get("approved_actions"),
        list,
    ):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "approved_actions must be a list.",
                "approved_actions",
                "Regenerate the approved-action packet.",
            )
        )

    declared_count = _int(
        packet.get("approved_action_count")
    )
    actual_count = len(approved_actions)

    if declared_count != actual_count:
        findings.append(
            _finding(
                "source-consistency",
                "high",
                (
                    "approved_action_count does not match "
                    f"approved_actions: {declared_count} != "
                    f"{actual_count}."
                ),
                "approved_action_count",
                "Regenerate the approved-action packet.",
            )
        )

    for field in PACKET_FALSE_FLAGS:
        if bool(packet.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"Source field must remain false: {field}.",
                    field,
                    "Block the unsafe approved-action packet.",
                )
            )

    if not bool(packet.get("planning_only")):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "planning_only must be true.",
                "planning_only",
                "Regenerate the approved-action packet.",
            )
        )

    if (
        _text(packet.get("execution_state"))
        != "not_executed"
    ):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "execution_state must be not_executed.",
                "execution_state",
                "Block the source packet.",
            )
        )

    safety = packet.get("safety")

    if not isinstance(safety, dict):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "safety must be an object.",
                "safety",
                "Regenerate the approved-action packet.",
            )
        )
        return findings

    for field in SAFETY_TRUE_FLAGS:
        if not bool(safety.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"safety.{field} must be true.",
                    f"safety.{field}",
                    "Restore the source safety guardrail.",
                )
            )

    for field in SAFETY_FALSE_FLAGS:
        if bool(safety.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"safety.{field} must remain false.",
                    f"safety.{field}",
                    "Block the unsafe source packet.",
                )
            )

    return findings


def _request_findings(
    actions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    action_ids: set[str] = set()
    manual_orders: set[int] = set()

    for index, action in enumerate(actions):
        subject = f"approved_actions[{index}]"

        for field in REQUIRED_APPROVED_ACTION_FIELDS:
            if field not in action:
                findings.append(
                    _finding(
                        "request-schema",
                        "high",
                        f"Required action field is missing: {field}.",
                        subject,
                        "Regenerate the approved-action packet.",
                    )
                )

        action_id = _text(action.get("action_id"))

        if not action_id:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    "action_id must not be empty.",
                    subject,
                    "Regenerate the approved action.",
                )
            )
        elif action_id in action_ids:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    f"Duplicate action_id: {action_id}.",
                    subject,
                    "Keep one request per action.",
                )
            )

        action_ids.add(action_id)

        manual_order = _int(
            action.get("manual_order")
        )

        if manual_order <= 0:
            findings.append(
                _finding(
                    "request-schema",
                    "medium",
                    "manual_order should be positive.",
                    subject,
                    "Restore deterministic ordering.",
                )
            )
        elif manual_order in manual_orders:
            findings.append(
                _finding(
                    "request-schema",
                    "medium",
                    f"Duplicate manual_order: {manual_order}.",
                    subject,
                    "Use unique request ordering.",
                )
            )

        manual_orders.add(manual_order)

        action_type = _text(
            action.get("action_type")
        )
        profile = ACTION_PROFILES.get(action_type)

        if profile is None:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    (
                        "Unsupported action type: "
                        f"{action_type or 'missing'}."
                    ),
                    subject,
                    "Use a supported approved action type.",
                )
            )
            continue

        expected_values = {
            "tool_family": profile["tool_family"],
            "adapter_family": profile[
                "adapter_family"
            ],
            "request_kind": profile["request_kind"],
            "risk_level": profile["risk_level"],
            "requires_scope_confirmation": profile[
                "requires_scope_confirmation"
            ],
            "requires_controlled_assets": profile[
                "requires_controlled_assets"
            ],
            "requires_runtime_gate": profile[
                "requires_runtime_gate"
            ],
        }

        for field, expected in expected_values.items():
            actual = action.get(field)

            if actual != expected:
                findings.append(
                    _finding(
                        "request-consistency",
                        "high",
                        (
                            f"{field} mismatch for {action_type}: "
                            f"{actual!r} != {expected!r}."
                        ),
                        subject,
                        "Regenerate the approved-action packet.",
                    )
                )

        adapter_family = _text(
            action.get("adapter_family")
        )

        if adapter_family not in ADAPTER_CONTRACTS:
            findings.append(
                _finding(
                    "request-schema",
                    "high",
                    (
                        "No adapter contract exists for "
                        f"{adapter_family or 'missing'}."
                    ),
                    subject,
                    "Add or select a supported adapter contract.",
                )
            )

        if not bool(
            action.get("requires_human_approval")
        ):
            findings.append(
                _finding(
                    "request-safety",
                    "high",
                    "requires_human_approval must be true.",
                    subject,
                    "Restore human approval requirements.",
                )
            )

        if not bool(action.get("manifest_eligible")):
            findings.append(
                _finding(
                    "request-readiness",
                    "high",
                    "manifest_eligible must be true.",
                    subject,
                    "Resolve approved-action packet blockers.",
                )
            )

        for field in ACTION_FALSE_FLAGS:
            if bool(action.get(field)):
                findings.append(
                    _finding(
                        "request-safety",
                        "high",
                        f"Action field must remain false: {field}.",
                        subject,
                        "Block the unsafe request source.",
                    )
                )

        blockers = _list_of_text(
            action.get("blocked_by")
        )

        if not blockers:
            findings.append(
                _finding(
                    "request-safety",
                    "high",
                    "blocked_by must not be empty.",
                    subject,
                    "Restore downstream safety blockers.",
                )
            )

        if not _text(
            action.get("expected_artifact")
        ):
            findings.append(
                _finding(
                    "request-quality",
                    "medium",
                    "expected_artifact should not be empty.",
                    subject,
                    "Specify the expected artifact.",
                )
            )

    return findings


def _build_typed_request(
    action: dict[str, Any],
    request_index: int,
    manifest_eligible: bool,
) -> dict[str, Any]:
    adapter_family = _text(
        action.get("adapter_family"),
        "unknown",
    )
    contract = ADAPTER_CONTRACTS.get(
        adapter_family,
        {
            "allowed_inputs": (),
            "required_outputs": (),
            "prohibited_operations": (
                "all runtime operations",
            ),
        },
    )

    requires_runtime_gate = bool(
        action.get("requires_runtime_gate")
    )

    blockers = _list_of_text(
        action.get("blocked_by")
    )
    blockers.extend(
        [
            "typed-request-human-review-required",
            "execution-gate-review-required",
            "runtime-execution-disabled",
        ]
    )

    if requires_runtime_gate:
        blockers.extend(
            [
                "focus-endpoint-required",
                "runtime-human-approval-required",
                "runtime-guard-confirmation-required",
            ]
        )

    request_id = f"RTR-{request_index:03d}"

    request = {
        "request_id": request_id,
        "action_id": _text(action.get("action_id")),
        "hypothesis_id": _text(
            action.get("hypothesis_id")
        ),
        "hypothesis_type": _text(
            action.get("hypothesis_type")
        ),
        "action_type": _text(
            action.get("action_type")
        ),
        "request_kind": _text(
            action.get("request_kind"),
            "unknown-request",
        ),
        "name": _text(
            action.get("title"),
            request_id,
        ),
        "purpose": _text(action.get("purpose")),
        "manual_order": _int(
            action.get("manual_order")
        ),
        "tool_family": _text(
            action.get("tool_family"),
            "unknown",
        ),
        "adapter_family": adapter_family,
        "risk_level": _text(
            action.get("risk_level"),
            "unknown",
        ),
        "risk_reasons": _list_of_text(
            action.get("risk_reasons")
        ),
        "decision_reason": _text(
            action.get("decision_reason")
        ),
        "expected_artifact": _text(
            action.get("expected_artifact")
        ),
        "requires_human_approval": True,
        "requires_scope_confirmation": bool(
            action.get(
                "requires_scope_confirmation"
            )
        ),
        "requires_controlled_assets": bool(
            action.get(
                "requires_controlled_assets"
            )
        ),
        "requires_runtime_gate": (
            requires_runtime_gate
        ),
        "requires_focus_endpoint": (
            requires_runtime_gate
        ),
        "requires_redaction_review": bool(
            action.get("requires_redaction_review")
        ),
        "requires_observation_capture": bool(
            action.get(
                "requires_observation_capture"
            )
        ),
        "approval_state": (
            "human-approved-for-planning"
        ),
        "request_state": (
            "typed-request-not-executable"
        ),
        "manifest_eligible": manifest_eligible,
        "allowed_inputs": list(
            contract["allowed_inputs"]
        ),
        "required_outputs": list(
            contract["required_outputs"]
        ),
        "prohibited_operations": list(
            contract["prohibited_operations"]
        ),
        "blocked_by": _dedupe(blockers),
        "command_generated": False,
        "payload_generated": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "state_mutation_allowed": False,
    }

    request["request_digest"] = _sha256(request)
    return request


def _execution_gate_input(
    target_name: str,
    focus_endpoint: str | None,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "target_name": target_name,
        "focus_endpoint": focus_endpoint,
        "source_approval_status": (
            "human-approved-for-planning"
        ),
        "execution_allowed": False,
        "provider_execution_enabled": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "requests": [
            {
                "name": _text(
                    item.get("name"),
                    "unknown-request",
                ),
                "tool_family": _text(
                    item.get("tool_family"),
                    "unknown",
                ),
                "purpose": _text(
                    item.get("purpose")
                ),
                "requires_human_approval": bool(
                    item.get(
                        "requires_human_approval"
                    )
                ),
                "execution_allowed": False,
                "blocked_by": _list_of_text(
                    item.get("blocked_by")
                ),
                "expected_artifact": _text(
                    item.get("expected_artifact")
                ),
            }
            for item in requests
        ],
    }


def _manifest_status(
    approved_actions: list[dict[str, Any]],
    source_findings: list[dict[str, str]],
    request_findings: list[dict[str, str]],
) -> str:
    high_source = [
        item
        for item in source_findings
        if item.get("severity") == "high"
    ]
    high_requests = [
        item
        for item in request_findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category") == "source-safety"
        for item in high_source
    ):
        return "blocked-unsafe-approved-action-packet"

    if any(
        item.get("category") == "source-readiness"
        for item in high_source
    ):
        return "blocked-approved-action-packet-not-ready"

    if high_source:
        return "blocked-invalid-approved-action-packet"

    if not approved_actions:
        return "blocked-no-approved-actions"

    if high_requests:
        return "blocked-invalid-typed-requests"

    return "ready-for-tool-execution-gate-review"


def _summary(status: str, request_count: int) -> str:
    if status == "ready-for-tool-execution-gate-review":
        return (
            f"{request_count} approved action(s) were converted "
            "into typed, planning-only tool requests. The "
            "existing execution gate preview remains fail-closed."
        )

    if status == "blocked-no-approved-actions":
        return (
            "No approved actions are available for typed "
            "request generation."
        )

    if status == (
        "blocked-approved-action-packet-not-ready"
    ):
        return (
            "The approved-action packet is not ready for typed "
            "request generation."
        )

    if status == (
        "blocked-unsafe-approved-action-packet"
    ):
        return (
            "Unsafe source flags blocked typed request "
            "generation."
        )

    if status == "blocked-invalid-typed-requests":
        return (
            "One or more approved actions could not be safely "
            "converted into typed requests."
        )

    return (
        "The approved-action packet is invalid for typed "
        "request generation."
    )


def _allowed_next_steps(
    status: str,
    request_count: int,
    requires_focus_endpoint: bool,
) -> list[str]:
    if status != "ready-for-tool-execution-gate-review":
        return []

    steps = [
        (
            f"Review all {request_count} typed requests, adapter "
            "contracts, risks, blockers, and expected artifacts."
        ),
        (
            "Review the generated compatibility input with the "
            "existing fail-closed tool execution gate."
        ),
    ]

    if requires_focus_endpoint:
        steps.append(
            "Select and validate a focus endpoint before any "
            "runtime-oriented execution-gate review."
        )

    steps.extend(
        [
            (
                "Keep every request execution-disabled until a "
                "later exact-action runtime approval exists."
            ),
            (
                "Preserve request and manifest digests in all "
                "downstream review artifacts."
            ),
        ]
    )

    return steps


def _count_by(
    items: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for item in items:
        value = _text(item.get(key), "unknown")
        counts[value] = counts.get(value, 0) + 1

    return dict(sorted(counts.items()))


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _finding(
    category: str,
    severity: str,
    message: str,
    subject: str,
    required_action: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "message": message,
        "subject": subject,
        "required_action": required_action,
    }


def _render_findings(value: Any) -> list[str]:
    findings = value if isinstance(value, list) else []
    lines: list[str] = []

    for item in findings:
        if not isinstance(item, dict):
            continue

        lines.append(
            "- "
            f"[{item.get('severity', 'unknown')}] "
            f"{item.get('category', 'finding')} / "
            f"{item.get('subject', 'unknown')}: "
            f"{item.get('message', '')} "
            f"Required action: "
            f"{item.get('required_action', '')}"
        )

    return lines or ["- none"]


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def _list_of_text(value: Any) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        return [value.strip()] if value.strip() else []

    if isinstance(value, tuple):
        value = list(value)

    if not isinstance(value, list):
        return []

    return [
        _text(item)
        for item in value
        if _text(item)
    ]


def _optional_text(value: Any) -> str | None:
    text = _text(value)
    return text if text else None


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default

    text = str(value).strip()
    return text if text else default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0

    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def _dedupe(values: list[str]) -> list[str]:
    return list(
        dict.fromkeys(
            value
            for value in values
            if value
        )
    )


__all__ = [
    "ADAPTER_CONTRACTS",
    "EXPECTED_APPROVED_PACKET_KIND",
    "EXPECTED_APPROVED_PACKET_STATUS",
    "build_research_typed_tool_request_manifest",
    "build_typed_manifest_from_file",
    "load_json_object",
    "render_research_typed_tool_request_manifest_markdown",
    "write_json",
    "write_markdown",
]
