from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.report_draft import build_report_draft, render_report_draft_markdown


def test_build_report_draft_from_orchestration_json():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ],
    )

    draft = build_report_draft(plan.to_dict())
    data = draft.to_dict()

    assert data["title"] == "Blackhole Report Draft: demo"
    assert data["target_name"] == "demo"
    assert data["endpoint_count"] == 2
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["sections"]
    assert "Priority Triage" in {section["title"] for section in data["sections"]}
    assert "Evidence Requirements" in {section["title"] for section in data["sections"]}
    assert "markdown" in data


def test_report_draft_markdown_contains_core_sections():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    draft = build_report_draft(plan.to_dict())
    markdown = render_report_draft_markdown(draft)

    assert "# Blackhole Report Draft: demo" in markdown
    assert "## Scope and Authorization" in markdown
    assert "## Priority Triage" in markdown
    assert "## Attack Surface Grouping" in markdown
    assert "## Evidence Requirements" in markdown
    assert "## Steps to Reproduce" in markdown
    assert "controlled-account-role-matrix" in markdown
    assert "/api/accounts/123/users/{id}/permissions" in markdown
    assert "Planning-only report draft" in markdown


def test_report_draft_handles_missing_optional_plan_data():
    draft = build_report_draft({"target_name": "empty"})
    markdown = render_report_draft_markdown(draft)

    assert draft.target_name == "empty"
    assert draft.endpoint_count == 0
    assert "No endpoint priority data" in markdown
    assert "No attack-surface group data" in markdown
    assert "No evidence requirement plan" in markdown
