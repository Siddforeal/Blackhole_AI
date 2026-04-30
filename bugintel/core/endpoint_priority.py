"""
Endpoint priority scoring for Blackhole AI Workbench.

This module is planning-only. It does not send requests, execute shell commands,
launch browsers, call LLM providers, mutate targets, or bypass authorization.

It ranks discovered endpoints so the future orchestrator can focus human review
and specialist-agent planning on the most security-sensitive attack surfaces.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.endpoint_investigation import build_endpoint_investigation_profile


@dataclass(frozen=True)
class EndpointPrioritySignal:
    name: str
    points: int
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EndpointPriorityResult:
    endpoint: str
    normalized_path: str
    score: int
    band: str
    categories: tuple[str, ...]
    signals: tuple[EndpointPrioritySignal, ...]
    recommended_next_steps: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "normalized_path": self.normalized_path,
            "score": self.score,
            "band": self.band,
            "categories": list(self.categories),
            "signals": [signal.to_dict() for signal in self.signals],
            "recommended_next_steps": list(self.recommended_next_steps),
            "planning_only": True,
            "execution_state": "not_executed",
        }


def score_endpoint(endpoint: str) -> EndpointPriorityResult:
    """Score one endpoint using static, planning-only heuristics."""
    profile = build_endpoint_investigation_profile(endpoint)
    value = endpoint.lower()
    signals: list[EndpointPrioritySignal] = []

    _add_category_signals(profile.categories, signals)
    _add_keyword_signals(value, signals)
    _add_deprioritization_signals(value, signals)

    raw_score = sum(signal.points for signal in signals)
    score = max(0, min(100, raw_score))
    band = _score_band(score)

    return EndpointPriorityResult(
        endpoint=endpoint,
        normalized_path=profile.normalized_path,
        score=score,
        band=band,
        categories=profile.categories,
        signals=tuple(signals),
        recommended_next_steps=_recommended_next_steps(profile.categories, score),
    )


def prioritize_endpoints(endpoints: list[str]) -> list[EndpointPriorityResult]:
    """Score and sort endpoints from highest to lowest research priority."""
    unique_endpoints = sorted(set(endpoints))
    results = [score_endpoint(endpoint) for endpoint in unique_endpoints]
    return sorted(results, key=lambda item: (-item.score, item.endpoint))


def _add_category_signals(
    categories: tuple[str, ...],
    signals: list[EndpointPrioritySignal],
) -> None:
    category_weights = {
        "api-endpoint": (5, "API-like endpoint discovered."),
        "authorization-sensitive": (30, "Endpoint appears related to users, accounts, permissions, billing, integrations, secrets, or other sensitive resources."),
        "object-reference": (25, "Endpoint appears to contain an object identifier or object reference pattern."),
        "file-surface": (25, "Endpoint appears related to file upload, download, attachments, media, or document access."),
        "auth-flow": (20, "Endpoint appears related to authentication, sessions, SSO, OAuth, MFA, passwords, or logout behavior."),
        "parameter-heavy": (10, "Endpoint appears likely to support filtering, search, pagination, sorting, or query-driven behavior."),
    }

    for category in categories:
        if category in category_weights:
            points, reason = category_weights[category]
            signals.append(
                EndpointPrioritySignal(
                    name=f"category:{category}",
                    points=points,
                    reason=reason,
                )
            )


def _add_keyword_signals(value: str, signals: list[EndpointPrioritySignal]) -> None:
    keyword_groups = [
        (
            "admin-control-plane",
            25,
            ("admin", "administrator", "superuser"),
            "Administrative/control-plane endpoint.",
        ),
        (
            "identity-access",
            20,
            ("account", "accounts", "user", "users", "member", "members", "team", "teams", "role", "roles", "permission", "permissions"),
            "Identity, membership, roles, or permissions endpoint.",
        ),
        (
            "tenant-project-boundary",
            20,
            ("project", "projects", "tenant", "tenants", "organization", "organizations", "workspace", "workspaces"),
            "Tenant, project, workspace, or organization boundary endpoint.",
        ),
        (
            "billing-money",
            20,
            ("billing", "invoice", "invoices", "payment", "payments", "subscription", "checkout", "plan"),
            "Billing, money, subscription, invoice, or checkout endpoint.",
        ),
        (
            "integration-webhook",
            18,
            ("integration", "integrations", "webhook", "webhooks", "oauth", "callback"),
            "Integration, webhook, OAuth, or callback endpoint.",
        ),
        (
            "export-download",
            15,
            ("export", "exports", "download", "downloads", "report", "reports"),
            "Export, report, or download endpoint.",
        ),
        (
            "secret-token-key",
            30,
            ("token", "tokens", "secret", "secrets", "key", "keys", "apikey", "api-key"),
            "Token, secret, key, or API-key endpoint.",
        ),
        (
            "write-like-action",
            15,
            ("create", "update", "delete", "remove", "assign", "invite", "migrate", "transfer", "swap", "grant", "revoke"),
            "Endpoint name suggests a state-changing or high-impact workflow.",
        ),
    ]

    for name, points, keywords, reason in keyword_groups:
        if any(keyword in value for keyword in keywords):
            signals.append(
                EndpointPrioritySignal(
                    name=f"keyword:{name}",
                    points=points,
                    reason=reason,
                )
            )


def _add_deprioritization_signals(value: str, signals: list[EndpointPrioritySignal]) -> None:
    low_signal_keywords = (
        "status",
        "health",
        "ping",
        "favicon",
        "logo",
        "asset",
        "assets",
        "static",
        "public",
        "robots.txt",
        "sitemap",
    )

    if any(keyword in value for keyword in low_signal_keywords):
        signals.append(
            EndpointPrioritySignal(
                name="deprioritize:low-signal-route",
                points=-15,
                reason="Endpoint appears to be a status, public, static, or low-signal route.",
            )
        )


def _score_band(score: int) -> str:
    if score >= 75:
        return "critical"
    if score >= 50:
        return "high"
    if score >= 25:
        return "medium"
    if score > 0:
        return "low"
    return "info"


def _recommended_next_steps(categories: tuple[str, ...], score: int) -> tuple[str, ...]:
    steps: list[str] = [
        "Review endpoint context from JS, HAR, browser evidence, or source before active testing.",
    ]

    if "authorization-sensitive" in categories:
        steps.append("Prepare owned-vs-foreign-vs-random authorization boundary checks with controlled test accounts.")

    if "object-reference" in categories:
        steps.append("Map identifier sources and compare baseline, foreign, random, and malformed object references.")

    if "file-surface" in categories:
        steps.append("Plan non-destructive file access checks with redacted evidence and no real user data exposure.")

    if "auth-flow" in categories:
        steps.append("Review session, redirect, CSRF, OAuth/SSO, MFA, and logout behavior.")

    if "parameter-heavy" in categories:
        steps.append("Plan low-volume parameter behavior checks for filters, pagination, sorting, and response-shape changes.")

    if score >= 50:
        steps.append("Create an evidence folder and prioritize manual validation before broad testing.")

    return tuple(steps)
