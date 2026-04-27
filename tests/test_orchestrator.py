from bugintel.core.orchestrator import create_orchestration_plan
from bugintel.core.task_tree import render_tree


def test_orchestrator_creates_plan_with_assignments():
    plan = create_orchestration_plan(
        target_name="demo-lab",
        endpoints=[
            "/api/users/me",
            "/api/files/upload",
        ],
    )

    assert plan.target_name == "demo-lab"
    assert len(plan.assignments) >= 4
    assert "All active testing must pass through Scope Guard." in plan.notes

    names = [item.agent_name for item in plan.assignments]

    assert "endpoint_agent" in names
    assert "curl_agent" in names
    assert "authz_agent" in names
    assert "source_agent" in names


def test_orchestrator_expands_task_tree_with_agent_plans():
    plan = create_orchestration_plan(
        target_name="demo-lab",
        endpoints=[
            "/api/accounts/123/users",
        ],
    )

    rendered = render_tree(plan.root)

    assert "/api/accounts/123/users" in rendered
    assert "endpoint_agent plan" in rendered
    assert "curl_agent plan" in rendered
    assert "authz_agent plan" in rendered


def test_orchestration_plan_serializes_to_dict():
    plan = create_orchestration_plan(
        target_name="demo-lab",
        endpoints=[
            "/api/projects/123",
        ],
    )

    data = plan.to_dict()

    assert data["target_name"] == "demo-lab"
    assert data["endpoints"] == ["/api/projects/123"]
    assert len(data["assignments"]) >= 3
    assert "task_tree" in data
