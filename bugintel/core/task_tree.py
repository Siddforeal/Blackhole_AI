"""
Task Tree for Blackhole AI Workbench.

Represents security research as a tree of tasks.

The tree helps the future AI orchestrator break a large target into smaller,
auditable steps such as recon, endpoint mining, response comparison, and report
generation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
from uuid import uuid4


class TaskStatus(str, Enum):
    PLANNED = "planned"
    APPROVED = "approved"
    RUNNING = "running"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    INTERESTING = "interesting"
    DISMISSED = "dismissed"


@dataclass
class TaskNode:
    title: str
    task_type: str
    description: str = ""
    status: TaskStatus = TaskStatus.PLANNED
    metadata: dict[str, Any] = field(default_factory=dict)
    children: list["TaskNode"] = field(default_factory=list)
    task_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    def add_child(
        self,
        title: str,
        task_type: str,
        description: str = "",
        status: TaskStatus = TaskStatus.PLANNED,
        metadata: dict[str, Any] | None = None,
    ) -> "TaskNode":
        child = TaskNode(
            title=title,
            task_type=task_type,
            description=description,
            status=status,
            metadata=metadata or {},
        )
        self.children.append(child)
        return child

    def mark(self, status: TaskStatus) -> None:
        self.status = status

    def to_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id,
            "title": self.title,
            "task_type": self.task_type,
            "description": self.description,
            "status": self.status.value,
            "metadata": self.metadata,
            "created_at": self.created_at,
            "children": [child.to_dict() for child in self.children],
        }


def build_endpoint_task_tree(target_name: str, endpoints: list[str]) -> TaskNode:
    """Build a starting task tree from discovered endpoints."""
    root = TaskNode(
        title=f"Security research workspace: {target_name}",
        task_type="workspace",
        description="Root task tree for authorized vulnerability research.",
    )

    web = root.add_child(
        title="Web attack surface",
        task_type="web",
        description="Website, frontend, JavaScript, forms, and browser-observed behavior.",
    )

    api = root.add_child(
        title="API attack surface",
        task_type="api",
        description="Discovered API endpoints and authorization-sensitive routes.",
    )

    root.add_child(
        title="Findings and reports",
        task_type="reporting",
        description="Validated findings, notes, and generated reports.",
    )

    web.add_child(
        title="Review frontend and JavaScript sources",
        task_type="endpoint-mining",
        description="Extract endpoints from JS, HTML, HAR, logs, and Burp exports.",
    )

    for endpoint in sorted(set(endpoints)):
        endpoint_node = api.add_child(
            title=endpoint,
            task_type="endpoint",
            description=f"Investigate endpoint {endpoint}",
            metadata={"endpoint": endpoint},
        )

        endpoint_node.add_child(
            title="Baseline request",
            task_type="http-baseline",
            description="Collect a known-good authorized response.",
            metadata={"endpoint": endpoint},
        )

        endpoint_node.add_child(
            title="Authentication required check",
            task_type="auth-check",
            description="Check whether the endpoint requires authentication.",
            metadata={"endpoint": endpoint},
        )

        endpoint_node.add_child(
            title="Response diff review",
            task_type="response-diff",
            description="Compare baseline, candidate, blocked, and random-ID responses.",
            metadata={"endpoint": endpoint},
        )

    return root


def render_tree(node: TaskNode, indent: str = "") -> str:
    """Render a task tree as plain text."""
    status = node.status.value
    line = f"{indent}- [{status}] {node.title} ({node.task_type})"
    lines = [line]

    for child in node.children:
        lines.append(render_tree(child, indent + "  "))

    return "\n".join(lines)
