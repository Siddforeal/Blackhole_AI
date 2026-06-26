from bugintel.core.case_intake_brain_handoff_evidence_checklist_exporter import (
    export_case_intake_brain_handoff_evidence_checklist,
)
from tests.test_case_intake_brain_handoff_answerer import _handoff


def test_evidence_checklist_exports_gaps() -> None:
    checklist = export_case_intake_brain_handoff_evidence_checklist(_handoff())

    assert checklist.target_name == "demo-program"
    assert checklist.blocked is False
    assert checklist.planning_only is True
    assert checklist.validation_allowed is False
    assert checklist.runtime_execution_allowed is False
    assert checklist.report_submission_allowed is False
    assert checklist.vulnerability_confirmation_allowed is False
    assert checklist.evidence_gap_count == len(_handoff()["evidence_gaps"])
    assert checklist.checklist_items
    assert checklist.checklist_items[0].checklist_id == "EC-001"
    assert checklist.checklist_items[0].checked is False


def test_evidence_checklist_serializes_safety_metadata() -> None:
    data = export_case_intake_brain_handoff_evidence_checklist(_handoff()).to_dict()

    assert data["kind"] == "case_intake_brain_handoff_evidence_checklist"
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["browser_execution"] is False
    assert data["safety"]["evidence_collection"] is False
    assert data["safety"]["target_mutation"] is False
    assert data["safety"]["report_submission"] is False
    assert data["safety"]["vulnerability_confirmation"] is False


def test_evidence_checklist_blocks_invalid_handoff() -> None:
    checklist = export_case_intake_brain_handoff_evidence_checklist({"kind": "wrong"})

    assert checklist.blocked is True
    assert checklist.handoff_status == "blocked-invalid-case-intake-brain-handoff"
    assert checklist.evidence_gap_count == 0
    assert checklist.checklist_items == ()


def test_evidence_checklist_markdown_groups_by_endpoint() -> None:
    markdown = export_case_intake_brain_handoff_evidence_checklist(_handoff()).to_markdown()

    assert "# Case Intake Brain Evidence Checklist" in markdown
    assert "## Checklist" in markdown
    assert "- [ ] `EC-001`" in markdown
    assert "/api/admin/users/{id}/permissions" in markdown
    assert "No network requests" in markdown
