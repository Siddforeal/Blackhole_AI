"""Research action proposal review gate.

v1.13.0 milestone:
research action proposal packet -> local-only human review gate.

This module validates structure, action semantics, tool-family assignments,
approval requirements, blockers, and fail-closed safety flags.

It does not generate commands, install software, execute tools, launch browsers,
interact with Burp Suite, use Kali tools, send requests, collect evidence,
validate findings, mutate state, submit reports, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


EXPECTED_KIND = "brain_chat_research_action_proposal_packet"

REQUIRED_PACKET_FIELDS: tuple[str, ...] = (
    "kind",
    "source",
    "target_name",
    "proposal_status",
    "review_status",
    "review_ready",
    "action_proposal_ready",
    "summary",
    "plan_count",
    "proposal_count",
    "proposals",
    "blockers",
    "human_review_items",
    "rejected_actions",
    "execution_allowed",
    "runtime_execution_allowed",
    "command_generation_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
    "planning_only",
    "execution_state",
    "safety",
)

REQUIRED_PROPOSAL_FIELDS: tuple[str, ...] = (
    "action_id",
    "hypothesis_id",
    "hypothesis_type",
    "action_type",
    "title",
    "purpose",
    "manual_order",
    "proposed_tool_family",
    "expected_artifact",
    "requires_human_approval",
    "requires_scope_confirmation",
    "execution_allowed",
    "runtime_execution_allowed",
    "command_generated",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "blocked_by",
)

ALLOWED_ACTION_TYPES: frozenset[str] = frozenset(
    {
        "local-source-review",
        "local-artifact-review",
        "scope-confirmation-preparation",
        "controlled-account-preparation",
        "browser-observation-proposal",
        "burp-request-review-proposal",
        "command-proposal-preparation",
        "evidence-plan-preparation",
    }
)

EXPECTED_TOOL_FAMILIES: dict[str, str] = {
    "local-source-review": "local-file-analysis",
    "local-artifact-review": "local-artifact-analysis",
    "scope-confirmation-preparation": "scope",
    "controlled-account-preparation": "test-controls",
    "browser-observation-proposal": "browser",
    "burp-request-review-proposal": "burp",
    "command-proposal-preparation": "shell-review",
    "evidence-plan-preparation": "evidence-planning",
}

SCOPE_REQUIRED_ACTIONS: frozenset[str] = frozenset(
    {
        "scope-confirmation-preparation",
        "controlled-account-preparation",
        "browser-observation-proposal",
        "burp-request-review-proposal",
        "command-proposal-preparation",
        "evidence-plan-preparation",
    }
)

REQUIRED_BLOCKERS: dict[str, tuple[str, ...]] = {
    "local-source-review": (
        "human-review",
        "local-artifacts-only",
    ),
    "local-artifact-review": (
        "human-review",
        "existing-artifacts-only",
    ),
    "scope-confirmation-preparation": (
        "scope-confirmation",
        "human-approval",
    ),
    "controlled-account-preparation": (
        "controlled-assets",
        "human-approval",
    ),
    "browser-observation-proposal": (
        "scope-confirmation",
        "human-approval",
        "browser-execution-gate",
    ),
    "burp-request-review-proposal": (
        "scope-confirmation",
        "human-approval",
        "burp-execution-gate",
    ),
    "command-proposal-preparation": (
        "command-safety-review",
        "human-approval",
        "runtime-execution-gate",
    ),
    "evidence-plan-preparation": (
        "human-approval",
        "evidence-collection-gate",
    ),
}

PACKET_FALSE_FLAGS: tuple[str, ...] = (
    "execution_allowed",
    "runtime_execution_allowed",
    "command_generation_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

PROPOSAL_FALSE_FLAGS: tuple[str, ...] = (
    "execution_allowed",
    "runtime_execution_allowed",
    "command_generated",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
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

SAFETY_TRUE_FLAGS: tuple[str, ...] = (
    "local_only",
    "planning_only",
    "human_approval_required",
)

SAFETY: dict[str, bool] = {
    "local_only": True,
    "planning_only": True,
    "human_approval_required": True,
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

REJECTED_ACTIONS: tuple[str, ...] = (
    "Do not execute action proposals from this review gate.",
    "Do not generate shell, curl, browser, Burp, Kali, scanner, or exploitation commands from this review gate.",
    "Do not install packages or modify the local runtime from this review gate.",
    "Do not browse, crawl, send requests, or interact with targets from this review gate.",
    "Do not collect evidence from this review gate.",
    "Do not validate exploitability from this review gate.",
    "Do not confirm vulnerabilities from this review gate.",
    "Do not submit or prepare a final report as confirmed from this review gate.",
    "Do not mutate case memory or research state from this review gate.",
)


def load_json(path: str | Path) -> dict[str, Any]:
    """Load one JSON object from disk."""
    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)

    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")

    return data


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    """Write deterministic JSON output."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(data, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def write_markdown(path: str | Path, text: str) -> None:
    """Write Markdown output."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text, encoding="utf-8")


def build_research_action_proposal_review_gate(
    packet: dict[str, Any],
    source: str = "brain-chat-research-action-proposal-review-gate",
) -> dict[str, Any]:
    """Build a deterministic local-only review gate."""

    schema_findings = _schema_findings(packet)
    safety_findings = _safety_findings(packet)
    proposal_findings = _proposal_findings(packet)

    proposals = _object_list(packet.get("proposals"))
    proposal_count = len(proposals)

    all_findings = schema_findings + safety_findings + proposal_findings
    high_findings = [
        item for item in all_findings
        if item.get("severity") == "high"
    ]
    medium_findings = [
        item for item in all_findings
        if item.get("severity") == "medium"
    ]

    if any(
        item.get("severity") == "high"
        for item in schema_findings
    ):
        review_status = "blocked-invalid-packet"
        review_ready = False
        recommendation = (
            "Fix the action proposal packet schema before human review."
        )
    elif proposal_count == 0:
        review_status = "blocked-no-action-proposals"
        review_ready = False
        recommendation = (
            "Provide at least one action proposal before human review."
        )
    elif high_findings:
        review_status = "blocked-unsafe-action-proposals"
        review_ready = False
        recommendation = (
            "Resolve unsafe flags, invalid action semantics, or missing "
            "approval gates before human review."
        )
    else:
        review_status = "needs-human-review"
        review_ready = True
        recommendation = (
            "Action proposals are structurally reviewable by a human. "
            "This gate does not approve command generation or execution."
        )

    human_review_items = _human_review_items(
        packet,
        schema_findings,
        safety_findings,
        proposal_findings,
    )

    return {
        "kind": "brain_chat_research_action_proposal_review_gate",
        "source": source,
        "target_name": _text(packet.get("target_name"), "unknown-target"),
        "review_status": review_status,
        "recommendation": recommendation,
        "packet_kind": _text(packet.get("kind")),
        "proposal_status": _text(packet.get("proposal_status"), "unknown"),
        "source_review_status": _text(packet.get("review_status"), "unknown"),
        "source_review_ready": bool(packet.get("review_ready")),
        "source_action_proposal_ready": bool(
            packet.get("action_proposal_ready")
        ),
        "plan_count": _int(packet.get("plan_count")),
        "declared_proposal_count": _int(packet.get("proposal_count")),
        "proposal_count": proposal_count,
        "review_ready": review_ready,
        "command_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "schema_findings": schema_findings,
        "safety_findings": safety_findings,
        "proposal_findings": proposal_findings,
        "counts": {
            "schema_findings": len(schema_findings),
            "safety_findings": len(safety_findings),
            "proposal_findings": len(proposal_findings),
            "high_findings": len(high_findings),
            "medium_findings": len(medium_findings),
            "human_review_items": len(human_review_items),
            "rejected_actions": len(REJECTED_ACTIONS),
        },
        "human_review_items": human_review_items,
        "rejected_actions": list(REJECTED_ACTIONS),
        "planning_only": True,
        "execution_state": "not_executed",
        "gate_state": "reviewed_not_used",
        "safety": dict(SAFETY),
    }


def render_research_action_proposal_review_gate_markdown(
    review_gate: dict[str, Any],
) -> str:
    """Render a human-readable action proposal review gate."""

    lines = [
        "# Research Action Proposal Review Gate",
        "",
        "## Review Status",
        "",
        f"- kind: `{review_gate.get('kind', '')}`",
        f"- target_name: `{review_gate.get('target_name', '')}`",
        f"- review_status: `{review_gate.get('review_status', '')}`",
        f"- recommendation: {review_gate.get('recommendation', '')}",
        f"- proposal_status: `{review_gate.get('proposal_status', '')}`",
        f"- source_review_status: `{review_gate.get('source_review_status', '')}`",
        (
            "- source_review_ready: "
            f"`{_bool_text(review_gate.get('source_review_ready'))}`"
        ),
        (
            "- source_action_proposal_ready: "
            f"`{_bool_text(review_gate.get('source_action_proposal_ready'))}`"
        ),
        f"- plan_count: `{review_gate.get('plan_count', 0)}`",
        (
            "- declared_proposal_count: "
            f"`{review_gate.get('declared_proposal_count', 0)}`"
        ),
        f"- proposal_count: `{review_gate.get('proposal_count', 0)}`",
        f"- review_ready: `{_bool_text(review_gate.get('review_ready'))}`",
        "- command_generation_allowed: `false`",
        "- package_installation_allowed: `false`",
        "- execution_allowed: `false`",
        "- runtime_execution_allowed: `false`",
        "- target_interaction_allowed: `false`",
        "- evidence_collection_allowed: `false`",
        "- validation_allowed: `false`",
        "- report_submission_allowed: `false`",
        "- vulnerability_confirmation_allowed: `false`",
        "",
        "## Schema Findings",
        "",
    ]

    lines.extend(_render_findings(review_gate.get("schema_findings")))
    lines.extend(["", "## Safety Findings", ""])
    lines.extend(_render_findings(review_gate.get("safety_findings")))
    lines.extend(["", "## Proposal Findings", ""])
    lines.extend(_render_findings(review_gate.get("proposal_findings")))

    lines.extend(["", "## Human Review Items", ""])
    human_review_items = _list_of_text(
        review_gate.get("human_review_items")
    )
    if human_review_items:
        lines.extend(f"- [ ] {item}" for item in human_review_items)
    else:
        lines.append("- none")

    lines.extend(["", "## Rejected Actions", ""])
    rejected = _list_of_text(review_gate.get("rejected_actions"))
    if rejected:
        lines.extend(f"- {item}" for item in rejected)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- This review gate is local and planning-only.",
            (
                "- It does not generate commands, install software, execute "
                "tools, browse, send requests, collect evidence, validate "
                "findings, submit reports, or confirm vulnerabilities."
            ),
            (
                "- A later action decision, command safety review, and "
                "execution gate remain required."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def build_review_gate_from_file(
    proposal_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Load a proposal packet and optionally write review outputs."""

    packet = load_json(proposal_file)
    review_gate = build_research_action_proposal_review_gate(packet)

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_action_proposal_review_gate_markdown(review_gate),
        )

    if json_output is not None:
        write_json(json_output, review_gate)

    return review_gate


def _schema_findings(
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_KIND:
        findings.append(
            _finding(
                "schema",
                "high",
                f"Packet kind must be {EXPECTED_KIND}.",
                "kind",
                "Build a valid research action proposal packet.",
            )
        )

    for field in REQUIRED_PACKET_FIELDS:
        if field not in packet:
            findings.append(
                _finding(
                    "schema",
                    "high",
                    f"Required packet field is missing: {field}.",
                    field,
                    "Regenerate the packet with all required fields.",
                )
            )

    proposals = packet.get("proposals")
    if "proposals" in packet and not isinstance(proposals, list):
        findings.append(
            _finding(
                "schema",
                "high",
                "proposals must be a list.",
                "proposals",
                "Regenerate proposals as a list of objects.",
            )
        )

    if isinstance(proposals, list):
        actual_count = len(
            [item for item in proposals if isinstance(item, dict)]
        )
        declared_count = _int(packet.get("proposal_count"))

        if declared_count != actual_count:
            findings.append(
                _finding(
                    "schema",
                    "medium",
                    (
                        "proposal_count does not match actual proposal count: "
                        f"{declared_count} != {actual_count}."
                    ),
                    "proposal_count",
                    "Review packet count consistency.",
                )
            )

    if _text(packet.get("proposal_status")) not in {
        "ready-for-action-proposal-review",
        "blocked-invalid-investigation-plan",
        "blocked-invalid-review-gate",
        "blocked-plan-review-mismatch",
        "blocked-pending-review-ready-plan",
        "blocked-no-investigation-plans",
    }:
        findings.append(
            _finding(
                "schema",
                "medium",
                (
                    "Unexpected proposal_status: "
                    f"{_text(packet.get('proposal_status'), 'missing')}."
                ),
                "proposal_status",
                "Review whether the expected proposal builder produced this packet.",
            )
        )

    if _text(packet.get("execution_state")) != "not_executed":
        findings.append(
            _finding(
                "schema",
                "high",
                "execution_state must be not_executed.",
                "execution_state",
                "Block this packet until execution state is reset.",
            )
        )

    if bool(packet.get("planning_only")) is not True:
        findings.append(
            _finding(
                "schema",
                "high",
                "planning_only must be true.",
                "planning_only",
                "Regenerate the packet in planning-only mode.",
            )
        )

    return findings


def _safety_findings(
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    for field in PACKET_FALSE_FLAGS:
        if field not in packet:
            continue
        if bool(packet.get(field)) is not False:
            findings.append(
                _finding(
                    "packet-safety",
                    "high",
                    f"Packet safety field must remain false: {field}.",
                    field,
                    "Block progression until the field is false.",
                )
            )

    safety = packet.get("safety")
    if not isinstance(safety, dict):
        return findings + [
            _finding(
                "safety",
                "high",
                "safety must be present as an object.",
                "safety",
                "Regenerate the packet with complete safety metadata.",
            )
        ]

    for field in SAFETY_TRUE_FLAGS:
        if field not in safety:
            findings.append(
                _finding(
                    "safety",
                    "medium",
                    f"Required true safety flag is missing: {field}.",
                    f"safety.{field}",
                    "Regenerate the packet with complete safety metadata.",
                )
            )
        elif bool(safety.get(field)) is not True:
            findings.append(
                _finding(
                    "safety",
                    "high",
                    f"Safety flag must be true: {field}.",
                    f"safety.{field}",
                    "Block progression until the required guardrail is enabled.",
                )
            )

    for field in SAFETY_FALSE_FLAGS:
        if field not in safety:
            findings.append(
                _finding(
                    "safety",
                    "medium",
                    f"Required false safety flag is missing: {field}.",
                    f"safety.{field}",
                    "Regenerate the packet with complete safety metadata.",
                )
            )
        elif bool(safety.get(field)) is not False:
            findings.append(
                _finding(
                    "safety",
                    "high",
                    f"Safety flag must remain false: {field}.",
                    f"safety.{field}",
                    "Block progression until the unsafe capability is disabled.",
                )
            )

    return findings


def _proposal_findings(
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    proposals = packet.get("proposals")

    if not isinstance(proposals, list):
        return findings

    action_ids: set[str] = set()
    manual_orders: set[int] = set()

    for index, proposal in enumerate(proposals):
        prefix = f"proposals[{index}]"

        if not isinstance(proposal, dict):
            findings.append(
                _finding(
                    "proposal",
                    "high",
                    "Proposal item must be an object.",
                    prefix,
                    "Regenerate all proposals as JSON objects.",
                )
            )
            continue

        action_id = _text(proposal.get("action_id"), f"proposal-{index}")
        subject = f"{prefix}:{action_id}"

        for field in REQUIRED_PROPOSAL_FIELDS:
            if field not in proposal:
                findings.append(
                    _finding(
                        "proposal",
                        "high",
                        f"Required proposal field is missing: {field}.",
                        subject,
                        "Regenerate the proposal with all required fields.",
                    )
                )

        if action_id in action_ids:
            findings.append(
                _finding(
                    "proposal",
                    "high",
                    f"Duplicate action_id detected: {action_id}.",
                    subject,
                    "Assign a unique action_id to every proposal.",
                )
            )
        action_ids.add(action_id)

        manual_order = _int(proposal.get("manual_order"))
        if manual_order <= 0:
            findings.append(
                _finding(
                    "proposal",
                    "medium",
                    "manual_order must be a positive integer.",
                    subject,
                    "Assign a positive manual review order.",
                )
            )
        elif manual_order in manual_orders:
            findings.append(
                _finding(
                    "proposal",
                    "medium",
                    f"Duplicate manual_order detected: {manual_order}.",
                    subject,
                    "Assign a unique deterministic review order.",
                )
            )
        manual_orders.add(manual_order)

        action_type = _text(proposal.get("action_type"))
        if action_type not in ALLOWED_ACTION_TYPES:
            findings.append(
                _finding(
                    "proposal",
                    "high",
                    f"Unsupported action_type: {action_type or 'missing'}.",
                    subject,
                    "Use one of the supported deterministic action types.",
                )
            )
        else:
            expected_family = EXPECTED_TOOL_FAMILIES[action_type]
            actual_family = _text(proposal.get("proposed_tool_family"))
            if actual_family != expected_family:
                findings.append(
                    _finding(
                        "proposal",
                        "medium",
                        (
                            f"Tool family mismatch for {action_type}: "
                            f"{actual_family or 'missing'} != {expected_family}."
                        ),
                        subject,
                        "Correct the action type to tool-family mapping.",
                    )
                )

        if not _text(proposal.get("hypothesis_id")):
            findings.append(
                _finding(
                    "proposal",
                    "high",
                    "hypothesis_id must not be empty.",
                    subject,
                    "Associate the action with one selected hypothesis.",
                )
            )

        for field in ("title", "purpose", "expected_artifact"):
            if not _text(proposal.get(field)):
                findings.append(
                    _finding(
                        "proposal",
                        "medium",
                        f"{field} should not be empty.",
                        subject,
                        "Provide human-reviewable proposal context.",
                    )
                )

        if bool(proposal.get("requires_human_approval")) is not True:
            findings.append(
                _finding(
                    "proposal-safety",
                    "high",
                    "requires_human_approval must be true.",
                    subject,
                    "Block progression until human approval is required.",
                )
            )

        if (
            action_type in SCOPE_REQUIRED_ACTIONS
            and bool(proposal.get("requires_scope_confirmation")) is not True
        ):
            findings.append(
                _finding(
                    "proposal-safety",
                    "high",
                    (
                        "requires_scope_confirmation must be true for "
                        f"{action_type}."
                    ),
                    subject,
                    "Require scope confirmation before later active workflows.",
                )
            )

        for field in PROPOSAL_FALSE_FLAGS:
            if bool(proposal.get(field)) is not False:
                findings.append(
                    _finding(
                        "proposal-safety",
                        "high",
                        f"Proposal flag must remain false: {field}.",
                        subject,
                        "Block progression until all execution flags are false.",
                    )
                )

        blockers = set(_list_of_text(proposal.get("blocked_by")))
        if not blockers:
            findings.append(
                _finding(
                    "proposal-safety",
                    "high",
                    "blocked_by must contain explicit review gates.",
                    subject,
                    "Regenerate the proposal with explicit blockers.",
                )
            )
        elif action_type in REQUIRED_BLOCKERS:
            for blocker in REQUIRED_BLOCKERS[action_type]:
                if blocker not in blockers:
                    findings.append(
                        _finding(
                            "proposal-safety",
                            "medium",
                            f"Required blocker is missing: {blocker}.",
                            subject,
                            "Restore the complete action-specific blocker set.",
                        )
                    )

    expected_orders = list(range(1, len(proposals) + 1))
    actual_orders = sorted(
        order for order in manual_orders
        if order > 0
    )
    if actual_orders and actual_orders != expected_orders:
        findings.append(
            _finding(
                "proposal",
                "medium",
                (
                    "manual_order values should form a continuous sequence "
                    f"from 1 to {len(proposals)}."
                ),
                "proposals.manual_order",
                "Regenerate deterministic proposal ordering.",
            )
        )

    return findings


def _human_review_items(
    packet: dict[str, Any],
    schema_findings: list[dict[str, str]],
    safety_findings: list[dict[str, str]],
    proposal_findings: list[dict[str, str]],
) -> list[str]:
    items = [
        "Confirm this review gate is used only for local human review.",
        "Confirm every proposal remains associated with an authorized hypothesis and target.",
        "Confirm no executable command or payload was generated.",
        "Confirm package installation remains blocked.",
        "Confirm browser, Burp, curl, Kali, scanner, shell, and network execution remain blocked.",
        "Confirm target interaction remains blocked.",
        "Confirm evidence collection and validation remain blocked.",
        "Confirm no vulnerability is treated as confirmed or reportable.",
        "Select, reject, or request revision for every action proposal before the next workflow stage.",
    ]

    if schema_findings:
        items.append(
            "Review schema findings and regenerate malformed packet fields."
        )

    if safety_findings:
        items.append(
            "Review packet safety findings and block progression until all guardrails pass."
        )

    if proposal_findings:
        items.append(
            "Review proposal findings for invalid actions, mappings, flags, blockers, or ordering."
        )

    if _object_list(packet.get("proposals")):
        items.append(
            "Review action relevance, expected artifacts, and hypothesis alignment."
        )

    return _dedupe(items)


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

    for finding in findings:
        if not isinstance(finding, dict):
            continue
        lines.append(
            "- "
            f"[{finding.get('severity', 'unknown')}] "
            f"{finding.get('category', 'finding')} / "
            f"{finding.get('subject', 'unknown')}: "
            f"{finding.get('message', '')} "
            f"Required action: {finding.get('required_action', '')}"
        )

    return lines or ["- none"]


def _object_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _list_of_text(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, tuple):
        value = list(value)
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _text(value: Any, default: str = "") -> str:
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _int(value: Any) -> int:
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        try:
            return int(value.strip())
        except ValueError:
            return 0
    return 0


def _bool_text(value: Any) -> str:
    return str(bool(value)).lower()


def _dedupe(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))


__all__ = [
    "ALLOWED_ACTION_TYPES",
    "EXPECTED_KIND",
    "EXPECTED_TOOL_FAMILIES",
    "REJECTED_ACTIONS",
    "SAFETY",
    "build_research_action_proposal_review_gate",
    "build_review_gate_from_file",
    "load_json",
    "render_research_action_proposal_review_gate_markdown",
    "write_json",
    "write_markdown",
]
