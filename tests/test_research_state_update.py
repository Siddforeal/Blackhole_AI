import pytest

from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.research_state import build_research_state_from_orchestration
from bugintel.core.research_state_update import (
    build_research_state_update_plan,
    render_research_state_update_plan_markdown,
)


def _state_data():
    orchestration = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )
    return build_research_state_from_orchestration(orchestration.to_dict()).to_dict()


def test_supported_result_moves_endpoint_to_report_candidate():
    state = _state_data()
    plan = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        "supported",
        note="Validated with controlled accounts.",
    )
    data = plan.to_dict()

    assert data["target_name"] == "demo"
    assert data["validation_result"] == "supported"
    assert data["planning_only"] is True
    assert any(action["new_value"] == "report-candidate" for action in data["actions"])
    assert any(action["new_value"] == "supported" for action in data["actions"])
    assert any(action["new_value"] == "attached-to-report" for action in data["actions"])
    assert any(action["new_value"] == "Validated with controlled accounts." for action in data["actions"])


def test_rejected_result_deprioritizes_endpoint():
    state = _state_data()
    plan = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        "rejected",
    )
    data = plan.to_dict()

    assert any(action["new_value"] == "deprioritized" for action in data["actions"])
    assert any(action["new_value"] == "rejected" for action in data["actions"])


def test_needs_more_evidence_result_sets_triage():
    state = _state_data()
    plan = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        "needs-more-evidence",
    )
    data = plan.to_dict()

    assert any(action["new_value"] == "needs-more-evidence" for action in data["actions"])


def test_invalid_validation_result_raises():
    with pytest.raises(ValueError):
        build_research_state_update_plan(_state_data(), "/x", "confirmed")


def test_render_update_plan_markdown():
    state = _state_data()
    plan = build_research_state_update_plan(
        state,
        "/api/accounts/123/users/{id}/permissions",
        "supported",
    )
    markdown = render_research_state_update_plan_markdown(plan)

    assert "# Blackhole Research State Update Plan: demo" in markdown
    assert "report-candidate" in markdown
    assert "Planning-only update plan" in markdown
