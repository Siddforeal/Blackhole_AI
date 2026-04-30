"""
Attack surface grouping for Blackhole AI Workbench.

This module is planning-only. It does not send requests, execute shell commands,
launch browsers, call LLM providers, mutate targets, or bypass authorization.

It groups discovered endpoints into meaningful research buckets so the future
orchestrator can reason about identity, tenant boundaries, files, auth flows,
billing, integrations, secrets, and low-signal routes.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from bugintel.core.endpoint_priority import EndpointPriorityResult, prioritize_endpoints


@dataclass(frozen=True)
class AttackSurfaceGroupSpec:
    name: str
    title: str
    description: str
    priority_hint: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AttackSurfaceGroup:
    spec: AttackSurfaceGroupSpec
    endpoints: list[EndpointPriorityResult] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.endpoints)

    @property
    def max_score(self) -> int:
        if not self.endpoints:
            return 0
        return max(endpoint.score for endpoint in self.endpoints)

    @property
    def average_score(self) -> float:
        if not self.endpoints:
            return 0.0
        return round(sum(endpoint.score for endpoint in self.endpoints) / len(self.endpoints), 2)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.spec.name,
            "title": self.spec.title,
            "description": self.spec.description,
            "priority_hint": self.spec.priority_hint,
            "count": self.count,
            "max_score": self.max_score,
            "average_score": self.average_score,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
        }


@dataclass(frozen=True)
class AttackSurfaceMap:
    endpoint_count: int
    groups: tuple[AttackSurfaceGroup, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_count": self.endpoint_count,
            "group_count": len(self.groups),
            "planning_only": True,
            "execution_state": "not_executed",
            "groups": [group.to_dict() for group in self.groups],
        }


GROUP_SPECS: tuple[AttackSurfaceGroupSpec, ...] = (
    AttackSurfaceGroupSpec(
        name="identity-access",
        title="Identity and access control",
        description="Users, accounts, members, teams, roles, permissions, and access-management surfaces.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="tenant-project-boundary",
        title="Tenant, project, and workspace boundaries",
        description="Projects, tenants, organizations, workspaces, and cross-boundary object references.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="file-surface",
        title="File upload, download, and document surfaces",
        description="Upload, download, attachment, avatar, image, media, and document endpoints.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="auth-flow",
        title="Authentication and session flows",
        description="Login, logout, session, SSO, OAuth, MFA, password reset, and auth callback routes.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="billing-money",
        title="Billing and money movement",
        description="Billing, invoice, payment, subscription, checkout, and plan-management routes.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="integration-webhook",
        title="Integrations, webhooks, and callbacks",
        description="Third-party integrations, webhooks, OAuth callbacks, and connected-app routes.",
        priority_hint="medium-high",
    ),
    AttackSurfaceGroupSpec(
        name="secret-token-key",
        title="Secrets, tokens, and API keys",
        description="Token, secret, key, API-key, and credential-management routes.",
        priority_hint="critical",
    ),
    AttackSurfaceGroupSpec(
        name="object-reference",
        title="Object references and IDOR/BAC candidates",
        description="Routes containing identifiers, UUIDs, numeric IDs, or object-reference patterns.",
        priority_hint="high",
    ),
    AttackSurfaceGroupSpec(
        name="parameter-heavy",
        title="Search, filtering, pagination, and query behavior",
        description="Search, query, filter, sort, page, and limit routes likely to expose response-shape behavior.",
        priority_hint="medium",
    ),
    AttackSurfaceGroupSpec(
        name="low-signal",
        title="Low-signal public/static/status routes",
        description="Health, status, ping, public, static, asset, robots, sitemap, and similar low-signal routes.",
        priority_hint="low",
    ),
    AttackSurfaceGroupSpec(
        name="general-api",
        title="General API surface",
        description="API endpoints that do not match a more specific attack-surface group.",
        priority_hint="medium",
    ),
)


def default_attack_surface_group_specs() -> dict[str, AttackSurfaceGroupSpec]:
    return {spec.name: spec for spec in GROUP_SPECS}


def classify_attack_surface_groups(endpoint: str) -> tuple[str, ...]:
    """Classify an endpoint into one or more attack-surface groups."""
    value = endpoint.lower()
    groups: list[str] = []

    if _contains_any(value, ("account", "accounts", "user", "users", "member", "members", "team", "teams", "role", "roles", "permission", "permissions")):
        groups.append("identity-access")

    if _contains_any(value, ("project", "projects", "tenant", "tenants", "organization", "organizations", "workspace", "workspaces")):
        groups.append("tenant-project-boundary")

    if _contains_any(value, ("upload", "uploads", "file", "files", "download", "downloads", "attachment", "attachments", "avatar", "image", "media", "document", "documents")):
        groups.append("file-surface")

    if _contains_any(value, ("login", "logout", "auth", "oauth", "sso", "session", "sessions", "password", "reset", "mfa", "2fa", "callback")):
        groups.append("auth-flow")

    if _contains_any(value, ("billing", "invoice", "invoices", "payment", "payments", "subscription", "subscriptions", "checkout", "plan", "plans")):
        groups.append("billing-money")

    if _contains_any(value, ("integration", "integrations", "webhook", "webhooks", "callback", "callbacks", "connected-app", "connected_apps")):
        groups.append("integration-webhook")

    if _contains_any(value, ("token", "tokens", "secret", "secrets", "key", "keys", "apikey", "api-key", "credential", "credentials")):
        groups.append("secret-token-key")

    if _looks_like_object_reference(value):
        groups.append("object-reference")

    if _contains_any(value, ("search", "query", "filter", "sort", "page", "limit")):
        groups.append("parameter-heavy")

    if _contains_any(value, ("status", "health", "ping", "favicon", "logo", "asset", "assets", "static", "public", "robots.txt", "sitemap")):
        groups.append("low-signal")

    if not groups:
        groups.append("general-api")

    return tuple(dict.fromkeys(groups))


def build_attack_surface_map(endpoints: list[str]) -> AttackSurfaceMap:
    """Build grouped attack-surface inventory from endpoint strings."""
    priority_results = prioritize_endpoints(endpoints)
    specs = default_attack_surface_group_specs()
    groups_by_name: dict[str, AttackSurfaceGroup] = {
        name: AttackSurfaceGroup(spec=spec)
        for name, spec in specs.items()
    }

    for result in priority_results:
        for group_name in classify_attack_surface_groups(result.endpoint):
            groups_by_name[group_name].endpoints.append(result)

    groups = [
        group
        for group in groups_by_name.values()
        if group.endpoints
    ]

    groups.sort(key=lambda item: (-item.max_score, item.spec.name))

    for group in groups:
        group.endpoints.sort(key=lambda item: (-item.score, item.endpoint))

    return AttackSurfaceMap(
        endpoint_count=len(priority_results),
        groups=tuple(groups),
    )


def _contains_any(value: str, needles: tuple[str, ...]) -> bool:
    return any(needle in value for needle in needles)


def _looks_like_object_reference(value: str) -> bool:
    hints = (
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

    if any(hint in value for hint in hints):
        return True

    parts = [part for part in value.replace("?", "/").replace("&", "/").split("/") if part]

    for part in parts:
        clean = part.strip("{}:<>").lower()

        if clean.isdigit() and len(clean) >= 2:
            return True

        hex_chars = clean.replace("-", "")
        if len(hex_chars) in {24, 32, 36} and all(char in "0123456789abcdef" for char in hex_chars):
            return True

    return False
