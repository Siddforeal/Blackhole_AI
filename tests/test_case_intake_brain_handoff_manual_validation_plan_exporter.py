from bugintel.core.case_intake_brain_handoff_manual_validation_plan_exporter import (
    export_case_intake_brain_handoff_manual_validation_plan,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def test_manual_validation_plan_exports_focus_endpoints() -> None:
    plan = export_case_intake_brain_handoff_manual_validation_plan(_handoff())

    assert plan.target_name == "demo-program"
    assert plan.blocked is False
    assert plan.planning_only is True
    assert plan.approval_required is True
    assert plan.read_only_required is True
    assert plan.validation_allowed is False
    assert plan.runtime_execution_allowed is False
    assert plan.report_submission_allowed is False
    assert plan.vulnerability_confirmation_allowed is False
    assert plan.plan_endpoint_count == len(_handoff()["focus_endpoints"])
    assert plan.evidence_gap_count == len(_handoff()["evidence_gaps"])

    first = plan.plan_endpoints[0]
    assert first.endpoint == "/api/admin/users/{id}/permissions"
    assert first.approval_required is True
    assert first.read_only_required is True
    assert first.checklist_ids[0] == "EC-001"
    assert first.validation_steps
    assert first.evidence_targets
    assert first.stop_conditions


def test_manual_validation_plan_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_manual_validation_plan"
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_manual_validation_plan_blocks_invalid_handoff() -> None:
    plan = export_case_intake_brain_handoff_manual_validation_plan({"kind": "wrong"})

    assert plan.blocked is True
    assert plan.handoff_status == "blocked-invalid-case-intake-brain-handoff"
    assert plan.plan_endpoint_count == 0
    assert plan.plan_endpoints == ()


def test_manual_validation_plan_markdown_is_reviewable() -> None:
    markdown = export_case_intake_brain_handoff_manual_validation_plan(_handoff()).to_markdown()

    assert "# Case Intake Brain Manual Validation Plan" in markdown
    assert "## Manual Validation Plan" in markdown
    assert "/api/admin/users/{id}/permissions" in markdown
    assert "Controlled account matrix" in markdown
    assert "Stop conditions" in markdown
    assert "No network requests" in markdown
