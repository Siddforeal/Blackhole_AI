from bugintel.core.endpoint_investigation import (
    build_endpoint_investigation_profile,
    classify_endpoint,
    expand_endpoint_task_tree,
)
from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.task_tree import build_endpoint_task_tree


def _flatten_types(node):
    values = [node.task_type]
    for child in node.children:
        values.extend(_flatten_types(child))
    return values


def test_classify_endpoint_marks_sensitive_object_reference():
    categories = classify_endpoint("/api/accounts/123/users/{id}/permissions")

    assert "api-endpoint" in categories
    assert "authorization-sensitive" in categories
    assert "object-reference" in categories


def test_build_endpoint_investigation_profile_adds_authz_and_object_tasks():
    profile = build_endpoint_investigation_profile("/api/projects/{projectId}/exports")

    task_types = {task.task_type for task in profile.tasks}

    assert "authorization-boundary-plan" in task_types
    assert "tenant-isolation-review" in task_types
    assert "object-reference-mutation-plan" in task_types
    assert "evidence-checklist" in task_types
    assert profile.normalized_path == "/api/projects/{projectId}/exports"


def test_file_endpoint_gets_file_surface_tasks():
    profile = build_endpoint_investigation_profile("/api/files/{id}/download")

    task_types = {task.task_type for task in profile.tasks}

    assert "file-surface-safety-review" in task_types
    assert "download-authorization-review" in task_types


def test_expand_endpoint_task_tree_attaches_planning_only_metadata():
    root = build_endpoint_task_tree(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}"],
    )

    profiles = expand_endpoint_task_tree(root)
    task_types = _flatten_types(root)

    assert len(profiles) == 1
    assert "authorization-boundary-plan" in task_types
    assert "object-reference-mutation-plan" in task_types

    endpoint_node = root.children[1].children[0]
    assert endpoint_node.metadata["investigation_profile"]["planning_only"] is True

    authz_node = next(
        child for child in endpoint_node.children
        if child.task_type == "authorization-boundary-plan"
    )
    assert authz_node.metadata["planning_only"] is True
    assert authz_node.metadata["execution_state"] == "not_executed"


def test_orchestrator_includes_endpoint_investigation_expansion():
    plan = create_orchestration_plan(
        target_name="demo",
        endpoints=["/api/accounts/123/users/{id}"],
    )
    data = plan.to_dict()
    task_types = _flatten_types(plan.root)

    assert "authorization-boundary-plan" in task_types
    assert "object-reference-mutation-plan" in task_types
    assert any("Expanded endpoint investigation profiles: 1." == note for note in data["notes"])
