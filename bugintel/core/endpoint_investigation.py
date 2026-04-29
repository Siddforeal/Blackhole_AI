"""
Endpoint investigation task expansion for Blackhole AI Workbench.

This module is planning-only. It does not run curl, launch browsers, call LLMs,
make network requests, mutate targets, or bypass authorization. It expands a
single discovered endpoint into a safe, human-reviewable investigation tree.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any
from urllib.parse import urlparse

from bugintel.core.task_tree import TaskNode


SENSITIVE_KEYWORDS: tuple[str, ...] = (
    "admin",
    "account",
    "accounts",
    "user",
    "users",
    "member",
    "members",
    "team",
    "teams",
    "project",
    "projects",
    "role",
    "roles",
    "permission",
    "permissions",
    "billing",
    "invoice",
    "invoices",
    "payment",
    "payments",
    "export",
    "exports",
    "integration",
    "integrations",
    "webhook",
    "webhooks",
    "token",
    "tokens",
    "key",
    "keys",
    "secret",
    "secrets",
)

OBJECT_ID_HINTS: tuple[str, ...] = (
    "{id}",
    ":id",
    "<id>",
    "uuid",
    "guid",
    "accountid",
    "account_id",
    "projectid",
    "project_id",
    "userid",
    "user_id",
    "teamid",
    "team_id",
)

FILE_KEYWORDS: tuple[str, ...] = (
    "upload",
    "uploads",
    "file",
    "files",
    "attachment",
    "attachments",
    "avatar",
    "image",
    "media",
    "document",
)

AUTH_KEYWORDS: tuple[str, ...] = (
    "login",
    "logout",
    "auth",
    "oauth",
    "sso",
    "session",
    "sessions",
    "password",
    "reset",
    "mfa",
    "2fa",
)


@dataclass(frozen=True)
class EndpointInvestigationTask:
    """A planning-only task template for one endpoint."""

    title: str
    task_type: str
    description: str
    priority: str
    agent_hint: str
    requires_scope_guard: bool = True
    requires_human_approval: bool = True
    metadata: dict[str, Any] | None = None

    def to_metadata(self, endpoint: str) -> dict[str, Any]:
        data = asdict(self)
        data.pop("metadata")
        data["endpoint"] = endpoint
        data["planning_only"] = True
        data["execution_state"] = "not_executed"
        if self.metadata:
            data.update(self.metadata)
        return data


@dataclass(frozen=True)
class EndpointInvestigationProfile:
    endpoint: str
    normalized_path: str
    categories: tuple[str, ...]
    tasks: tuple[EndpointInvestigationTask, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "normalized_path": self.normalized_path,
            "categories": list(self.categories),
            "tasks": [
                {
                    "title": task.title,
                    "task_type": task.task_type,
                    "description": task.description,
                    "priority": task.priority,
                    "agent_hint": task.agent_hint,
                    "requires_scope_guard": task.requires_scope_guard,
                    "requires_human_approval": task.requires_human_approval,
                    "metadata": task.metadata or {},
                }
                for task in self.tasks
            ],
        }


def classify_endpoint(endpoint: str) -> tuple[str, ...]:
    """Classify an endpoint into high-level investigation categories."""
    value = endpoint.lower()
    categories: list[str] = ["api-endpoint"]

    if any(keyword in value for keyword in SENSITIVE_KEYWORDS):
        categories.append("authorization-sensitive")

    if any(hint in value for hint in OBJECT_ID_HINTS) or _looks_like_numeric_or_uuid_path(value):
        categories.append("object-reference")

    if any(keyword in value for keyword in FILE_KEYWORDS):
        categories.append("file-surface")

    if any(keyword in value for keyword in AUTH_KEYWORDS):
        categories.append("auth-flow")

    if any(keyword in value for keyword in ("search", "query", "filter", "sort", "page", "limit")):
        categories.append("parameter-heavy")

    return tuple(dict.fromkeys(categories))


def build_endpoint_investigation_profile(endpoint: str) -> EndpointInvestigationProfile:
    """Build a safe task profile for a discovered endpoint."""
    normalized_path = _normalize_endpoint_path(endpoint)
    categories = classify_endpoint(endpoint)
    tasks = list(_base_tasks())

    if "authorization-sensitive" in categories:
        tasks.extend(_authorization_tasks())

    if "object-reference" in categories:
        tasks.extend(_object_reference_tasks())

    if "file-surface" in categories:
        tasks.extend(_file_surface_tasks())

    if "auth-flow" in categories:
        tasks.extend(_auth_flow_tasks())

    if "parameter-heavy" in categories:
        tasks.extend(_parameter_tasks())

    tasks.append(
        EndpointInvestigationTask(
            title="Evidence and report checklist",
            task_type="evidence-checklist",
            description="Track required screenshots, request/response samples, redactions, and report impact notes.",
            priority="medium",
            agent_hint="report_agent",
            requires_scope_guard=False,
            requires_human_approval=False,
        )
    )

    return EndpointInvestigationProfile(
        endpoint=endpoint,
        normalized_path=normalized_path,
        categories=categories,
        tasks=tuple(tasks),
    )


def expand_endpoint_node_with_investigation_tasks(endpoint_node: TaskNode) -> EndpointInvestigationProfile:
    """
    Attach investigation tasks below one endpoint node.

    Existing child task types are preserved and not duplicated.
    """
    endpoint = str(endpoint_node.metadata.get("endpoint") or endpoint_node.title)
    profile = build_endpoint_investigation_profile(endpoint)
    existing_types = {child.task_type for child in endpoint_node.children}

    endpoint_node.metadata["investigation_profile"] = {
        "categories": list(profile.categories),
        "normalized_path": profile.normalized_path,
        "planning_only": True,
    }

    for task in profile.tasks:
        if task.task_type in existing_types:
            continue

        endpoint_node.add_child(
            title=task.title,
            task_type=task.task_type,
            description=task.description,
            metadata=task.to_metadata(endpoint),
        )
        existing_types.add(task.task_type)

    return profile


def expand_endpoint_task_tree(root: TaskNode) -> list[EndpointInvestigationProfile]:
    """Attach investigation tasks to every endpoint node in a task tree."""
    profiles: list[EndpointInvestigationProfile] = []

    for node in _walk(root):
        if node.task_type == "endpoint":
            profiles.append(expand_endpoint_node_with_investigation_tasks(node))

    return profiles


def _base_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="Method policy review",
            task_type="method-policy-review",
            description="Plan safe checks for allowed and rejected HTTP methods without mutating data.",
            priority="medium",
            agent_hint="endpoint_agent",
        ),
        EndpointInvestigationTask(
            title="Parameter and schema review",
            task_type="parameter-schema-review",
            description="Identify path, query, header, and body parameters that need controlled validation.",
            priority="medium",
            agent_hint="endpoint_agent",
        ),
        EndpointInvestigationTask(
            title="Error and oracle review",
            task_type="error-oracle-review",
            description="Compare error shapes for baseline, unauthorized, random, and malformed cases.",
            priority="medium",
            agent_hint="authz_agent",
        ),
    )


def _authorization_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="Authorization boundary plan",
            task_type="authorization-boundary-plan",
            description="Plan account, role, team, and project boundary checks using only authorized test identities.",
            priority="high",
            agent_hint="authz_agent",
            metadata={"requires_multiple_test_identities": True},
        ),
        EndpointInvestigationTask(
            title="Tenant isolation review",
            task_type="tenant-isolation-review",
            description="Plan same-role cross-tenant checks and blocked-vs-random response comparisons.",
            priority="high",
            agent_hint="authz_agent",
            metadata={"test_style": "baseline_candidate_random_diff"},
        ),
    )


def _object_reference_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="Object reference mutation plan",
            task_type="object-reference-mutation-plan",
            description="Plan safe owned-vs-foreign-vs-random identifier checks for IDOR/BAC validation.",
            priority="high",
            agent_hint="authz_agent",
            metadata={"test_style": "owned_foreign_random"},
        ),
        EndpointInvestigationTask(
            title="Identifier source mapping",
            task_type="identifier-source-mapping",
            description="Track where object identifiers originate: UI, JS, HAR, API response, mobile config, or source.",
            priority="medium",
            agent_hint="source_agent",
            metadata={"planning_only": True},
        ),
    )


def _file_surface_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="File surface safety review",
            task_type="file-surface-safety-review",
            description="Plan non-destructive upload/download checks, content-type handling, and access-control validation.",
            priority="high",
            agent_hint="source_agent",
            metadata={"avoid_real_user_files": True},
        ),
        EndpointInvestigationTask(
            title="Download authorization review",
            task_type="download-authorization-review",
            description="Plan owned-vs-foreign file download checks with redacted evidence and no sensitive data exposure.",
            priority="high",
            agent_hint="authz_agent",
            metadata={"requires_redaction": True},
        ),
    )


def _auth_flow_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="Session and auth-flow review",
            task_type="session-auth-flow-review",
            description="Plan checks for session state, token handling, redirects, CSRF boundaries, and logout behavior.",
            priority="high",
            agent_hint="browser_agent",
            metadata={"focus": "auth_flow"},
        ),
    )


def _parameter_tasks() -> tuple[EndpointInvestigationTask, ...]:
    return (
        EndpointInvestigationTask(
            title="Parameter behavior review",
            task_type="parameter-behavior-review",
            description="Plan safe query/body parameter checks for filtering, pagination, sorting, and response-shape changes.",
            priority="medium",
            agent_hint="endpoint_agent",
            metadata={"avoid_high_volume_fuzzing": True},
        ),
    )


def _walk(node: TaskNode) -> list[TaskNode]:
    nodes = [node]
    for child in node.children:
        nodes.extend(_walk(child))
    return nodes


def _normalize_endpoint_path(endpoint: str) -> str:
    parsed = urlparse(endpoint)
    if parsed.scheme and parsed.netloc:
        return parsed.path or "/"
    return endpoint.split("?", 1)[0] or "/"


def _looks_like_numeric_or_uuid_path(value: str) -> bool:
    parts = [part for part in value.replace("?", "/").replace("&", "/").split("/") if part]

    for part in parts:
        clean = part.strip("{}:<>").lower()
        if clean.isdigit() and len(clean) >= 2:
            return True

        hex_chars = clean.replace("-", "")
        if len(hex_chars) in {24, 32, 36} and all(char in "0123456789abcdef" for char in hex_chars):
            return True

    return False
