from __future__ import annotations

import copy
import json

import pytest

from bugintel.core.brain_chat_research_action_decision_packet import (
    build_research_action_decision_packet,
    build_research_action_decision_template,
)
from bugintel.core.brain_chat_research_action_proposal_packet import (
    build_research_action_proposal_packet,
)
from bugintel.core.brain_chat_research_action_proposal_review_gate import (
    build_research_action_proposal_review_gate,
)
from bugintel.core.brain_chat_research_approved_action_packet import (
    build_research_approved_action_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_packet import (
    build_research_investigation_plan_packet,
)
from bugintel.core.brain_chat_research_investigation_plan_review_gate import (
    build_research_investigation_plan_review_gate,
)
from bugintel.core.brain_chat_research_typed_tool_request_manifest import (
    build_research_typed_tool_request_manifest,
)
from bugintel.core.brain_chat_research_typed_tool_request_review_gate import (
    EXPECTED_KIND,
    EXPECTED_STATUS,
    PACKET_FALSE_FLAGS,
    READY_STATUS,
    REQUEST_FALSE_FLAGS,
    SAFETY_FALSE_FLAGS,
    SAFETY_TRUE_FLAGS,
    build_research_typed_tool_request_review_gate,
    build_review_gate_from_file,
    render_research_typed_tool_request_review_gate_markdown,
)


FOCUS_ENDPOINT = "/api/projects/123/workers/456"


def _selection_packet() -> dict:
    return {
        "kind": (
            "brain_chat_research_hypothesis_selection_packet"
        ),
        "target_name": "demo-self-hosted-product",
        "selection_status": (
            "ready-for-local-investigation-planning"
        ),
        "primary_hypothesis_id": "HYP-005",
        "selected_hypotheses": [
            {
                "hypothesis_id": "HYP-005",
                "hypothesis_type": (
                    "worker-execution-trust-boundary"
                ),
                "title": "Worker execution trust boundary",
                "priority": "high",
                "confidence": "high",
                "score": 386,
                "tags": [
                    "worker",
                    "runner",
                    "deployment",
                ],
            },
        ],
    }


def _approved_action_packet(
    decisions: list[str] | None = None,
) -> dict:
    plan = build_research_investigation_plan_packet(
        _selection_packet()
    )
    plan_review = (
        build_research_investigation_plan_review_gate(
            plan
        )
    )

    proposal = build_research_action_proposal_packet(
        plan,
        plan_review,
    ).to_dict()

    proposal_review = (
        build_research_action_proposal_review_gate(
            proposal
        )
    )

    decision_input = (
        build_research_action_decision_template(
            proposal
        )
    )
    decision_input["reviewer"] = (
        "authorized-human-reviewer"
    )
    decision_input["overall_reason"] = (
        "Approved for typed tool-request planning."
    )

    values = decisions or [
        "approved"
        for _ in decision_input["decisions"]
    ]

    assert len(values) == len(
        decision_input["decisions"]
    )

    for item, decision in zip(
        decision_input["decisions"],
        values,
        strict=True,
    ):
        item["decision"] = decision
        item["reason"] = (
            f"Human decision recorded as {decision}."
        )

    decision_packet = (
        build_research_action_decision_packet(
            proposal,
            proposal_review,
            decision_input,
        )
    )

    return build_research_approved_action_packet(
        decision_packet
    )


def _manifest(
    *,
    focus_endpoint: str | None = FOCUS_ENDPOINT,
) -> dict:
    approved = _approved_action_packet()

    if focus_endpoint is not None:
        approved["focus_endpoint"] = focus_endpoint

    return build_research_typed_tool_request_manifest(
        approved
    )


def _review(
    *,
    focus_endpoint: str | None = FOCUS_ENDPOINT,
) -> dict:
    return build_research_typed_tool_request_review_gate(
        _manifest(focus_endpoint=focus_endpoint)
    )


def _categories(review: dict) -> set[str]:
    findings = (
        review["manifest_findings"]
        + review["request_findings"]
        + review["gate_findings"]
    )
    return {
        item["category"]
        for item in findings
    }


def _subjects(review: dict) -> set[str]:
    findings = (
        review["manifest_findings"]
        + review["request_findings"]
        + review["gate_findings"]
    )
    return {
        item["subject"]
        for item in findings
    }


def test_expected_constants() -> None:
    assert EXPECTED_KIND == (
        "brain_chat_research_typed_tool_request_manifest"
    )
    assert EXPECTED_STATUS == (
        "ready-for-tool-execution-gate-review"
    )
    assert READY_STATUS == (
        "ready-for-runtime-approval-template"
    )


def test_valid_focused_manifest_is_ready() -> None:
    review = _review()

    assert review["kind"] == (
        "brain_chat_research_typed_tool_request_review_gate"
    )
    assert review["target_name"] == (
        "demo-self-hosted-product"
    )
    assert review["focus_endpoint"] == FOCUS_ENDPOINT
    assert review["review_status"] == READY_STATUS
    assert review["review_ready"] is True
    assert (
        review["runtime_approval_template_ready"]
        is True
    )
    assert review["runtime_execution_allowed"] is False
    assert review["typed_request_count"] == 8
    assert review["counts"]["high_findings"] == 0
    assert review["counts"]["medium_findings"] == 0
    assert review["counts"]["ready_requests"] == 8
    assert review["counts"]["blocked_requests"] == 0


def test_valid_request_reviews_preserve_identity() -> None:
    review = _review()

    assert [
        item["request_id"]
        for item in review["request_reviews"]
    ] == [
        "RTR-001",
        "RTR-002",
        "RTR-003",
        "RTR-004",
        "RTR-005",
        "RTR-006",
        "RTR-007",
        "RTR-008",
    ]

    for item in review["request_reviews"]:
        assert item["action_id"]
        assert item["tool_family"]
        assert item["adapter_family"]
        assert item["risk_level"]
        assert item["request_digest"]
        assert item["review_status"] == READY_STATUS
        assert item["review_ready"] is True
        assert item["runtime_execution_allowed"] is False
        assert item["finding_count"] == 0


def test_missing_focus_endpoint_is_blocked() -> None:
    review = _review(focus_endpoint=None)

    assert review["review_status"] == (
        "blocked-missing-focus-endpoint"
    )
    assert review["review_ready"] is False
    assert (
        review["runtime_approval_template_ready"]
        is False
    )
    assert review["runtime_execution_allowed"] is False
    assert "focus-endpoint" in _categories(review)
    assert review["counts"]["high_findings"] >= 1

    for item in review["request_reviews"]:
        assert item["review_ready"] is False
        assert item["runtime_execution_allowed"] is False


def test_request_tampering_breaks_both_digests() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0]["purpose"] = (
        "tampered purpose"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert review["review_ready"] is False
    assert review["counts"]["high_findings"] >= 2
    assert {
        "manifest-integrity",
        "request-integrity",
    }.issubset(_categories(review))


def test_review_generation_is_deterministic() -> None:
    manifest = _manifest()

    first = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )
    second = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert first == second


def test_review_does_not_mutate_manifest() -> None:
    manifest = _manifest()
    before = copy.deepcopy(manifest)

    build_research_typed_tool_request_review_gate(
        manifest
    )

    assert manifest == before


def test_wrong_manifest_kind_is_blocked() -> None:
    manifest = _manifest()
    manifest["kind"] = "wrong-kind"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert review["review_ready"] is False
    assert "kind" in _subjects(review)


def test_non_ready_manifest_status_is_blocked() -> None:
    manifest = _manifest()
    manifest["manifest_status"] = (
        "blocked-invalid-typed-requests"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-manifest-not-ready"
    )
    assert review["review_ready"] is False


@pytest.mark.parametrize(
    "field",
    [
        "manifest_ready",
        "execution_gate_input_ready",
        "execution_gate_review_ready",
        "existing_tool_execution_gate_compatible",
    ],
)
def test_manifest_readiness_flags_are_required(
    field: str,
) -> None:
    manifest = _manifest()
    manifest[field] = False

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-manifest-not-ready"
    )
    assert field in _subjects(review)


def test_typed_request_count_mismatch_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_request_count"] = 999

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "typed_request_count" in _subjects(review)


def test_invalid_source_digest_is_blocked() -> None:
    manifest = _manifest()
    manifest["approved_action_packet_digest"] = (
        "not-a-digest"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert (
        "approved_action_packet_digest"
        in _subjects(review)
    )


def test_invalid_manifest_digest_is_blocked() -> None:
    manifest = _manifest()
    manifest["manifest_digest"] = "0" * 64

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "manifest-integrity" in _categories(review)


@pytest.mark.parametrize(
    "field",
    PACKET_FALSE_FLAGS,
)
def test_packet_execution_flags_fail_closed(
    field: str,
) -> None:
    manifest = _manifest()
    manifest[field] = True

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert review["review_ready"] is False
    assert review["runtime_execution_allowed"] is False
    assert field in _subjects(review)


def test_manifest_must_remain_planning_only() -> None:
    manifest = _manifest()
    manifest["planning_only"] = False

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "planning_only" in _subjects(review)


def test_manifest_must_remain_not_executed() -> None:
    manifest = _manifest()
    manifest["execution_state"] = "executed"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "execution_state" in _subjects(review)


def test_missing_manifest_safety_object_is_blocked() -> None:
    manifest = _manifest()
    del manifest["safety"]

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "safety" in _subjects(review)


@pytest.mark.parametrize(
    "field",
    SAFETY_TRUE_FLAGS,
)
def test_required_true_safety_flags(
    field: str,
) -> None:
    manifest = _manifest()
    manifest["safety"][field] = False

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert f"safety.{field}" in _subjects(review)


@pytest.mark.parametrize(
    "field",
    SAFETY_FALSE_FLAGS,
)
def test_required_false_safety_flags(
    field: str,
) -> None:
    manifest = _manifest()
    manifest["safety"][field] = True

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert f"safety.{field}" in _subjects(review)


def test_duplicate_request_id_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][1]["request_id"] = (
        manifest["typed_requests"][0]["request_id"]
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-schema" in _categories(review)


def test_duplicate_action_id_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][1]["action_id"] = (
        manifest["typed_requests"][0]["action_id"]
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-schema" in _categories(review)


def test_duplicate_manual_order_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][1]["manual_order"] = (
        manifest["typed_requests"][0]["manual_order"]
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-order" in _categories(review)


def test_non_deterministic_request_id_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0]["request_id"] = (
        "RTR-999"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-order" in _categories(review)


def test_missing_required_request_field_is_blocked() -> None:
    manifest = _manifest()
    del manifest["typed_requests"][0]["purpose"]

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-schema" in _categories(review)


def test_unsupported_action_type_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0]["action_type"] = (
        "unknown-action-type"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-profile" in _categories(review)


def test_tool_family_profile_mismatch_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0]["tool_family"] = (
        "browser"
    )

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-profile" in _categories(review)


def test_adapter_contract_mismatch_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][
        "prohibited_operations"
    ] = ["incorrect-operation"]

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-contract" in _categories(review)


def test_unknown_adapter_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][
        "adapter_family"
    ] = "unknown-adapter"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "request-contract" in _categories(review)


def test_human_approval_requirement_is_enforced() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][
        "requires_human_approval"
    ] = False

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "request-safety" in _categories(review)


def test_planning_approval_state_is_enforced() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][
        "approval_state"
    ] = "runtime-approved"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "request-safety" in _categories(review)


def test_request_state_is_enforced() -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][
        "request_state"
    ] = "executable"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "request-safety" in _categories(review)


@pytest.mark.parametrize(
    "field",
    REQUEST_FALSE_FLAGS,
)
def test_request_execution_flags_fail_closed(
    field: str,
) -> None:
    manifest = _manifest()
    manifest["typed_requests"][0][field] = True

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert review["runtime_execution_allowed"] is False
    assert "request-safety" in _categories(review)


def test_execution_gate_target_mismatch_is_blocked() -> None:
    manifest = _manifest()
    manifest["execution_gate_input"][
        "target_name"
    ] = "different-target"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "gate-consistency" in _categories(review)


def test_execution_gate_focus_mismatch_is_blocked() -> None:
    manifest = _manifest()
    manifest["execution_gate_input"][
        "focus_endpoint"
    ] = "/different"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "gate-consistency" in _categories(review)


def test_execution_gate_request_count_mismatch() -> None:
    manifest = _manifest()
    manifest["execution_gate_input"]["requests"].pop()

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "gate-consistency" in _categories(review)


def test_execution_gate_preview_tampering_is_blocked() -> None:
    manifest = _manifest()
    manifest["execution_gate_preview"][
        "gate_decision"
    ] = "eligible"

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-invalid-typed-tool-requests"
    )
    assert "gate-consistency" in _categories(review)


def test_execution_allowed_preview_is_unsafe() -> None:
    manifest = _manifest()
    manifest["execution_gate_preview"][
        "execution_allowed"
    ] = True

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-unsafe-manifest"
    )
    assert "gate-safety" in _categories(review)


def test_empty_request_manifest_is_blocked() -> None:
    manifest = _manifest()
    manifest["typed_requests"] = []
    manifest["typed_request_count"] = 0
    manifest["execution_gate_input"]["requests"] = []

    review = (
        build_research_typed_tool_request_review_gate(
            manifest
        )
    )

    assert review["review_status"] == (
        "blocked-no-typed-requests"
    )
    assert review["review_ready"] is False
    assert review["typed_request_count"] == 0


def test_review_output_remains_fail_closed() -> None:
    review = _review()

    assert review["command_generation_allowed"] is False
    assert review["payload_generation_allowed"] is False
    assert review["package_installation_allowed"] is False
    assert review["execution_allowed"] is False
    assert review["runtime_execution_allowed"] is False
    assert review["network_interaction_allowed"] is False
    assert review["target_interaction_allowed"] is False
    assert review["evidence_collection_allowed"] is False
    assert review["validation_allowed"] is False
    assert review["state_mutation_allowed"] is False
    assert review["report_submission_allowed"] is False
    assert (
        review["vulnerability_confirmation_allowed"]
        is False
    )
    assert review["planning_only"] is True
    assert review["execution_state"] == "not_executed"

    safety = review["safety"]

    assert safety["local_only"] is True
    assert safety["planning_only"] is True
    assert safety["integrity_review_only"] is True
    assert (
        safety["runtime_approval_template_required"]
        is True
    )
    assert (
        safety["exact_action_approval_required"]
        is True
    )
    assert safety["runtime_execution_allowed"] is False


def test_markdown_contains_required_sections() -> None:
    review = _review()

    markdown = (
        render_research_typed_tool_request_review_gate_markdown(
            review
        )
    )

    assert (
        "# Research Typed Tool Request Review Gate"
        in markdown
    )
    assert "## Review Status" in markdown
    assert "## Request Reviews" in markdown
    assert "## Manifest Findings" in markdown
    assert "## Request Findings" in markdown
    assert "## Execution-Gate Findings" in markdown
    assert "## Allowed Next Steps" in markdown
    assert "## Safety" in markdown
    assert (
        "review_status: "
        "`ready-for-runtime-approval-template`"
        in markdown
    )
    assert "review_ready: `true`" in markdown
    assert (
        "runtime_execution_allowed: `false`"
        in markdown
    )


def test_file_builder_writes_markdown_and_json(
    tmp_path,
) -> None:
    manifest_file = tmp_path / "manifest.json"
    markdown_file = (
        tmp_path
        / "output"
        / "typed-request-review.md"
    )
    json_file = (
        tmp_path
        / "output"
        / "typed-request-review.json"
    )

    manifest_file.write_text(
        json.dumps(_manifest()),
        encoding="utf-8",
    )

    review = build_review_gate_from_file(
        manifest_file,
        output_file=markdown_file,
        json_output=json_file,
    )

    assert review["review_status"] == READY_STATUS
    assert markdown_file.exists()
    assert json_file.exists()

    written = json.loads(
        json_file.read_text(encoding="utf-8")
    )

    assert written["kind"] == (
        "brain_chat_research_typed_tool_request_review_gate"
    )
    assert written["review_ready"] is True
    assert (
        written["runtime_approval_template_ready"]
        is True
    )
    assert written["runtime_execution_allowed"] is False

    markdown = markdown_file.read_text(
        encoding="utf-8"
    )
    assert (
        "# Research Typed Tool Request Review Gate"
        in markdown
    )


def test_non_object_file_is_rejected(tmp_path) -> None:
    manifest_file = tmp_path / "list.json"
    manifest_file.write_text(
        json.dumps(["not", "an", "object"]),
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="Expected JSON object",
    ):
        build_review_gate_from_file(manifest_file)
