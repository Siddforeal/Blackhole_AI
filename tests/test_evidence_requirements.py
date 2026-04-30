from bugintel.core.evidence_requirements import (
    build_endpoint_evidence_plan,
    build_evidence_requirement_plan,
)


def test_identity_object_endpoint_gets_authz_and_object_evidence_requirements():
    plan = build_endpoint_evidence_plan("/api/accounts/123/users/{id}/permissions")
    names = {requirement.name for requirement in plan.requirements}

    assert plan.priority_score >= 75
    assert plan.priority_band == "critical"
    assert "identity-access" in plan.attack_surface_groups
    assert "object-reference" in plan.attack_surface_groups
    assert "controlled-account-role-matrix" in names
    assert "authorization-decision-diff" in names
    assert "identifier-source-map" in names
    assert "owned-foreign-random-response-matrix" in names


def test_file_surface_endpoint_gets_safe_file_requirements():
    plan = build_endpoint_evidence_plan("/api/files/{id}/download")
    names = {requirement.name for requirement in plan.requirements}

    assert "file-surface" in plan.attack_surface_groups
    assert "safe-test-file-manifest" in names
    assert "file-access-control-evidence" in names


def test_integration_endpoint_gets_secret_redaction_requirement():
    plan = build_endpoint_evidence_plan("/api/integrations/webhooks")
    names = {requirement.name for requirement in plan.requirements}

    assert "integration-webhook" in plan.attack_surface_groups
    assert "integration-secret-redaction-proof" in names
    assert "integration-boundary-evidence" in names


def test_low_signal_endpoint_gets_deprioritization_note():
    plan = build_endpoint_evidence_plan("/api/status")
    names = {requirement.name for requirement in plan.requirements}

    assert "low-signal" in plan.attack_surface_groups
    assert "low-signal-deprioritization-note" in names


def test_evidence_requirement_plan_sorts_by_priority():
    plan = build_evidence_requirement_plan(
        [
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ]
    )

    data = plan.to_dict()

    assert data["endpoint_count"] == 3
    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["endpoint_plans"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoint_plans"][0]["priority_score"] >= data["endpoint_plans"][1]["priority_score"]


def test_requirement_to_dict_contains_safety_metadata():
    plan = build_endpoint_evidence_plan("/api/projects/{projectId}/exports")
    data = plan.to_dict()

    assert data["planning_only"] is True
    assert data["execution_state"] == "not_executed"
    assert data["requirements"]
    assert data["recommended_collection_order"]
    assert all("redaction_required" in item for item in data["requirements"])
    assert all("human_approval_required" in item for item in data["requirements"])
