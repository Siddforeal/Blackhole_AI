"""Research approved-action packet.

This module converts a valid research action decision packet into a normalized,
planning-only approved-action packet.

The output is the typed bridge between explicit human action decisions and a
future research-specific tool-request manifest.

It does not generate commands, install packages, execute tools, launch
browsers, interact with Burp Suite, use Kali tools, send requests, collect
evidence, validate findings, mutate targets, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


EXPECTED_DECISION_KIND = (
    "brain_chat_research_action_decision_packet"
)
EXPECTED_DECISION_STATUS = (
    "ready-for-approved-action-packet"
)

REQUIRED_ACTION_FIELDS: tuple[str, ...] = (
    "action_id",
    "hypothesis_id",
    "hypothesis_type",
    "action_type",
    "title",
    "purpose",
    "manual_order",
    "proposed_tool_family",
    "expected_artifact",
    "decision",
    "decision_reason",
    "effective_approval_granted",
    "command_generated",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "blocked_by",
)

ACTION_PROFILES: dict[str, dict[str, Any]] = {
    "local-source-review": {
        "tool_family": "local-file-analysis",
        "adapter_family": "local-file",
        "request_kind": "local-source-inspection-request",
        "risk_level": "low",
        "requires_scope_confirmation": False,
        "requires_controlled_assets": False,
        "requires_runtime_gate": False,
    },
    "local-artifact-review": {
        "tool_family": "local-artifact-analysis",
        "adapter_family": "local-artifact",
        "request_kind": "local-artifact-inspection-request",
        "risk_level": "low",
        "requires_scope_confirmation": False,
        "requires_controlled_assets": False,
        "requires_runtime_gate": False,
    },
    "scope-confirmation-preparation": {
        "tool_family": "scope",
        "adapter_family": "scope-review",
        "request_kind": "scope-confirmation-request",
        "risk_level": "low",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": False,
        "requires_runtime_gate": False,
    },
    "controlled-account-preparation": {
        "tool_family": "test-controls",
        "adapter_family": "controlled-assets",
        "request_kind": "controlled-account-preparation-request",
        "risk_level": "medium",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": True,
        "requires_runtime_gate": False,
    },
    "browser-observation-proposal": {
        "tool_family": "browser",
        "adapter_family": "browser",
        "request_kind": "browser-observation-request",
        "risk_level": "medium",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": True,
        "requires_runtime_gate": True,
    },
    "burp-request-review-proposal": {
        "tool_family": "burp",
        "adapter_family": "burp",
        "request_kind": "burp-request-review-request",
        "risk_level": "medium",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": True,
        "requires_runtime_gate": True,
    },
    "command-proposal-preparation": {
        "tool_family": "shell-review",
        "adapter_family": "shell-review",
        "request_kind": "command-review-preparation-request",
        "risk_level": "high",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": True,
        "requires_runtime_gate": True,
    },
    "evidence-plan-preparation": {
        "tool_family": "evidence-planning",
        "adapter_family": "evidence",
        "request_kind": "evidence-plan-request",
        "risk_level": "medium",
        "requires_scope_confirmation": True,
        "requires_controlled_assets": True,
        "requires_runtime_gate": True,
    },
}

PACKET_FALSE_FLAGS: tuple[str, ...] = (
    "command_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

ACTION_FALSE_FLAGS: tuple[str, ...] = (
    "command_generated",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
)

SAFETY_TRUE_FLAGS: tuple[str, ...] = (
    "local_only",
    "planning_only",
    "human_decision_required",
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

SAFETY: dict[str, bool] = {
    "local_only": True,
    "planning_only": True,
    "human_approval_recorded": True,
    "typed_normalization_only": True,
    "network_interaction": False,
    "target_mutation": False,
    "command_generation": False,
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

REJECTED_NEXT_STEPS: tuple[str, ...] = (
    "Do not execute an approved action from this packet.",
    "Do not generate shell, curl, browser, Burp, Kali, scanner, or exploitation commands.",
    "Do not install packages or change the runtime environment.",
    "Do not send requests or interact with a target.",
    "Do not collect evidence or validate exploitability.",
    "Do not mutate case memory or research state.",
    "Do not submit reports or confirm vulnerabilities.",
)


def load_json_object(path: str | Path) -> dict[str, Any]:
    """Load one JSON object from disk."""
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


def build_research_approved_action_packet(
    decision_packet: dict[str, Any],
    source: str = "brain-chat-research-approved-action-packet",
) -> dict[str, Any]:
    """Build a normalized approved-action packet."""

    source_packet = copy.deepcopy(decision_packet)
    source_actions = _object_list(
        source_packet.get("approved_actions")
    )

    source_findings = _source_findings(
        source_packet,
        source_actions,
    )
    action_findings = _action_findings(source_actions)

    high_source_findings = [
        item
        for item in source_findings
        if item.get("severity") == "high"
    ]
    high_action_findings = [
        item
        for item in action_findings
        if item.get("severity") == "high"
    ]

    packet_status = _packet_status(
        source_packet=source_packet,
        source_actions=source_actions,
        source_findings=source_findings,
        action_findings=action_findings,
    )

    packet_ready = (
        packet_status
        == "ready-for-typed-tool-request-manifest"
    )

    approved_actions = [
        _normalize_action(
            action,
            manifest_eligible=packet_ready,
        )
        for action in sorted(
            source_actions,
            key=lambda item: (
                _int(item.get("manual_order")),
                _text(item.get("action_id")),
            ),
        )
    ]

    tool_family_counts = _count_by(
        approved_actions,
        "tool_family",
    )
    adapter_family_counts = _count_by(
        approved_actions,
        "adapter_family",
    )
    risk_level_counts = _count_by(
        approved_actions,
        "risk_level",
    )

    runtime_gated_count = sum(
        bool(item.get("requires_runtime_gate"))
        for item in approved_actions
    )
    scope_confirmation_count = sum(
        bool(item.get("requires_scope_confirmation"))
        for item in approved_actions
    )
    controlled_assets_count = sum(
        bool(item.get("requires_controlled_assets"))
        for item in approved_actions
    )

    allowed_next_steps = _allowed_next_steps(
        packet_status,
        len(approved_actions),
    )

    return {
        "kind": "brain_chat_research_approved_action_packet",
        "source": source,
        "target_name": _text(
            source_packet.get("target_name"),
            "unknown-target",
        ),
        "packet_status": packet_status,
        "summary": _summary(
            packet_status,
            len(approved_actions),
        ),
        "reviewer": _text(
            source_packet.get("reviewer")
        ),
        "overall_reason": _text(
            source_packet.get("overall_reason")
        ),
        "source_decision_status": _text(
            source_packet.get("decision_status"),
            "unknown",
        ),
        "source_decision_ready": bool(
            source_packet.get("decision_ready")
        ),
        "source_effective_approval_granted": bool(
            source_packet.get(
                "effective_approval_granted"
            )
        ),
        "source_approved_action_packet_ready": bool(
            source_packet.get(
                "approved_action_packet_ready"
            )
        ),
        "source_proposal_count": _int(
            source_packet.get("proposal_count")
        ),
        "source_decision_count": _int(
            source_packet.get("decision_count")
        ),
        "declared_approved_action_count": _int(
            source_packet.get("approved_action_count")
        ),
        "approved_action_count": len(approved_actions),
        "packet_ready": packet_ready,
        "typed_tool_request_manifest_ready": packet_ready,
        "execution_gate_ready": False,
        "runtime_execution_allowed": False,
        "approved_actions": approved_actions,
        "tool_family_counts": tool_family_counts,
        "adapter_family_counts": adapter_family_counts,
        "risk_level_counts": risk_level_counts,
        "scope_confirmation_action_count": (
            scope_confirmation_count
        ),
        "controlled_assets_action_count": (
            controlled_assets_count
        ),
        "runtime_gated_action_count": runtime_gated_count,
        "source_findings": source_findings,
        "action_findings": action_findings,
        "counts": {
            "approved_actions": len(approved_actions),
            "source_findings": len(source_findings),
            "action_findings": len(action_findings),
            "high_findings": len(
                high_source_findings
                + high_action_findings
            ),
            "medium_findings": len(
                [
                    item
                    for item in (
                        source_findings
                        + action_findings
                    )
                    if item.get("severity") == "medium"
                ]
            ),
            "tool_families": len(tool_family_counts),
            "adapter_families": len(adapter_family_counts),
            "risk_levels": len(risk_level_counts),
            "scope_confirmation_actions": (
                scope_confirmation_count
            ),
            "controlled_assets_actions": (
                controlled_assets_count
            ),
            "runtime_gated_actions": runtime_gated_count,
        },
        "allowed_next_steps": allowed_next_steps,
        "rejected_next_steps": list(
            REJECTED_NEXT_STEPS
        ),
        "command_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": dict(SAFETY),
    }


def render_research_approved_action_packet_markdown(
    packet: dict[str, Any],
) -> str:
    """Render approved-action packet Markdown."""

    lines = [
        "# Research Approved Action Packet",
        "",
        "## Packet Status",
        "",
        f"- target_name: `{packet.get('target_name', '')}`",
        f"- packet_status: `{packet.get('packet_status', '')}`",
        f"- packet_ready: `{_bool_text(packet.get('packet_ready'))}`",
        (
            "- typed_tool_request_manifest_ready: "
            f"`{_bool_text(packet.get('typed_tool_request_manifest_ready'))}`"
        ),
        (
            "- runtime_execution_allowed: "
            f"`{_bool_text(packet.get('runtime_execution_allowed'))}`"
        ),
        f"- reviewer: `{packet.get('reviewer') or 'unspecified'}`",
        f"- summary: {packet.get('summary', '')}",
        "",
        "## Source Decision",
        "",
        (
            "- source_decision_status: "
            f"`{packet.get('source_decision_status', '')}`"
        ),
        (
            "- source_decision_ready: "
            f"`{_bool_text(packet.get('source_decision_ready'))}`"
        ),
        (
            "- source_effective_approval_granted: "
            f"`{_bool_text(packet.get('source_effective_approval_granted'))}`"
        ),
        (
            "- source_approved_action_packet_ready: "
            f"`{_bool_text(packet.get('source_approved_action_packet_ready'))}`"
        ),
        (
            "- approved_action_count: "
            f"`{packet.get('approved_action_count', 0)}`"
        ),
        "",
        "## Approved Actions",
        "",
        (
            "| Order | Action ID | Action Type | Tool Family | "
            "Adapter | Risk | Scope | Controlled Assets | "
            "Runtime Gate | Manifest Eligible |"
        ),
        (
            "|---:|---|---|---|---|---|---|---|---|---|"
        ),
    ]

    for item in _object_list(
        packet.get("approved_actions")
    ):
        lines.append(
            "| "
            f"{item.get('manual_order', 0)} | "
            f"`{item.get('action_id', '')}` | "
            f"`{item.get('action_type', '')}` | "
            f"`{item.get('tool_family', '')}` | "
            f"`{item.get('adapter_family', '')}` | "
            f"`{item.get('risk_level', '')}` | "
            f"`{_bool_text(item.get('requires_scope_confirmation'))}` | "
            f"`{_bool_text(item.get('requires_controlled_assets'))}` | "
            f"`{_bool_text(item.get('requires_runtime_gate'))}` | "
            f"`{_bool_text(item.get('manifest_eligible'))}` |"
        )

    lines.extend(["", "## Source Findings", ""])
    lines.extend(
        _render_findings(packet.get("source_findings"))
    )

    lines.extend(["", "## Action Findings", ""])
    lines.extend(
        _render_findings(packet.get("action_findings"))
    )

    lines.extend(["", "## Allowed Next Steps", ""])
    allowed = _list_of_text(
        packet.get("allowed_next_steps")
    )
    lines.extend(
        [f"- {item}" for item in allowed]
        or ["- none"]
    )

    lines.extend(["", "## Rejected Next Steps", ""])
    rejected = _list_of_text(
        packet.get("rejected_next_steps")
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
            "- This packet performs typed normalization only.",
            "- Command generation allowed: `false`",
            "- Package installation allowed: `false`",
            "- Runtime execution allowed: `false`",
            "- Target interaction allowed: `false`",
            "- Evidence collection allowed: `false`",
            "- Validation allowed: `false`",
            (
                "- A typed tool-request manifest and separate "
                "execution gate are still required."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def build_approved_action_packet_from_file(
    decision_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Load a decision packet and optionally write outputs."""

    decision_packet = load_json_object(decision_file)

    packet = build_research_approved_action_packet(
        decision_packet
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_approved_action_packet_markdown(
                packet
            ),
        )

    if json_output is not None:
        write_json(json_output, packet)

    return packet


def _source_findings(
    packet: dict[str, Any],
    approved_actions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_DECISION_KIND:
        findings.append(
            _finding(
                "source-schema",
                "high",
                (
                    "Decision packet kind must be "
                    f"{EXPECTED_DECISION_KIND}."
                ),
                "kind",
                "Provide a valid research action decision packet.",
            )
        )

    if not _text(packet.get("target_name")):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "target_name must not be empty.",
                "target_name",
                "Regenerate the decision packet.",
            )
        )

    if not _text(packet.get("reviewer")):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "reviewer must not be empty.",
                "reviewer",
                "Record the human reviewer.",
            )
        )

    if (
        _text(packet.get("decision_status"))
        != EXPECTED_DECISION_STATUS
    ):
        findings.append(
            _finding(
                "source-readiness",
                "high",
                (
                    "Decision status must be "
                    f"{EXPECTED_DECISION_STATUS}."
                ),
                "decision_status",
                "Resolve decision-packet blockers first.",
            )
        )

    for field in (
        "decision_ready",
        "effective_approval_granted",
        "approved_action_packet_ready",
    ):
        if not bool(packet.get(field)):
            findings.append(
                _finding(
                    "source-readiness",
                    "high",
                    f"{field} must be true.",
                    field,
                    "Use a decision packet ready for this stage.",
                )
            )

    if not isinstance(packet.get("approved_actions"), list):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "approved_actions must be a list.",
                "approved_actions",
                "Regenerate the decision packet.",
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
                "Regenerate the decision packet.",
            )
        )

    for field in PACKET_FALSE_FLAGS:
        if bool(packet.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"Source safety field must remain false: {field}.",
                    field,
                    "Block the unsafe decision packet.",
                )
            )

    if not bool(packet.get("planning_only")):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "planning_only must be true.",
                "planning_only",
                "Regenerate the decision packet.",
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
                "Block the source decision packet.",
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
                "Regenerate the decision packet.",
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
                    "Restore the required safety guardrail.",
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
                    "Block the unsafe decision packet.",
                )
            )

    return findings


def _action_findings(
    approved_actions: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    action_ids: set[str] = set()
    manual_orders: set[int] = set()

    for index, action in enumerate(approved_actions):
        subject = f"approved_actions[{index}]"

        for field in REQUIRED_ACTION_FIELDS:
            if field not in action:
                findings.append(
                    _finding(
                        "action-schema",
                        "high",
                        f"Required action field is missing: {field}.",
                        subject,
                        "Regenerate the decision packet.",
                    )
                )

        action_id = _text(action.get("action_id"))

        if not action_id:
            findings.append(
                _finding(
                    "action-schema",
                    "high",
                    "action_id must not be empty.",
                    subject,
                    "Regenerate the approved action.",
                )
            )
        elif action_id in action_ids:
            findings.append(
                _finding(
                    "action-schema",
                    "high",
                    f"Duplicate action_id: {action_id}.",
                    subject,
                    "Keep one approved action per action ID.",
                )
            )

        action_ids.add(action_id)

        manual_order = _int(action.get("manual_order"))

        if manual_order <= 0:
            findings.append(
                _finding(
                    "action-schema",
                    "medium",
                    "manual_order should be a positive integer.",
                    subject,
                    "Restore deterministic action ordering.",
                )
            )
        elif manual_order in manual_orders:
            findings.append(
                _finding(
                    "action-schema",
                    "medium",
                    f"Duplicate manual_order: {manual_order}.",
                    subject,
                    "Use unique action ordering.",
                )
            )

        manual_orders.add(manual_order)

        action_type = _text(action.get("action_type"))
        profile = ACTION_PROFILES.get(action_type)

        if profile is None:
            findings.append(
                _finding(
                    "action-schema",
                    "high",
                    (
                        "Unsupported approved action type: "
                        f"{action_type or 'missing'}."
                    ),
                    subject,
                    "Use a supported research action type.",
                )
            )
        else:
            expected_family = str(profile["tool_family"])
            actual_family = _text(
                action.get("proposed_tool_family")
            )

            if actual_family != expected_family:
                findings.append(
                    _finding(
                        "action-consistency",
                        "high",
                        (
                            "Tool-family mismatch: "
                            f"{actual_family or 'missing'} != "
                            f"{expected_family}."
                        ),
                        subject,
                        "Regenerate the approved action.",
                    )
                )

        if _text(action.get("decision")) != "approved":
            findings.append(
                _finding(
                    "action-consistency",
                    "high",
                    "Approved action decision must be approved.",
                    subject,
                    "Remove non-approved actions.",
                )
            )

        if not bool(
            action.get("effective_approval_granted")
        ):
            findings.append(
                _finding(
                    "action-consistency",
                    "high",
                    (
                        "effective_approval_granted must be "
                        "true for an approved action."
                    ),
                    subject,
                    "Use an effectively approved decision packet.",
                )
            )

        for field in ACTION_FALSE_FLAGS:
            if bool(action.get(field)):
                findings.append(
                    _finding(
                        "action-safety",
                        "high",
                        f"Action safety field must remain false: {field}.",
                        subject,
                        "Block the unsafe approved action.",
                    )
                )

        blockers = _list_of_text(
            action.get("blocked_by")
        )

        if not blockers:
            findings.append(
                _finding(
                    "action-safety",
                    "high",
                    "blocked_by must not be empty.",
                    subject,
                    "Restore downstream safety blockers.",
                )
            )

        if not _text(action.get("expected_artifact")):
            findings.append(
                _finding(
                    "action-quality",
                    "medium",
                    "expected_artifact should not be empty.",
                    subject,
                    "Specify the expected planning artifact.",
                )
            )

    return findings


def _normalize_action(
    action: dict[str, Any],
    manifest_eligible: bool,
) -> dict[str, Any]:
    action_type = _text(action.get("action_type"))
    profile = ACTION_PROFILES.get(
        action_type,
        {
            "tool_family": _text(
                action.get("proposed_tool_family"),
                "unknown",
            ),
            "adapter_family": "unknown",
            "request_kind": "unknown-request",
            "risk_level": "unknown",
            "requires_scope_confirmation": True,
            "requires_controlled_assets": True,
            "requires_runtime_gate": True,
        },
    )

    requires_scope = bool(
        profile["requires_scope_confirmation"]
    )
    requires_controlled_assets = bool(
        profile["requires_controlled_assets"]
    )
    requires_runtime_gate = bool(
        profile["requires_runtime_gate"]
    )

    blockers = _list_of_text(action.get("blocked_by"))
    blockers.extend(
        [
            "typed-tool-request-manifest-required",
            "human-tool-request-review-required",
            "tool-execution-gate-required",
        ]
    )

    if requires_scope:
        blockers.append("scope-confirmation-required")

    if requires_controlled_assets:
        blockers.append("controlled-assets-required")

    if requires_runtime_gate:
        blockers.extend(
            [
                "runtime-human-approval-required",
                "non-destructive-runtime-guard-required",
                "observation-capture-plan-required",
            ]
        )

    return {
        "action_id": _text(action.get("action_id")),
        "hypothesis_id": _text(
            action.get("hypothesis_id")
        ),
        "hypothesis_type": _text(
            action.get("hypothesis_type")
        ),
        "action_type": action_type,
        "title": _text(action.get("title")),
        "purpose": _text(action.get("purpose")),
        "manual_order": _int(
            action.get("manual_order")
        ),
        "decision_reason": _text(
            action.get("decision_reason")
        ),
        "expected_artifact": _text(
            action.get("expected_artifact")
        ),
        "tool_family": str(profile["tool_family"]),
        "adapter_family": str(
            profile["adapter_family"]
        ),
        "request_kind": str(profile["request_kind"]),
        "risk_level": str(profile["risk_level"]),
        "risk_reasons": _risk_reasons(
            action_type,
            requires_scope,
            requires_controlled_assets,
            requires_runtime_gate,
        ),
        "requires_human_approval": True,
        "requires_scope_confirmation": requires_scope,
        "requires_controlled_assets": (
            requires_controlled_assets
        ),
        "requires_runtime_gate": (
            requires_runtime_gate
        ),
        "requires_redaction_review": True,
        "requires_observation_capture": (
            requires_runtime_gate
        ),
        "manifest_eligible": manifest_eligible,
        "command_generated": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "state_mutation_allowed": False,
        "blocked_by": _dedupe(blockers),
    }


def _risk_reasons(
    action_type: str,
    requires_scope: bool,
    requires_controlled_assets: bool,
    requires_runtime_gate: bool,
) -> list[str]:
    reasons = [
        "Action originates from an explicitly reviewed human decision.",
        "No runtime execution is authorized by this packet.",
    ]

    if requires_scope:
        reasons.append(
            "Action depends on confirmed authorized scope."
        )

    if requires_controlled_assets:
        reasons.append(
            "Action requires controlled accounts, objects, tenants, projects, files, or sessions."
        )

    if requires_runtime_gate:
        reasons.append(
            "Action could lead to future side effects and requires a separate execution gate."
        )

    if action_type == "command-proposal-preparation":
        reasons.append(
            "Command-oriented planning receives high risk classification."
        )

    return reasons


def _packet_status(
    source_packet: dict[str, Any],
    source_actions: list[dict[str, Any]],
    source_findings: list[dict[str, str]],
    action_findings: list[dict[str, str]],
) -> str:
    high_source = [
        item
        for item in source_findings
        if item.get("severity") == "high"
    ]
    high_actions = [
        item
        for item in action_findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category") == "source-safety"
        for item in high_source
    ):
        return "blocked-unsafe-decision-packet"

    if any(
        item.get("category") == "source-readiness"
        for item in high_source
    ):
        return "blocked-decision-not-ready"

    if high_source:
        return "blocked-invalid-decision-packet"

    if not source_actions:
        return "blocked-no-approved-actions"

    if high_actions:
        return "blocked-inconsistent-approved-actions"

    return "ready-for-typed-tool-request-manifest"


def _summary(status: str, action_count: int) -> str:
    if status == "ready-for-typed-tool-request-manifest":
        return (
            f"{action_count} effectively approved action(s) "
            "were normalized for a future typed tool-request "
            "manifest. Runtime execution remains disabled."
        )

    if status == "blocked-no-approved-actions":
        return (
            "The decision packet contains no effectively "
            "approved actions."
        )

    if status == "blocked-decision-not-ready":
        return (
            "The source decision packet is not ready for an "
            "approved-action packet."
        )

    if status == "blocked-unsafe-decision-packet":
        return (
            "The source decision packet contains unsafe flags "
            "and was blocked."
        )

    if status == "blocked-inconsistent-approved-actions":
        return (
            "One or more approved actions are malformed or "
            "inconsistent."
        )

    return (
        "The source decision packet is invalid for this stage."
    )


def _allowed_next_steps(
    status: str,
    action_count: int,
) -> list[str]:
    if status != "ready-for-typed-tool-request-manifest":
        return []

    return [
        (
            "Build a typed planning-only tool-request manifest "
            f"for the {action_count} normalized approved "
            "action(s)."
        ),
        (
            "Review every typed request for tool family, adapter "
            "family, risk, scope, controlled assets, redaction, "
            "and expected artifacts."
        ),
        (
            "Submit the typed manifest to the existing "
            "fail-closed tool execution gate."
        ),
    ]


def _count_by(
    items: list[dict[str, Any]],
    key: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for item in items:
        value = _text(item.get(key), "unknown")
        counts[value] = counts.get(value, 0) + 1

    return dict(sorted(counts.items()))


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
    "ACTION_PROFILES",
    "EXPECTED_DECISION_KIND",
    "EXPECTED_DECISION_STATUS",
    "build_approved_action_packet_from_file",
    "build_research_approved_action_packet",
    "load_json_object",
    "render_research_approved_action_packet_markdown",
    "write_json",
    "write_markdown",
]
