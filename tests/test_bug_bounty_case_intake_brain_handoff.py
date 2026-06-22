from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow
from bugintel.core.bug_bounty_case_intake_brain_handoff import build_case_intake_brain_handoff


def test_case_intake_brain_handoff_builds_focus_context():
    intake = build_bug_bounty_case_intake_workflow(
        """
        GET /api/status
        GET /api/admin/users/{id}/permissions
        GET /api/files/{id}/download
        """,
        target_name="demo-program",
        top_n=3,
    ).to_dict()

    handoff = build_case_intake_brain_handoff(intake)
    data = handoff.to_dict()

    assert data["kind"] == "case_intake_brain_handoff"
    assert data["source_kind"] == "bug_bounty_case_intake_workflow"
    assert data["target_name"] == "demo-program"
    assert data["status"] == "ready-for-brain-case-context"
    assert data["focus_endpoint_count"] == 2
    assert data["deferred_endpoint_count"] == 1
    assert data["focus_endpoints"][0]["endpoint"] == "/api/admin/users/{id}/permissions"
    assert data["focus_endpoints"][0]["why_focus"]
    assert data["evidence_gaps"]
    assert data["brain_questions"]
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"


def test_case_intake_brain_handoff_blocks_invalid_kind():
    handoff = build_case_intake_brain_handoff({"kind": "wrong"})
    data = handoff.to_dict()

    assert data["status"] == "blocked-invalid-case-intake-workflow"
    assert data["focus_endpoint_count"] == 0
    assert data["evidence_gaps"][0]["gap_type"] == "blocked-input"


def test_case_intake_brain_handoff_blocks_unsafe_source():
    intake = build_bug_bounty_case_intake_workflow(
        "GET /api/admin/users/{id}/permissions",
        target_name="unsafe-demo",
    ).to_dict()
    intake["safety"]["network_requests"] = True

    handoff = build_case_intake_brain_handoff(intake)
    data = handoff.to_dict()

    assert data["status"] == "blocked-unsafe-case-intake-workflow"
    assert data["focus_endpoint_count"] == 0
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False
