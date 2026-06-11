"""Research action decision packet.

This module imports explicit human decisions for reviewed research action
proposals.

It validates proposal/review consistency, decision coverage, decision values,
reviewer metadata, and fail-closed safety fields.

It records approval metadata only. It does not generate commands, install
software, execute tools, launch browsers, interact with Burp Suite, use Kali
tools, send requests, collect evidence, mutate targets, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any


EXPECTED_PROPOSAL_KIND = (
    "brain_chat_research_action_proposal_packet"
)
EXPECTED_REVIEW_KIND = (
    "brain_chat_research_action_proposal_review_gate"
)
EXPECTED_DECISION_INPUT_KIND = (
    "brain_chat_research_action_decision_input"
)

VALID_DECISIONS: tuple[str, ...] = (
    "approved",
    "rejected",
    "changes-requested",
    "deferred",
)

PROPOSAL_FALSE_FLAGS: tuple[str, ...] = (
    "execution_allowed",
    "runtime_execution_allowed",
    "command_generation_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

REVIEW_FALSE_FLAGS: tuple[str, ...] = (
    "command_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
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
    "human_decision_required": True,
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
    "Do not execute an approved research action from this decision packet.",
    "Do not generate shell, curl, browser, Burp, Kali, scanner, or exploitation commands.",
    "Do not install packages or modify the runtime environment.",
    "Do not send requests or interact with a target.",
    "Do not collect evidence or validate exploitability.",
    "Do not mutate case memory or research state.",
    "Do not submit a report or confirm a vulnerability.",
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


def build_research_action_decision_template(
    proposal_packet: dict[str, Any],
) -> dict[str, Any]:
    """Build a local human-decision input template."""

    proposals = _object_list(proposal_packet.get("proposals"))

    decisions = [
        {
            "action_id": _text(proposal.get("action_id")),
            "decision": "deferred",
            "reason": "Pending explicit human decision.",
        }
        for proposal in proposals
        if _text(proposal.get("action_id"))
    ]

    return {
        "kind": EXPECTED_DECISION_INPUT_KIND,
        "target_name": _text(
            proposal_packet.get("target_name"),
            "unknown-target",
        ),
        "reviewer": "",
        "overall_reason": "",
        "decisions": decisions,
        "planning_only": True,
        "execution_state": "not_executed",
    }


def build_research_action_decision_packet(
    proposal_packet: dict[str, Any],
    review_gate: dict[str, Any],
    decision_input: dict[str, Any],
    source: str = "brain-chat-research-action-decision-packet",
) -> dict[str, Any]:
    """Build the deterministic research action decision packet."""

    proposal_copy = copy.deepcopy(proposal_packet)
    review_copy = copy.deepcopy(review_gate)
    decision_copy = copy.deepcopy(decision_input)

    proposals = _object_list(proposal_copy.get("proposals"))

    source_findings = _source_findings(
        proposal_copy,
        review_copy,
        proposals,
    )
    decision_findings = _decision_findings(
        proposal_copy,
        decision_copy,
        proposals,
    )

    source_high = [
        item
        for item in source_findings
        if item.get("severity") == "high"
    ]
    decision_high = [
        item
        for item in decision_findings
        if item.get("severity") == "high"
    ]

    decision_map = _build_decision_map(
        decision_copy,
        proposals,
    )

    preliminary_records = [
        _decision_record(
            proposal,
            decision_map.get(
                _text(proposal.get("action_id"))
            ),
            effective=False,
        )
        for proposal in proposals
    ]

    preliminary_counts = _decision_counts(preliminary_records)

    decision_status = _decision_status(
        source_findings=source_findings,
        decision_findings=decision_findings,
        counts=preliminary_counts,
    )

    approved_action_packet_ready = (
        decision_status == "ready-for-approved-action-packet"
    )

    records = [
        _decision_record(
            proposal,
            decision_map.get(
                _text(proposal.get("action_id"))
            ),
            effective=approved_action_packet_ready,
        )
        for proposal in proposals
    ]

    counts = _decision_counts(records)

    approved_actions = [
        item
        for item in records
        if item["decision"] == "approved"
    ]
    rejected_actions = [
        item
        for item in records
        if item["decision"] == "rejected"
    ]
    changes_requested_actions = [
        item
        for item in records
        if item["decision"] == "changes-requested"
    ]
    deferred_actions = [
        item
        for item in records
        if item["decision"] == "deferred"
    ]
    unresolved_action_ids = [
        item["action_id"]
        for item in records
        if item["decision"] == "missing"
    ]

    decision_ready = not source_high and not decision_high
    effective_approval_granted = (
        approved_action_packet_ready
        and bool(approved_actions)
        and all(
            item["effective_approval_granted"]
            for item in approved_actions
        )
    )

    allowed_next_steps = _allowed_next_steps(
        decision_status,
        counts,
    )

    return {
        "kind": "brain_chat_research_action_decision_packet",
        "source": source,
        "target_name": _text(
            proposal_copy.get("target_name"),
            "unknown-target",
        ),
        "decision_status": decision_status,
        "summary": _summary(decision_status, counts),
        "reviewer": _text(decision_copy.get("reviewer")),
        "overall_reason": _text(
            decision_copy.get("overall_reason")
        ),
        "proposal_status": _text(
            proposal_copy.get("proposal_status"),
            "unknown",
        ),
        "review_status": _text(
            review_copy.get("review_status"),
            "unknown",
        ),
        "source_review_ready": bool(
            review_copy.get("review_ready")
        ),
        "source_action_proposal_ready": bool(
            proposal_copy.get("action_proposal_ready")
        ),
        "plan_count": _int(
            proposal_copy.get("plan_count")
        ),
        "proposal_count": len(proposals),
        "decision_count": len(
            _object_list(decision_copy.get("decisions"))
        ),
        "decision_ready": decision_ready,
        "effective_approval_granted": (
            effective_approval_granted
        ),
        "approved_action_packet_ready": (
            approved_action_packet_ready
        ),
        "tool_request_manifest_ready": False,
        "execution_gate_ready": False,
        "approved_action_count": counts["approved"],
        "rejected_action_count": counts["rejected"],
        "changes_requested_count": (
            counts["changes_requested"]
        ),
        "deferred_action_count": counts["deferred"],
        "missing_decision_count": counts["missing"],
        "unresolved_action_ids": unresolved_action_ids,
        "action_decisions": records,
        "approved_actions": approved_actions,
        "rejected_actions": rejected_actions,
        "changes_requested_actions": (
            changes_requested_actions
        ),
        "deferred_actions": deferred_actions,
        "source_findings": source_findings,
        "decision_findings": decision_findings,
        "counts": {
            **counts,
            "source_findings": len(source_findings),
            "decision_findings": len(decision_findings),
            "high_findings": len(
                source_high + decision_high
            ),
            "medium_findings": len(
                [
                    item
                    for item in (
                        source_findings
                        + decision_findings
                    )
                    if item.get("severity") == "medium"
                ]
            ),
        },
        "allowed_next_steps": allowed_next_steps,
        "rejected_next_steps": list(
            REJECTED_NEXT_STEPS
        ),
        "command_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
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


def render_research_action_decision_packet_markdown(
    packet: dict[str, Any],
) -> str:
    """Render a human-readable decision packet."""

    lines = [
        "# Research Action Decision Packet",
        "",
        "## Decision Status",
        "",
        f"- target_name: `{packet.get('target_name', '')}`",
        (
            "- decision_status: "
            f"`{packet.get('decision_status', '')}`"
        ),
        (
            "- decision_ready: "
            f"`{_bool_text(packet.get('decision_ready'))}`"
        ),
        (
            "- effective_approval_granted: "
            f"`{_bool_text(packet.get('effective_approval_granted'))}`"
        ),
        (
            "- approved_action_packet_ready: "
            f"`{_bool_text(packet.get('approved_action_packet_ready'))}`"
        ),
        f"- reviewer: `{packet.get('reviewer') or 'unspecified'}`",
        f"- summary: {packet.get('summary', '')}",
        "",
        "## Counts",
        "",
        f"- proposal_count: `{packet.get('proposal_count', 0)}`",
        f"- decision_count: `{packet.get('decision_count', 0)}`",
        (
            "- approved_action_count: "
            f"`{packet.get('approved_action_count', 0)}`"
        ),
        (
            "- rejected_action_count: "
            f"`{packet.get('rejected_action_count', 0)}`"
        ),
        (
            "- changes_requested_count: "
            f"`{packet.get('changes_requested_count', 0)}`"
        ),
        (
            "- deferred_action_count: "
            f"`{packet.get('deferred_action_count', 0)}`"
        ),
        (
            "- missing_decision_count: "
            f"`{packet.get('missing_decision_count', 0)}`"
        ),
        "",
        "## Action Decisions",
        "",
        "| Order | Action ID | Tool Family | Decision | Effective Approval | Reason |",
        "|---:|---|---|---|---|---|",
    ]

    for item in _object_list(
        packet.get("action_decisions")
    ):
        lines.append(
            "| "
            f"{item.get('manual_order', 0)} | "
            f"`{item.get('action_id', '')}` | "
            f"`{item.get('proposed_tool_family', '')}` | "
            f"`{item.get('decision', '')}` | "
            f"`{_bool_text(item.get('effective_approval_granted'))}` | "
            f"{item.get('decision_reason') or 'none'} |"
        )

    lines.extend(["", "## Source Findings", ""])
    lines.extend(
        _render_findings(packet.get("source_findings"))
    )

    lines.extend(["", "## Decision Findings", ""])
    lines.extend(
        _render_findings(packet.get("decision_findings"))
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
            "- This packet records local human decisions only.",
            "- Command generation allowed: `false`",
            "- Package installation allowed: `false`",
            "- Runtime execution allowed: `false`",
            "- Target interaction allowed: `false`",
            "- Evidence collection allowed: `false`",
            "- Validation allowed: `false`",
            (
                "- Approved actions still require an approved-action "
                "packet, typed tool-request manifest, and execution gate."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def build_decision_packet_from_files(
    proposal_file: str | Path,
    review_file: str | Path,
    decision_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Load inputs and optionally write decision outputs."""

    proposal_packet = load_json_object(proposal_file)
    review_gate = load_json_object(review_file)
    decision_input = load_json_object(decision_file)

    packet = build_research_action_decision_packet(
        proposal_packet,
        review_gate,
        decision_input,
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_action_decision_packet_markdown(
                packet
            ),
        )

    if json_output is not None:
        write_json(json_output, packet)

    return packet


def _source_findings(
    proposal_packet: dict[str, Any],
    review_gate: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if (
        proposal_packet.get("kind")
        != EXPECTED_PROPOSAL_KIND
    ):
        findings.append(
            _finding(
                "source-schema",
                "high",
                (
                    "Proposal packet kind must be "
                    f"{EXPECTED_PROPOSAL_KIND}."
                ),
                "proposal.kind",
                "Provide a valid action proposal packet.",
            )
        )

    if review_gate.get("kind") != EXPECTED_REVIEW_KIND:
        findings.append(
            _finding(
                "source-schema",
                "high",
                (
                    "Review gate kind must be "
                    f"{EXPECTED_REVIEW_KIND}."
                ),
                "review.kind",
                "Provide a valid action proposal review gate.",
            )
        )

    proposal_target = _text(
        proposal_packet.get("target_name")
    )
    review_target = _text(
        review_gate.get("target_name")
    )

    if not proposal_target:
        findings.append(
            _finding(
                "source-schema",
                "high",
                "Proposal target_name is missing.",
                "proposal.target_name",
                "Regenerate the proposal packet.",
            )
        )

    if proposal_target != review_target:
        findings.append(
            _finding(
                "source-consistency",
                "high",
                "Proposal and review target names do not match.",
                "target_name",
                "Use the matching review gate.",
            )
        )

    if (
        _text(proposal_packet.get("proposal_status"))
        != "ready-for-action-proposal-review"
    ):
        findings.append(
            _finding(
                "source-review",
                "high",
                "Proposal packet is not review-ready.",
                "proposal.proposal_status",
                "Resolve proposal-packet blockers first.",
            )
        )

    if not bool(
        proposal_packet.get("action_proposal_ready")
    ):
        findings.append(
            _finding(
                "source-review",
                "high",
                "action_proposal_ready must be true.",
                "proposal.action_proposal_ready",
                "Use a ready action proposal packet.",
            )
        )

    if (
        _text(review_gate.get("review_status"))
        != "needs-human-review"
    ):
        findings.append(
            _finding(
                "source-review",
                "high",
                "Review gate must have needs-human-review status.",
                "review.review_status",
                "Resolve review-gate blockers first.",
            )
        )

    if not bool(review_gate.get("review_ready")):
        findings.append(
            _finding(
                "source-review",
                "high",
                "Review gate is not ready.",
                "review.review_ready",
                "Use a human-reviewable review gate.",
            )
        )

    if not bool(
        review_gate.get("source_action_proposal_ready")
    ):
        findings.append(
            _finding(
                "source-review",
                "high",
                "Review gate does not recognize a ready proposal packet.",
                "review.source_action_proposal_ready",
                "Regenerate the review gate.",
            )
        )

    actual_count = len(proposals)
    proposal_count = _int(
        proposal_packet.get("proposal_count")
    )
    review_count = _int(
        review_gate.get("proposal_count")
    )

    if proposal_count != actual_count:
        findings.append(
            _finding(
                "source-consistency",
                "high",
                (
                    "Proposal count does not match actual "
                    f"proposals: {proposal_count} != {actual_count}."
                ),
                "proposal.proposal_count",
                "Regenerate the proposal packet.",
            )
        )

    if review_count != actual_count:
        findings.append(
            _finding(
                "source-consistency",
                "high",
                (
                    "Review proposal count does not match actual "
                    f"proposals: {review_count} != {actual_count}."
                ),
                "review.proposal_count",
                "Regenerate the review gate.",
            )
        )

    proposal_ids = [
        _text(item.get("action_id"))
        for item in proposals
    ]

    if any(not action_id for action_id in proposal_ids):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "Every proposal requires an action_id.",
                "proposal.proposals",
                "Regenerate proposals with action IDs.",
            )
        )

    if len(set(proposal_ids)) != len(proposal_ids):
        findings.append(
            _finding(
                "source-schema",
                "high",
                "Proposal action IDs must be unique.",
                "proposal.proposals",
                "Regenerate proposals with unique action IDs.",
            )
        )

    for field in PROPOSAL_FALSE_FLAGS:
        if bool(proposal_packet.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"Proposal safety field must remain false: {field}.",
                    f"proposal.{field}",
                    "Block the unsafe proposal packet.",
                )
            )

    for field in REVIEW_FALSE_FLAGS:
        if bool(review_gate.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    f"Review safety field must remain false: {field}.",
                    f"review.{field}",
                    "Block the unsafe review gate.",
                )
            )

    _append_nested_safety_findings(
        findings,
        proposal_packet,
        "proposal",
    )
    _append_nested_safety_findings(
        findings,
        review_gate,
        "review",
    )

    if not bool(proposal_packet.get("planning_only")):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "Proposal packet must remain planning-only.",
                "proposal.planning_only",
                "Regenerate the proposal packet.",
            )
        )

    if not bool(review_gate.get("planning_only")):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "Review gate must remain planning-only.",
                "review.planning_only",
                "Regenerate the review gate.",
            )
        )

    if (
        _text(proposal_packet.get("execution_state"))
        != "not_executed"
    ):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "Proposal execution_state must be not_executed.",
                "proposal.execution_state",
                "Block the source packet.",
            )
        )

    if (
        _text(review_gate.get("execution_state"))
        != "not_executed"
    ):
        findings.append(
            _finding(
                "source-safety",
                "high",
                "Review execution_state must be not_executed.",
                "review.execution_state",
                "Block the source review gate.",
            )
        )

    return findings


def _decision_findings(
    proposal_packet: dict[str, Any],
    decision_input: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if (
        decision_input.get("kind")
        != EXPECTED_DECISION_INPUT_KIND
    ):
        findings.append(
            _finding(
                "decision-schema",
                "high",
                (
                    "Decision input kind must be "
                    f"{EXPECTED_DECISION_INPUT_KIND}."
                ),
                "decision.kind",
                "Use the generated decision template.",
            )
        )

    proposal_target = _text(
        proposal_packet.get("target_name")
    )
    decision_target = _text(
        decision_input.get("target_name")
    )

    if decision_target != proposal_target:
        findings.append(
            _finding(
                "decision-consistency",
                "high",
                "Decision and proposal target names do not match.",
                "decision.target_name",
                "Use a decision file for the same target.",
            )
        )

    if not _text(decision_input.get("reviewer")):
        findings.append(
            _finding(
                "decision-schema",
                "high",
                "reviewer must not be empty.",
                "decision.reviewer",
                "Record the human reviewer.",
            )
        )

    decisions = decision_input.get("decisions")

    if not isinstance(decisions, list):
        findings.append(
            _finding(
                "decision-schema",
                "high",
                "decisions must be a list.",
                "decision.decisions",
                "Use the generated decision template.",
            )
        )
        return findings

    proposal_ids = {
        _text(item.get("action_id"))
        for item in proposals
        if _text(item.get("action_id"))
    }

    seen: set[str] = set()
    decided: set[str] = set()

    for index, item in enumerate(decisions):
        subject = f"decision.decisions[{index}]"

        if not isinstance(item, dict):
            findings.append(
                _finding(
                    "decision-schema",
                    "high",
                    "Decision item must be an object.",
                    subject,
                    "Replace it with a structured decision.",
                )
            )
            continue

        action_id = _text(item.get("action_id"))

        if not action_id:
            findings.append(
                _finding(
                    "decision-schema",
                    "high",
                    "Decision action_id must not be empty.",
                    subject,
                    "Associate the decision with an action.",
                )
            )
            continue

        if action_id in seen:
            findings.append(
                _finding(
                    "decision-schema",
                    "high",
                    f"Duplicate decision for action_id: {action_id}.",
                    subject,
                    "Keep exactly one decision per action.",
                )
            )

        seen.add(action_id)

        if action_id not in proposal_ids:
            findings.append(
                _finding(
                    "decision-consistency",
                    "high",
                    f"Unknown action_id: {action_id}.",
                    subject,
                    "Remove decisions for unknown actions.",
                )
            )
            continue

        decided.add(action_id)

        raw_decision = _text(item.get("decision"))

        try:
            normalized = _normalize_decision(raw_decision)
        except ValueError:
            findings.append(
                _finding(
                    "decision-schema",
                    "high",
                    (
                        f"Invalid decision for {action_id}: "
                        f"{raw_decision or 'missing'}."
                    ),
                    subject,
                    (
                        "Use approved, rejected, "
                        "changes-requested, or deferred."
                    ),
                )
            )
            continue

        reason = _text(item.get("reason"))

        if (
            normalized
            in {"rejected", "changes-requested", "deferred"}
            and not reason
        ):
            findings.append(
                _finding(
                    "decision-quality",
                    "medium",
                    (
                        f"A reason should be provided for "
                        f"{normalized}: {action_id}."
                    ),
                    subject,
                    "Record a human-readable rationale.",
                )
            )

    missing = sorted(proposal_ids - decided)

    for action_id in missing:
        findings.append(
            _finding(
                "decision-coverage",
                "high",
                f"Missing decision for action_id: {action_id}.",
                action_id,
                "Decide every proposal exactly once.",
            )
        )

    if not bool(decision_input.get("planning_only")):
        findings.append(
            _finding(
                "decision-safety",
                "high",
                "Decision input must remain planning-only.",
                "decision.planning_only",
                "Use a planning-only decision file.",
            )
        )

    if (
        _text(decision_input.get("execution_state"))
        != "not_executed"
    ):
        findings.append(
            _finding(
                "decision-safety",
                "high",
                "Decision execution_state must be not_executed.",
                "decision.execution_state",
                "Reset the decision input state.",
            )
        )

    return findings


def _append_nested_safety_findings(
    findings: list[dict[str, str]],
    packet: dict[str, Any],
    prefix: str,
) -> None:
    safety = packet.get("safety")

    if not isinstance(safety, dict):
        findings.append(
            _finding(
                "source-safety",
                "high",
                f"{prefix}.safety must be an object.",
                f"{prefix}.safety",
                "Regenerate the source artifact.",
            )
        )
        return

    for field in SAFETY_FALSE_FLAGS:
        if bool(safety.get(field)):
            findings.append(
                _finding(
                    "source-safety",
                    "high",
                    (
                        f"Nested safety flag must remain "
                        f"false: {prefix}.safety.{field}."
                    ),
                    f"{prefix}.safety.{field}",
                    "Block the unsafe source artifact.",
                )
            )


def _build_decision_map(
    decision_input: dict[str, Any],
    proposals: list[dict[str, Any]],
) -> dict[str, dict[str, str]]:
    proposal_ids = {
        _text(item.get("action_id"))
        for item in proposals
        if _text(item.get("action_id"))
    }

    mapping: dict[str, dict[str, str]] = {}

    for item in _object_list(
        decision_input.get("decisions")
    ):
        action_id = _text(item.get("action_id"))

        if (
            not action_id
            or action_id not in proposal_ids
            or action_id in mapping
        ):
            continue

        try:
            decision = _normalize_decision(
                _text(item.get("decision"))
            )
        except ValueError:
            continue

        mapping[action_id] = {
            "decision": decision,
            "reason": _text(item.get("reason")),
        }

    return mapping


def _decision_record(
    proposal: dict[str, Any],
    decision_item: dict[str, str] | None,
    effective: bool,
) -> dict[str, Any]:
    action_id = _text(proposal.get("action_id"))
    decision = (
        decision_item["decision"]
        if decision_item
        else "missing"
    )
    reason = (
        decision_item.get("reason", "")
        if decision_item
        else ""
    )

    effective_approval = (
        effective and decision == "approved"
    )

    blockers = _list_of_text(proposal.get("blocked_by"))

    if effective_approval:
        blockers.extend(
            [
                "approved-action-packet-required",
                "typed-tool-request-manifest-required",
                "execution-gate-required",
            ]
        )

    return {
        "action_id": action_id,
        "hypothesis_id": _text(
            proposal.get("hypothesis_id")
        ),
        "hypothesis_type": _text(
            proposal.get("hypothesis_type")
        ),
        "action_type": _text(
            proposal.get("action_type")
        ),
        "title": _text(proposal.get("title")),
        "purpose": _text(proposal.get("purpose")),
        "manual_order": _int(
            proposal.get("manual_order")
        ),
        "proposed_tool_family": _text(
            proposal.get("proposed_tool_family")
        ),
        "expected_artifact": _text(
            proposal.get("expected_artifact")
        ),
        "decision": decision,
        "decision_reason": reason,
        "effective_approval_granted": (
            effective_approval
        ),
        "command_generated": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "blocked_by": _dedupe(blockers),
    }


def _decision_counts(
    records: list[dict[str, Any]],
) -> dict[str, int]:
    return {
        "approved": sum(
            item.get("decision") == "approved"
            for item in records
        ),
        "rejected": sum(
            item.get("decision") == "rejected"
            for item in records
        ),
        "changes_requested": sum(
            item.get("decision") == "changes-requested"
            for item in records
        ),
        "deferred": sum(
            item.get("decision") == "deferred"
            for item in records
        ),
        "missing": sum(
            item.get("decision") == "missing"
            for item in records
        ),
    }


def _decision_status(
    source_findings: list[dict[str, str]],
    decision_findings: list[dict[str, str]],
    counts: dict[str, int],
) -> str:
    high_source = [
        item
        for item in source_findings
        if item.get("severity") == "high"
    ]
    high_decision = [
        item
        for item in decision_findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category") == "source-safety"
        for item in high_source
    ):
        return "blocked-unsafe-source"

    if any(
        item.get("category") == "source-review"
        for item in high_source
    ):
        return "blocked-review-not-ready"

    if high_source:
        return "blocked-invalid-source"

    invalid_decision_findings = [
        item
        for item in high_decision
        if item.get("category") != "decision-coverage"
    ]

    if invalid_decision_findings:
        return "blocked-invalid-decisions"

    if counts["missing"] > 0:
        return "blocked-incomplete-decisions"

    if high_decision:
        return "blocked-invalid-decisions"

    if counts["changes_requested"] > 0:
        return "changes-requested"

    if counts["approved"] > 0:
        return "ready-for-approved-action-packet"

    if counts["deferred"] > 0:
        return "deferred"

    return "rejected"


def _summary(
    status: str,
    counts: dict[str, int],
) -> str:
    if status == "ready-for-approved-action-packet":
        return (
            f"{counts['approved']} action(s) have effective "
            "human approval for the next local packet stage. "
            "Runtime execution remains disabled."
        )

    if status == "changes-requested":
        return (
            "One or more actions require revision before an "
            "approved-action packet may be built."
        )

    if status == "rejected":
        return (
            "No actions were approved. No downstream action "
            "packet may be built."
        )

    if status == "deferred":
        return (
            "All non-rejected actions remain deferred. "
            "No downstream action packet is ready."
        )

    return (
        "The decision packet is blocked by invalid, unsafe, "
        "incomplete, or non-review-ready inputs."
    )


def _allowed_next_steps(
    status: str,
    counts: dict[str, int],
) -> list[str]:
    if status == "ready-for-approved-action-packet":
        return [
            (
                "Build a local approved-action packet containing "
                f"only the {counts['approved']} effectively "
                "approved action(s)."
            ),
            (
                "Map approved actions into typed planning-only "
                "tool requests."
            ),
            (
                "Submit the typed manifest to the existing "
                "tool execution gate for fail-closed review."
            ),
        ]

    if status == "changes-requested":
        return [
            "Revise the affected action proposals.",
            "Regenerate and review the proposal packet.",
            "Submit a new complete human decision file.",
        ]

    if status == "deferred":
        return [
            "Record a later explicit decision for deferred actions."
        ]

    return []


def _normalize_decision(value: str) -> str:
    normalized = (
        value.strip()
        .lower()
        .replace("_", "-")
        .replace(" ", "-")
    )

    if normalized not in VALID_DECISIONS:
        raise ValueError(
            f"Invalid research action decision: {value!r}"
        )

    return normalized


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
    "EXPECTED_DECISION_INPUT_KIND",
    "EXPECTED_PROPOSAL_KIND",
    "EXPECTED_REVIEW_KIND",
    "VALID_DECISIONS",
    "build_decision_packet_from_files",
    "build_research_action_decision_packet",
    "build_research_action_decision_template",
    "load_json_object",
    "render_research_action_decision_packet_markdown",
    "write_json",
    "write_markdown",
]
