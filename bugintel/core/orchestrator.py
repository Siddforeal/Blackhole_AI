"""
Orchestrator Planner for Blackhole AI Workbench.

The orchestrator is the planning brain of the workbench.

It does not execute network actions directly. It creates a human-reviewable
research plan, assigns specialist agents, and expands the task tree.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from bugintel.core.agent_registry import AgentSpec, suggest_agents_for_endpoint
from bugintel.core.task_tree import TaskNode, build_endpoint_task_tree
from bugintel.core.endpoint_investigation import expand_endpoint_task_tree
from bugintel.core.endpoint_priority import EndpointPriorityResult, prioritize_endpoints


@dataclass
class AgentAssignment:
    endpoint: str
    agent_name: str
    mode: str
    purpose: str
    capabilities: list[str]
    requires_scope_guard: bool
    requires_human_approval: bool


@dataclass
class OrchestrationPlan:
    target_name: str
    endpoints: list[str]
    root: TaskNode
    assignments: list[AgentAssignment] = field(default_factory=list)
    endpoint_priorities: list[EndpointPriorityResult] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "endpoints": self.endpoints,
            "assignments": [
                {
                    "endpoint": item.endpoint,
                    "agent_name": item.agent_name,
                    "mode": item.mode,
                    "purpose": item.purpose,
                    "capabilities": item.capabilities,
                    "requires_scope_guard": item.requires_scope_guard,
                    "requires_human_approval": item.requires_human_approval,
                }
                for item in self.assignments
            ],
            "endpoint_priorities": [
                item.to_dict()
                for item in self.endpoint_priorities
            ],
            "notes": self.notes,
            "task_tree": self.root.to_dict(),
        }


def create_orchestration_plan(target_name: str, endpoints: list[str]) -> OrchestrationPlan:
    """
    Create a safe multi-agent research plan from discovered endpoints.

    Each endpoint receives specialist agent assignments. Sensitive-looking
    endpoints receive authz_agent planning tasks.
    """
    clean_endpoints = sorted(set(endpoints))
    root = build_endpoint_task_tree(target_name=target_name, endpoints=clean_endpoints)
    investigation_profiles = expand_endpoint_task_tree(root)
    endpoint_priorities = prioritize_endpoints(clean_endpoints)
    _attach_priority_metadata(root, endpoint_priorities)

    assignments: list[AgentAssignment] = []

    for endpoint in clean_endpoints:
        agents = suggest_agents_for_endpoint(endpoint)

        for agent in agents:
            assignments.append(_assignment(endpoint, agent))

    _attach_agent_tasks(root, assignments)

    notes = [
        "This is a planning artifact only.",
        f"Expanded endpoint investigation profiles: {len(investigation_profiles)}.",
        f"Scored endpoint priorities: {len(endpoint_priorities)}.",
        "All active testing must pass through Scope Guard.",
        "Network execution requires explicit human approval.",
        "Findings require manual validation before reporting.",
    ]

    return OrchestrationPlan(
        target_name=target_name,
        endpoints=clean_endpoints,
        root=root,
        assignments=assignments,
        endpoint_priorities=endpoint_priorities,
        notes=notes,
    )


def _assignment(endpoint: str, agent: AgentSpec) -> AgentAssignment:
    return AgentAssignment(
        endpoint=endpoint,
        agent_name=agent.name,
        mode=agent.mode,
        purpose=agent.purpose,
        capabilities=agent.capabilities,
        requires_scope_guard=agent.requires_scope_guard,
        requires_human_approval=agent.requires_human_approval,
    )


def _attach_agent_tasks(root: TaskNode, assignments: list[AgentAssignment]) -> None:
    """
    Add agent-specific child tasks below endpoint nodes.

    This makes the task tree expand from:
    endpoint -> baseline/auth/response-diff

    Into:
    endpoint -> specialist agent plans
    """
    endpoint_to_assignments: dict[str, list[AgentAssignment]] = {}

    for assignment in assignments:
        endpoint_to_assignments.setdefault(assignment.endpoint, []).append(assignment)

    api_node = _find_first_node_by_type(root, "api")

    if api_node is None:
        return

    for endpoint_node in api_node.children:
        endpoint = endpoint_node.metadata.get("endpoint")

        if not endpoint:
            continue

        for assignment in endpoint_to_assignments.get(endpoint, []):
            endpoint_node.add_child(
                title=f"{assignment.agent_name} plan",
                task_type="agent-plan",
                description=assignment.purpose,
                metadata={
                    "endpoint": endpoint,
                    "agent": assignment.agent_name,
                    "mode": assignment.mode,
                    "capabilities": assignment.capabilities,
                    "requires_scope_guard": assignment.requires_scope_guard,
                    "requires_human_approval": assignment.requires_human_approval,
                },
            )



def _attach_priority_metadata(root: TaskNode, priorities: list[EndpointPriorityResult]) -> None:
    """Attach endpoint priority metadata to endpoint nodes."""
    priority_by_endpoint = {item.endpoint: item for item in priorities}
    api_node = _find_first_node_by_type(root, "api")

    if api_node is None:
        return

    for endpoint_node in api_node.children:
        endpoint = endpoint_node.metadata.get("endpoint")

        if not endpoint:
            continue

        priority = priority_by_endpoint.get(endpoint)

        if priority is None:
            continue

        endpoint_node.metadata["priority"] = {
            "score": priority.score,
            "band": priority.band,
            "signals": [signal.to_dict() for signal in priority.signals],
            "recommended_next_steps": list(priority.recommended_next_steps),
            "planning_only": True,
            "execution_state": "not_executed",
        }

def _find_first_node_by_type(node: TaskNode, task_type: str) -> TaskNode | None:
    if node.task_type == task_type:
        return node

    for child in node.children:
        found = _find_first_node_by_type(child, task_type)
        if found is not None:
            return found

    return None
