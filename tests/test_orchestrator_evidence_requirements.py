from bugintel.core.orchestrator import create_orchestration_plan


def _endpoint_nodes(root):
    api_node = next(child for child in root.children if child.task_type == "api")
    return api_node.children


def test_orchestrator_includes_evidence_requirement_plan():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ],
    )

    assert plan.evidence_requirement_plan is not None
    assert plan.evidence_requirement_plan.endpoint_count == 3
    assert any(note == "Planned evidence requirements for endpoints: 3." for note in plan.notes)


def test_orchestrator_to_dict_contains_evidence_requirements():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    data = plan.to_dict()

    assert "evidence_requirement_plan" in data
    evidence = data["evidence_requirement_plan"]

    assert evidence["planning_only"] is True
    assert evidence["execution_state"] == "not_executed"
    assert evidence["endpoint_plans"]
    assert evidence["endpoint_plans"][0]["requirements"]


def test_orchestrator_attaches_evidence_requirement_metadata_to_endpoint_nodes():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    endpoint_node = _endpoint_nodes(plan.root)[0]
    evidence = endpoint_node.metadata["evidence_requirements"]
    requirement_names = {item["name"] for item in evidence["requirements"]}

    assert evidence["planning_only"] is True
    assert evidence["execution_state"] == "not_executed"
    assert "controlled-account-role-matrix" in requirement_names
    assert "authorization-decision-diff" in requirement_names
    assert evidence["recommended_collection_order"]
