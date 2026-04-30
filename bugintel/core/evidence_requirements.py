"""
Evidence requirement planning for Blackhole AI Workbench.

This module is planning-only. It does not send requests, execute shell commands,
launch browsers, call LLM providers, mutate targets, or bypass authorization.

It translates endpoint priority and attack-surface groups into evidence
checklists that help a human researcher collect safe, report-quality proof.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.core.attack_surface import classify_attack_surface_groups
from bugintel.core.endpoint_priority import score_endpoint


@dataclass(frozen=True)
class EvidenceRequirement:
    name: str
    artifact_type: str
    description: str
    applies_to: tuple[str, ...]
    sensitivity: str = "normal"
    redaction_required: bool = False
    human_approval_required: bool = False
    metadata: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["applies_to"] = list(self.applies_to)
        data["metadata"] = self.metadata or {}
        return data


@dataclass(frozen=True)
class EndpointEvidencePlan:
    endpoint: str
    normalized_path: str
    priority_score: int
    priority_band: str
    attack_surface_groups: tuple[str, ...]
    requirements: tuple[EvidenceRequirement, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "normalized_path": self.normalized_path,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "attack_surface_groups": list(self.attack_surface_groups),
            "requirements": [requirement.to_dict() for requirement in self.requirements],
            "recommended_collection_order": [requirement.name for requirement in self.requirements],
            "planning_only": True,
            "execution_state": "not_executed",
        }


@dataclass(frozen=True)
class EvidenceRequirementPlan:
    endpoint_count: int
    endpoint_plans: tuple[EndpointEvidencePlan, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint_count": self.endpoint_count,
            "planning_only": True,
            "execution_state": "not_executed",
            "endpoint_plans": [plan.to_dict() for plan in self.endpoint_plans],
        }


def build_endpoint_evidence_plan(endpoint: str) -> EndpointEvidencePlan:
    """Build report-quality evidence requirements for one endpoint."""
    priority = score_endpoint(endpoint)
    groups = classify_attack_surface_groups(endpoint)

    requirements = list(_base_requirements())

    for group in groups:
        requirements.extend(_requirements_for_group(group))

    deduped = _dedupe_requirements(requirements)

    return EndpointEvidencePlan(
        endpoint=endpoint,
        normalized_path=priority.normalized_path,
        priority_score=priority.score,
        priority_band=priority.band,
        attack_surface_groups=groups,
        requirements=tuple(deduped),
    )


def build_evidence_requirement_plan(endpoints: list[str]) -> EvidenceRequirementPlan:
    """Build evidence plans for endpoints sorted by priority."""
    unique_endpoints = sorted(set(endpoints))
    plans = [build_endpoint_evidence_plan(endpoint) for endpoint in unique_endpoints]
    plans.sort(key=lambda item: (-item.priority_score, item.endpoint))

    return EvidenceRequirementPlan(
        endpoint_count=len(plans),
        endpoint_plans=tuple(plans),
    )


def _base_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="scope-and-authorization-proof",
            artifact_type="notes",
            description="Record program scope, testing authorization, target, account ownership, and safe-testing constraints.",
            applies_to=("all",),
            sensitivity="normal",
            redaction_required=False,
            human_approval_required=False,
        ),
        EvidenceRequirement(
            name="baseline-request-response-sample",
            artifact_type="http-sample",
            description="Collect a redacted baseline request/response shape for the owned or allowed endpoint path.",
            applies_to=("all",),
            sensitivity="medium",
            redaction_required=True,
            human_approval_required=True,
        ),
        EvidenceRequirement(
            name="redaction-checklist",
            artifact_type="checklist",
            description="Confirm tokens, cookies, emails, user data, secrets, and private identifiers are redacted before sharing.",
            applies_to=("all",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=False,
        ),
    )


def _requirements_for_group(group: str) -> tuple[EvidenceRequirement, ...]:
    by_group = {
        "identity-access": _identity_access_requirements,
        "tenant-project-boundary": _tenant_boundary_requirements,
        "file-surface": _file_surface_requirements,
        "auth-flow": _auth_flow_requirements,
        "billing-money": _billing_requirements,
        "integration-webhook": _integration_requirements,
        "secret-token-key": _secret_token_requirements,
        "object-reference": _object_reference_requirements,
        "parameter-heavy": _parameter_requirements,
        "low-signal": _low_signal_requirements,
        "general-api": _general_api_requirements,
    }

    builder = by_group.get(group, _general_api_requirements)
    return builder()


def _identity_access_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="controlled-account-role-matrix",
            artifact_type="matrix",
            description="Document controlled test identities, roles, account/project membership, and expected access boundaries.",
            applies_to=("identity-access",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
        EvidenceRequirement(
            name="authorization-decision-diff",
            artifact_type="http-diff",
            description="Capture allowed vs denied response differences for authorized test identities without exposing real user data.",
            applies_to=("identity-access",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _tenant_boundary_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="tenant-boundary-test-matrix",
            artifact_type="matrix",
            description="Plan same-role cross-tenant, cross-project, or cross-workspace checks using only controlled accounts.",
            applies_to=("tenant-project-boundary",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _file_surface_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="safe-test-file-manifest",
            artifact_type="notes",
            description="Document safe synthetic files used for testing and confirm no real user/customer files are accessed.",
            applies_to=("file-surface",),
            sensitivity="medium",
            redaction_required=False,
            human_approval_required=True,
        ),
        EvidenceRequirement(
            name="file-access-control-evidence",
            artifact_type="http-diff",
            description="Capture owned vs unauthorized file access behavior with redacted request/response samples.",
            applies_to=("file-surface",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _auth_flow_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="session-state-transition-notes",
            artifact_type="notes",
            description="Record login, logout, redirect, token, CSRF, OAuth/SSO, MFA, and session-state observations.",
            applies_to=("auth-flow",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _billing_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="non-mutating-billing-proof",
            artifact_type="notes",
            description="Document that billing/payment/invoice checks are read-only and do not trigger real charges or subscription changes.",
            applies_to=("billing-money",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _integration_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="integration-secret-redaction-proof",
            artifact_type="checklist",
            description="Confirm integration tokens, webhook URLs, OAuth codes, callbacks, and connected-app secrets are redacted.",
            applies_to=("integration-webhook",),
            sensitivity="critical",
            redaction_required=True,
            human_approval_required=False,
        ),
        EvidenceRequirement(
            name="integration-boundary-evidence",
            artifact_type="http-diff",
            description="Capture controlled integration visibility or boundary behavior without invoking third-party webhooks.",
            applies_to=("integration-webhook",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _secret_token_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="secret-token-exposure-redaction",
            artifact_type="redacted-sample",
            description="If token/key/secret exposure is observed, store only redacted samples and metadata needed to prove impact safely.",
            applies_to=("secret-token-key",),
            sensitivity="critical",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _object_reference_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="identifier-source-map",
            artifact_type="mapping",
            description="Map where object identifiers came from: UI, JS, HAR, API response, mobile config, or controlled source.",
            applies_to=("object-reference",),
            sensitivity="medium",
            redaction_required=True,
            human_approval_required=False,
        ),
        EvidenceRequirement(
            name="owned-foreign-random-response-matrix",
            artifact_type="matrix",
            description="Compare owned, foreign controlled, random, and malformed object-reference behavior.",
            applies_to=("object-reference",),
            sensitivity="high",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _parameter_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="parameter-behavior-matrix",
            artifact_type="matrix",
            description="Track low-volume filter, query, pagination, sorting, and response-shape behavior.",
            applies_to=("parameter-heavy",),
            sensitivity="medium",
            redaction_required=True,
            human_approval_required=True,
        ),
    )


def _low_signal_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="low-signal-deprioritization-note",
            artifact_type="notes",
            description="Record why the route is low priority unless later evidence shows sensitive behavior.",
            applies_to=("low-signal",),
            sensitivity="normal",
            redaction_required=False,
            human_approval_required=False,
        ),
    )


def _general_api_requirements() -> tuple[EvidenceRequirement, ...]:
    return (
        EvidenceRequirement(
            name="general-api-context-note",
            artifact_type="notes",
            description="Capture route context, source, and reason for keeping the endpoint in the research queue.",
            applies_to=("general-api",),
            sensitivity="normal",
            redaction_required=False,
            human_approval_required=False,
        ),
    )


def _dedupe_requirements(requirements: list[EvidenceRequirement]) -> list[EvidenceRequirement]:
    deduped: dict[str, EvidenceRequirement] = {}

    for requirement in requirements:
        deduped.setdefault(requirement.name, requirement)

    return list(deduped.values())
