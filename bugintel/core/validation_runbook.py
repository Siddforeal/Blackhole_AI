"""
Validation runbook builder for Blackhole AI Workbench.

This module creates safe, planning-only validation runbooks from orchestration
JSON. It does not send requests, execute shell commands, launch browsers,
call LLM providers, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class ValidationStep:
    name: str
    phase: str
    description: str
    expected_artifact: str
    redaction_required: bool = False
    human_approval_required: bool = False
    stop_condition: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EndpointValidationRunbook:
    endpoint: str
    priority_score: int
    priority_band: str
    attack_surface_groups: tuple[str, ...]
    steps: tuple[ValidationStep, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "attack_surface_groups": list(self.attack_surface_groups),
            "steps": [step.to_dict() for step in self.steps],
            "planning_only": True,
            "execution_state": "not_executed",
        }


@dataclass(frozen=True)
class ValidationRunbook:
    target_name: str
    endpoint_count: int
    endpoint_runbooks: tuple[EndpointValidationRunbook, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "endpoint_count": self.endpoint_count,
            "planning_only": True,
            "execution_state": "not_executed",
            "endpoint_runbooks": [runbook.to_dict() for runbook in self.endpoint_runbooks],
            "markdown": render_validation_runbook_markdown(self),
        }


def build_validation_runbook(orchestration_data: dict[str, Any]) -> ValidationRunbook:
    """Build a validation runbook from orchestration JSON."""
    target_name = str(orchestration_data.get("target_name") or "unknown-target")
    evidence_plan = orchestration_data.get("evidence_requirement_plan") or {}
    endpoint_plans = evidence_plan.get("endpoint_plans") or []

    runbooks: list[EndpointValidationRunbook] = []

    for endpoint_plan in endpoint_plans:
        endpoint = str(endpoint_plan.get("endpoint") or "unknown-endpoint")
        score = int(endpoint_plan.get("priority_score") or 0)
        band = str(endpoint_plan.get("priority_band") or "info")
        groups = tuple(str(item) for item in endpoint_plan.get("attack_surface_groups") or [])
        requirements = endpoint_plan.get("requirements") or []

        steps = _build_steps_for_endpoint(endpoint, groups, requirements)

        runbooks.append(
            EndpointValidationRunbook(
                endpoint=endpoint,
                priority_score=score,
                priority_band=band,
                attack_surface_groups=groups,
                steps=tuple(steps),
            )
        )

    runbooks.sort(key=lambda item: (-item.priority_score, item.endpoint))

    return ValidationRunbook(
        target_name=target_name,
        endpoint_count=len(runbooks),
        endpoint_runbooks=tuple(runbooks),
    )


def render_validation_runbook_markdown(runbook: ValidationRunbook) -> str:
    """Render a validation runbook as Markdown."""
    lines = [
        f"# Blackhole Validation Runbook: {runbook.target_name}",
        "",
        "> Planning-only validation runbook. Execute steps manually only on authorized targets and controlled accounts.",
        "",
        f"- Target: `{runbook.target_name}`",
        f"- Endpoint runbooks: `{runbook.endpoint_count}`",
        f"- Execution state: `{runbook.to_dict_shallow()['execution_state']}`",
        "",
        "## Global Safety Rules",
        "",
        "- [ ] Confirm the target is in scope.",
        "- [ ] Use controlled accounts and synthetic data only.",
        "- [ ] Avoid destructive writes unless explicitly authorized.",
        "- [ ] Redact cookies, tokens, API keys, emails, IDs, and private data.",
        "- [ ] Stop immediately if real customer data appears.",
        "- [ ] Keep evidence minimal, relevant, and sanitized.",
        "",
    ]

    for endpoint_runbook in runbook.endpoint_runbooks:
        lines.append(f"## `{endpoint_runbook.endpoint}`")
        lines.append("")
        lines.append(f"- Priority: `{endpoint_runbook.priority_band}` / `{endpoint_runbook.priority_score}`")
        lines.append(f"- Attack surface groups: `{', '.join(endpoint_runbook.attack_surface_groups) or 'none'}`")
        lines.append("")
        lines.append("| # | Phase | Step | Artifact | Redact | Approval | Stop Condition |")
        lines.append("|---:|---|---|---|---|---|---|")

        for index, step in enumerate(endpoint_runbook.steps, start=1):
            stop = step.stop_condition or ""
            lines.append(
                f"| {index} | {step.phase} | {step.name} | {step.expected_artifact} | "
                f"{'YES' if step.redaction_required else 'NO'} | "
                f"{'YES' if step.human_approval_required else 'NO'} | {stop} |"
            )

        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_steps_for_endpoint(
    endpoint: str,
    groups: tuple[str, ...],
    requirements: list[dict[str, Any]],
) -> list[ValidationStep]:
    steps = [
        ValidationStep(
            name="Confirm scope and authorization",
            phase="preflight",
            description="Confirm target, endpoint, account, object, and data are in scope and controlled.",
            expected_artifact="scope note",
            redaction_required=False,
            human_approval_required=False,
            stop_condition="Stop if endpoint or data is out of scope.",
        ),
        ValidationStep(
            name="Prepare redaction plan",
            phase="preflight",
            description="List sensitive values that must be redacted before collecting or sharing evidence.",
            expected_artifact="redaction checklist",
            redaction_required=True,
            human_approval_required=False,
        ),
        ValidationStep(
            name="Collect baseline behavior",
            phase="baseline",
            description="Manually collect a minimal redacted baseline request/response or UI behavior sample.",
            expected_artifact="redacted baseline sample",
            redaction_required=True,
            human_approval_required=True,
            stop_condition="Stop if real customer data appears.",
        ),
    ]

    if "identity-access" in groups:
        steps.extend(_identity_access_steps())

    if "tenant-project-boundary" in groups:
        steps.extend(_tenant_boundary_steps())

    if "object-reference" in groups:
        steps.extend(_object_reference_steps())

    if "file-surface" in groups:
        steps.extend(_file_surface_steps())

    if "auth-flow" in groups:
        steps.extend(_auth_flow_steps())

    if "billing-money" in groups:
        steps.extend(_billing_steps())

    if "integration-webhook" in groups:
        steps.extend(_integration_steps())

    if "secret-token-key" in groups:
        steps.extend(_secret_token_steps())

    if "parameter-heavy" in groups:
        steps.extend(_parameter_steps())

    if "low-signal" in groups:
        steps.extend(_low_signal_steps())

    requirement_names = {str(item.get("name")) for item in requirements}

    if "owned-foreign-random-response-matrix" in requirement_names:
        steps.append(
            ValidationStep(
                name="Build owned/foreign/random response matrix",
                phase="evidence",
                description="Compare owned, controlled-foreign, random, and malformed object behavior.",
                expected_artifact="response matrix",
                redaction_required=True,
                human_approval_required=True,
                stop_condition="Stop if response exposes unauthorized private data.",
            )
        )

    steps.append(
        ValidationStep(
            name="Make reportability decision",
            phase="decision",
            description="Decide whether evidence proves a security boundary violation and real impact.",
            expected_artifact="validation decision note",
            redaction_required=False,
            human_approval_required=False,
        )
    )

    return _dedupe_steps(steps)


def _identity_access_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Document controlled account role matrix",
            phase="setup",
            description="Document each controlled account, role, team, tenant, and expected permission boundary.",
            expected_artifact="role matrix",
            redaction_required=True,
            human_approval_required=True,
        ),
        ValidationStep(
            name="Compare allowed and denied authorization decisions",
            phase="validation",
            description="Compare expected allowed vs denied behavior with controlled identities only.",
            expected_artifact="authorization diff",
            redaction_required=True,
            human_approval_required=True,
        ),
    ]


def _tenant_boundary_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Plan cross-tenant or cross-project boundary check",
            phase="setup",
            description="Use only controlled tenants/projects/workspaces to plan a same-role boundary check.",
            expected_artifact="tenant boundary matrix",
            redaction_required=True,
            human_approval_required=True,
        )
    ]


def _object_reference_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Map identifier source",
            phase="setup",
            description="Record whether object identifiers came from UI, JS, HAR, API response, or mobile config.",
            expected_artifact="identifier source map",
            redaction_required=True,
            human_approval_required=False,
        ),
        ValidationStep(
            name="Validate object-reference handling",
            phase="validation",
            description="Manually compare owned, controlled-foreign, random, and malformed object references.",
            expected_artifact="object-reference comparison",
            redaction_required=True,
            human_approval_required=True,
            stop_condition="Stop if unauthorized private data appears.",
        ),
    ]


def _file_surface_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Prepare synthetic test file manifest",
            phase="setup",
            description="Use only synthetic files and record filenames, owners, and expected access boundaries.",
            expected_artifact="safe test file manifest",
            redaction_required=False,
            human_approval_required=True,
        ),
        ValidationStep(
            name="Validate file access boundary",
            phase="validation",
            description="Compare owned vs unauthorized controlled file access behavior without touching real customer files.",
            expected_artifact="file access-control diff",
            redaction_required=True,
            human_approval_required=True,
            stop_condition="Stop if real customer files become visible.",
        ),
    ]


def _auth_flow_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Map session state transitions",
            phase="validation",
            description="Record login, logout, reset, MFA, OAuth, redirect, CSRF, and session state transitions.",
            expected_artifact="session transition notes",
            redaction_required=True,
            human_approval_required=True,
        )
    ]


def _billing_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Confirm billing checks are non-mutating",
            phase="preflight",
            description="Verify billing/payment/invoice checks cannot trigger real charges or subscription changes.",
            expected_artifact="billing safety note",
            redaction_required=True,
            human_approval_required=True,
            stop_condition="Stop if any path may create a real charge or plan change.",
        )
    ]


def _integration_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Redact integration secrets",
            phase="preflight",
            description="Confirm webhook URLs, OAuth codes, callbacks, and connected-app secrets are redacted.",
            expected_artifact="integration redaction note",
            redaction_required=True,
            human_approval_required=False,
        ),
        ValidationStep(
            name="Validate integration boundary without invocation",
            phase="validation",
            description="Validate visibility or boundary behavior without invoking third-party webhooks.",
            expected_artifact="integration boundary evidence",
            redaction_required=True,
            human_approval_required=True,
        ),
    ]


def _secret_token_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Store only redacted secret exposure sample",
            phase="evidence",
            description="If a token/key/secret appears, store only a redacted sample plus metadata needed to prove impact.",
            expected_artifact="redacted secret exposure sample",
            redaction_required=True,
            human_approval_required=True,
            stop_condition="Stop if a live secret is exposed; do not use it.",
        )
    ]


def _parameter_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Track parameter behavior safely",
            phase="validation",
            description="Track low-volume filter, query, pagination, sorting, and response-shape behavior.",
            expected_artifact="parameter behavior matrix",
            redaction_required=True,
            human_approval_required=True,
        )
    ]


def _low_signal_steps() -> list[ValidationStep]:
    return [
        ValidationStep(
            name="Record low-signal deprioritization",
            phase="decision",
            description="Record why the route is low priority unless new sensitive behavior is found.",
            expected_artifact="deprioritization note",
            redaction_required=False,
            human_approval_required=False,
        )
    ]


def _dedupe_steps(steps: list[ValidationStep]) -> list[ValidationStep]:
    deduped: dict[str, ValidationStep] = {}

    for step in steps:
        deduped.setdefault(step.name, step)

    return list(deduped.values())


def _to_dict_shallow(runbook: ValidationRunbook) -> dict[str, Any]:
    return {
        "target_name": runbook.target_name,
        "endpoint_count": runbook.endpoint_count,
        "planning_only": True,
        "execution_state": "not_executed",
    }


ValidationRunbook.to_dict_shallow = _to_dict_shallow  # type: ignore[attr-defined]
