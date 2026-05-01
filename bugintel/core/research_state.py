"""
Research state / case memory for Blackhole AI Workbench.

This module creates a structured planning-only case memory from orchestration
JSON. It does not send requests, execute shell commands, launch browsers,
call LLM providers, mutate targets, or bypass authorization.

The research state is the foundation for the future Blackhole AI brain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any
import re


@dataclass(frozen=True)
class ResearchArtifact:
    name: str
    artifact_type: str
    path: str
    status: str = "planned"
    redaction_required: bool = False
    human_approval_required: bool = False
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchHypothesis:
    name: str
    endpoint: str
    description: str
    confidence: str = "medium"
    status: str = "open"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchDecision:
    name: str
    status: str
    rationale: str
    related_endpoint: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResearchEndpointState:
    endpoint: str
    slug: str
    priority_score: int
    priority_band: str
    attack_surface_groups: tuple[str, ...]
    requirement_names: tuple[str, ...]
    artifacts: tuple[ResearchArtifact, ...] = field(default_factory=tuple)
    hypotheses: tuple[ResearchHypothesis, ...] = field(default_factory=tuple)
    triage_state: str = "planned"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "slug": self.slug,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "attack_surface_groups": list(self.attack_surface_groups),
            "requirement_names": list(self.requirement_names),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "hypotheses": [hypothesis.to_dict() for hypothesis in self.hypotheses],
            "triage_state": self.triage_state,
            "planning_only": True,
            "execution_state": "not_executed",
        }


@dataclass(frozen=True)
class ResearchState:
    target_name: str
    endpoint_count: int
    endpoints: tuple[ResearchEndpointState, ...]
    decisions: tuple[ResearchDecision, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "orchestration-json"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "endpoint_count": self.endpoint_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "source": self.source,
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
            "decisions": [decision.to_dict() for decision in self.decisions],
            "markdown": render_research_state_markdown(self),
        }


def build_research_state_from_orchestration(orchestration_data: dict[str, Any]) -> ResearchState:
    """Build a planning-only research state from orchestration JSON."""
    target_name = str(orchestration_data.get("target_name") or "unknown-target")
    evidence_plan = orchestration_data.get("evidence_requirement_plan") or {}
    endpoint_plans = evidence_plan.get("endpoint_plans") or []

    endpoint_states: list[ResearchEndpointState] = []

    for endpoint_plan in endpoint_plans:
        endpoint = str(endpoint_plan.get("endpoint") or "unknown-endpoint")
        groups = tuple(str(item) for item in endpoint_plan.get("attack_surface_groups") or [])
        requirements = endpoint_plan.get("requirements") or []
        requirement_names = tuple(str(item.get("name")) for item in requirements if item.get("name"))

        artifacts = tuple(
            _artifact_from_requirement(endpoint, item)
            for item in requirements
            if item.get("name")
        )

        hypotheses = tuple(_hypotheses_for_endpoint(endpoint, groups))

        endpoint_states.append(
            ResearchEndpointState(
                endpoint=endpoint,
                slug=slugify_endpoint(endpoint),
                priority_score=int(endpoint_plan.get("priority_score") or 0),
                priority_band=str(endpoint_plan.get("priority_band") or "info"),
                attack_surface_groups=groups,
                requirement_names=requirement_names,
                artifacts=artifacts,
                hypotheses=hypotheses,
                triage_state=_triage_state_for_endpoint(
                    priority_band=str(endpoint_plan.get("priority_band") or "info"),
                    groups=groups,
                ),
            )
        )

    endpoint_states.sort(key=lambda item: (-item.priority_score, item.endpoint))

    return ResearchState(
        target_name=target_name,
        endpoint_count=len(endpoint_states),
        endpoints=tuple(endpoint_states),
        decisions=tuple(_global_decisions(endpoint_states)),
    )


def render_research_state_markdown(state: ResearchState) -> str:
    """Render a human-readable research state summary."""
    lines = [
        f"# Blackhole Research State: {state.target_name}",
        "",
        "> Planning-only case memory. This is the foundation for future AI reasoning.",
        "",
        f"- Target: `{state.target_name}`",
        f"- Endpoints: `{state.endpoint_count}`",
        f"- Execution state: `{state.execution_state}`",
        "",
        "## Global Decisions",
        "",
    ]

    for decision in state.decisions:
        endpoint = f" — `{decision.related_endpoint}`" if decision.related_endpoint else ""
        lines.append(f"- `{decision.status}` — {decision.name}{endpoint}: {decision.rationale}")

    lines.extend(["", "## Endpoint Memory", ""])

    for endpoint_state in state.endpoints:
        lines.append(f"### `{endpoint_state.endpoint}`")
        lines.append("")
        lines.append(f"- Priority: `{endpoint_state.priority_band}` / `{endpoint_state.priority_score}`")
        lines.append(f"- Triage state: `{endpoint_state.triage_state}`")
        lines.append(f"- Attack surface groups: `{', '.join(endpoint_state.attack_surface_groups) or 'none'}`")
        lines.append("")
        lines.append("Hypotheses:")
        for hypothesis in endpoint_state.hypotheses:
            lines.append(f"- `{hypothesis.status}` / `{hypothesis.confidence}` — {hypothesis.name}: {hypothesis.description}")
        lines.append("")
        lines.append("Planned artifacts:")
        for artifact in endpoint_state.artifacts:
            lines.append(
                f"- `{artifact.status}` — {artifact.name} "
                f"({artifact.artifact_type}, redact={'yes' if artifact.redaction_required else 'no'}, "
                f"approval={'yes' if artifact.human_approval_required else 'no'})"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def slugify_endpoint(endpoint: str) -> str:
    """Create a stable slug for endpoint memory keys."""
    value = endpoint.lower()
    value = re.sub(r"^https?://", "", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:90] or "endpoint"


def _artifact_from_requirement(endpoint: str, requirement: dict[str, Any]) -> ResearchArtifact:
    name = str(requirement.get("name") or "unnamed-requirement")
    artifact_type = str(requirement.get("artifact_type") or "artifact")
    slug = slugify_endpoint(endpoint)
    artifact_slug = slugify_endpoint(name)

    return ResearchArtifact(
        name=name,
        artifact_type=artifact_type,
        path=f"endpoints/{slug}/artifacts/{artifact_slug}.md",
        redaction_required=bool(requirement.get("redaction_required")),
        human_approval_required=bool(requirement.get("human_approval_required")),
        notes=str(requirement.get("description") or ""),
    )


def _hypotheses_for_endpoint(endpoint: str, groups: tuple[str, ...]) -> list[ResearchHypothesis]:
    hypotheses: list[ResearchHypothesis] = []

    if "identity-access" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="authorization-boundary-hypothesis",
                endpoint=endpoint,
                description="Endpoint may expose role, user, team, account, or permission boundary behavior.",
                confidence="medium-high",
            )
        )

    if "tenant-project-boundary" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="tenant-boundary-hypothesis",
                endpoint=endpoint,
                description="Endpoint may enforce tenant, project, organization, or workspace isolation.",
                confidence="medium-high",
            )
        )

    if "object-reference" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="object-reference-hypothesis",
                endpoint=endpoint,
                description="Endpoint contains object identifiers that may require IDOR/BAC validation with controlled objects.",
                confidence="medium-high",
            )
        )

    if "file-surface" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="file-access-boundary-hypothesis",
                endpoint=endpoint,
                description="Endpoint may require file ownership, upload/download, or attachment access-control validation.",
                confidence="medium-high",
            )
        )

    if "auth-flow" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="auth-flow-state-hypothesis",
                endpoint=endpoint,
                description="Endpoint may affect session, OAuth, SSO, MFA, reset, or authentication state transitions.",
                confidence="medium",
            )
        )

    if "integration-webhook" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="integration-boundary-hypothesis",
                endpoint=endpoint,
                description="Endpoint may expose integration, webhook, callback, or connected-app boundary behavior.",
                confidence="medium",
            )
        )

    if "secret-token-key" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="secret-handling-hypothesis",
                endpoint=endpoint,
                description="Endpoint may expose token, secret, key, API-key, or credential-handling behavior.",
                confidence="high",
            )
        )

    if "billing-money" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="billing-safety-hypothesis",
                endpoint=endpoint,
                description="Endpoint may involve billing, payments, subscriptions, invoices, or plan changes and requires non-mutating validation.",
                confidence="medium-high",
            )
        )

    if "low-signal" in groups:
        hypotheses.append(
            ResearchHypothesis(
                name="low-signal-deprioritization-hypothesis",
                endpoint=endpoint,
                description="Endpoint appears low-signal unless later evidence shows sensitive behavior.",
                confidence="high",
                status="deprioritized",
            )
        )

    if not hypotheses:
        hypotheses.append(
            ResearchHypothesis(
                name="general-api-context-hypothesis",
                endpoint=endpoint,
                description="Endpoint should remain in the case memory until source, context, or behavior is understood.",
                confidence="low",
            )
        )

    return hypotheses


def _triage_state_for_endpoint(priority_band: str, groups: tuple[str, ...]) -> str:
    if "low-signal" in groups:
        return "deprioritized"
    if priority_band in {"critical", "high"}:
        return "ready-for-manual-validation"
    if priority_band == "medium":
        return "queued"
    return "watchlist"


def _global_decisions(endpoints: list[ResearchEndpointState]) -> list[ResearchDecision]:
    high_count = sum(1 for endpoint in endpoints if endpoint.priority_band in {"critical", "high"})
    approval_count = sum(
        1
        for endpoint in endpoints
        for artifact in endpoint.artifacts
        if artifact.human_approval_required
    )

    return [
        ResearchDecision(
            name="confirm-scope-and-authorization",
            status="required",
            rationale="Research state cannot move to active validation until target scope and authorization are confirmed.",
        ),
        ResearchDecision(
            name="manual-validation-required",
            status="required",
            rationale="Blackhole is planning-only; all validation must be executed by a human on authorized targets.",
        ),
        ResearchDecision(
            name="prioritize-high-signal-endpoints",
            status="planned",
            rationale=f"{high_count} endpoint(s) are critical/high priority and should be reviewed before low-signal routes.",
        ),
        ResearchDecision(
            name="approval-gated-artifacts",
            status="planned",
            rationale=f"{approval_count} planned artifact(s) require human approval before collection.",
        ),
    ]
