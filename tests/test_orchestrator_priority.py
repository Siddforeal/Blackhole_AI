from bugintel.core.orchestrator import create_orchestration_plan


def _endpoint_nodes(root):
    api_node = next(child for child in root.children if child.task_type == "api")
    return api_node.children


def test_orchestrator_includes_endpoint_priorities_in_plan():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
        ],
    )

    assert len(plan.endpoint_priorities) == 3
    assert plan.endpoint_priorities[0].endpoint == "/api/accounts/123/users/{id}/permissions"
    assert plan.endpoint_priorities[0].score >= plan.endpoint_priorities[1].score
    assert any(note == "Scored endpoint priorities: 3." for note in plan.notes)


def test_orchestrator_to_dict_contains_priority_results():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    data = plan.to_dict()

    assert "endpoint_priorities" in data
    assert data["endpoint_priorities"][0]["endpoint"] == "/api/accounts/123/users/{id}/permissions"
    assert data["endpoint_priorities"][0]["planning_only"] is True
    assert data["endpoint_priorities"][0]["execution_state"] == "not_executed"
    assert data["endpoint_priorities"][0]["signals"]


def test_orchestrator_attaches_priority_metadata_to_endpoint_nodes():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    endpoint_node = _endpoint_nodes(plan.root)[0]
    priority = endpoint_node.metadata["priority"]

    assert priority["score"] >= 75
    assert priority["band"] == "critical"
    assert priority["planning_only"] is True
    assert priority["execution_state"] == "not_executed"
    assert priority["signals"]
    assert priority["recommended_next_steps"]
