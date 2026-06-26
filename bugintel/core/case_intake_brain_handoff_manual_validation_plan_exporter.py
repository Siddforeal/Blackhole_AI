"""
Brain handoff manual validation plan exporter.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It converts focus endpoints and evidence gaps from a case_intake_brain_handoff
artifact into a reviewable manual validation plan.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainManualValidationPlanEndpoint:
    endpoint: str
    lane: str
    priority_score: int
    priority_band: str
    categories: tuple[str, ...]
    why_focus: tuple[str, ...]
    validation_steps: tuple[str, ...]
    evidence_targets: tuple[str, ...]
    checklist_ids: tuple[str, ...]
    stop_conditions: tuple[str, ...]
    controlled_account_matrix: tuple[str, ...]
    approval_required: bool = True
    read_only_required: bool = True
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "lane": self.lane,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "categories": list(self.categories),
            "why_focus": list(self.why_focus),
            "validation_steps": list(self.validation_steps),
            "evidence_targets": list(self.evidence_targets),
            "checklist_ids": list(self.checklist_ids),
            "stop_conditions": list(self.stop_conditions),
            "controlled_account_matrix": list(self.controlled_account_matrix),
            "approval_required": self.approval_required,
            "read_only_required": self.read_only_required,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
        }


@dataclass(frozen=True)
class CaseIntakeBrainManualValidationPlan:
    target_name: str
    handoff_status: str
    plan_endpoints: tuple[CaseIntakeBrainManualValidationPlanEndpoint, ...]
    deferred_endpoints: tuple[str, ...]
    plan_endpoint_count: int
    deferred_endpoint_count: int
    evidence_gap_count: int
    approval_required: bool
    read_only_required: bool
    blocked: bool
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-manual-validation-plan-exporter"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_manual_validation_plan",
            "source": self.source,
            "target_name": self.target_name,
            "handoff_status": self.handoff_status,
            "plan_endpoints": [endpoint.to_dict() for endpoint in self.plan_endpoints],
            "deferred_endpoints": list(self.deferred_endpoints),
            "plan_endpoint_count": self.plan_endpoint_count,
            "deferred_endpoint_count": self.deferred_endpoint_count,
            "evidence_gap_count": self.evidence_gap_count,
            "approval_required": self.approval_required,
            "read_only_required": self.read_only_required,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Manual Validation Plan") -> str:
        lines = [
            f"# {title}",
            "",
            "## Summary",
            "",
            f"- Target: `{self.target_name}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Plan endpoints: `{self.plan_endpoint_count}`",
            f"- Deferred endpoints: `{self.deferred_endpoint_count}`",
            f"- Evidence gaps: `{self.evidence_gap_count}`",
            f"- Approval required: `{self.approval_required}`",
            f"- Read-only required: `{self.read_only_required}`",
            f"- Blocked: `{self.blocked}`",
            f"- Planning only: `{self.planning_only}`",
            f"- Execution state: `{self.execution_state}`",
            "",
            "## Safety",
            "",
            "- No network requests",
            "- No tool execution",
            "- No browser execution",
            "- No provider calls",
            "- No evidence collection",
            "- No target mutation",
            "- No report submission",
            "- No vulnerability confirmation",
            "",
            "## Manual Validation Plan",
            "",
        ]

        if not self.plan_endpoints:
            lines.extend(
                [
                    "No P1/P2 focus endpoints are available for manual validation planning.",
                    "",
                    "Regenerate the handoff from a case intake artifact with P1/P2 focus endpoints.",
                    "",
                ]
            )
            return "\n".join(lines).rstrip() + "\n"

        for index, endpoint in enumerate(self.plan_endpoints, start=1):
            lines.extend(
                [
                    f"### {index}. `{endpoint.endpoint}`",
                    "",
                    f"- Lane: `{endpoint.lane}`",
                    f"- Score: `{endpoint.priority_score}`",
                    f"- Band: `{endpoint.priority_band}`",
                    f"- Approval required: `{endpoint.approval_required}`",
                    f"- Read-only required: `{endpoint.read_only_required}`",
                    "",
                    "Why focus:",
                    "",
                ]
            )
            lines.extend(_markdown_list(endpoint.why_focus))
            lines.extend(["", "Controlled account matrix:", ""])
            lines.extend(_markdown_list(endpoint.controlled_account_matrix))
            lines.extend(["", "Manual validation steps:", ""])
            lines.extend(f"{step_number}. {step}" for step_number, step in enumerate(endpoint.validation_steps, start=1))
            lines.extend(["", "Evidence targets:", ""])
            lines.extend(_markdown_list(endpoint.evidence_targets))
            lines.extend(["", "Linked checklist IDs:", ""])
            lines.extend(_markdown_list(endpoint.checklist_ids))
            lines.extend(["", "Stop conditions:", ""])
            lines.extend(_markdown_list(endpoint.stop_conditions))
            lines.append("")

        if self.deferred_endpoints:
            lines.extend(["## Deferred Endpoints", ""])
            lines.extend(f"- `{endpoint}`" for endpoint in self.deferred_endpoints)
            lines.append("")

        return "\n".join(lines).rstrip() + "\n"


def export_case_intake_brain_handoff_manual_validation_plan(
    handoff: dict[str, Any],
) -> CaseIntakeBrainManualValidationPlan:
    handoff_data = handoff if isinstance(handoff, dict) else {}
    target_name = str(handoff_data.get("target_name") or "bug-bounty-target")
    handoff_status = str(handoff_data.get("status") or "unknown")
    deferred = tuple(_strings(handoff_data.get("deferred_endpoints")))

    if str(handoff_data.get("kind") or "") != "case_intake_brain_handoff":
        return CaseIntakeBrainManualValidationPlan(
            target_name=target_name,
            handoff_status="blocked-invalid-case-intake-brain-handoff",
            plan_endpoints=(),
            deferred_endpoints=deferred,
            plan_endpoint_count=0,
            deferred_endpoint_count=len(deferred),
            evidence_gap_count=0,
            approval_required=True,
            read_only_required=True,
            blocked=True,
        )

    if _unsafe_handoff(handoff_data):
        return CaseIntakeBrainManualValidationPlan(
            target_name=target_name,
            handoff_status="blocked-unsafe-case-intake-brain-handoff",
            plan_endpoints=(),
            deferred_endpoints=deferred,
            plan_endpoint_count=0,
            deferred_endpoint_count=len(deferred),
            evidence_gap_count=0,
            approval_required=True,
            read_only_required=True,
            blocked=True,
        )

    focus_endpoints = _objects(handoff_data.get("focus_endpoints"))
    gaps = _objects(handoff_data.get("evidence_gaps"))
    checklist_ids_by_endpoint = _checklist_ids_by_endpoint(gaps)

    plan_endpoints = tuple(
        _plan_endpoint(endpoint, checklist_ids_by_endpoint.get(str(endpoint.get("endpoint") or ""), ()))
        for endpoint in focus_endpoints
    )

    return CaseIntakeBrainManualValidationPlan(
        target_name=target_name,
        handoff_status=handoff_status,
        plan_endpoints=plan_endpoints,
        deferred_endpoints=deferred,
        plan_endpoint_count=len(plan_endpoints),
        deferred_endpoint_count=len(deferred),
        evidence_gap_count=len(gaps),
        approval_required=True,
        read_only_required=True,
        blocked=handoff_status.startswith("blocked-") or not plan_endpoints,
    )


def _plan_endpoint(
    endpoint: dict[str, Any],
    checklist_ids: tuple[str, ...],
) -> CaseIntakeBrainManualValidationPlanEndpoint:
    endpoint_value = str(endpoint.get("endpoint") or "unknown-endpoint")
    categories = tuple(_strings(endpoint.get("categories")))
    why_focus = tuple(_strings(endpoint.get("why_focus"))) or (
        "Endpoint was selected as a P1/P2 focus endpoint by the handoff.",
    )
    raw_steps = tuple(_strings(endpoint.get("next_manual_steps")))
    requirement_names = tuple(_strings(endpoint.get("evidence_requirement_names")))

    validation_steps = _validation_steps(endpoint_value, categories, raw_steps)
    evidence_targets = _evidence_targets(endpoint_value, categories, requirement_names, checklist_ids)

    return CaseIntakeBrainManualValidationPlanEndpoint(
        endpoint=endpoint_value,
        lane=str(endpoint.get("lane") or "unknown"),
        priority_score=_int(endpoint.get("priority_score")),
        priority_band=str(endpoint.get("priority_band") or "unknown"),
        categories=categories,
        why_focus=why_focus,
        validation_steps=validation_steps,
        evidence_targets=evidence_targets,
        checklist_ids=checklist_ids or ("no-linked-checklist-items",),
        stop_conditions=_stop_conditions(categories),
        controlled_account_matrix=_controlled_account_matrix(categories),
        approval_required=True,
        read_only_required=True,
    )


def _validation_steps(
    endpoint: str,
    categories: tuple[str, ...],
    raw_steps: tuple[str, ...],
) -> tuple[str, ...]:
    steps = [
        "Confirm the target, endpoint, program scope, allowed test methods, and safe test window.",
        "Prepare controlled accounts only: owner account, second controlled account, lower-privileged role where applicable, and logged-out state where applicable.",
        f"Map all identifiers used by `{endpoint}` to synthetic controlled objects only.",
        "Prepare a read-only baseline request/response expectation without sending live traffic from this exporter.",
    ]

    if "authorization-sensitive" in categories:
        steps.append("Plan owned-vs-second-controlled-account authorization boundary checks.")

    if "object-reference" in categories:
        steps.append("Plan owned, second-controlled, random, and malformed identifier comparisons using synthetic IDs only.")

    if "file-surface" in categories:
        steps.append("Use only synthetic files created for testing and avoid real user files.")

    if any("billing" in category for category in categories):
        steps.append("Keep billing validation read-only and avoid charges, invoice mutation, refunds, or payment operations.")

    steps.extend(raw_steps[:4])
    steps.append("Stop before any live interaction until a human approves the exact request, account matrix, and redaction plan.")

    return tuple(dict.fromkeys(steps))


def _evidence_targets(
    endpoint: str,
    categories: tuple[str, ...],
    requirement_names: tuple[str, ...],
    checklist_ids: tuple[str, ...],
) -> tuple[str, ...]:
    targets = [
        "Scope proof and authorization note for the target and endpoint.",
        "Controlled account matrix showing account ownership and role boundaries.",
        "Redaction checklist for tokens, cookies, identifiers, personal data, and secrets.",
        f"Baseline request/response sample plan for `{endpoint}` without collecting evidence in this exporter.",
    ]

    if "authorization-sensitive" in categories:
        targets.append("Authorization decision diff plan across owner, second controlled account, lower role, and logged-out state.")

    if "object-reference" in categories:
        targets.append("Owned/foreign/random/malformed object-reference response matrix plan.")

    if "file-surface" in categories:
        targets.append("Synthetic file manifest and file-access-control evidence plan.")

    for name in requirement_names:
        targets.append(f"Evidence requirement target: `{name}`.")

    for checklist_id in checklist_ids:
        targets.append(f"Close checklist item `{checklist_id}` before drafting report claims.")

    return tuple(dict.fromkeys(targets))


def _controlled_account_matrix(categories: tuple[str, ...]) -> tuple[str, ...]:
    matrix = [
        "Account A: controlled owner account for the synthetic object.",
        "Account B: second controlled account with no ownership of Account A objects.",
        "Account C: lower-privileged controlled role where the app supports roles.",
        "Logged-out state: only where the endpoint can be safely observed without authentication.",
    ]

    if "file-surface" in categories:
        matrix.append("Synthetic file: harmless file created only for this validation plan.")

    return tuple(matrix)


def _stop_conditions(categories: tuple[str, ...]) -> tuple[str, ...]:
    conditions = [
        "Stop if the endpoint is out of scope or program rules do not explicitly allow the planned manual test.",
        "Stop if the step would access real user data, secrets, payments, invoices, files, or production records.",
        "Stop if the step would mutate target data, trigger workflows, send messages, charge money, or change permissions.",
        "Stop if tokens, cookies, identifiers, or personal data cannot be safely redacted.",
        "Stop if the request rate, account state, or environment cannot be controlled.",
    ]

    if "file-surface" in categories:
        conditions.append("Stop if any non-synthetic file would be accessed or downloaded.")

    return tuple(conditions)


def _checklist_ids_by_endpoint(gaps: list[dict[str, Any]]) -> dict[str, tuple[str, ...]]:
    grouped: dict[str, list[str]] = {}
    for index, gap in enumerate(gaps, start=1):
        endpoint = str(gap.get("endpoint") or "unknown-endpoint")
        grouped.setdefault(endpoint, []).append(f"EC-{index:03d}")
    return {endpoint: tuple(ids) for endpoint, ids in grouped.items()}


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, dict)]


def _strings(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value if str(item).strip()]


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0


def _markdown_list(items: tuple[str, ...]) -> list[str]:
    return [f"- {item}" for item in items] if items else ["- None"]


def _unsafe_handoff(handoff: dict[str, Any]) -> bool:
    safety = handoff.get("safety") if isinstance(handoff.get("safety"), dict) else {}
    unsafe_keys = (
        "network_requests",
        "tool_execution",
        "browser_execution",
        "llm_provider_calls",
        "provider_execution",
        "target_mutation",
        "evidence_collection",
        "validation_execution",
        "report_submission",
        "vulnerability_confirmation",
    )
    return any(bool(safety.get(key)) for key in unsafe_keys)


def _safety_metadata() -> dict[str, bool]:
    return {
        "local_only": True,
        "deterministic": True,
        "planning_only": True,
        "network_requests": False,
        "tool_execution": False,
        "browser_execution": False,
        "llm_provider_calls": False,
        "provider_execution": False,
        "target_mutation": False,
        "evidence_collection": False,
        "validation_execution": False,
        "report_submission": False,
        "vulnerability_confirmation": False,
        "requires_human_authorization_before_testing": True,
    }
