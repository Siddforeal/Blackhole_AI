"""Research observation packet for the Blackhole reasoning loop.

This module converts local, user-provided observation records into a
deterministic feedback packet suitable for later review, hypothesis updates,
research-state transitions, criticism, and replanning.

The packet may describe observations produced elsewhere, including results
from human-approved testing, browser inspection, Burp Suite exports, command
output, source review, or local artifact analysis.

This module itself does not execute commands, launch browsers, use Burp Suite,
run Kali tools, send requests, interact with targets, collect evidence, alter
hypothesis state, mutate research state, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

import copy
import hashlib
import json
import re
from pathlib import Path
from typing import Any


KNOWN_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "manual-note",
        "command-output",
        "test-result",
        "http-request",
        "http-response",
        "browser-network",
        "browser-console",
        "browser-dom",
        "browser-screenshot",
        "burp-request",
        "burp-response",
        "har-entry",
        "local-file",
        "local-artifact",
        "source-code",
        "mobile-artifact",
        "log-entry",
        "error-output",
        "unknown",
    }
)

KNOWN_OUTCOMES: frozenset[str] = frozenset(
    {
        "supports-hypothesis",
        "weakly-supports-hypothesis",
        "contradicts-hypothesis",
        "weakly-contradicts-hypothesis",
        "inconclusive",
        "blocked",
        "error",
        "no-observable-change",
        "not-tested",
    }
)

KNOWN_EVIDENCE_STRENGTHS: frozenset[str] = frozenset(
    {
        "none",
        "weak",
        "moderate",
        "strong",
    }
)

KNOWN_REDACTION_STATUSES: frozenset[str] = frozenset(
    {
        "reviewed",
        "not-required",
        "pending",
        "failed",
        "unknown",
    }
)

KNOWN_SCOPE_STATUSES: frozenset[str] = frozenset(
    {
        "confirmed",
        "not-applicable",
        "pending",
        "unknown",
    }
)

KNOWN_CONTROLLED_ASSET_STATUSES: frozenset[str] = frozenset(
    {
        "confirmed",
        "not-required",
        "pending",
        "unknown",
    }
)

LIVE_OBSERVATION_SOURCE_TYPES: frozenset[str] = frozenset(
    {
        "command-output",
        "test-result",
        "http-request",
        "http-response",
        "browser-network",
        "browser-console",
        "browser-dom",
        "browser-screenshot",
        "burp-request",
        "burp-response",
        "har-entry",
        "log-entry",
        "error-output",
    }
)

PACKET_FALSE_FLAGS: tuple[str, ...] = (
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

RAW_UNSAFE_TRUE_FIELDS: tuple[str, ...] = (
    "command_generation_allowed",
    "payload_generation_allowed",
    "package_installation_allowed",
    "execution_allowed",
    "runtime_execution_allowed",
    "network_interaction_allowed",
    "target_interaction_allowed",
    "evidence_collection_allowed",
    "validation_allowed",
    "state_mutation_allowed",
    "report_submission_allowed",
    "vulnerability_confirmation_allowed",
)

OBSERVATION_SAFETY: dict[str, bool] = {
    "local_only": True,
    "deterministic": True,
    "planning_only": True,
    "import_only": True,
    "normalization_only": True,
    "observation_review_required": True,
    "hypothesis_update_review_required": True,
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
}

SECRET_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "authorization-header",
        re.compile(
            r"(?i)\bauthorization\s*:\s*(?:bearer|basic)\s+\S+"
        ),
    ),
    (
        "cookie-header",
        re.compile(
            r"(?i)\b(?:cookie|set-cookie)\s*:\s*[^\n]+"
        ),
    ),
    (
        "api-key",
        re.compile(
            r"(?i)\b(?:api[_-]?key|secret[_-]?key|access[_-]?token)"
            r"\s*[:=]\s*[\"']?[A-Za-z0-9._~+/=-]{12,}"
        ),
    ),
    (
        "jwt-like-token",
        re.compile(
            r"\beyJ[A-Za-z0-9_-]{8,}\."
            r"[A-Za-z0-9_-]{8,}\."
            r"[A-Za-z0-9_-]{8,}\b"
        ),
    ),
    (
        "private-key",
        re.compile(
            r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
        ),
    ),
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
    """Write deterministic JSON output."""
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
    """Write Markdown output."""
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(value, encoding="utf-8")


def build_research_observation_packet(
    observation_input: dict[str, Any],
    source: str = "brain-chat-research-observation-packet",
) -> dict[str, Any]:
    """Build a deterministic local observation packet."""
    payload = copy.deepcopy(
        observation_input
        if isinstance(observation_input, dict)
        else {}
    )

    target_name = _text(
        payload.get("target_name"),
        "unknown-target",
    )
    focus_endpoint = _optional_text(
        payload.get("focus_endpoint")
    )
    source_manifest_digest = _optional_text(
        payload.get("source_manifest_digest")
        or payload.get("manifest_digest")
    )
    source_review_digest = _optional_text(
        payload.get("source_review_digest")
        or payload.get("review_digest")
    )

    raw_observations = payload.get("observations")
    input_findings: list[dict[str, str]] = []

    if raw_observations is None:
        raw_observations = []
    elif not isinstance(raw_observations, list):
        input_findings.append(
            _finding(
                category="packet-schema",
                severity="high",
                subject="observations",
                message="observations must be a list.",
                required_action=(
                    "Provide a JSON list of observation objects."
                ),
            )
        )
        raw_observations = []

    observations: list[dict[str, Any]] = []
    observation_findings: list[dict[str, str]] = []

    for index, raw in enumerate(
        raw_observations,
        start=1,
    ):
        observation, findings = _normalize_observation(
            raw,
            index=index,
            packet_focus_endpoint=focus_endpoint,
        )
        observations.append(observation)
        observation_findings.extend(findings)

    packet_findings = _packet_findings(
        payload=payload,
        target_name=target_name,
        source_manifest_digest=source_manifest_digest,
        source_review_digest=source_review_digest,
        observations=observations,
    )

    findings = (
        input_findings
        + packet_findings
        + observation_findings
    )

    preliminary_impacts = _preliminary_hypothesis_impacts(
        observations
    )

    packet_status = _packet_status(
        observations=observations,
        findings=findings,
    )
    packet_ready = (
        packet_status == "ready-for-observation-review"
    )

    outcome_counts = _count_by(
        observations,
        "outcome",
    )
    source_type_counts = _count_by(
        observations,
        "source_type",
    )
    strength_counts = _count_by(
        observations,
        "evidence_strength",
    )
    redaction_counts = _count_by(
        observations,
        "redaction_status",
    )
    scope_counts = _count_by(
        observations,
        "scope_status",
    )

    linked_request_ids = sorted(
        {
            _text(item.get("request_id"))
            for item in observations
            if _text(item.get("request_id"))
        }
    )
    linked_action_ids = sorted(
        {
            _text(item.get("action_id"))
            for item in observations
            if _text(item.get("action_id"))
        }
    )
    linked_hypothesis_ids = sorted(
        {
            _text(item.get("hypothesis_id"))
            for item in observations
            if _text(item.get("hypothesis_id"))
        }
    )

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

    packet_digest_material = {
        "target_name": target_name,
        "focus_endpoint": focus_endpoint,
        "source_manifest_digest": source_manifest_digest,
        "source_review_digest": source_review_digest,
        "observations": observations,
    }
    packet_digest = _sha256(packet_digest_material)

    return {
        "kind": "brain_chat_research_observation_packet",
        "source": source,
        "target_name": target_name,
        "focus_endpoint": focus_endpoint,
        "packet_status": packet_status,
        "summary": _summary(
            packet_status,
            observation_count=len(observations),
            hypothesis_count=len(
                preliminary_impacts
            ),
        ),
        "packet_ready": packet_ready,
        "observation_review_ready": packet_ready,
        "hypothesis_feedback_review_ready": packet_ready,
        "research_state_transition_ready": False,
        "critic_review_ready": False,
        "replanning_ready": False,
        "source_manifest_digest": source_manifest_digest,
        "source_review_digest": source_review_digest,
        "observation_count": len(observations),
        "observations": observations,
        "preliminary_hypothesis_impacts": (
            preliminary_impacts
        ),
        "linked_request_ids": linked_request_ids,
        "linked_action_ids": linked_action_ids,
        "linked_hypothesis_ids": (
            linked_hypothesis_ids
        ),
        "outcome_counts": outcome_counts,
        "source_type_counts": source_type_counts,
        "evidence_strength_counts": strength_counts,
        "redaction_status_counts": redaction_counts,
        "scope_status_counts": scope_counts,
        "findings": findings,
        "counts": {
            "observations": len(observations),
            "linked_requests": len(
                linked_request_ids
            ),
            "linked_actions": len(
                linked_action_ids
            ),
            "linked_hypotheses": len(
                linked_hypothesis_ids
            ),
            "preliminary_hypothesis_impacts": len(
                preliminary_impacts
            ),
            "findings": len(findings),
            "high_findings": len(high_findings),
            "medium_findings": len(
                medium_findings
            ),
            "low_findings": len(low_findings),
            "human_reviewed_observations": sum(
                bool(item.get("human_reviewed"))
                for item in observations
            ),
            "pending_redaction_observations": sum(
                item.get("redaction_status")
                in {"pending", "failed", "unknown"}
                for item in observations
            ),
            "scope_confirmed_observations": sum(
                item.get("scope_status")
                in {"confirmed", "not-applicable"}
                for item in observations
            ),
            "controlled_asset_confirmed_observations": sum(
                item.get("controlled_assets_status")
                in {"confirmed", "not-required"}
                for item in observations
            ),
        },
        "allowed_next_steps": _allowed_next_steps(
            packet_status,
            observation_count=len(observations),
        ),
        "rejected_next_steps": [
            "Do not automatically change hypothesis confidence from this packet.",
            "Do not automatically mutate persistent research state.",
            "Do not execute follow-up commands or tools.",
            "Do not send requests or interact with targets.",
            "Do not treat imported observations as verified evidence before review.",
            "Do not submit reports or confirm vulnerabilities.",
        ],
        "packet_digest": packet_digest,
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
        "safety": dict(OBSERVATION_SAFETY),
    }


def build_observation_packet_from_file(
    observation_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Build an observation packet from a local JSON file."""
    payload = load_json_object(observation_file)
    packet = build_research_observation_packet(
        payload
    )

    if output_file is not None:
        write_markdown(
            output_file,
            render_research_observation_packet_markdown(
                packet
            ),
        )

    if json_output is not None:
        write_json(json_output, packet)

    return packet


def render_research_observation_packet_markdown(
    packet: dict[str, Any],
) -> str:
    """Render one observation packet as Markdown."""
    lines = [
        "# Research Observation Packet",
        "",
        "## Packet Status",
        "",
        (
            "- target_name: "
            f"`{packet.get('target_name', '')}`"
        ),
        (
            "- focus_endpoint: "
            f"`{packet.get('focus_endpoint') or 'none'}`"
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
            "- observation_review_ready: "
            f"`{_bool_text(packet.get('observation_review_ready'))}`"
        ),
        (
            "- hypothesis_feedback_review_ready: "
            f"`{_bool_text(packet.get('hypothesis_feedback_review_ready'))}`"
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
            "- packet_digest: "
            f"`{packet.get('packet_digest', '')}`"
        ),
        f"- summary: {packet.get('summary', '')}",
        "",
        "## Observations",
        "",
        (
            "| ID | Request | Action | Hypothesis | Source | "
            "Outcome | Strength | Scope | Redaction | Reviewed |"
        ),
        (
            "|---|---|---|---|---|---|---|---|---|---|"
        ),
    ]

    for item in _object_list(
        packet.get("observations")
    ):
        lines.append(
            "| "
            f"`{item.get('observation_id', '')}` | "
            f"`{item.get('request_id') or 'none'}` | "
            f"`{item.get('action_id') or 'none'}` | "
            f"`{item.get('hypothesis_id') or 'none'}` | "
            f"`{item.get('source_type', '')}` | "
            f"`{item.get('outcome', '')}` | "
            f"`{item.get('evidence_strength', '')}` | "
            f"`{item.get('scope_status', '')}` | "
            f"`{item.get('redaction_status', '')}` | "
            f"`{_bool_text(item.get('human_reviewed'))}` |"
        )

        lines.extend(
            [
                "",
                (
                    f"### {item.get('observation_id', '')}: "
                    f"{item.get('summary') or 'No summary'}"
                ),
                "",
                (
                    "- preliminary hypothesis effect: "
                    f"`{item.get('preliminary_hypothesis_effect', '')}`"
                ),
                (
                    "- preliminary confidence delta: "
                    f"`{item.get('preliminary_confidence_delta', 0)}`"
                ),
                (
                    "- observation digest: "
                    f"`{item.get('observation_digest', '')}`"
                ),
                "- details:",
            ]
        )

        details = _list_of_text(item.get("details"))
        lines.extend(
            [f"  - {value}" for value in details]
            or ["  - none"]
        )

        lines.append("- artifact references:")
        artifacts = _list_of_text(
            item.get("artifact_refs")
        )
        lines.extend(
            [f"  - `{value}`" for value in artifacts]
            or ["  - none"]
        )

        lines.append("- signals:")
        signals = _list_of_text(item.get("signals"))
        lines.extend(
            [f"  - {value}" for value in signals]
            or ["  - none"]
        )

        lines.append("- errors:")
        errors = _list_of_text(item.get("errors"))
        lines.extend(
            [f"  - {value}" for value in errors]
            or ["  - none"]
        )
        lines.append("")

    lines.extend(
        [
            "## Preliminary Hypothesis Impacts",
            "",
            (
                "| Hypothesis | Observations | Net Delta | "
                "Preliminary Direction |"
            ),
            "|---|---:|---:|---|",
        ]
    )

    for item in _object_list(
        packet.get(
            "preliminary_hypothesis_impacts"
        )
    ):
        lines.append(
            "| "
            f"`{item.get('hypothesis_id', '')}` | "
            f"{item.get('observation_count', 0)} | "
            f"{item.get('net_confidence_delta', 0)} | "
            f"`{item.get('preliminary_direction', '')}` |"
        )

    lines.extend(["", "## Findings", ""])
    lines.extend(
        _render_findings(packet.get("findings"))
    )

    lines.extend(["", "## Allowed Next Steps", ""])
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
            "## Safety",
            "",
            "- This packet only imports and normalizes local observation records.",
            "- Imported observations remain unverified until separately reviewed.",
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


def _normalize_observation(
    raw: Any,
    index: int,
    packet_focus_endpoint: str | None,
) -> tuple[dict[str, Any], list[dict[str, str]]]:
    subject = f"observations[{index - 1}]"
    findings: list[dict[str, str]] = []

    if not isinstance(raw, dict):
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message="Observation must be an object.",
                required_action=(
                    "Replace the value with an observation object."
                ),
            )
        )
        raw = {}

    observation_id = f"OBS-{index:03d}"

    provided_id = _text(
        raw.get("observation_id")
        or raw.get("id")
    )
    if provided_id and provided_id != observation_id:
        findings.append(
            _finding(
                category="observation-identity",
                severity="medium",
                subject=subject,
                message=(
                    f"Provided observation ID {provided_id!r} was "
                    f"normalized to {observation_id}."
                ),
                required_action=(
                    "Use deterministic observation ordering and IDs."
                ),
            )
        )

    source_type_raw = _text(
        raw.get("source_type")
        or raw.get("type"),
        "unknown",
    ).lower()

    if source_type_raw not in KNOWN_SOURCE_TYPES:
        findings.append(
            _finding(
                category="observation-schema",
                severity="medium",
                subject=subject,
                message=(
                    "Unsupported source_type was normalized to "
                    f"unknown: {source_type_raw!r}."
                ),
                required_action=(
                    "Select a supported observation source type."
                ),
            )
        )
        source_type = "unknown"
    else:
        source_type = source_type_raw

    outcome_raw = _text(
        raw.get("outcome"),
        "inconclusive",
    ).lower()

    if outcome_raw not in KNOWN_OUTCOMES:
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    f"Unsupported observation outcome: "
                    f"{outcome_raw!r}."
                ),
                required_action=(
                    "Use a supported deterministic outcome."
                ),
            )
        )
        outcome = "inconclusive"
    else:
        outcome = outcome_raw

    strength_raw = _text(
        raw.get("evidence_strength")
        or raw.get("strength"),
        "",
    ).lower()

    if not strength_raw:
        evidence_strength = _default_strength(
            outcome
        )
        findings.append(
            _finding(
                category="observation-quality",
                severity="low",
                subject=subject,
                message=(
                    "evidence_strength was not supplied and was "
                    f"defaulted to {evidence_strength}."
                ),
                required_action=(
                    "Review and explicitly assign evidence strength."
                ),
            )
        )
    elif (
        strength_raw
        not in KNOWN_EVIDENCE_STRENGTHS
    ):
        evidence_strength = "none"
        findings.append(
            _finding(
                category="observation-schema",
                severity="high",
                subject=subject,
                message=(
                    "Unsupported evidence_strength: "
                    f"{strength_raw!r}."
                ),
                required_action=(
                    "Use none, weak, moderate, or strong."
                ),
            )
        )
    else:
        evidence_strength = strength_raw

    summary = _text(
        raw.get("summary")
        or raw.get("title")
    )

    if not summary:
        findings.append(
            _finding(
                category="observation-quality",
                severity="high",
                subject=subject,
                message="Observation summary must not be empty.",
                required_action=(
                    "Add a concise factual observation summary."
                ),
            )
        )

    details = _list_of_text(
        raw.get("details")
        or raw.get("observations")
        or raw.get("notes")
    )
    artifact_refs = _list_of_text(
        raw.get("artifact_refs")
        or raw.get("artifacts")
        or raw.get("evidence_refs")
    )
    signals = _list_of_text(raw.get("signals"))
    errors = _list_of_text(
        raw.get("errors")
        or raw.get("error")
    )

    request_id = _optional_text(
        raw.get("request_id")
    )
    action_id = _optional_text(
        raw.get("action_id")
    )
    hypothesis_id = _optional_text(
        raw.get("hypothesis_id")
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
                    "Link the observation before hypothesis feedback."
                ),
            )
        )

    focus_endpoint = _optional_text(
        raw.get("focus_endpoint")
    ) or packet_focus_endpoint

    redaction_status = _normalized_enum(
        raw.get("redaction_status"),
        allowed=KNOWN_REDACTION_STATUSES,
        default="unknown",
    )
    scope_status = _normalized_enum(
        raw.get("scope_status"),
        allowed=KNOWN_SCOPE_STATUSES,
        default="unknown",
    )
    controlled_assets_status = _normalized_enum(
        raw.get("controlled_assets_status"),
        allowed=KNOWN_CONTROLLED_ASSET_STATUSES,
        default="unknown",
    )

    if redaction_status in {
        "pending",
        "failed",
        "unknown",
    }:
        findings.append(
            _finding(
                category="observation-redaction",
                severity="high",
                subject=subject,
                message=(
                    "Observation redaction is not complete: "
                    f"{redaction_status}."
                ),
                required_action=(
                    "Review and redact secrets, identifiers, "
                    "private data, and sensitive artifacts."
                ),
            )
        )

    if (
        source_type in LIVE_OBSERVATION_SOURCE_TYPES
        and scope_status != "confirmed"
    ):
        findings.append(
            _finding(
                category="observation-scope",
                severity="high",
                subject=subject,
                message=(
                    "Live-derived observation requires confirmed "
                    f"scope; current status is {scope_status}."
                ),
                required_action=(
                    "Confirm authorization and target scope."
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
                    "Observation scope status requires review: "
                    f"{scope_status}."
                ),
                required_action=(
                    "Confirm scope or mark it not applicable."
                ),
            )
        )

    if (
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
                    "Live-derived observation requires controlled "
                    "asset confirmation."
                ),
                required_action=(
                    "Confirm all accounts, tenants, objects, "
                    "projects, files, and test data are controlled."
                ),
            )
        )

    human_reviewed = bool(
        raw.get("human_reviewed")
    )

    if not human_reviewed:
        findings.append(
            _finding(
                category="observation-review",
                severity="medium",
                subject=subject,
                message=(
                    "Observation has not been marked as "
                    "human-reviewed."
                ),
                required_action=(
                    "Perform human review before hypothesis updates."
                ),
            )
        )

    for field in RAW_UNSAFE_TRUE_FIELDS:
        if bool(raw.get(field)):
            findings.append(
                _finding(
                    category="observation-safety",
                    severity="high",
                    subject=subject,
                    message=(
                        f"Imported observation field {field} "
                        "must not grant authority."
                    ),
                    required_action=(
                        "Remove unsafe authority flags from the "
                        "observation record."
                    ),
                )
            )

    sensitive_matches = _sensitive_matches(
        [
            summary,
            *details,
            *signals,
            *errors,
            *artifact_refs,
        ]
    )

    for match_name in sensitive_matches:
        findings.append(
            _finding(
                category="sensitive-data",
                severity="high",
                subject=subject,
                message=(
                    "Possible unredacted sensitive material "
                    f"detected: {match_name}."
                ),
                required_action=(
                    "Remove or redact the sensitive material "
                    "before continuing."
                ),
            )
        )

    preliminary_delta = _confidence_delta(
        outcome=outcome,
        evidence_strength=evidence_strength,
    )
    preliminary_effect = _hypothesis_effect(
        preliminary_delta
    )

    normalized = {
        "observation_id": observation_id,
        "request_id": request_id,
        "action_id": action_id,
        "hypothesis_id": hypothesis_id,
        "target_name": _optional_text(
            raw.get("target_name")
        ),
        "focus_endpoint": focus_endpoint,
        "source_type": source_type,
        "outcome": outcome,
        "evidence_strength": evidence_strength,
        "summary": summary,
        "details": details,
        "artifact_refs": artifact_refs,
        "signals": signals,
        "errors": errors,
        "observed_at": _optional_text(
            raw.get("observed_at")
        ),
        "scope_status": scope_status,
        "controlled_assets_status": (
            controlled_assets_status
        ),
        "redaction_status": redaction_status,
        "human_reviewed": human_reviewed,
        "observation_origin": _text(
            raw.get("observation_origin"),
            "imported-user-provided",
        ),
        "preliminary_hypothesis_effect": (
            preliminary_effect
        ),
        "preliminary_confidence_delta": (
            preliminary_delta
        ),
        "hypothesis_mutation_allowed": False,
        "state_mutation_allowed": False,
        "execution_allowed": False,
        "runtime_execution_allowed": False,
        "network_interaction_allowed": False,
        "target_interaction_allowed": False,
        "evidence_collection_allowed": False,
        "validation_allowed": False,
        "local_only": True,
        "planning_only": True,
        "execution_state": "not_executed",
    }

    normalized["observation_digest"] = _sha256(
        normalized
    )

    return normalized, findings


def _packet_findings(
    payload: dict[str, Any],
    target_name: str,
    source_manifest_digest: str | None,
    source_review_digest: str | None,
    observations: list[dict[str, Any]],
) -> list[dict[str, str]]:
    findings: list[dict[str, str]] = []

    if target_name == "unknown-target":
        findings.append(
            _finding(
                category="packet-quality",
                severity="medium",
                subject="target_name",
                message="target_name is missing or unknown.",
                required_action=(
                    "Bind observations to an authorized target."
                ),
            )
        )

    for name, digest in (
        (
            "source_manifest_digest",
            source_manifest_digest,
        ),
        (
            "source_review_digest",
            source_review_digest,
        ),
    ):
        if digest and not _is_sha256(digest):
            findings.append(
                _finding(
                    category="source-integrity",
                    severity="high",
                    subject=name,
                    message=(
                        f"{name} must be a lowercase SHA-256 digest."
                    ),
                    required_action=(
                        "Provide the exact digest from the source "
                        "planning or review artifact."
                    ),
                )
            )

    declared_count = payload.get(
        "observation_count"
    )
    if declared_count is not None:
        if _int(declared_count) != len(observations):
            findings.append(
                _finding(
                    category="packet-consistency",
                    severity="high",
                    subject="observation_count",
                    message=(
                        "Declared observation_count does not match "
                        "the observations list."
                    ),
                    required_action=(
                        "Correct or remove observation_count."
                    ),
                )
            )

    for field in PACKET_FALSE_FLAGS:
        if bool(payload.get(field)):
            findings.append(
                _finding(
                    category="packet-safety",
                    severity="high",
                    subject=field,
                    message=f"{field} must remain false.",
                    required_action=(
                        "Remove unsafe authority from the import packet."
                    ),
                )
            )

    return findings


def _preliminary_hypothesis_impacts(
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
            _int(
                item.get(
                    "preliminary_confidence_delta"
                )
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


def _packet_status(
    observations: list[dict[str, Any]],
    findings: list[dict[str, str]],
) -> str:
    if not observations:
        return "blocked-no-observations"

    high = [
        item
        for item in findings
        if item.get("severity") == "high"
    ]

    if any(
        item.get("category")
        in {
            "packet-safety",
            "observation-safety",
            "sensitive-data",
        }
        for item in high
    ):
        return "blocked-unsafe-observations"

    # Structural corruption takes precedence over secondary
    # findings produced by normalization defaults.
    if any(
        item.get("category")
        in {
            "packet-schema",
            "observation-schema",
        }
        for item in high
    ):
        return "blocked-invalid-observations"

    if any(
        item.get("category")
        == "observation-redaction"
        for item in high
    ):
        return "blocked-redaction-required"

    if any(
        item.get("category")
        in {
            "observation-scope",
            "controlled-assets",
        }
        for item in high
    ):
        return "blocked-authorization-review-required"

    if high:
        return "blocked-invalid-observations"

    if any(
        item.get("severity") == "medium"
        for item in findings
    ):
        return "review-needed-observation-gaps"

    return "ready-for-observation-review"


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


def _default_strength(outcome: str) -> str:
    if outcome in {
        "supports-hypothesis",
        "contradicts-hypothesis",
    }:
        return "moderate"

    if outcome in {
        "weakly-supports-hypothesis",
        "weakly-contradicts-hypothesis",
    }:
        return "weak"

    return "none"


def _sensitive_matches(
    values: list[str],
) -> list[str]:
    text = "\n".join(
        value
        for value in values
        if value
    )
    matches: list[str] = []

    for name, pattern in SECRET_PATTERNS:
        if pattern.search(text):
            matches.append(name)

    return sorted(set(matches))


def _normalized_enum(
    value: Any,
    allowed: frozenset[str],
    default: str,
) -> str:
    normalized = _text(value, default).lower()
    return (
        normalized
        if normalized in allowed
        else default
    )


def _summary(
    status: str,
    observation_count: int,
    hypothesis_count: int,
) -> str:
    if status == "ready-for-observation-review":
        return (
            f"{observation_count} observation(s) were normalized "
            f"for review across {hypothesis_count} linked "
            "hypothesis or hypotheses. No hypothesis or research "
            "state was changed."
        )

    return (
        f"{observation_count} observation(s) were imported, "
        f"but feedback processing is not ready: {status}."
    )


def _allowed_next_steps(
    status: str,
    observation_count: int,
) -> list[str]:
    if status != "ready-for-observation-review":
        return []

    return [
        (
            f"Review all {observation_count} normalized "
            "observation records and source linkages."
        ),
        (
            "Verify scope, controlled assets, redaction, artifact "
            "references, and human-review status."
        ),
        (
            "Create a separate observation review gate before "
            "applying preliminary hypothesis impacts."
        ),
        (
            "Preserve packet and observation digests in all "
            "downstream feedback artifacts."
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
        stripped = value.strip()
        return [stripped] if stripped else []

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
    "KNOWN_CONTROLLED_ASSET_STATUSES",
    "KNOWN_EVIDENCE_STRENGTHS",
    "KNOWN_OUTCOMES",
    "KNOWN_REDACTION_STATUSES",
    "KNOWN_SCOPE_STATUSES",
    "KNOWN_SOURCE_TYPES",
    "LIVE_OBSERVATION_SOURCE_TYPES",
    "OBSERVATION_SAFETY",
    "PACKET_FALSE_FLAGS",
    "RAW_UNSAFE_TRUE_FIELDS",
    "SECRET_PATTERNS",
    "build_observation_packet_from_file",
    "build_research_observation_packet",
    "load_json_object",
    "render_research_observation_packet_markdown",
    "write_json",
    "write_markdown",
]
