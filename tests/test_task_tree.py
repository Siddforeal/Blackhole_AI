from bugintel.core.task_tree import TaskNode, TaskStatus, build_endpoint_task_tree, render_tree


def test_task_node_can_add_child_and_serialize():
    root = TaskNode(title="Root", task_type="workspace")
    child = root.add_child(title="Mine endpoints", task_type="endpoint-mining")

    child.mark(TaskStatus.COMPLETED)

    data = root.to_dict()

    assert data["title"] == "Root"
    assert data["children"][0]["title"] == "Mine endpoints"
    assert data["children"][0]["status"] == "completed"


def test_build_endpoint_task_tree_creates_endpoint_children():
    root = build_endpoint_task_tree(
        target_name="demo-lab",
        endpoints=[
            "/api/users/me",
            "/api/projects/123",
        ],
    )

    rendered = render_tree(root)

    assert "Security research workspace: demo-lab" in rendered
    assert "/api/users/me" in rendered
    assert "/api/projects/123" in rendered
    assert "Baseline request" in rendered
    assert "Authentication required check" in rendered
    assert "Response diff review" in rendered
