from __future__ import annotations

import copy
import json
import re

import pytest

from bugintel.core.brain_chat_research_observation_packet import (
    KNOWN_CONTROLLED_ASSET_STATUSES,
    KNOWN_EVIDENCE_STRENGTHS,
    KNOWN_OUTCOMES,
    KNOWN_REDACTION_STATUSES,
    KNOWN_SCOPE_STATUSES,
    KNOWN_SOURCE_TYPES,
    LIVE_OBSERVATION_SOURCE_TYPES,
    OBSERVATION_SAFETY,
    PACKET_FALSE_FLAGS,
    RAW_UNSAFE_TRUE_FIELDS,
    build_observation_packet_from_file,
    build_research_observation_packet,
    render_research_observation_packet_markdown,
)


FOCUS_ENDPOINT = "/api/projects/123/workers/456"
VALID_DIGEST = "a" * 64


def _base_observation(**overrides) -> dict:
    observation = {
        "request_id": "RTR-001",
        "action_id": "ACT-001",
        "hypothesis_id": "HYP-005",
        "source_type": "manual-note",
        "outcome": "supports-hypothesis",
        "evidence_strength": "moderate",
        "summary": (
            "Local source review shows user-controlled worker "
            "configuration reaches job planning."
        ),
        "details": [
            "Reviewed the local controller-to-worker data flow.",
            "No live target interaction was performed.",
        ],
        "artifact_refs": [
            "notes/worker-dataflow.md",
        ],
        "signals": [
            "user-controlled worker configuration",
            "privileged worker boundary",
        ],
        "errors": [],
        "scope_status": "not-applicable",
        "controlled_assets_status": "not-required",
        "redaction_status": "not-required",
        "human_reviewed": True,
    }
    observation.update(overrides)
    return observation


def _ready_input(
    observations: list | None = None,
    **overrides,
) -> dict:
    value = {
        "target_name": "demo-self-hosted-product",
        "focus_endpoint": FOCUS_ENDPOINT,
        "source_manifest_digest": VALID_DIGEST,
        "source_review_digest": "b" * 64,
        "observations": (
            observations
            if observations is not None
            else [_base_observation()]
        ),
    }
    value.update(overrides)
    return value


def _build(
    observations: list | None = None,
    **overrides,
) -> dict:
    return build_research_observation_packet(
        _ready_input(
            observations=observations,
            **overrides,
        )
    )


def _categories(packet: dict) -> set[str]:
    return {
        item["category"]
        for item in packet["findings"]
    }


def _subjects(packet: dict) -> set[str]:
    return {
        item["subject"]
        for item in packet["findings"]
    }


def _high_categories(packet: dict) -> set[str]:
    return {
        item["category"]
        for item in packet["findings"]
        if item["severity"] == "high"
    }


def test_known_constant_sets_are_complete() -> None:
    assert "manual-note" in KNOWN_SOURCE_TYPES
    assert "command-output" in KNOWN_SOURCE_TYPES
    assert "browser-network" in KNOWN_SOURCE_TYPES
    assert "burp-response" in KNOWN_SOURCE_TYPES
    assert "source-code" in KNOWN_SOURCE_TYPES

    assert "supports-hypothesis" in KNOWN_OUTCOMES
    assert "contradicts-hypothesis" in KNOWN_OUTCOMES
    assert "inconclusive" in KNOWN_OUTCOMES
    assert "blocked" in KNOWN_OUTCOMES
    assert "error" in KNOWN_OUTCOMES

    assert KNOWN_EVIDENCE_STRENGTHS == {
        "none",
        "weak",
        "moderate",
        "strong",
    }

    assert "reviewed" in KNOWN_REDACTION_STATUSES
    assert "confirmed" in KNOWN_SCOPE_STATUSES
    assert (
        "confirmed"
        in KNOWN_CONTROLLED_ASSET_STATUSES
    )


def test_valid_observation_packet_is_ready() -> None:
    packet = _build()

    assert packet["kind"] == (
        "brain_chat_research_observation_packet"
    )
    assert packet["target_name"] == (
        "demo-self-hosted-product"
    )
    assert packet["focus_endpoint"] == FOCUS_ENDPOINT
    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["packet_ready"] is True
    assert packet["observation_review_ready"] is True
    assert (
        packet["hypothesis_feedback_review_ready"]
        is True
    )
    assert (
        packet["research_state_transition_ready"]
        is False
    )
    assert packet["critic_review_ready"] is False
    assert packet["replanning_ready"] is False
    assert packet["observation_count"] == 1
    assert packet["counts"]["observations"] == 1
    assert packet["counts"]["high_findings"] == 0
    assert packet["counts"]["medium_findings"] == 0
    assert packet["counts"]["low_findings"] == 0


def test_valid_observation_is_normalized() -> None:
    packet = _build()
    observation = packet["observations"][0]

    assert observation["observation_id"] == "OBS-001"
    assert observation["request_id"] == "RTR-001"
    assert observation["action_id"] == "ACT-001"
    assert observation["hypothesis_id"] == "HYP-005"
    assert observation["focus_endpoint"] == FOCUS_ENDPOINT
    assert observation["source_type"] == "manual-note"
    assert observation["outcome"] == (
        "supports-hypothesis"
    )
    assert observation["evidence_strength"] == (
        "moderate"
    )
    assert observation["scope_status"] == (
        "not-applicable"
    )
    assert observation["controlled_assets_status"] == (
        "not-required"
    )
    assert observation["redaction_status"] == (
        "not-required"
    )
    assert observation["human_reviewed"] is True
    assert observation["observation_origin"] == (
        "imported-user-provided"
    )
    assert observation[
        "preliminary_hypothesis_effect"
    ] == "slightly-strengthen"
    assert observation[
        "preliminary_confidence_delta"
    ] == 2
    assert observation["hypothesis_mutation_allowed"] is False
    assert observation["state_mutation_allowed"] is False
    assert observation["runtime_execution_allowed"] is False
    assert observation["execution_state"] == "not_executed"
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        observation["observation_digest"],
    )


def test_preliminary_hypothesis_impact_is_created() -> None:
    packet = _build()

    assert packet["preliminary_hypothesis_impacts"] == [
        {
            "hypothesis_id": "HYP-005",
            "observation_count": 1,
            "observation_ids": ["OBS-001"],
            "net_confidence_delta": 2,
            "preliminary_direction": (
                "slightly-strengthen"
            ),
            "automatic_update_allowed": False,
            "human_review_required": True,
        }
    ]


def test_packet_digest_is_sha256() -> None:
    packet = _build()

    assert re.fullmatch(
        r"[0-9a-f]{64}",
        packet["packet_digest"],
    )


def test_packet_generation_is_deterministic() -> None:
    payload = _ready_input()

    first = build_research_observation_packet(
        payload
    )
    second = build_research_observation_packet(
        payload
    )

    assert first == second
    assert (
        first["packet_digest"]
        == second["packet_digest"]
    )
    assert (
        first["observations"][0][
            "observation_digest"
        ]
        == second["observations"][0][
            "observation_digest"
        ]
    )


def test_packet_builder_does_not_mutate_input() -> None:
    payload = _ready_input()
    before = copy.deepcopy(payload)

    build_research_observation_packet(payload)

    assert payload == before


def test_changed_observation_changes_digests() -> None:
    first = _build()

    second = _build(
        observations=[
            _base_observation(
                summary="Different factual observation."
            )
        ]
    )

    assert (
        first["packet_digest"]
        != second["packet_digest"]
    )
    assert (
        first["observations"][0][
            "observation_digest"
        ]
        != second["observations"][0][
            "observation_digest"
        ]
    )


def test_empty_packet_is_blocked() -> None:
    packet = build_research_observation_packet({})

    assert packet["packet_status"] == (
        "blocked-no-observations"
    )
    assert packet["packet_ready"] is False
    assert packet["observation_review_ready"] is False
    assert (
        packet["hypothesis_feedback_review_ready"]
        is False
    )
    assert packet["observation_count"] == 0
    assert packet["runtime_execution_allowed"] is False
    assert "packet-quality" in _categories(packet)


def test_observations_must_be_a_list() -> None:
    packet = build_research_observation_packet(
        {
            "target_name": "demo",
            "observations": {
                "summary": "not a list",
            },
        }
    )

    assert packet["packet_status"] == (
        "blocked-no-observations"
    )
    assert "packet-schema" in _categories(packet)
    assert "observations" in _subjects(packet)


def test_non_object_observation_is_blocked() -> None:
    packet = _build(
        observations=["not-an-object"]
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert packet["packet_ready"] is False
    assert "observation-schema" in _categories(packet)
    assert packet["observations"][0][
        "observation_id"
    ] == "OBS-001"


def test_observation_ids_are_deterministic() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
            ),
            _base_observation(
                request_id="RTR-003",
                action_id="ACT-003",
            ),
        ]
    )

    assert [
        item["observation_id"]
        for item in packet["observations"]
    ] == [
        "OBS-001",
        "OBS-002",
        "OBS-003",
    ]


def test_provided_non_deterministic_id_is_normalized() -> None:
    packet = _build(
        observations=[
            _base_observation(
                observation_id="custom-id",
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert packet["observations"][0][
        "observation_id"
    ] == "OBS-001"
    assert "observation-identity" in _categories(packet)


@pytest.mark.parametrize(
    "source_type",
    sorted(KNOWN_SOURCE_TYPES),
)
def test_all_known_source_types_are_preserved(
    source_type: str,
) -> None:
    overrides = {
        "source_type": source_type,
    }

    if source_type in LIVE_OBSERVATION_SOURCE_TYPES:
        overrides.update(
            {
                "scope_status": "confirmed",
                "controlled_assets_status": (
                    "confirmed"
                ),
            }
        )

    packet = _build(
        observations=[
            _base_observation(**overrides)
        ]
    )

    assert packet["observations"][0][
        "source_type"
    ] == source_type
    assert "observation-schema" not in _categories(
        packet
    )


def test_unsupported_source_type_is_normalized() -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="unsupported-source",
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert packet["observations"][0][
        "source_type"
    ] == "unknown"
    assert "observation-schema" in _categories(packet)


@pytest.mark.parametrize(
    "outcome",
    sorted(KNOWN_OUTCOMES),
)
def test_all_known_outcomes_are_preserved(
    outcome: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                outcome=outcome,
                evidence_strength="moderate",
            )
        ]
    )

    assert packet["observations"][0][
        "outcome"
    ] == outcome
    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )


def test_unsupported_outcome_is_blocked() -> None:
    packet = _build(
        observations=[
            _base_observation(
                outcome="definitely-vulnerable",
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert packet["observations"][0][
        "outcome"
    ] == "inconclusive"
    assert "observation-schema" in _categories(packet)


@pytest.mark.parametrize(
    ("outcome", "expected_strength"),
    [
        ("supports-hypothesis", "moderate"),
        ("weakly-supports-hypothesis", "weak"),
        ("contradicts-hypothesis", "moderate"),
        ("weakly-contradicts-hypothesis", "weak"),
        ("inconclusive", "none"),
        ("blocked", "none"),
        ("error", "none"),
        ("no-observable-change", "none"),
        ("not-tested", "none"),
    ],
)
def test_missing_strength_gets_deterministic_default(
    outcome: str,
    expected_strength: str,
) -> None:
    observation = _base_observation(
        outcome=outcome,
    )
    observation.pop("evidence_strength")

    packet = _build(
        observations=[observation]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["observations"][0][
        "evidence_strength"
    ] == expected_strength
    assert packet["counts"]["low_findings"] == 1
    assert "observation-quality" in _categories(packet)


def test_invalid_evidence_strength_is_blocked() -> None:
    packet = _build(
        observations=[
            _base_observation(
                evidence_strength="absolute-proof",
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert packet["observations"][0][
        "evidence_strength"
    ] == "none"
    assert "observation-schema" in _categories(packet)


def test_missing_summary_is_blocked() -> None:
    packet = _build(
        observations=[
            _base_observation(
                summary="",
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert "observation-quality" in _high_categories(
        packet
    )


def test_title_is_accepted_as_summary_alias() -> None:
    observation = _base_observation()
    observation.pop("summary")
    observation["title"] = "Imported title summary."

    packet = _build(
        observations=[observation]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["observations"][0][
        "summary"
    ] == "Imported title summary."


def test_notes_are_accepted_as_details_alias() -> None:
    observation = _base_observation()
    observation.pop("details")
    observation["notes"] = [
        "Imported note one.",
        "Imported note two.",
    ]

    packet = _build(
        observations=[observation]
    )

    assert packet["observations"][0]["details"] == [
        "Imported note one.",
        "Imported note two.",
    ]


def test_artifacts_are_accepted_as_alias() -> None:
    observation = _base_observation()
    observation.pop("artifact_refs")
    observation["artifacts"] = [
        "artifacts/result.json",
    ]

    packet = _build(
        observations=[observation]
    )

    assert packet["observations"][0][
        "artifact_refs"
    ] == ["artifacts/result.json"]


def test_observation_requires_linkage() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id=None,
                action_id=None,
                hypothesis_id=None,
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-linkage" in _categories(packet)
    assert packet[
        "preliminary_hypothesis_impacts"
    ] == []


def test_action_only_linkage_is_accepted() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id=None,
                hypothesis_id=None,
                action_id="ACT-123",
            )
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["linked_action_ids"] == [
        "ACT-123"
    ]
    assert packet[
        "preliminary_hypothesis_impacts"
    ] == []


def test_packet_focus_endpoint_is_applied() -> None:
    observation = _base_observation()
    observation.pop("focus_endpoint", None)

    packet = _build(
        observations=[observation]
    )

    assert packet["observations"][0][
        "focus_endpoint"
    ] == FOCUS_ENDPOINT


def test_observation_focus_endpoint_overrides_packet() -> None:
    packet = _build(
        observations=[
            _base_observation(
                focus_endpoint="/api/custom",
            )
        ]
    )

    assert packet["observations"][0][
        "focus_endpoint"
    ] == "/api/custom"


@pytest.mark.parametrize(
    "redaction_status",
    [
        "pending",
        "failed",
        "unknown",
    ],
)
def test_incomplete_redaction_is_blocked(
    redaction_status: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                redaction_status=redaction_status,
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-redaction-required"
    )
    assert "observation-redaction" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    "redaction_status",
    [
        "reviewed",
        "not-required",
    ],
)
def test_complete_redaction_is_accepted(
    redaction_status: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                redaction_status=redaction_status,
            )
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )


def test_invalid_redaction_status_becomes_unknown() -> None:
    packet = _build(
        observations=[
            _base_observation(
                redaction_status="done-ish",
            )
        ]
    )

    assert packet["observations"][0][
        "redaction_status"
    ] == "unknown"
    assert packet["packet_status"] == (
        "blocked-redaction-required"
    )


@pytest.mark.parametrize(
    "scope_status",
    [
        "pending",
        "unknown",
        "not-applicable",
    ],
)
def test_live_observation_requires_confirmed_scope(
    scope_status: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="http-response",
                scope_status=scope_status,
                controlled_assets_status="confirmed",
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-authorization-review-required"
    )
    assert "observation-scope" in _high_categories(
        packet
    )


def test_live_observation_with_confirmed_scope_is_accepted() -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="http-response",
                scope_status="confirmed",
                controlled_assets_status="confirmed",
            )
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )


def test_local_observation_pending_scope_needs_review() -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="source-code",
                scope_status="pending",
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-scope" in _categories(packet)


@pytest.mark.parametrize(
    "controlled_status",
    [
        "pending",
        "unknown",
    ],
)
def test_live_observation_requires_controlled_assets(
    controlled_status: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="browser-network",
                scope_status="confirmed",
                controlled_assets_status=(
                    controlled_status
                ),
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-authorization-review-required"
    )
    assert "controlled-assets" in _high_categories(
        packet
    )


@pytest.mark.parametrize(
    "controlled_status",
    [
        "confirmed",
        "not-required",
    ],
)
def test_live_controlled_asset_status_is_accepted(
    controlled_status: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="browser-network",
                scope_status="confirmed",
                controlled_assets_status=(
                    controlled_status
                ),
            )
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )


def test_invalid_controlled_asset_status_is_normalized() -> None:
    packet = _build(
        observations=[
            _base_observation(
                source_type="manual-note",
                controlled_assets_status="maybe",
            )
        ]
    )

    assert packet["observations"][0][
        "controlled_assets_status"
    ] == "unknown"


def test_unreviewed_observation_needs_review() -> None:
    packet = _build(
        observations=[
            _base_observation(
                human_reviewed=False,
            )
        ]
    )

    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert "observation-review" in _categories(packet)
    assert packet["counts"][
        "human_reviewed_observations"
    ] == 0


@pytest.mark.parametrize(
    "field",
    RAW_UNSAFE_TRUE_FIELDS,
)
def test_observation_authority_flags_are_blocked(
    field: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                **{field: True},
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-observations"
    )
    assert packet["packet_ready"] is False
    assert "observation-safety" in _high_categories(
        packet
    )
    assert packet["runtime_execution_allowed"] is False


@pytest.mark.parametrize(
    "field",
    PACKET_FALSE_FLAGS,
)
def test_packet_authority_flags_are_blocked(
    field: str,
) -> None:
    packet = build_research_observation_packet(
        _ready_input(
            **{field: True},
        )
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-observations"
    )
    assert "packet-safety" in _high_categories(
        packet
    )
    assert field in _subjects(packet)


@pytest.mark.parametrize(
    ("sensitive_text", "expected_name"),
    [
        (
            "Authorization: Bearer super-secret-token",
            "authorization-header",
        ),
        (
            "Cookie: session=abcdef123456",
            "cookie-header",
        ),
        (
            "api_key=abcdefghijklmnop",
            "api-key",
        ),
        (
            (
                "eyJabcdefghijk."
                "abcdefghijkl."
                "abcdefghijklm"
            ),
            "jwt-like-token",
        ),
        (
            "-----BEGIN PRIVATE KEY-----",
            "private-key",
        ),
    ],
)
def test_sensitive_material_is_blocked(
    sensitive_text: str,
    expected_name: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                details=[sensitive_text],
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-observations"
    )
    assert "sensitive-data" in _high_categories(
        packet
    )
    assert any(
        expected_name in item["message"]
        for item in packet["findings"]
    )


def test_sensitive_material_in_artifact_reference_is_detected() -> None:
    packet = _build(
        observations=[
            _base_observation(
                artifact_refs=[
                    (
                        "Authorization: Bearer "
                        "sensitive-artifact-token"
                    )
                ],
            )
        ]
    )

    assert packet["packet_status"] == (
        "blocked-unsafe-observations"
    )
    assert "sensitive-data" in _categories(packet)


@pytest.mark.parametrize(
    "field",
    [
        "source_manifest_digest",
        "source_review_digest",
    ],
)
def test_invalid_source_digest_is_blocked(
    field: str,
) -> None:
    packet = _build(
        **{field: "not-a-valid-digest"}
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert "source-integrity" in _high_categories(
        packet
    )
    assert field in _subjects(packet)


def test_uppercase_source_digest_is_rejected() -> None:
    packet = _build(
        source_manifest_digest="A" * 64
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert "source-integrity" in _categories(packet)


def test_missing_source_digests_are_allowed() -> None:
    payload = _ready_input()
    payload.pop("source_manifest_digest")
    payload.pop("source_review_digest")

    packet = build_research_observation_packet(
        payload
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["source_manifest_digest"] is None
    assert packet["source_review_digest"] is None


def test_declared_observation_count_must_match() -> None:
    packet = _build(
        observation_count=99
    )

    assert packet["packet_status"] == (
        "blocked-invalid-observations"
    )
    assert "packet-consistency" in _categories(packet)
    assert "observation_count" in _subjects(packet)


def test_correct_declared_count_is_accepted() -> None:
    packet = _build(
        observation_count=1
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )


def test_unknown_target_requires_review() -> None:
    packet = _build(
        target_name=""
    )

    assert packet["target_name"] == "unknown-target"
    assert packet["packet_status"] == (
        "review-needed-observation-gaps"
    )
    assert "packet-quality" in _categories(packet)


@pytest.mark.parametrize(
    (
        "outcome",
        "strength",
        "expected_delta",
        "expected_effect",
    ),
    [
        (
            "supports-hypothesis",
            "strong",
            3,
            "strengthen",
        ),
        (
            "supports-hypothesis",
            "moderate",
            2,
            "slightly-strengthen",
        ),
        (
            "supports-hypothesis",
            "weak",
            1,
            "slightly-strengthen",
        ),
        (
            "weakly-supports-hypothesis",
            "strong",
            1,
            "slightly-strengthen",
        ),
        (
            "contradicts-hypothesis",
            "strong",
            -3,
            "weaken",
        ),
        (
            "contradicts-hypothesis",
            "moderate",
            -2,
            "slightly-weaken",
        ),
        (
            "weakly-contradicts-hypothesis",
            "strong",
            -1,
            "slightly-weaken",
        ),
        (
            "inconclusive",
            "strong",
            0,
            "hold",
        ),
        (
            "error",
            "strong",
            0,
            "hold",
        ),
        (
            "blocked",
            "moderate",
            0,
            "hold",
        ),
        (
            "no-observable-change",
            "moderate",
            0,
            "hold",
        ),
    ],
)
def test_preliminary_confidence_delta_mapping(
    outcome: str,
    strength: str,
    expected_delta: int,
    expected_effect: str,
) -> None:
    packet = _build(
        observations=[
            _base_observation(
                outcome=outcome,
                evidence_strength=strength,
            )
        ]
    )

    observation = packet["observations"][0]

    assert observation[
        "preliminary_confidence_delta"
    ] == expected_delta
    assert observation[
        "preliminary_hypothesis_effect"
    ] == expected_effect


def test_multiple_observations_are_aggregated() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
                hypothesis_id="HYP-005",
                outcome="supports-hypothesis",
                evidence_strength="strong",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                hypothesis_id="HYP-005",
                outcome="contradicts-hypothesis",
                evidence_strength="weak",
            ),
            _base_observation(
                request_id="RTR-003",
                action_id="ACT-003",
                hypothesis_id="HYP-007",
                outcome="supports-hypothesis",
                evidence_strength="moderate",
            ),
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert packet["observation_count"] == 3

    impacts = {
        item["hypothesis_id"]: item
        for item in packet[
            "preliminary_hypothesis_impacts"
        ]
    }

    assert impacts["HYP-005"][
        "observation_count"
    ] == 2
    assert impacts["HYP-005"][
        "net_confidence_delta"
    ] == 2
    assert impacts["HYP-005"][
        "preliminary_direction"
    ] == "slightly-strengthen"
    assert impacts["HYP-007"][
        "net_confidence_delta"
    ] == 2


def test_hypothesis_impact_order_is_deterministic() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                hypothesis_id="HYP-999",
            ),
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
                hypothesis_id="HYP-001",
            ),
        ]
    )

    assert [
        item["hypothesis_id"]
        for item in packet[
            "preliminary_hypothesis_impacts"
        ]
    ] == [
        "HYP-001",
        "HYP-999",
    ]


def test_linked_ids_are_unique_and_sorted() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                hypothesis_id="HYP-002",
            ),
            _base_observation(
                request_id="RTR-001",
                action_id="ACT-001",
                hypothesis_id="HYP-001",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                hypothesis_id="HYP-002",
            ),
        ]
    )

    assert packet["linked_request_ids"] == [
        "RTR-001",
        "RTR-002",
    ]
    assert packet["linked_action_ids"] == [
        "ACT-001",
        "ACT-002",
    ]
    assert packet["linked_hypothesis_ids"] == [
        "HYP-001",
        "HYP-002",
    ]


def test_count_maps_are_generated() -> None:
    packet = _build(
        observations=[
            _base_observation(
                request_id="RTR-001",
                source_type="manual-note",
                outcome="supports-hypothesis",
                evidence_strength="strong",
                redaction_status="reviewed",
            ),
            _base_observation(
                request_id="RTR-002",
                action_id="ACT-002",
                source_type="source-code",
                outcome="inconclusive",
                evidence_strength="none",
                redaction_status="not-required",
            ),
        ]
    )

    assert packet["outcome_counts"] == {
        "inconclusive": 1,
        "supports-hypothesis": 1,
    }
    assert packet["source_type_counts"] == {
        "manual-note": 1,
        "source-code": 1,
    }
    assert packet["evidence_strength_counts"] == {
        "none": 1,
        "strong": 1,
    }
    assert packet["redaction_status_counts"] == {
        "not-required": 1,
        "reviewed": 1,
    }


def test_allowed_next_steps_only_when_ready() -> None:
    ready = _build()
    blocked = build_research_observation_packet({})

    assert len(ready["allowed_next_steps"]) == 4
    assert blocked["allowed_next_steps"] == []


def test_rejected_next_steps_are_explicit() -> None:
    packet = _build()
    text = " ".join(packet["rejected_next_steps"])

    assert "hypothesis confidence" in text
    assert "persistent research state" in text
    assert "commands or tools" in text
    assert "interact with targets" in text
    assert "verified evidence" in text
    assert "confirm vulnerabilities" in text


def test_packet_output_remains_fail_closed() -> None:
    packet = _build()

    for field in PACKET_FALSE_FLAGS:
        assert packet[field] is False

    assert packet["planning_only"] is True
    assert packet["execution_state"] == (
        "not_executed"
    )


def test_packet_safety_contract() -> None:
    packet = _build()
    safety = packet["safety"]

    assert safety == OBSERVATION_SAFETY

    assert safety["local_only"] is True
    assert safety["deterministic"] is True
    assert safety["planning_only"] is True
    assert safety["import_only"] is True
    assert safety["normalization_only"] is True
    assert (
        safety["observation_review_required"]
        is True
    )
    assert (
        safety["hypothesis_update_review_required"]
        is True
    )
    assert (
        safety[
            "research_state_transition_review_required"
        ]
        is True
    )

    for field in (
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
    ):
        assert safety[field] is False


def test_markdown_contains_required_sections() -> None:
    packet = _build()

    markdown = (
        render_research_observation_packet_markdown(
            packet
        )
    )

    assert "# Research Observation Packet" in markdown
    assert "## Packet Status" in markdown
    assert "## Observations" in markdown
    assert (
        "## Preliminary Hypothesis Impacts"
        in markdown
    )
    assert "## Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Safety" in markdown

    assert (
        "packet_status: "
        "`ready-for-observation-review`"
        in markdown
    )
    assert "packet_ready: `true`" in markdown
    assert (
        "research_state_transition_ready: `false`"
        in markdown
    )
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )
    assert "OBS-001" in markdown
    assert "HYP-005" in markdown
    assert "notes/worker-dataflow.md" in markdown


def test_blocked_markdown_renders_findings() -> None:
    packet = _build(
        observations=[
            _base_observation(
                summary="",
            )
        ]
    )

    markdown = (
        render_research_observation_packet_markdown(
            packet
        )
    )

    assert "blocked-invalid-observations" in markdown
    assert "[high] observation-quality" in markdown
    assert (
        "Observation summary must not be empty."
        in markdown
    )


def test_file_builder_writes_markdown_and_json(
    tmp_path,
) -> None:
    input_file = tmp_path / "observations.json"
    markdown_file = (
        tmp_path
        / "output"
        / "observation-packet.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "observation-packet.json"
    )

    input_file.write_text(
        json.dumps(_ready_input()),
        encoding="utf-8",
    )

    packet = build_observation_packet_from_file(
        input_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_observation_packet"
    )
    assert written["packet_ready"] is True
    assert written["observation_count"] == 1
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )

    assert "# Research Observation Packet" in markdown


def test_non_object_file_is_rejected(tmp_path) -> None:
    input_file = tmp_path / "list.json"
    input_file.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Expected JSON object",
    ):
        build_observation_packet_from_file(
            input_file
        )


def test_custom_source_name_is_preserved() -> None:
    packet = build_research_observation_packet(
        _ready_input(),
        source="custom-observation-import",
    )

    assert packet["source"] == (
        "custom-observation-import"
    )


def test_unicode_content_is_deterministic() -> None:
    packet = _build(
        observations=[
            _base_observation(
                summary=(
                    "Observation includes Unicode: "
                    "résumé — 東京 — 🔒"
                ),
                details=[
                    "Deterministic UTF-8 serialization.",
                ],
            )
        ]
    )

    assert packet["packet_status"] == (
        "ready-for-observation-review"
    )
    assert re.fullmatch(
        r"[0-9a-f]{64}",
        packet["packet_digest"],
    )


def test_duplicate_text_values_are_deduplicated() -> None:
    packet = _build(
        observations=[
            _base_observation(
                details=[
                    "same detail",
                    "same detail",
                    "second detail",
                ],
                artifact_refs=[
                    "artifact.json",
                    "artifact.json",
                ],
                signals=[
                    "signal",
                    "signal",
                ],
            )
        ]
    )

    observation = packet["observations"][0]

    assert observation["details"] == [
        "same detail",
        "second detail",
    ]
    assert observation["artifact_refs"] == [
        "artifact.json",
    ]
    assert observation["signals"] == [
        "signal",
    ]


def test_observed_at_is_preserved() -> None:
    packet = _build(
        observations=[
            _base_observation(
                observed_at="2026-06-12T12:34:56Z",
            )
        ]
    )

    assert packet["observations"][0][
        "observed_at"
    ] == "2026-06-12T12:34:56Z"


def test_custom_observation_origin_is_preserved() -> None:
    packet = _build(
        observations=[
            _base_observation(
                observation_origin=(
                    "human-reviewed-local-import"
                ),
            )
        ]
    )

    assert packet["observations"][0][
        "observation_origin"
    ] == "human-reviewed-local-import"


def test_no_hypothesis_or_state_is_automatically_changed() -> None:
    packet = _build(
        observations=[
            _base_observation(
                outcome="supports-hypothesis",
                evidence_strength="strong",
            )
        ]
    )

    observation = packet["observations"][0]
    impact = packet[
        "preliminary_hypothesis_impacts"
    ][0]

    assert observation[
        "preliminary_confidence_delta"
    ] == 3
    assert observation[
        "hypothesis_mutation_allowed"
    ] is False
    assert observation["state_mutation_allowed"] is False
    assert impact["automatic_update_allowed"] is False
    assert impact["human_review_required"] is True
    assert (
        packet["research_state_transition_ready"]
        is False
    )
