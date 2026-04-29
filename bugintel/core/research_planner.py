"""
Deterministic research planning models for BugIntel AI Workbench.

This module does not call an LLM, does not execute commands, and does not
perform network activity. It only converts existing evidence into structured
research hypotheses and recommendations.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from typing import Any
from urllib.parse import urlparse


@dataclass(frozen=True)
class EvidenceReference:
    """Reference to an existing evidence item."""

    evidence_type: str
    source: str
    locator: str = ""
    summary: str = ""
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchHypothesis:
    """A testable security research hypothesis."""

    title: str
    category: str
    rationale: str
    confidence: str = "medium"
    evidence: tuple[EvidenceReference, ...] = ()
    suggested_tests: tuple[str, ...] = ()
    tags: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "category": self.category,
            "rationale": self.rationale,
            "confidence": self.confidence,
            "evidence": [ref.to_dict() for ref in self.evidence],
            "suggested_tests": list(self.suggested_tests),
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class ResearchRecommendation:
    """A recommended next research action."""

    priority: int
    title: str
    reason: str
    next_actions: tuple[str, ...] = ()
    related_hypotheses: tuple[str, ...] = ()
    safety_notes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "priority": self.priority,
            "title": self.title,
            "reason": self.reason,
            "next_actions": list(self.next_actions),
            "related_hypotheses": list(self.related_hypotheses),
            "safety_notes": list(self.safety_notes),
        }


@dataclass(frozen=True)
class ResearchPlan:
    """Structured research plan built from existing evidence."""

    target_name: str
    source_evidence_type: str
    generated_by: str = "deterministic"
    hypotheses: tuple[ResearchHypothesis, ...] = ()
    recommendations: tuple[ResearchRecommendation, ...] = ()
    safety_notes: tuple[str, ...] = (
        "Review all recommendations manually before testing.",
        "Only test assets and accounts that are explicitly authorized.",
        "Use Scope Guard before generating or executing requests.",
    )

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "source_evidence_type": self.source_evidence_type,
            "generated_by": self.generated_by,
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "recommendations": [recommendation.to_dict() for recommendation in self.recommendations],
            "safety_notes": list(self.safety_notes),
        }


def _event_url(event: dict[str, Any]) -> str:
    return str(event.get("url") or event.get("request", {}).get("url") or "")


def _event_method(event: dict[str, Any]) -> str:
    return str(event.get("method") or event.get("request", {}).get("method") or "GET").upper()


def _event_status(event: dict[str, Any]) -> int | None:
    status = event.get("status_code", event.get("status"))

    if status is None:
        return None

    try:
        return int(status)
    except (TypeError, ValueError):
        return None


def _looks_like_api_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path.lower()

    return (
        "/api/" in path
        or path.startswith("/api")
        or "/graphql" in path
        or path.endswith(".json")
        or "/v1/" in path
        or "/v2/" in path
        or "/admin" in path
    )


def _looks_like_id_bearing_url(url: str) -> bool:
    parsed = urlparse(url)
    path = parsed.path

    return bool(
        re.search(r"/[0-9]{3,}(?:/|$)", path)
        or re.search(
            r"/[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}(?:/|$)",
            path,
        )
    )


def _is_sensitive_surface_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    sensitive_terms = (
        "admin",
        "account",
        "user",
        "team",
        "role",
        "permission",
        "invite",
        "token",
        "key",
        "secret",
        "export",
        "webhook",
        "billing",
    )

    return any(term in path for term in sensitive_terms)


def _has_browser_evidence_shape(value: dict[str, Any]) -> bool:
    return any(
        key in value
        for key in (
            "network_events",
            "screenshots",
            "html_snapshots",
            "execution_output",
        )
    )


def normalize_browser_evidence(value: dict[str, Any]) -> dict[str, Any]:
    """
    Normalize raw capture-result JSON or saved evidence-store JSON.

    Supported inputs include:
    - Raw browser capture result JSON.
    - Saved evidence JSON where browser fields are top-level.
    - Saved evidence JSON where browser fields are nested under payload/data/evidence.
    """
    if _has_browser_evidence_shape(value):
        return value

    for key in ("payload", "data", "evidence", "browser_capture", "capture_result"):
        nested = value.get(key)

        if isinstance(nested, dict) and _has_browser_evidence_shape(nested):
            normalized = dict(nested)

            for metadata_key in (
                "target_name",
                "task_name",
                "evidence_type",
                "browser",
                "start_url",
                "captured_at",
            ):
                if metadata_key not in normalized and metadata_key in value:
                    normalized[metadata_key] = value[metadata_key]

            return normalized

    return value


def build_research_plan_from_browser_evidence(
    evidence: dict[str, Any],
) -> ResearchPlan:
    """Build a deterministic research plan from browser evidence JSON."""
    evidence = normalize_browser_evidence(evidence)

    target_name = str(evidence.get("target_name") or "unknown-target")
    evidence_type = str(evidence.get("evidence_type") or "browser")
    task_name = str(evidence.get("task_name") or "browser evidence")

    network_events = [
        event
        for event in evidence.get("network_events", [])
        if isinstance(event, dict)
    ]

    hypotheses: list[ResearchHypothesis] = []
    recommendations: list[ResearchRecommendation] = []

    api_events = [
        event
        for event in network_events
        if _looks_like_api_url(_event_url(event))
    ]

    if api_events:
        ref = EvidenceReference(
            evidence_type=evidence_type,
            source=task_name,
            locator="network_events",
            summary=f"{len(api_events)} browser-observed API-like request(s).",
            tags=("browser", "api"),
        )
        hypotheses.append(
            ResearchHypothesis(
                title="Browser-observed API surface may contain testable authorization boundaries",
                category="api-authorization",
                rationale="Browser evidence contains API-like requests that can be reviewed for authentication, authorization, and object-level access-control behavior.",
                confidence="medium",
                evidence=(ref,),
                suggested_tests=(
                    "Group API requests by host, path, method, status code, and authenticated context.",
                    "For authorized targets, compare own-object, foreign-object, random-object, and unauthenticated responses.",
                    "Prioritize read-only checks before any mutation testing.",
                ),
                tags=("api", "bac", "idor"),
            )
        )

    id_events = [
        event
        for event in api_events
        if _looks_like_id_bearing_url(_event_url(event))
    ]

    if id_events:
        ref = EvidenceReference(
            evidence_type=evidence_type,
            source=task_name,
            locator="network_events",
            summary=f"{len(id_events)} API-like request(s) include path identifiers.",
            tags=("browser", "identifier"),
        )
        hypotheses.append(
            ResearchHypothesis(
                title="Identifier-bearing API routes may require object-level authorization review",
                category="object-authorization",
                rationale="One or more browser-observed API paths include numeric or UUID-like identifiers, which often map to projects, accounts, users, dashboards, exports, or similar objects.",
                confidence="medium",
                evidence=(ref,),
                suggested_tests=(
                    "Confirm whether each identifier belongs to the current authorized account or object.",
                    "Use a second authorized test account when the program permits cross-account checks.",
                    "Stop when foreign, random, and unauthenticated controls are consistently blocked.",
                ),
                tags=("idor", "bac", "object-id"),
            )
        )

    sensitive_events = [
        event
        for event in api_events
        if _is_sensitive_surface_url(_event_url(event))
    ]

    if sensitive_events:
        ref = EvidenceReference(
            evidence_type=evidence_type,
            source=task_name,
            locator="network_events",
            summary=f"{len(sensitive_events)} API-like request(s) touch sensitive-sounding surfaces.",
            tags=("browser", "sensitive-surface"),
        )
        hypotheses.append(
            ResearchHypothesis(
                title="Sensitive browser-reached surfaces should be prioritized for authorization and exposure review",
                category="sensitive-surface-review",
                rationale="Browser traffic references paths associated with account, user, role, token, webhook, export, billing, or administrative workflows.",
                confidence="medium",
                evidence=(ref,),
                suggested_tests=(
                    "Review response shape and status codes for each sensitive-looking route.",
                    "Check whether lower-privileged users can access the same read-only route.",
                    "Avoid write or destructive actions unless the program explicitly permits them.",
                ),
                tags=("admin", "sensitive", "authorization"),
            )
        )

    server_error_events = [
        event
        for event in network_events
        if (_event_status(event) or 0) >= 500
    ]

    if server_error_events:
        ref = EvidenceReference(
            evidence_type=evidence_type,
            source=task_name,
            locator="network_events",
            summary=f"{len(server_error_events)} request(s) returned HTTP 5xx.",
            tags=("browser", "error-handling"),
        )
        hypotheses.append(
            ResearchHypothesis(
                title="Server errors may indicate brittle validation or unsafe error handling",
                category="error-handling",
                rationale="HTTP 5xx responses observed in browser evidence may reveal unstable validation, object lookup, or backend exception handling.",
                confidence="low",
                evidence=(ref,),
                suggested_tests=(
                    "Confirm whether the 5xx response is reproducible with a minimal read-only request.",
                    "Compare valid, random, malformed, and unauthorized controls.",
                    "Do not submit unless impact is more than generic error handling.",
                ),
                tags=("500", "error-handling"),
            )
        )

    if evidence.get("screenshots") or evidence.get("html_snapshots"):
        ref = EvidenceReference(
            evidence_type=evidence_type,
            source=task_name,
            locator="browser_artifacts",
            summary="Browser evidence includes screenshot and/or HTML snapshot artifacts.",
            tags=("browser", "artifact"),
        )
        hypotheses.append(
            ResearchHypothesis(
                title="Browser artifacts can support manual exposure and workflow review",
                category="browser-evidence-review",
                rationale="Screenshots and HTML snapshots can help verify what was visible in the tested browser context without relying only on raw network traffic.",
                confidence="medium",
                evidence=(ref,),
                suggested_tests=(
                    "Review redacted HTML previews for forms, links, embedded endpoints, and sensitive labels.",
                    "Use screenshot metadata to confirm the tested workflow state.",
                    "Do not treat UI visibility alone as impact; validate backend authorization separately.",
                ),
                tags=("browser", "evidence"),
            )
        )

    if hypotheses:
        recommendations.append(
            ResearchRecommendation(
                priority=1,
                title="Review browser-observed API routes before expanding testing",
                reason="The plan identified testable hypotheses from existing evidence without making new network requests.",
                next_actions=(
                    "Export the unique browser-observed API routes.",
                    "Group them by authorization boundary and object type.",
                    "Create read-only validation checks for the highest-signal routes.",
                ),
                related_hypotheses=tuple(h.title for h in hypotheses[:3]),
                safety_notes=(
                    "Keep tests inside the authorized program scope.",
                    "Prefer read-only checks and controlled test accounts.",
                    "Do not execute suggested actions automatically.",
                ),
            )
        )
    else:
        recommendations.append(
            ResearchRecommendation(
                priority=1,
                title="Collect more evidence before planning deeper tests",
                reason="No high-signal API, identifier, sensitive-surface, or error-handling patterns were detected.",
                next_actions=(
                    "Capture browser traffic for an authenticated workflow.",
                    "Import HAR or browser capture evidence.",
                    "Run the planner again on the richer evidence file.",
                ),
                safety_notes=(
                    "Only capture workflows and accounts you are authorized to test.",
                ),
            )
        )

    return ResearchPlan(
        target_name=target_name,
        source_evidence_type=evidence_type,
        hypotheses=tuple(hypotheses),
        recommendations=tuple(recommendations),
    )
