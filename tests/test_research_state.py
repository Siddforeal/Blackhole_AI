from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import (
    build_research_state_from_orchestration,
    render_research_state_markdown,
    slugify_endpoint,
)


def test_slugify_endpoint_for_research_state_keys():
    assert slugify_endpoint("/api/accounts/123/users/{id}/permissions") == "api-accounts-123-users-id-permissions"


def test_build_research_state_from_orchestration_json():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    data = state.to_dict()

    assert data["target_name"] == "demo"
    assert data["endpoint_count"] == 3
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["endpoints"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoints"][0]["priority_band"] == "critical"


def test_research_state_identity_endpoint_has_hypotheses_and_artifacts():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    endpoint = state.to_dict()["endpoints"][0]

    hypothesis_names = {item["name"] for item in endpoint["hypotheses"]}
    artifact_names = {item["name"] for item in endpoint["artifacts"]}

    assert "authorization-boundary-hypothesis" in hypothesis_names
    assert "object-reference-hypothesis" in hypothesis_names
    assert "controlled-account-role-matrix" in artifact_names
    assert "owned-foreign-random-response-matrix" in artifact_names
    assert endpoint["triage_state"] == "ready-for-manual-validation"


def test_research_state_file_endpoint_has_file_hypothesis():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/files/{id}/download"],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    endpoint = state.to_dict()["endpoints"][0]
    hypothesis_names = {item["name"] for item in endpoint["hypotheses"]}

    assert "file-access-boundary-hypothesis" in hypothesis_names


def test_research_state_low_signal_endpoint_is_deprioritized():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/status"],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    endpoint = state.to_dict()["endpoints"][0]
    hypothesis_names = {item["name"] for item in endpoint["hypotheses"]}

    assert endpoint["triage_state"] == "deprioritized"
    assert "low-signal-deprioritization-hypothesis" in hypothesis_names


def test_research_state_global_decisions_are_present():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    decision_names = {item["name"] for item in state.to_dict()["decisions"]}

    assert "confirm-scope-and-authorization" in decision_names
    assert "manual-validation-required" in decision_names
    assert "prioritize-high-signal-endpoints" in decision_names
    assert "approval-gated-artifacts" in decision_names


def test_render_research_state_markdown_contains_case_memory():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    state = build_research_state_from_orchestration(plan.to_dict())
    markdown = render_research_state_markdown(state)

    assert "# Blackhole Research State: demo" in markdown
    assert "Planning-only case memory" in markdown
    assert "authorization-boundary-hypothesis" in markdown
    assert "controlled-account-role-matrix" in markdown
    assert "/api/accounts/123/users/{id}/permissions" in markdown
