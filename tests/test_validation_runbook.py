from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.validation_runbook import build_validation_runbook, render_validation_runbook_markdown


def test_build_validation_runbook_from_orchestration():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
            "/api/status",
        ],
    )

    runbook = build_validation_runbook(plan.to_dict())
    data = runbook.to_dict()

    assert data["target_name"] == "demo"
    assert data["endpoint_count"] == 3
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["endpoint_runbooks"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoint_runbooks"][0]["steps"]


def test_validation_runbook_includes_identity_and_object_steps():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    runbook = build_validation_runbook(plan.to_dict())
    steps = {step["name"] for step in runbook.to_dict()["endpoint_runbooks"][0]["steps"]}

    assert "Document controlled account role matrix" in steps
    assert "Compare allowed and denied authorization decisions" in steps
    assert "Map identifier source" in steps
    assert "Validate object-reference handling" in steps
    assert "Build owned/foreign/random response matrix" in steps


def test_validation_runbook_includes_file_surface_steps():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/files/{id}/download"],
    )

    runbook = build_validation_runbook(plan.to_dict())
    steps = {step["name"] for step in runbook.to_dict()["endpoint_runbooks"][0]["steps"]}

    assert "Prepare synthetic test file manifest" in steps
    assert "Validate file access boundary" in steps


def test_validation_runbook_markdown_contains_safety_and_steps():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    runbook = build_validation_runbook(plan.to_dict())
    markdown = render_validation_runbook_markdown(runbook)

    assert "# Blackhole Validation Runbook: demo" in markdown
    assert "Global Safety Rules" in markdown
    assert "Confirm scope and authorization" in markdown
    assert "Validate object-reference handling" in markdown
    assert "Planning-only validation runbook" in markdown


def test_validation_runbook_handles_missing_evidence_plan():
    runbook = build_validation_runbook({"target_name": "empty"})
    data = runbook.to_dict()

    assert data["target_name"] == "empty"
    assert data["endpoint_count"] == 0
    assert data["endpoint_runbooks"] == []
