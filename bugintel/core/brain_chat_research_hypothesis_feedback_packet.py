"""Proposed hypothesis feedback derived from reviewed observations.

This module joins:

- the original research hypothesis packet,
- a normalized research observation packet, and
- its successful observation review gate.

It creates deterministic proposals describing how verified observation
impacts could affect hypothesis confidence. It does not mutate the original
hypothesis packet, persistent research state, selection state, investigation
plans, or any runtime system.

No command generation, tool execution, browser activity, Burp activity,
network interaction, target interaction, evidence collection, validation,
report submission, or vulnerability confirmation occurs here.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


EXPECTED_HYPOTHESIS_KIND = (
    "brain_chat_research_hypothesis_packet"
)
EXPECTED_HYPOTHESIS_STATUS = (
    "ready-for-hypothesis-review"
)

EXPECTED_OBSERVATION_KIND = (
    "brain_chat_research_observation_packet"
)
EXPECTED_OBSERVATION_STATUS = (
    "ready-for-observation-review"
)

EXPECTED_REVIEW_KIND = (
    "brain_chat_research_observation_review_gate"
)
EXPECTED_REVIEW_STATUS = (
    "ready-for-hypothesis-feedback-review"
)

READY_STATUS = "ready-for-hypothesis-feedback-review"

CONFIDENCE_LEVELS: tuple[str, ...] = (
    "low",
    "medium",
    "high",
)

INPUT_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "command_generation_allowed",
    "payload_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "hypothesis_mutation_allowed",
    "state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

FEEDBACK_SAFETY: dict[str, bool] = {
    "local_only": True,
    "deterministic": True,
    "planning_only": True,
    "proposal_only": True,
    "observation_review_required": True,
    "human_feedback_review_required": True,
    "confidence_update_review_required": True,
    "research_state_transition_review_required": True,
    "command_generation": False,
    "payload_generation": False,
    "package_installation": False,
    "tool_execution": False,
    "browser_execution": False,
    "curl_execution": False,
    "kali_execution": False,
    "burp_execution": False,
    "provider_execution": False,
    "network_interaction": False,
    "target_interaction": False,
    "evidence_collection": False,
    "validation_execution": False,
    "hypothesis_mutation": False,
    "selection_mutation": False,
    "investigation_plan_mutation": False,
    "state_mutation": False,
    "runtime_execution_allowed": False,
    "report_submission": False,
    "vulnerability_confirmation": False,
}


def load_json_object(
    path: str | Path,
) -> dict[str, Any]:
    """Load one JSON object from disk."""
    source = Path(path)

    with source.open(
        "r",
        encoding="utf-8",
    ) as handle:
        value = json.load(handle)

    if not isinstance(value, dict):
        raise ValueError(
            f"Expected JSON object in {source}"
        )

    return value


def write_json(
    path: str | Path,
    value: dict[str, Any],
) -> None:
    """Write deterministic JSON."""
    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.write_text(
        json.dumps(
            value,
            indent=2,
            sort_keys=True,
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )


def write_markdown(
    path: str | Path,
    value: str,
) -> None:
    """Write Markdown."""
    output = Path(path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )
    output.write_text(
        value,
        encoding="utf-8",
    )


def build_research_hypothesis_feedback_packet(
    hypothesis_packet: Any,
    observation_packet: dict[str, Any],
    observation_review: dict[str, Any],
    source: str = (
        "brain-chat-research-hypothesis-feedback-packet"
    ),
) -> dict[str, Any]:
    """Build deterministic proposed hypothesis feedback."""
    hypotheses_input = _mapping(
        hypothesis_packet
    )
    observations_input = copy.deepcopy(
        observation_packet
        if isinstance(observation_packet, dict)
        else {}
    )
    review_input = copy.deepcopy(
        observation_review
        if isinstance(observation_review, dict)
        else {}
    )

    hypotheses = _object_list(
        hypotheses_input.get("hypotheses")
    )
    expected_impacts = _object_list(
        review_input.get(
            "expected_preliminary_hypothesis_impacts"
        )
    )

    findings: list[dict[str, str]] = []

    findings.extend(
        _review_hypothesis_packet(
            hypotheses_input,
            hypotheses,
        )
    )
    findings.extend(
        _review_observation_packet(
            observations_input
        )
    )
    findings.extend(
        _review_observation_gate(
            observations_input,
            review_input,
        )
    )

    hypothesis_index, index_findings = (
        _index_hypotheses(hypotheses)
    )
    findings.extend(index_findings)

    findings.extend(
        _review_impact_linkage(
            expected_impacts,
            hypothesis_index,
        )
    )

    proposals = _build_feedback_proposals(
        expected_impacts,
        hypothesis_index,
    )

    status = _packet_status(
        findings=findings,
        impact_count=len(expected_impacts),
        proposal_count=len(proposals),
    )
    packet_ready = status == READY_STATUS

    high_findings = [
        item
        for item in findings
        if item.get("severity") == "high"
    ]
    medium_findings = [
        item
        for item in findings
        if item.get("severity") == "medium"
    ]
    low_findings = [
        item
        for item in findings
        if item.get("severity") == "low"
    ]

    categorical_changes = sum(
        bool(
            item.get(
                "categorical_confidence_change"
            )
        )
        for item in proposals
    )
    strengthening = sum(
        _int(item.get("net_confidence_delta"))
        > 0
        for item in proposals
    )
    weakening = sum(
        _int(item.get("net_confidence_delta"))
        < 0
        for item in proposals
    )
    held = sum(
        _int(item.get("net_confidence_delta"))
        == 0
        for item in proposals
    )

    hypothesis_packet_digest = _sha256(
        hypotheses_input
    )
    observation_packet_digest = _optional_text(
        observations_input.get("packet_digest")
    )
    observation_review_digest = _optional_text(
        review_input.get("review_digest")
    )

    feedback_material = {
        "hypothesis_packet_digest": (
            hypothesis_packet_digest
        ),
        "observation_packet_digest": (
            observation_packet_digest
        ),
        "observation_review_digest": (
            observation_review_digest
        ),
        "proposals": proposals,
    }
    feedback_digest = _sha256(
        feedback_material
    )

    target_name = _text(
        hypotheses_input.get("target_name")
        or observations_input.get("target_name")
        or review_input.get("target_name"),
        "unknown-target",
    )

    return {
        "kind": (
            "brain_chat_research_hypothesis_feedback_packet"
        ),
        "source": source,
        "target_name": target_name,
        "packet_status": status,
        "summary": _summary(
            status=status,
            proposal_count=len(proposals),
            categorical_changes=(
                categorical_changes
            ),
        ),
        "packet_ready": packet_ready,
        "hypothesis_feedback_review_ready": (
            packet_ready
        ),
        "confidence_update_ready": False,
        "selection_update_ready": False,
        "investigation_plan_update_ready": False,
        "research_state_transition_ready": False,
        "critic_review_ready": False,
        "replanning_ready": False,
        "source_hypothesis_packet_kind": (
            _optional_text(
                hypotheses_input.get("kind")
            )
        ),
        "source_hypothesis_packet_status": (
            _optional_text(
                hypotheses_input.get(
                    "packet_status"
                )
            )
        ),
        "source_observation_packet_kind": (
            _optional_text(
                observations_input.get("kind")
            )
        ),
        "source_observation_packet_status": (
            _optional_text(
                observations_input.get(
                    "packet_status"
                )
            )
        ),
        "source_observation_review_kind": (
            _optional_text(
                review_input.get("kind")
            )
        ),
        "source_observation_review_status": (
            _optional_text(
                review_input.get(
                    "review_status"
                )
            )
        ),
        "hypothesis_packet_digest": (
            hypothesis_packet_digest
        ),
        "observation_packet_digest": (
            observation_packet_digest
        ),
        "observation_review_digest": (
            observation_review_digest
        ),
        "feedback_proposal_count": len(
            proposals
        ),
        "feedback_proposals": proposals,
        "findings": findings,
        "counts": {
            "source_hypotheses": len(
                hypotheses
            ),
            "verified_hypothesis_impacts": len(
                expected_impacts
            ),
            "feedback_proposals": len(
                proposals
            ),
            "categorical_confidence_changes": (
                categorical_changes
            ),
            "strengthening_proposals": (
                strengthening
            ),
            "weakening_proposals": weakening,
            "hold_proposals": held,
            "findings": len(findings),
            "high_findings": len(
                high_findings
            ),
            "medium_findings": len(
                medium_findings
            ),
            "low_findings": len(
                low_findings
            ),
        },
        "allowed_next_steps": _allowed_next_steps(
            status
        ),
        "rejected_next_steps": [
            (
                "Do not directly replace confidence values in "
                "the source hypothesis packet."
            ),
            (
                "Do not automatically reorder selected "
                "hypotheses."
            ),
            (
                "Do not automatically alter investigation "
                "plans or approved actions."
            ),
            (
                "Do not mutate persistent research state."
            ),
            (
                "Do not generate or execute follow-up commands."
            ),
            (
                "Do not send requests, submit reports, or "
                "confirm vulnerabilities."
            ),
        ],
        "feedback_digest": feedback_digest,
        "command_generation_allowed": False,
        "payload_generation_allowed": False,
        "package_installation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "hypothesis_mutation_allowed": False,
        "selection_mutation_allowed": False,
        "investigation_plan_mutation_allowed": False,
        "state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": dict(FEEDBACK_SAFETY),
    }


def build_feedback_packet_from_files(
    hypothesis_packet_file: str | Path,
    observation_packet_file: str | Path,
    observation_review_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Build feedback from three local JSON files."""
    hypotheses = load_json_object(
        hypothesis_packet_file
    )
    observations = load_json_object(
        observation_packet_file
    )
    review = load_json_object(
        observation_review_file
    )

    packet = (
        build_research_hypothesis_feedback_packet(
            hypotheses,
            observations,
            review,
        )
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_hypothesis_feedback_packet_markdown(
                packet
            ),
        )

    if json_output is not None:
        write_json(
            json_output,
            packet,
        )

    return packet


def render_research_hypothesis_feedback_packet_markdown(
    packet: dict[str, Any],
) -> str:
    """Render the feedback packet as Markdown."""
    counts = packet.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    lines = [
        "# Research Hypothesis Feedback Packet",
        "",
        "## Packet Status",
        "",
        (
            "- target_name: "
            f"`{packet.get('target_name', '')}`"
        ),
        (
            "- packet_status: "
            f"`{packet.get('packet_status', '')}`"
        ),
        (
            "- packet_ready: "
            f"`{_bool_text(packet.get('packet_ready'))}`"
        ),
        (
            "- hypothesis_feedback_review_ready: "
            f"`{_bool_text(packet.get('hypothesis_feedback_review_ready'))}`"
        ),
        (
            "- confidence_update_ready: "
            f"`{_bool_text(packet.get('confidence_update_ready'))}`"
        ),
        (
            "- research_state_transition_ready: "
            f"`{_bool_text(packet.get('research_state_transition_ready'))}`"
        ),
        (
            "- runtime_execution_allowed: "
            f"`{_bool_text(packet.get('runtime_execution_allowed'))}`"
        ),
        (
            "- feedback_digest: "
            f"`{packet.get('feedback_digest', '')}`"
        ),
        f"- summary: {packet.get('summary', '')}",
        "",
        "## Counts",
        "",
        (
            "- source_hypotheses: "
            f"`{counts.get('source_hypotheses', 0)}`"
        ),
        (
            "- verified_hypothesis_impacts: "
            f"`{counts.get('verified_hypothesis_impacts', 0)}`"
        ),
        (
            "- feedback_proposals: "
            f"`{counts.get('feedback_proposals', 0)}`"
        ),
        (
            "- categorical_confidence_changes: "
            f"`{counts.get('categorical_confidence_changes', 0)}`"
        ),
        (
            "- high_findings: "
            f"`{counts.get('high_findings', 0)}`"
        ),
        (
            "- medium_findings: "
            f"`{counts.get('medium_findings', 0)}`"
        ),
        "",
        "## Feedback Proposals",
        "",
        (
            "| Feedback | Hypothesis | Current | Proposed | "
            "Delta | Direction | Disposition | Categorical Change |"
        ),
        (
            "|---|---|---|---|---:|---|---|---|"
        ),
    ]

    for item in _object_list(
        packet.get("feedback_proposals")
    ):
        lines.append(
            "| "
            f"`{item.get('feedback_id', '')}` | "
            f"`{item.get('hypothesis_id', '')}` | "
            f"`{item.get('current_confidence', '')}` | "
            f"`{item.get('proposed_confidence', '')}` | "
            f"{item.get('net_confidence_delta', 0)} | "
            f"`{item.get('evidence_direction', '')}` | "
            f"`{item.get('proposed_disposition', '')}` | "
            f"`{_bool_text(item.get('categorical_confidence_change'))}` |"
        )

        lines.extend(
            [
                "",
                (
                    "### "
                    f"{item.get('feedback_id', '')}: "
                    f"{item.get('hypothesis_id', '')}"
                ),
                "",
                (
                    "- title: "
                    f"{item.get('title', '')}"
                ),
                (
                    "- attack_surface: "
                    f"`{item.get('attack_surface', '')}`"
                ),
                (
                    "- observation_count: "
                    f"`{item.get('observation_count', 0)}`"
                ),
                (
                    "- confidence_mutation_allowed: "
                    f"`{_bool_text(item.get('confidence_mutation_allowed'))}`"
                ),
                (
                    "- state_mutation_allowed: "
                    f"`{_bool_text(item.get('state_mutation_allowed'))}`"
                ),
                (
                    "- proposal_digest: "
                    f"`{item.get('proposal_digest', '')}`"
                ),
                "- observation_ids:",
            ]
        )

        observation_ids = _list_of_text(
            item.get("observation_ids")
        )
        lines.extend(
            [
                f"  - `{value}`"
                for value in observation_ids
            ]
            or ["  - none"]
        )
        lines.append("")

    lines.extend(
        [
            "## Findings",
            "",
        ]
    )
    lines.extend(
        _render_findings(
            packet.get("findings")
        )
    )

    lines.extend(
        [
            "",
            "## Allowed Next Steps",
            "",
        ]
    )
    lines.extend(
        [
            f"- {item}"
            for item in _list_of_text(
                packet.get("allowed_next_steps")
            )
        ]
        or ["- none"]
    )

    lines.extend(
        [
            "",
            "## Rejected Next Steps",
            "",
        ]
    )
    lines.extend(
        [
            f"- {item}"
            for item in _list_of_text(
                packet.get("rejected_next_steps")
            )
        ]
        or ["- none"]
    )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            (
                "- This packet contains proposed confidence "
                "feedback only."
            ),
            "- Hypothesis mutation allowed: `false`",
            "- Selection mutation allowed: `false`",
            "- Research-state mutation allowed: `false`",
            "- Tool execution allowed: `false`",
            "- Runtime execution allowed: `false`",
            "",
        ]
    )

    return "\n".join(lines)


def _review_hypothesis_packet(
    packet: dict[str, Any],
    hypotheses: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if (
        packet.get("kind")
        != EXPECTED_HYPOTHESIS_KIND
    ):
        findings.append(
            _finding(
                category="hypothesis-schema",
                severity="high",
                subject="kind",
                message=(
                    "Unexpected hypothesis packet kind."
                ),
                required_action=(
                    "Provide a research hypothesis packet."
                ),
            )
        )

    if (
        packet.get("packet_status")
        != EXPECTED_HYPOTHESIS_STATUS
    ):
        findings.append(
            _finding(
                category="hypothesis-readiness",
                severity="high",
                subject="packet_status",
                message=(
                    "Hypothesis packet is not ready for "
                    "feedback."
                ),
                required_action=(
                    "Resolve hypothesis packet blockers."
                ),
            )
        )

    declared_count = packet.get(
        "hypothesis_count"
    )

    if (
        not isinstance(declared_count, int)
        or isinstance(declared_count, bool)
        or declared_count != len(hypotheses)
    ):
        findings.append(
            _finding(
                category="hypothesis-schema",
                severity="high",
                subject="hypothesis_count",
                message=(
                    "hypothesis_count does not match "
                    "the hypotheses list."
                ),
                required_action=(
                    "Rebuild the hypothesis packet."
                ),
            )
        )

    if not hypotheses:
        findings.append(
            _finding(
                category="hypothesis-schema",
                severity="high",
                subject="hypotheses",
                message=(
                    "At least one hypothesis is required."
                ),
                required_action=(
                    "Provide a non-empty hypothesis packet."
                ),
            )
        )

    if packet.get("planning_only") is not True:
        findings.append(
            _finding(
                category="hypothesis-safety",
                severity="high",
                subject="planning_only",
                message="planning_only must be true.",
                required_action=(
                    "Restore the planning-only contract."
                ),
            )
        )

    if (
        packet.get("execution_state")
        != "not_executed"
    ):
        findings.append(
            _finding(
                category="hypothesis-safety",
                severity="high",
                subject="execution_state",
                message=(
                    "execution_state must be not_executed."
                ),
                required_action=(
                    "Reject hypotheses claiming execution."
                ),
            )
        )

    return findings


def _review_observation_packet(
    packet: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if (
        packet.get("kind")
        != EXPECTED_OBSERVATION_KIND
    ):
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject="kind",
                message=(
                    "Unexpected observation packet kind."
                ),
                required_action=(
                    "Provide a normalized observation packet."
                ),
            )
        )

    if (
        packet.get("packet_status")
        != EXPECTED_OBSERVATION_STATUS
    ):
        findings.append(
            _finding(
                category="observation-readiness",
                severity="high",
                subject="packet_status",
                message=(
                    "Observation packet is not ready."
                ),
                required_action=(
                    "Resolve observation packet blockers."
                ),
            )
        )

    digest = _optional_text(
        packet.get("packet_digest")
    )

    if not digest or not _is_sha256(digest):
        findings.append(
            _finding(
                category="source-integrity",
                severity="high",
                subject="observation_packet_digest",
                message=(
                    "Observation packet digest is invalid."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )

    for field in INPUT_REQUIRED_FALSE_FLAGS:
        if packet.get(field) is not False:
            findings.append(
                _finding(
                    category="observation-safety",
                    severity="high",
                    subject=field,
                    message=(
                        f"{field} must remain false."
                    ),
                    required_action=(
                        "Restore fail-closed packet flags."
                    ),
                )
            )

    return findings


def _review_observation_gate(
    packet: dict[str, Any],
    review: dict[str, Any],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if review.get("kind") != EXPECTED_REVIEW_KIND:
        findings.append(
            _finding(
                category="review-schema",
                severity="high",
                subject="kind",
                message=(
                    "Unexpected observation review kind."
                ),
                required_action=(
                    "Provide an observation review gate."
                ),
            )
        )

    if (
        review.get("review_status")
        != EXPECTED_REVIEW_STATUS
        or review.get("review_ready") is not True
        or review.get(
            "hypothesis_feedback_packet_ready"
        )
        is not True
    ):
        findings.append(
            _finding(
                category="review-readiness",
                severity="high",
                subject="review_status",
                message=(
                    "Observation review is not ready for "
                    "hypothesis feedback."
                ),
                required_action=(
                    "Resolve all observation review blockers."
                ),
            )
        )

    packet_digest = _optional_text(
        packet.get("packet_digest")
    )
    source_packet_digest = _optional_text(
        review.get("source_packet_digest")
    )

    if (
        not packet_digest
        or source_packet_digest != packet_digest
    ):
        findings.append(
            _finding(
                category="source-integrity",
                severity="high",
                subject="source_packet_digest",
                message=(
                    "Observation review does not reference "
                    "the supplied observation packet."
                ),
                required_action=(
                    "Use the matching reviewed packet."
                ),
            )
        )

    review_digest = _optional_text(
        review.get("review_digest")
    )

    if not review_digest or not _is_sha256(
        review_digest
    ):
        findings.append(
            _finding(
                category="source-integrity",
                severity="high",
                subject="review_digest",
                message=(
                    "Observation review digest is invalid."
                ),
                required_action=(
                    "Rebuild the observation review gate."
                ),
            )
        )
    else:
        material = {
            "source_packet_digest": (
                source_packet_digest
            ),
            "review_status": review.get(
                "review_status"
            ),
            "packet_findings": review.get(
                "packet_findings"
            ),
            "observation_reviews": review.get(
                "observation_reviews"
            ),
            (
                "expected_preliminary_"
                "hypothesis_impacts"
            ): review.get(
                "expected_preliminary_hypothesis_impacts"
            ),
            "impact_findings": review.get(
                "impact_findings"
            ),
        }

        if _sha256(material) != review_digest:
            findings.append(
                _finding(
                    category="source-integrity",
                    severity="high",
                    subject="review_digest",
                    message=(
                        "Observation review digest does not "
                        "match review contents."
                    ),
                    required_action=(
                        "Reject the modified review."
                    ),
                )
            )

    packet_impacts = packet.get(
        "preliminary_hypothesis_impacts"
    )
    review_impacts = review.get(
        "expected_preliminary_hypothesis_impacts"
    )

    if packet_impacts != review_impacts:
        findings.append(
            _finding(
                category="impact-integrity",
                severity="high",
                subject=(
                    "expected_preliminary_hypothesis_impacts"
                ),
                message=(
                    "Reviewed impacts do not match the "
                    "observation packet."
                ),
                required_action=(
                    "Use matching packet and review artifacts."
                ),
            )
        )

    for field in INPUT_REQUIRED_FALSE_FLAGS:
        if review.get(field) is not False:
            findings.append(
                _finding(
                    category="review-safety",
                    severity="high",
                    subject=field,
                    message=(
                        f"{field} must remain false."
                    ),
                    required_action=(
                        "Restore fail-closed review flags."
                    ),
                )
            )

    return findings


def _index_hypotheses(
    hypotheses: list[dict[str, Any]],
) -> tuple[
    dict[str, dict[str, Any]],
    list[dict[str, str]],
]:
    index: dict[str, dict[str, Any]] = {}
    findings: list[dict[str, str]] = []

    for position, hypothesis in enumerate(
        hypotheses,
        start=1,
    ):
        subject = f"hypotheses[{position - 1}]"
        hypothesis_id = _text(
            hypothesis.get("hypothesis_id")
        )

        if not hypothesis_id:
            findings.append(
                _finding(
                    category="hypothesis-schema",
                    severity="high",
                    subject=subject,
                    message=(
                        "hypothesis_id must not be empty."
                    ),
                    required_action=(
                        "Rebuild the hypothesis packet."
                    ),
                )
            )
            continue

        if hypothesis_id in index:
            findings.append(
                _finding(
                    category="hypothesis-schema",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "Duplicate hypothesis ID."
                    ),
                    required_action=(
                        "Use unique hypothesis IDs."
                    ),
                )
            )
            continue

        confidence = _text(
            hypothesis.get("confidence")
        )

        if confidence not in CONFIDENCE_LEVELS:
            findings.append(
                _finding(
                    category="hypothesis-schema",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "Unsupported hypothesis confidence: "
                        f"{confidence!r}."
                    ),
                    required_action=(
                        "Use low, medium, or high."
                    ),
                )
            )

        index[hypothesis_id] = hypothesis

    return index, findings


def _review_impact_linkage(
    impacts: list[dict[str, Any]],
    hypothesis_index: dict[str, dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []
    seen: set[str] = set()

    for position, impact in enumerate(
        impacts,
        start=1,
    ):
        subject = (
            _text(impact.get("hypothesis_id"))
            or f"impacts[{position - 1}]"
        )
        hypothesis_id = _text(
            impact.get("hypothesis_id")
        )

        if not hypothesis_id:
            findings.append(
                _finding(
                    category="impact-schema",
                    severity="high",
                    subject=subject,
                    message=(
                        "Impact hypothesis_id is missing."
                    ),
                    required_action=(
                        "Rebuild the observation review."
                    ),
                )
            )
            continue

        if hypothesis_id in seen:
            findings.append(
                _finding(
                    category="impact-schema",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "Duplicate hypothesis impact."
                    ),
                    required_action=(
                        "Rebuild the observation review."
                    ),
                )
            )

        seen.add(hypothesis_id)

        if hypothesis_id not in hypothesis_index:
            findings.append(
                _finding(
                    category="hypothesis-linkage",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "Reviewed impact references an unknown "
                        "hypothesis."
                    ),
                    required_action=(
                        "Use the original matching hypothesis "
                        "packet."
                    ),
                )
            )

        delta = impact.get(
            "net_confidence_delta"
        )

        if (
            not isinstance(delta, int)
            or isinstance(delta, bool)
        ):
            findings.append(
                _finding(
                    category="impact-schema",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "net_confidence_delta must be an integer."
                    ),
                    required_action=(
                        "Rebuild the observation review."
                    ),
                )
            )
            continue

        expected_direction = _direction(
            delta
        )

        if (
            impact.get("preliminary_direction")
            != expected_direction
        ):
            findings.append(
                _finding(
                    category="impact-consistency",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "Impact direction does not match "
                        "net_confidence_delta."
                    ),
                    required_action=(
                        "Rebuild the observation review."
                    ),
                )
            )

        if (
            impact.get("automatic_update_allowed")
            is not False
        ):
            findings.append(
                _finding(
                    category="impact-safety",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "automatic_update_allowed must remain "
                        "false."
                    ),
                    required_action=(
                        "Restore fail-closed impact flags."
                    ),
                )
            )

        if (
            impact.get("human_review_required")
            is not True
        ):
            findings.append(
                _finding(
                    category="impact-safety",
                    severity="high",
                    subject=hypothesis_id,
                    message=(
                        "human_review_required must be true."
                    ),
                    required_action=(
                        "Restore mandatory human review."
                    ),
                )
            )

    return findings


def _build_feedback_proposals(
    impacts: list[dict[str, Any]],
    hypothesis_index: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    proposals: list[dict[str, Any]] = []

    valid_impacts = [
        impact
        for impact in impacts
        if (
            _text(impact.get("hypothesis_id"))
            in hypothesis_index
            and isinstance(
                impact.get(
                    "net_confidence_delta"
                ),
                int,
            )
            and not isinstance(
                impact.get(
                    "net_confidence_delta"
                ),
                bool,
            )
        )
    ]

    valid_impacts.sort(
        key=lambda item: _text(
            item.get("hypothesis_id")
        )
    )

    for position, impact in enumerate(
        valid_impacts,
        start=1,
    ):
        hypothesis_id = _text(
            impact.get("hypothesis_id")
        )
        hypothesis = hypothesis_index[
            hypothesis_id
        ]
        current_confidence = _text(
            hypothesis.get("confidence"),
            "low",
        )
        delta = _int(
            impact.get("net_confidence_delta")
        )
        proposed_confidence = (
            _proposed_confidence(
                current_confidence,
                delta,
            )
        )

        proposal = {
            "feedback_id": f"HFB-{position:03d}",
            "hypothesis_id": hypothesis_id,
            "title": _text(
                hypothesis.get("title"),
                "Untitled hypothesis",
            ),
            "attack_surface": _text(
                hypothesis.get("attack_surface"),
                "unknown attack surface",
            ),
            "hypothesis_type": _text(
                hypothesis.get("hypothesis_type"),
                "unknown",
            ),
            "current_priority": _text(
                hypothesis.get("priority"),
                "low",
            ),
            "current_confidence": (
                current_confidence
            ),
            "proposed_confidence": (
                proposed_confidence
            ),
            "categorical_confidence_change": (
                proposed_confidence
                != current_confidence
            ),
            "net_confidence_delta": delta,
            "evidence_direction": _direction(
                delta
            ),
            "proposed_disposition": (
                _disposition(
                    current_confidence,
                    proposed_confidence,
                    delta,
                )
            ),
            "observation_count": _int(
                impact.get("observation_count")
            ),
            "observation_ids": (
                _list_of_text(
                    impact.get("observation_ids")
                )
            ),
            "automatic_update_allowed": False,
            "confidence_mutation_allowed": False,
            "selection_mutation_allowed": False,
            "investigation_plan_mutation_allowed": False,
            "state_mutation_allowed": False,
            "human_review_required": True,
            "required_review": (
                "human-hypothesis-feedback-review"
            ),
            "planning_only": True,
            "execution_allowed": False,
            "runtime_execution_allowed": False,
        }

        proposal["proposal_digest"] = _sha256(
            proposal
        )
        proposals.append(proposal)

    return proposals


def _proposed_confidence(
    current: str,
    delta: int,
) -> str:
    if current not in CONFIDENCE_LEVELS:
        return current

    index = CONFIDENCE_LEVELS.index(current)

    if delta >= 3:
        index = min(
            index + 1,
            len(CONFIDENCE_LEVELS) - 1,
        )
    elif delta <= -3:
        index = max(index - 1, 0)

    return CONFIDENCE_LEVELS[index]


def _disposition(
    current: str,
    proposed: str,
    delta: int,
) -> str:
    if proposed != current:
        if delta > 0:
            return "propose-confidence-promotion"
        return "propose-confidence-demotion"

    if delta > 0:
        return (
            "retain-confidence-with-positive-trend"
        )

    if delta < 0:
        return (
            "retain-confidence-with-negative-trend"
        )

    return "retain-confidence"


def _direction(delta: int) -> str:
    if delta >= 3:
        return "strengthen"
    if delta > 0:
        return "slightly-strengthen"
    if delta <= -3:
        return "weaken"
    if delta < 0:
        return "slightly-weaken"
    return "hold"


def _packet_status(
    findings: list[dict[str, str]],
    impact_count: int,
    proposal_count: int,
) -> str:
    high = [
        item
        for item in findings
        if item.get("severity") == "high"
    ]

    high_categories = {
        item.get("category")
        for item in high
    }

    # Readiness failures are primary. Modifying a readiness
    # field can also invalidate an artifact digest, but the
    # useful primary status remains the readiness failure.
    if "hypothesis-readiness" in high_categories:
        return "blocked-hypothesis-packet-not-ready"

    if "observation-readiness" in high_categories:
        return "blocked-observation-packet-not-ready"

    if "review-readiness" in high_categories:
        return "blocked-observation-review-not-ready"

    # Explicit authority or execution claims remain the
    # strongest safety failure after readiness classification.
    if high_categories.intersection(
        {
            "hypothesis-safety",
            "observation-safety",
            "review-safety",
            "impact-safety",
        }
    ):
        return "blocked-unsafe-feedback-input"

    # Direct source and cross-artifact integrity failures.
    if high_categories.intersection(
        {
            "source-integrity",
            "impact-integrity",
        }
    ):
        return "blocked-feedback-integrity-failure"

    # Structural defects take precedence over derivative
    # unknown-hypothesis findings. An empty or malformed
    # hypothesis index naturally makes linked impacts unknown.
    if high_categories.intersection(
        {
            "hypothesis-schema",
            "observation-schema",
            "review-schema",
            "impact-schema",
            "impact-consistency",
        }
    ):
        return "blocked-invalid-feedback-input"

    # This status is reserved for a valid hypothesis packet
    # whose reviewed impacts reference an absent hypothesis.
    if "hypothesis-linkage" in high_categories:
        return "blocked-unknown-hypothesis"

    if high:
        return "blocked-invalid-feedback-input"

    if impact_count == 0:
        return "review-needed-no-hypothesis-impacts"

    if proposal_count != impact_count:
        return "review-needed-feedback-gaps"

    if any(
        item.get("severity") == "medium"
        for item in findings
    ):
        return "review-needed-feedback-gaps"

    return READY_STATUS

def _summary(
    status: str,
    proposal_count: int,
    categorical_changes: int,
) -> str:
    if status == READY_STATUS:
        return (
            f"{proposal_count} reviewed hypothesis feedback "
            f"proposal(s) were created; "
            f"{categorical_changes} propose a categorical "
            "confidence change. No hypothesis was mutated."
        )

    return (
        f"{proposal_count} hypothesis feedback proposal(s) "
        f"were created, but feedback review is not ready: "
        f"{status}."
    )


def _allowed_next_steps(
    status: str,
) -> list[str]:
    if status != READY_STATUS:
        return []

    return [
        (
            "Review each proposed confidence disposition "
            "against the linked observations."
        ),
        (
            "Approve, reject, defer, or request changes for "
            "each feedback proposal in a later human-review "
            "artifact."
        ),
        (
            "Preserve hypothesis, observation, review, proposal, "
            "and packet digests downstream."
        ),
        (
            "Keep confidence and persistent research-state "
            "mutation disabled until a dedicated transition "
            "gate approves it."
        ),
    ]


def _mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, dict):
        return copy.deepcopy(value)

    to_dict = getattr(value, "to_dict", None)

    if callable(to_dict):
        result = to_dict()

        if isinstance(result, dict):
            return copy.deepcopy(result)

    return {}


def _finding(
    category: str,
    severity: str,
    subject: str,
    message: str,
    required_action: str,
) -> dict[str, str]:
    return {
        "category": category,
        "severity": severity,
        "subject": subject,
        "message": message,
        "required_action": required_action,
    }


def _render_findings(
    value: Any,
) -> list[str]:
    findings = (
        value
        if isinstance(value, list)
        else []
    )
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
            "Required action: "
            f"{finding.get('required_action', '')}"
        )

    return lines or ["- none"]


def _object_list(
    value: Any,
) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [
        item
        for item in value
        if isinstance(item, dict)
    ]


def _list_of_text(
    value: Any,
) -> list[str]:
    if value is None:
        return []

    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []

    if not isinstance(
        value,
        (list, tuple, set),
    ):
        return []

    result: list[str] = []

    for item in value:
        text = _text(item)

        if text and text not in result:
            result.append(text)

    return result


def _optional_text(
    value: Any,
) -> str | None:
    text = _text(value)
    return text if text else None


def _text(
    value: Any,
    default: str = "",
) -> str:
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


def _is_sha256(value: str) -> bool:
    return bool(
        re.fullmatch(
            r"[0-9a-f]{64}",
            value,
        )
    )


def _sha256(value: Any) -> str:
    encoded = json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")

    return hashlib.sha256(encoded).hexdigest()


def _bool_text(value: Any) -> str:
    return str(bool(value)).lower()


__all__ = [
    "CONFIDENCE_LEVELS",
    "EXPECTED_HYPOTHESIS_KIND",
    "EXPECTED_HYPOTHESIS_STATUS",
    "EXPECTED_OBSERVATION_KIND",
    "EXPECTED_OBSERVATION_STATUS",
    "EXPECTED_REVIEW_KIND",
    "EXPECTED_REVIEW_STATUS",
    "FEEDBACK_SAFETY",
    "INPUT_REQUIRED_FALSE_FLAGS",
    "READY_STATUS",
    "build_feedback_packet_from_files",
    "build_research_hypothesis_feedback_packet",
    "load_json_object",
    "render_research_hypothesis_feedback_packet_markdown",
    "write_json",
    "write_markdown",
]
