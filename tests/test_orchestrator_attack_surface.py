from bugintel.core.orchestrator import create_orchestration_plan


def _endpoint_nodes(root):
    api_node = next(child for child in root.children if child.task_type == "api")
    return api_node.children


def test_orchestrator_includes_attack_surface_map():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=[
            "/api/status",
            "/api/accounts/123/users/{id}/permissions",
            "/api/files/{id}/download",
            "/api/integrations/webhooks",
        ],
    )

    assert plan.attack_surface_map is not None
    assert plan.attack_surface_map.endpoint_count == 4

    group_names = [group.spec.name for group in plan.attack_surface_map.groups]

    assert "identity-access" in group_names
    assert "file-surface" in group_names
    assert "integration-webhook" in group_names
    assert "low-signal" in group_names
    assert any(note == "Grouped attack surfaces: 5." for note in plan.notes)


def test_orchestrator_to_dict_contains_attack_surface_map():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    data = plan.to_dict()

    assert "attack_surface_map" in data
    assert data["attack_surface_map"]["planning_only"] is True
    assert data["attack_surface_map"]["execution_state"] == "not_executed"
    assert data["attack_surface_map"]["groups"]


def test_orchestrator_attaches_attack_surface_metadata_to_endpoint_nodes():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}/permissions"],
    )

    endpoint_node = _endpoint_nodes(plan.root)[0]
    groups = endpoint_node.metadata["attack_surface_groups"]

    assert groups["planning_only"] is True
    assert groups["execution_state"] == "not_executed"
    assert "identity-access" in groups["groups"]
    assert "object-reference" in groups["groups"]
