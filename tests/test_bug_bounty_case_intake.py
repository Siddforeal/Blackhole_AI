from bugintel.core.bug_bounty_case_intake import build_bug_bounty_case_intake_workflow


def test_bug_bounty_case_intake_prioritizes_p1_p2_surfaces():
    workflow = build_bug_bounty_case_intake_workflow(
        """
        GET /api/status
        GET /api/admin/users/{id}/permissions
        POST /api/billing/invoices/{invoiceId}
        /api/files/{id}/download
        """,
        target_name="demo-program",
        top_n=3,
    )

    data = workflow.to_dict()

    assert data["kind"] == "bug_bounty_case_intake_workflow"
    assert data["target_name"] == "demo-program"
    assert data["status"] == "ready-for-human-manual-testing-plan"
    assert data["endpoint_count"] == 4
    assert data["selected_endpoint_count"] == 3
    assert data["lane_counts"]["p1-potential-review"] >= 1
    assert data["lane_counts"]["p2-potential-review"] >= 1
    assert data["top_endpoints"][0]["priority_score"] >= data["top_endpoints"][1]["priority_score"]
    assert data["manual_testing_plan"]
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"


def test_bug_bounty_case_intake_includes_tasks_and_evidence_requirements():
    workflow = build_bug_bounty_case_intake_workflow(
        "GET /api/accounts/{accountId}/users/{userId}/roles",
        top_n=1,
    )

    endpoint = workflow.to_dict()["top_endpoints"][0]

    assert endpoint["p1_p2_lane"] in {"p1-potential-review", "p2-potential-review"}
    assert "authorization-sensitive" in endpoint["categories"]
    assert "object-reference" in endpoint["categories"]
    assert endpoint["investigation_tasks"]
    assert endpoint["evidence_requirements"]
    assert any(requirement["redaction_required"] for requirement in endpoint["evidence_requirements"])
    assert endpoint["planning_only"] is True
    assert endpoint["execution_state"] == "not_executed"


def test_bug_bounty_case_intake_handles_no_endpoints_safely():
    workflow = build_bug_bounty_case_intake_workflow(
        "no useful endpoint material here",
        target_name="empty-case",
    )

    data = workflow.to_dict()

    assert data["status"] == "blocked-no-endpoints"
    assert data["endpoint_count"] == 0
    assert data["selected_endpoint_count"] == 0
    assert data["manual_testing_plan"]
    assert data["safety"]["network_requests"] is False
    assert data["safety"]["tool_execution"] is False
    assert data["safety"]["vulnerability_confirmation"] is False
