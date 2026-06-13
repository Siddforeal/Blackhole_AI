"""Fail-closed review gate for research observation packets.

This module independently verifies an imported research observation packet
before its preliminary hypothesis effects may be used by a later feedback or
research-state transition stage.

It verifies packet and observation digests, deterministic observation
identities, source linkage, outcome and evidence-strength semantics,
redaction, authorization, controlled assets, human review, preliminary
confidence calculations, aggregate hypothesis impacts, and fail-closed safety
flags.

It does not execute commands, launch browsers, use Burp Suite, run Kali tools,
send requests, interact with targets, collect evidence, validate findings,
change hypothesis confidence, mutate research state, submit reports, or
confirm vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_research_observation_packet import (
    KNOWN_CONTROLLED_ASSET_STATUSES,
    KNOWN_EVIDENCE_STRENGTHS,
    KNOWN_OUTCOMES,
    KNOWN_REDACTION_STATUSES,
    KNOWN_SCOPE_STATUSES,
    KNOWN_SOURCE_TYPES,
    LIVE_OBSERVATION_SOURCE_TYPES,
)


EXPECTED_KIND = "brain_chat_research_observation_packet"
EXPECTED_STATUS = "ready-for-observation-review"
READY_STATUS = "ready-for-hypothesis-feedback-review"

PACKET_REQUIRED_TRUE_FLAGS: tuple[str, ...] = (
    "packet_ready",
    "observation_review_ready",
    "hypothesis_feedback_review_ready",
    "planning_only",
)

PACKET_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "research_state_transition_ready",
    "critic_review_ready",
    "replanning_ready",
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

OBSERVATION_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "hypothesis_mutation_allowed",
    "state_mutation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
)

SAFETY_REQUIRED_TRUE_FLAGS: tuple[str, ...] = (
    "local_only",
    "deterministic",
    "planning_only",
    "import_only",
    "normalization_only",
    "observation_review_required",
    "hypothesis_update_review_required",
    "research_state_transition_review_required",
)

SAFETY_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "command_generation",
    "payload_generation",
    "package_installation",
    "tool_execution",
    "browser_execution",
    "curl_execution",
    "kali_execution",
    "burp_execution",
    "provider_execution",
    "network_interaction",
    "target_interaction",
    "evidence_collection",
    "validation_execution",
    "hypothesis_mutation",
    "state_mutation",
    "runtime_execution_allowed",
    "report_submission",
    "vulnerability_confirmation",
)

INTEGRITY_CATEGORIES: frozenset[str] = frozenset(
    {
        "packet-integrity",
        "observation-integrity",
        "impact-integrity",
        "source-integrity",
    }
)

UNSAFE_CATEGORIES: frozenset[str] = frozenset(
    {
        "packet-safety",
        "observation-safety",
        "sensitive-data",
    }
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
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8")


def build_research_observation_review_gate(
    observation_packet: dict[str, Any],
    source: str = (
        "brain-chat-research-observation-review-gate"
    ),
) -> dict[str, Any]:
    """Independently review one observation packet."""
    packet = copy.deepcopy(
        observation_packet
        if isinstance(observation_packet, dict)
        else {}
    )

    observations = _object_list(
        packet.get("observations")
    )

    packet_findings = _review_packet(
        packet,
        observations,
    )

    observation_reviews: list[dict[str, Any]] = []
    observation_findings: list[dict[str, str]] = []

    seen_observation_ids: set[str] = set()

    for index, observation in enumerate(
        observations,
        start=1,
    ):
        review = _review_observation(
            observation,
            index=index,
            packet=packet,
            seen_observation_ids=seen_observation_ids,
        )
        observation_reviews.append(review)
        observation_findings.extend(
            review["findings"]
        )

    expected_impacts = _expected_impacts(
        observations
    )
    impact_findings = _review_impacts(
        packet.get(
            "preliminary_hypothesis_impacts"
        ),
        expected_impacts,
    )

    review_status = _review_status(
        observation_count=len(observations),
        packet_findings=packet_findings,
        observation_findings=(
            observation_findings
        ),
        impact_findings=impact_findings,
    )

    review_ready = review_status == READY_STATUS

    all_findings = (
        packet_findings
        + observation_findings
        + impact_findings
    )

    high_findings = [
        item
        for item in all_findings
        if item.get("severity") == "high"
    ]
    medium_findings = [
        item
        for item in all_findings
        if item.get("severity") == "medium"
    ]
    low_findings = [
        item
        for item in all_findings
        if item.get("severity") == "low"
    ]

    ready_observations = sum(
        bool(item.get("review_ready"))
        for item in observation_reviews
    )
    blocked_observations = sum(
        item.get("review_status", "").startswith(
            "blocked-"
        )
        for item in observation_reviews
    )
    review_needed_observations = sum(
        item.get("review_status")
        == "review-needed-observation-gaps"
        for item in observation_reviews
    )

    review_material = {
        "source_packet_digest": _optional_text(
            packet.get("packet_digest")
        ),
        "review_status": review_status,
        "packet_findings": packet_findings,
        "observation_reviews": (
            observation_reviews
        ),
        "expected_preliminary_hypothesis_impacts": (
            expected_impacts
        ),
        "impact_findings": impact_findings,
    }

    review_digest = _sha256(review_material)

    return {
        "kind": (
            "brain_chat_research_observation_review_gate"
        ),
        "source": source,
        "target_name": _text(
            packet.get("target_name"),
            "unknown-target",
        ),
        "focus_endpoint": _optional_text(
            packet.get("focus_endpoint")
        ),
        "source_packet_kind": _optional_text(
            packet.get("kind")
        ),
        "source_packet_status": _optional_text(
            packet.get("packet_status")
        ),
        "source_packet_digest": _optional_text(
            packet.get("packet_digest")
        ),
        "source_manifest_digest": _optional_text(
            packet.get("source_manifest_digest")
        ),
        "source_review_digest": _optional_text(
            packet.get("source_review_digest")
        ),
        "review_status": review_status,
        "summary": _summary(
            review_status,
            observation_count=len(observations),
            ready_observations=ready_observations,
        ),
        "review_ready": review_ready,
        "hypothesis_feedback_packet_ready": (
            review_ready
        ),
        "research_state_transition_ready": False,
        "critic_review_ready": False,
        "replanning_ready": False,
        "observation_count": len(observations),
        "observation_reviews": observation_reviews,
        "expected_preliminary_hypothesis_impacts": (
            expected_impacts
        ),
        "packet_findings": packet_findings,
        "observation_findings": (
            observation_findings
        ),
        "impact_findings": impact_findings,
        "counts": {
            "observations": len(observations),
            "ready_observations": ready_observations,
            "blocked_observations": (
                blocked_observations
            ),
            "review_needed_observations": (
                review_needed_observations
            ),
            "expected_hypothesis_impacts": len(
                expected_impacts
            ),
            "packet_findings": len(
                packet_findings
            ),
            "observation_findings": len(
                observation_findings
            ),
            "impact_findings": len(
                impact_findings
            ),
            "findings": len(all_findings),
            "high_findings": len(high_findings),
            "medium_findings": len(
                medium_findings
            ),
            "low_findings": len(low_findings),
        },
        "allowed_next_steps": _allowed_next_steps(
            review_status
        ),
        "rejected_next_steps": [
            "Do not automatically mutate hypothesis confidence.",
            "Do not automatically mutate persistent research state.",
            "Do not generate or execute follow-up commands.",
            "Do not send network requests or interact with targets.",
            "Do not collect additional evidence from this review gate.",
            "Do not submit reports or confirm vulnerabilities.",
        ],
        "review_digest": review_digest,
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
        "state_mutation_allowed": False,
        "report_submission_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "planning_only": True,
        "execution_state": "not_executed",
        "safety": {
            "local_only": True,
            "deterministic": True,
            "planning_only": True,
            "review_only": True,
            "packet_integrity_verified": (
                not any(
                    item.get("category")
                    == "packet-integrity"
                    for item in packet_findings
                )
            ),
            "observation_integrity_verified": (
                not any(
                    item.get("category")
                    == "observation-integrity"
                    for item in observation_findings
                )
            ),
            "hypothesis_feedback_review_required": True,
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
            "state_mutation": False,
            "runtime_execution_allowed": False,
            "report_submission": False,
            "vulnerability_confirmation": False,
        },
    }


def build_review_gate_from_file(
    observation_packet_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Build a review gate from a local JSON packet."""
    packet = load_json_object(
        observation_packet_file
    )
    review = build_research_observation_review_gate(
        packet
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_observation_review_gate_markdown(
                review
            ),
        )

    if json_output is not None:
        write_json(json_output, review)

    return review


def render_research_observation_review_gate_markdown(
    review: dict[str, Any],
) -> str:
    """Render the review gate as Markdown."""
    counts = review.get("counts")
    if not isinstance(counts, dict):
        counts = {}

    lines = [
        "# Research Observation Review Gate",
        "",
        "## Review Status",
        "",
        (
            "- target_name: "
            f"`{review.get('target_name', '')}`"
        ),
        (
            "- focus_endpoint: "
            f"`{review.get('focus_endpoint') or 'none'}`"
        ),
        (
            "- source_packet_status: "
            f"`{review.get('source_packet_status') or 'unknown'}`"
        ),
        (
            "- review_status: "
            f"`{review.get('review_status', '')}`"
        ),
        (
            "- review_ready: "
            f"`{_bool_text(review.get('review_ready'))}`"
        ),
        (
            "- hypothesis_feedback_packet_ready: "
            f"`{_bool_text(review.get('hypothesis_feedback_packet_ready'))}`"
        ),
        (
            "- research_state_transition_ready: "
            f"`{_bool_text(review.get('research_state_transition_ready'))}`"
        ),
        (
            "- runtime_execution_allowed: "
            f"`{_bool_text(review.get('runtime_execution_allowed'))}`"
        ),
        (
            "- source_packet_digest: "
            f"`{review.get('source_packet_digest') or 'none'}`"
        ),
        (
            "- review_digest: "
            f"`{review.get('review_digest') or 'none'}`"
        ),
        f"- summary: {review.get('summary', '')}",
        "",
        "## Counts",
        "",
        (
            f"- observations: "
            f"`{counts.get('observations', 0)}`"
        ),
        (
            f"- ready_observations: "
            f"`{counts.get('ready_observations', 0)}`"
        ),
        (
            f"- blocked_observations: "
            f"`{counts.get('blocked_observations', 0)}`"
        ),
        (
            "- review_needed_observations: "
            f"`{counts.get('review_needed_observations', 0)}`"
        ),
        (
            f"- high_findings: "
            f"`{counts.get('high_findings', 0)}`"
        ),
        (
            f"- medium_findings: "
            f"`{counts.get('medium_findings', 0)}`"
        ),
        (
            f"- low_findings: "
            f"`{counts.get('low_findings', 0)}`"
        ),
        "",
        "## Observation Reviews",
        "",
        (
            "| Observation | Request | Action | Hypothesis | "
            "Outcome | Strength | Delta | Status | Ready | Findings |"
        ),
        (
            "|---|---|---|---|---|---|---:|---|---|---:|"
        ),
    ]

    for item in _object_list(
        review.get("observation_reviews")
    ):
        lines.append(
            "| "
            f"`{item.get('observation_id', '')}` | "
            f"`{item.get('request_id') or 'none'}` | "
            f"`{item.get('action_id') or 'none'}` | "
            f"`{item.get('hypothesis_id') or 'none'}` | "
            f"`{item.get('outcome') or 'unknown'}` | "
            f"`{item.get('evidence_strength') or 'unknown'}` | "
            f"{item.get('expected_confidence_delta', 0)} | "
            f"`{item.get('review_status') or 'unknown'}` | "
            f"`{_bool_text(item.get('review_ready'))}` | "
            f"{item.get('finding_count', 0)} |"
        )

    lines.extend(
        [
            "",
            "## Expected Preliminary Hypothesis Impacts",
            "",
            (
                "| Hypothesis | Observations | Net Delta | "
                "Direction |"
            ),
            "|---|---:|---:|---|",
        ]
    )

    for item in _object_list(
        review.get(
            "expected_preliminary_hypothesis_impacts"
        )
    ):
        lines.append(
            "| "
            f"`{item.get('hypothesis_id', '')}` | "
            f"{item.get('observation_count', 0)} | "
            f"{item.get('net_confidence_delta', 0)} | "
            f"`{item.get('preliminary_direction', '')}` |"
        )

    finding_sections = (
        (
            "Packet Findings",
            review.get("packet_findings"),
        ),
        (
            "Observation Findings",
            review.get("observation_findings"),
        ),
        (
            "Impact Findings",
            review.get("impact_findings"),
        ),
    )

    for heading, findings in finding_sections:
        lines.extend(["", f"## {heading}", ""])
        lines.extend(_render_findings(findings))

    lines.extend(["", "## Allowed Next Steps", ""])
    lines.extend(
        [
            f"- {item}"
            for item in _list_of_text(
                review.get("allowed_next_steps")
            )
        ]
        or ["- none"]
    )

    lines.extend(["", "## Rejected Next Steps", ""])
    lines.extend(
        [
            f"- {item}"
            for item in _list_of_text(
                review.get("rejected_next_steps")
            )
        ]
        or ["- none"]
    )

    lines.extend(
        [
            "",
            "## Safety",
            "",
            "- This gate performs local integrity and consistency review only.",
            "- Hypothesis mutation allowed: `false`",
            "- Research-state mutation allowed: `false`",
            "- Command generation allowed: `false`",
            "- Tool execution allowed: `false`",
            "- Network interaction allowed: `false`",
            "- Runtime execution allowed: `false`",
            "",
        ]
    )

    return "\n".join(lines)


def _review_packet(
    packet: dict[str, Any],
    observations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if packet.get("kind") != EXPECTED_KIND:
        findings.append(
            _finding(
                category="packet-schema",
                severity="high",
                subject="kind",
                message=(
                    f"Expected packet kind {EXPECTED_KIND!r}."
                ),
                required_action=(
                    "Provide a research observation packet."
                ),
            )
        )

    if packet.get("packet_status") != EXPECTED_STATUS:
        findings.append(
            _finding(
                category="packet-readiness",
                severity="medium",
                subject="packet_status",
                message=(
                    "Observation packet is not ready for review: "
                    f"{packet.get('packet_status')!r}."
                ),
                required_action=(
                    "Resolve observation packet blockers first."
                ),
            )
        )

    for field in PACKET_REQUIRED_TRUE_FLAGS:
        if packet.get(field) is not True:
            findings.append(
                _finding(
                    category="packet-readiness",
                    severity="medium",
                    subject=field,
                    message=f"{field} must be true.",
                    required_action=(
                        "Rebuild a ready observation packet."
                    ),
                )
            )

    for field in PACKET_REQUIRED_FALSE_FLAGS:
        if packet.get(field) is not False:
            findings.append(
                _finding(
                    category="packet-safety",
                    severity="high",
                    subject=field,
                    message=f"{field} must remain false.",
                    required_action=(
                        "Remove unsafe authority from the packet."
                    ),
                )
            )

    if packet.get("execution_state") != "not_executed":
        findings.append(
            _finding(
                category="packet-safety",
                severity="high",
                subject="execution_state",
                message=(
                    "execution_state must be not_executed."
                ),
                required_action=(
                    "Reject packets claiming runtime execution."
                ),
            )
        )

    declared_count = packet.get(
        "observation_count"
    )

    if (
        not isinstance(declared_count, int)
        or isinstance(declared_count, bool)
        or declared_count != len(observations)
    ):
        findings.append(
            _finding(
                category="packet-schema",
                severity="high",
                subject="observation_count",
                message=(
                    "observation_count does not match the "
                    "observation list."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )

    if not observations:
        findings.append(
            _finding(
                category="packet-schema",
                severity="high",
                subject="observations",
                message=(
                    "Observation review requires at least one "
                    "observation."
                ),
                required_action=(
                    "Provide a non-empty observation packet."
                ),
            )
        )

    for field in (
        "source_manifest_digest",
        "source_review_digest",
    ):
        value = _optional_text(packet.get(field))

        if value and not _is_sha256(value):
            findings.append(
                _finding(
                    category="source-integrity",
                    severity="high",
                    subject=field,
                    message=(
                        f"{field} is not a lowercase SHA-256 digest."
                    ),
                    required_action=(
                        "Provide the exact upstream digest."
                    ),
                )
            )

    packet_digest = _optional_text(
        packet.get("packet_digest")
    )

    if not packet_digest or not _is_sha256(
        packet_digest
    ):
        findings.append(
            _finding(
                category="packet-integrity",
                severity="high",
                subject="packet_digest",
                message=(
                    "packet_digest must be a lowercase SHA-256 "
                    "digest."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )
    else:
        digest_material = {
            "target_name": _text(
                packet.get("target_name"),
                "unknown-target",
            ),
            "focus_endpoint": _optional_text(
                packet.get("focus_endpoint")
            ),
            "source_manifest_digest": _optional_text(
                packet.get("source_manifest_digest")
            ),
            "source_review_digest": _optional_text(
                packet.get("source_review_digest")
            ),
            "observations": observations,
        }
        expected_digest = _sha256(
            digest_material
        )

        if packet_digest != expected_digest:
            findings.append(
                _finding(
                    category="packet-integrity",
                    severity="high",
                    subject="packet_digest",
                    message=(
                        "packet_digest does not match packet "
                        "contents."
                    ),
                    required_action=(
                        "Reject the modified packet and rebuild it."
                    ),
                )
            )

    safety = packet.get("safety")

    if not isinstance(safety, dict):
        findings.append(
            _finding(
                category="packet-safety",
                severity="high",
                subject="safety",
                message="safety must be an object.",
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )
    else:
        for field in SAFETY_REQUIRED_TRUE_FLAGS:
            if safety.get(field) is not True:
                findings.append(
                    _finding(
                        category="packet-safety",
                        severity="high",
                        subject=f"safety.{field}",
                        message=(
                            f"safety.{field} must be true."
                        ),
                        required_action=(
                            "Restore the fail-closed safety contract."
                        ),
                    )
                )

        for field in SAFETY_REQUIRED_FALSE_FLAGS:
            if safety.get(field) is not False:
                findings.append(
                    _finding(
                        category="packet-safety",
                        severity="high",
                        subject=f"safety.{field}",
                        message=(
                            f"safety.{field} must remain false."
                        ),
                        required_action=(
                            "Restore the fail-closed safety contract."
                        ),
                    )
                )

    expected_linked_request_ids = sorted(
        {
            _text(item.get("request_id"))
            for item in observations
            if _text(item.get("request_id"))
        }
    )
    expected_linked_action_ids = sorted(
        {
            _text(item.get("action_id"))
            for item in observations
            if _text(item.get("action_id"))
        }
    )
    expected_linked_hypothesis_ids = sorted(
        {
            _text(item.get("hypothesis_id"))
            for item in observations
            if _text(item.get("hypothesis_id"))
        }
    )

    linkage_expectations = (
        (
            "linked_request_ids",
            expected_linked_request_ids,
        ),
        (
            "linked_action_ids",
            expected_linked_action_ids,
        ),
        (
            "linked_hypothesis_ids",
            expected_linked_hypothesis_ids,
        ),
    )

    for field, expected in linkage_expectations:
        actual = _list_of_text(packet.get(field))

        if actual != expected:
            findings.append(
                _finding(
                    category="packet-consistency",
                    severity="high",
                    subject=field,
                    message=(
                        f"{field} does not match observation "
                        "linkage."
                    ),
                    required_action=(
                        "Rebuild the observation packet."
                    ),
                )
            )

    count_expectations = (
        (
            "outcome_counts",
            _count_by(observations, "outcome"),
        ),
        (
            "source_type_counts",
            _count_by(observations, "source_type"),
        ),
        (
            "evidence_strength_counts",
            _count_by(
                observations,
                "evidence_strength",
            ),
        ),
        (
            "redaction_status_counts",
            _count_by(
                observations,
                "redaction_status",
            ),
        ),
        (
            "scope_status_counts",
            _count_by(
                observations,
                "scope_status",
            ),
        ),
    )

    for field, expected in count_expectations:
        actual = packet.get(field)

        if actual != expected:
            findings.append(
                _finding(
                    category="packet-consistency",
                    severity="high",
                    subject=field,
                    message=(
                        f"{field} does not match observations."
                    ),
                    required_action=(
                        "Rebuild the observation packet."
                    ),
                )
            )

    return findings


def _review_observation(
    observation: dict[str, Any],
    index: int,
    packet: dict[str, Any],
    seen_observation_ids: set[str],
) -> dict[str, Any]:
    expected_id = f"OBS-{index:03d}"
    observation_id = _text(
        observation.get("observation_id")
    )
    subject = observation_id or expected_id
    findings: list[dict[str, str]] = []

    if observation_id != expected_id:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    f"Expected deterministic ID {expected_id}; "
                    f"received {observation_id!r}."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )

    if observation_id in seen_observation_ids:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message="Duplicate observation ID.",
                required_action=(
                    "Assign unique deterministic observation IDs."
                ),
            )
        )

    if observation_id:
        seen_observation_ids.add(observation_id)

    request_id = _optional_text(
        observation.get("request_id")
    )
    action_id = _optional_text(
        observation.get("action_id")
    )
    hypothesis_id = _optional_text(
        observation.get("hypothesis_id")
    )

    if not any(
        (request_id, action_id, hypothesis_id)
    ):
        findings.append(
            _finding(
                category="observation-linkage",
                severity="medium",
                subject=subject,
                message=(
                    "Observation is not linked to a request, "
                    "action, or hypothesis."
                ),
                required_action=(
                    "Add valid source linkage before feedback."
                ),
            )
        )

    source_type = _text(
        observation.get("source_type")
    )

    if source_type not in KNOWN_SOURCE_TYPES:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    f"Unsupported source_type: {source_type!r}."
                ),
                required_action=(
                    "Use a supported source type."
                ),
            )
        )

    outcome = _text(
        observation.get("outcome")
    )

    if outcome not in KNOWN_OUTCOMES:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    f"Unsupported outcome: {outcome!r}."
                ),
                required_action=(
                    "Use a supported observation outcome."
                ),
            )
        )

    evidence_strength = _text(
        observation.get("evidence_strength")
    )

    if (
        evidence_strength
        not in KNOWN_EVIDENCE_STRENGTHS
    ):
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    "Unsupported evidence_strength: "
                    f"{evidence_strength!r}."
                ),
                required_action=(
                    "Use none, weak, moderate, or strong."
                ),
            )
        )

    if not _text(observation.get("summary")):
        findings.append(
            _finding(
                category="observation-quality",
                severity="high",
                subject=subject,
                message="Observation summary is empty.",
                required_action=(
                    "Add a concise factual summary."
                ),
            )
        )

    for field in (
        "details",
        "artifact_refs",
        "signals",
        "errors",
    ):
        value = observation.get(field)

        if not isinstance(value, list) or any(
            not isinstance(item, str)
            for item in value
        ):
            findings.append(
                _finding(
                    category="observation-schema",
                    severity="high",
                    subject=subject,
                    message=(
                        f"{field} must be a list of strings."
                    ),
                    required_action=(
                        "Rebuild the normalized observation."
                    ),
                )
            )

    redaction_status = _text(
        observation.get("redaction_status")
    )

    if (
        redaction_status
        not in KNOWN_REDACTION_STATUSES
    ):
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    "Unsupported redaction_status: "
                    f"{redaction_status!r}."
                ),
                required_action=(
                    "Use a supported redaction status."
                ),
            )
        )
    elif redaction_status not in {
        "reviewed",
        "not-required",
    }:
        findings.append(
            _finding(
                category="observation-redaction",
                severity="high",
                subject=subject,
                message=(
                    "Observation redaction review is incomplete."
                ),
                required_action=(
                    "Complete redaction review."
                ),
            )
        )

    scope_status = _text(
        observation.get("scope_status")
    )

    if scope_status not in KNOWN_SCOPE_STATUSES:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    f"Unsupported scope_status: "
                    f"{scope_status!r}."
                ),
                required_action=(
                    "Use a supported scope status."
                ),
            )
        )
    elif (
        source_type in LIVE_OBSERVATION_SOURCE_TYPES
        and scope_status != "confirmed"
    ):
        findings.append(
            _finding(
                category="observation-scope",
                severity="high",
                subject=subject,
                message=(
                    "Live-derived observations require confirmed "
                    "scope."
                ),
                required_action=(
                    "Verify target authorization and scope."
                ),
            )
        )
    elif scope_status not in {
        "confirmed",
        "not-applicable",
    }:
        findings.append(
            _finding(
                category="observation-scope",
                severity="medium",
                subject=subject,
                message=(
                    "Observation scope status requires review."
                ),
                required_action=(
                    "Confirm scope or mark it not applicable."
                ),
            )
        )

    controlled_assets_status = _text(
        observation.get(
            "controlled_assets_status"
        )
    )

    if (
        controlled_assets_status
        not in KNOWN_CONTROLLED_ASSET_STATUSES
    ):
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    "Unsupported controlled_assets_status: "
                    f"{controlled_assets_status!r}."
                ),
                required_action=(
                    "Use a supported controlled-assets status."
                ),
            )
        )
    elif (
        source_type in LIVE_OBSERVATION_SOURCE_TYPES
        and controlled_assets_status
        not in {"confirmed", "not-required"}
    ):
        findings.append(
            _finding(
                category="controlled-assets",
                severity="high",
                subject=subject,
                message=(
                    "Live-derived observations require controlled "
                    "asset confirmation."
                ),
                required_action=(
                    "Confirm all accounts, objects, and test data "
                    "are controlled."
                ),
            )
        )

    if observation.get("human_reviewed") is not True:
        findings.append(
            _finding(
                category="observation-review",
                severity="medium",
                subject=subject,
                message=(
                    "Observation has not been human-reviewed."
                ),
                required_action=(
                    "Complete human review before feedback."
                ),
            )
        )

    if observation.get("local_only") is not True:
        findings.append(
            _finding(
                category="observation-safety",
                severity="high",
                subject=subject,
                message="local_only must be true.",
                required_action=(
                    "Restore the fail-closed observation contract."
                ),
            )
        )

    if observation.get("planning_only") is not True:
        findings.append(
            _finding(
                category="observation-safety",
                severity="high",
                subject=subject,
                message="planning_only must be true.",
                required_action=(
                    "Restore the fail-closed observation contract."
                ),
            )
        )

    if (
        observation.get("execution_state")
        != "not_executed"
    ):
        findings.append(
            _finding(
                category="observation-safety",
                severity="high",
                subject=subject,
                message=(
                    "execution_state must be not_executed."
                ),
                required_action=(
                    "Reject observations claiming execution."
                ),
            )
        )

    for field in OBSERVATION_REQUIRED_FALSE_FLAGS:
        if observation.get(field) is not False:
            findings.append(
                _finding(
                    category="observation-safety",
                    severity="high",
                    subject=subject,
                    message=f"{field} must remain false.",
                    required_action=(
                        "Restore fail-closed observation flags."
                    ),
                )
            )

    expected_delta = _confidence_delta(
        outcome,
        evidence_strength,
    )
    expected_effect = _hypothesis_effect(
        expected_delta
    )

    if (
        observation.get(
            "preliminary_confidence_delta"
        )
        != expected_delta
    ):
        findings.append(
            _finding(
                category="observation-consistency",
                severity="high",
                subject=subject,
                message=(
                    "preliminary_confidence_delta does not match "
                    "outcome and evidence strength."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )

    if (
        observation.get(
            "preliminary_hypothesis_effect"
        )
        != expected_effect
    ):
        findings.append(
            _finding(
                category="observation-consistency",
                severity="high",
                subject=subject,
                message=(
                    "preliminary_hypothesis_effect does not match "
                    "the expected confidence delta."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )

    observation_digest = _optional_text(
        observation.get("observation_digest")
    )

    if (
        not observation_digest
        or not _is_sha256(observation_digest)
    ):
        findings.append(
            _finding(
                category="observation-integrity",
                severity="high",
                subject=subject,
                message=(
                    "observation_digest must be a lowercase "
                    "SHA-256 digest."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        )
    else:
        digest_material = copy.deepcopy(
            observation
        )
        digest_material.pop(
            "observation_digest",
            None,
        )
        expected_digest = _sha256(
            digest_material
        )

        if observation_digest != expected_digest:
            findings.append(
                _finding(
                    category="observation-integrity",
                    severity="high",
                    subject=subject,
                    message=(
                        "observation_digest does not match "
                        "observation contents."
                    ),
                    required_action=(
                        "Reject the modified observation."
                    ),
                )
            )

    high_count = sum(
        item.get("severity") == "high"
        for item in findings
    )
    medium_count = sum(
        item.get("severity") == "medium"
        for item in findings
    )

    if high_count:
        review_status = (
            "blocked-invalid-observation"
        )
    elif medium_count:
        review_status = (
            "review-needed-observation-gaps"
        )
    else:
        review_status = READY_STATUS

    return {
        "observation_id": observation_id,
        "request_id": request_id,
        "action_id": action_id,
        "hypothesis_id": hypothesis_id,
        "source_type": source_type,
        "outcome": outcome,
        "evidence_strength": evidence_strength,
        "expected_confidence_delta": (
            expected_delta
        ),
        "expected_hypothesis_effect": (
            expected_effect
        ),
        "observation_digest": (
            observation_digest
        ),
        "review_status": review_status,
        "review_ready": (
            review_status == READY_STATUS
        ),
        "hypothesis_feedback_ready": (
            review_status == READY_STATUS
            and bool(hypothesis_id)
        ),
        "automatic_hypothesis_update_allowed": False,
        "state_mutation_allowed": False,
        "runtime_execution_allowed": False,
        "finding_count": len(findings),
        "high_finding_count": high_count,
        "medium_finding_count": medium_count,
        "findings": findings,
    }


def _review_impacts(
    actual_value: Any,
    expected: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if not isinstance(actual_value, list):
        return [
            _finding(
                category="impact-integrity",
                severity="high",
                subject=(
                    "preliminary_hypothesis_impacts"
                ),
                message=(
                    "preliminary_hypothesis_impacts must be a list."
                ),
                required_action=(
                    "Rebuild the observation packet."
                ),
            )
        ]

    actual = [
        item
        for item in actual_value
        if isinstance(item, dict)
    ]

    if actual != expected:
        findings.append(
            _finding(
                category="impact-integrity",
                severity="high",
                subject=(
                    "preliminary_hypothesis_impacts"
                ),
                message=(
                    "Preliminary hypothesis impacts do not match "
                    "the normalized observations."
                ),
                required_action=(
                    "Reject the modified impacts and rebuild the "
                    "observation packet."
                ),
            )
        )

    return findings


def _expected_impacts(
    observations: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}

    for observation in observations:
        hypothesis_id = _text(
            observation.get("hypothesis_id")
        )

        if not hypothesis_id:
            continue

        grouped.setdefault(
            hypothesis_id,
            [],
        ).append(observation)

    impacts: list[dict[str, Any]] = []

    for hypothesis_id in sorted(grouped):
        items = grouped[hypothesis_id]

        delta = sum(
            _confidence_delta(
                _text(item.get("outcome")),
                _text(
                    item.get("evidence_strength")
                ),
            )
            for item in items
        )

        impacts.append(
            {
                "hypothesis_id": hypothesis_id,
                "observation_count": len(items),
                "observation_ids": [
                    _text(
                        item.get("observation_id")
                    )
                    for item in items
                ],
                "net_confidence_delta": delta,
                "preliminary_direction": (
                    _hypothesis_effect(delta)
                ),
                "automatic_update_allowed": False,
                "human_review_required": True,
            }
        )

    return impacts


def _review_status(
    observation_count: int,
    packet_findings: list[dict[str, str]],
    observation_findings: list[dict[str, str]],
    impact_findings: list[dict[str, str]],
) -> str:
    findings = (
        packet_findings
        + observation_findings
        + impact_findings
    )

    high = [
        item
        for item in findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category") in UNSAFE_CATEGORIES
        for item in high
    ):
        return "blocked-unsafe-observations"

    # Direct source, packet, and observation digest failures
    # take precedence because the reviewed artifact cannot be
    # trusted. Derived impact mismatches are handled after
    # structural/schema validation.
    if any(
        item.get("category")
        in {
            "source-integrity",
            "packet-integrity",
            "observation-integrity",
        }
        for item in high
    ):
        return "blocked-observation-integrity-failure"

    if any(
        item.get("category") == "packet-schema"
        for item in high
    ):
        return "blocked-invalid-observation-packet"

    if observation_count == 0:
        return "blocked-no-observations"

    if any(
        item.get("category")
        == "packet-readiness"
        for item in findings
    ):
        return "blocked-observation-packet-not-ready"

    # Structural observation defects take precedence over
    # secondary impact mismatches caused by invalid IDs,
    # outcomes, or evidence-strength values.
    if any(
        item.get("category")
        == "observation-schema"
        for item in high
    ):
        return "blocked-invalid-observations"

    if any(
        item.get("category")
        == "impact-integrity"
        for item in high
    ):
        return "blocked-observation-integrity-failure"

    if high:
        return "blocked-invalid-observations"

    if any(
        item.get("severity") == "medium"
        for item in findings
    ):
        return "review-needed-observation-gaps"

    return READY_STATUS


def _confidence_delta(
    outcome: str,
    evidence_strength: str,
) -> int:
    strength = {
        "none": 0,
        "weak": 1,
        "moderate": 2,
        "strong": 3,
    }.get(evidence_strength, 0)

    if outcome == "supports-hypothesis":
        return strength

    if outcome == "weakly-supports-hypothesis":
        return min(strength, 1)

    if outcome == "contradicts-hypothesis":
        return -strength

    if outcome == "weakly-contradicts-hypothesis":
        return -min(strength, 1)

    return 0


def _hypothesis_effect(delta: int) -> str:
    if delta >= 3:
        return "strengthen"
    if delta > 0:
        return "slightly-strengthen"
    if delta <= -3:
        return "weaken"
    if delta < 0:
        return "slightly-weaken"
    return "hold"


def _summary(
    status: str,
    observation_count: int,
    ready_observations: int,
) -> str:
    if status == READY_STATUS:
        return (
            f"{ready_observations} of {observation_count} "
            "observation(s) passed integrity, linkage, "
            "authorization, redaction, safety, and preliminary "
            "hypothesis-impact review."
        )

    return (
        f"{observation_count} observation(s) were reviewed, "
        f"but hypothesis feedback is not ready: {status}."
    )


def _allowed_next_steps(
    status: str,
) -> list[str]:
    if status != READY_STATUS:
        return []

    return [
        (
            "Create a separate reviewed hypothesis-feedback "
            "packet from the verified observation impacts."
        ),
        (
            "Preserve source packet, observation, and review "
            "digests in every downstream feedback artifact."
        ),
        (
            "Require explicit human review before changing "
            "hypothesis confidence."
        ),
        (
            "Keep persistent research-state mutation disabled "
            "until a dedicated transition gate approves it."
        ),
    ]


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


def _render_findings(value: Any) -> list[str]:
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


def _count_by(
    items: list[dict[str, Any]],
    field: str,
) -> dict[str, int]:
    counts: dict[str, int] = {}

    for item in items:
        value = _text(
            item.get(field),
            "unknown",
        )
        counts[value] = counts.get(value, 0) + 1

    return dict(sorted(counts.items()))


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
        text = value.strip()
        return [text] if text else []

    if not isinstance(value, (list, tuple, set)):
        return []

    result: list[str] = []

    for item in value:
        text = _text(item)

        if text and text not in result:
            result.append(text)

    return result


def _optional_text(value: Any) -> str | None:
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
    "EXPECTED_KIND",
    "EXPECTED_STATUS",
    "INTEGRITY_CATEGORIES",
    "OBSERVATION_REQUIRED_FALSE_FLAGS",
    "PACKET_REQUIRED_FALSE_FLAGS",
    "PACKET_REQUIRED_TRUE_FLAGS",
    "READY_STATUS",
    "SAFETY_REQUIRED_FALSE_FLAGS",
    "SAFETY_REQUIRED_TRUE_FLAGS",
    "UNSAFE_CATEGORIES",
    "build_research_observation_review_gate",
    "build_review_gate_from_file",
    "load_json_object",
    "render_research_observation_review_gate_markdown",
    "write_json",
    "write_markdown",
]
