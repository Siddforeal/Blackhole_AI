"""
Bug bounty case intake workflow for Blackhole AI Workbench.

This module is planning-only. It does not send requests, execute shell commands,
launch browsers, call LLM providers, mutate targets, collect evidence, submit
reports, or confirm vulnerabilities.

It connects existing endpoint mining, endpoint priority, investigation planning,
and evidence requirement helpers into one human-facing intake packet for
authorized bug bounty work.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from bugintel.analyzers.endpoint_miner import mine_endpoints
from bugintel.core.endpoint_investigation import build_endpoint_investigation_profile
from bugintel.core.endpoint_priority import prioritize_endpoints
from bugintel.core.evidence_requirements import build_evidence_requirement_plan


@dataclass(frozen=True)
class BugBountyCaseIntakeEndpoint:
    endpoint: str
    normalized_path: str
    priority_score: int
    priority_band: str
    p1_p2_lane: str
    categories: tuple[str, ...]
    signal_names: tuple[str, ...]
    recommended_next_steps: tuple[str, ...]
    investigation_tasks: tuple[dict[str, Any], ...]
    evidence_requirements: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["categories"] = list(self.categories)
        data["signal_names"] = list(self.signal_names)
        data["recommended_next_steps"] = list(self.recommended_next_steps)
        data["investigation_tasks"] = list(self.investigation_tasks)
        data["evidence_requirements"] = list(self.evidence_requirements)
        data["planning_only"] = True
        data["execution_state"] = "not_executed"
        return data


@dataclass(frozen=True)
class BugBountyCaseIntakeWorkflow:
    kind: str
    target_name: str
    status: str
    endpoint_count: int
    selected_endpoint_count: int
    lane_counts: dict[str, int]
    top_endpoints: tuple[BugBountyCaseIntakeEndpoint, ...]
    manual_testing_plan: tuple[str, ...]
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "target_name": self.target_name,
            "status": self.status,
            "endpoint_count": self.endpoint_count,
            "selected_endpoint_count": self.selected_endpoint_count,
            "lane_counts": dict(self.lane_counts),
            "top_endpoints": [endpoint.to_dict() for endpoint in self.top_endpoints],
            "manual_testing_plan": list(self.manual_testing_plan),
            "safety": dict(self.safety),
            "planning_only": True,
            "execution_state": "not_executed",
        }


def build_bug_bounty_case_intake_workflow(
    text: str,
    *,
    target_name: str = "bug-bounty-target",
    top_n: int = 10,
) -> BugBountyCaseIntakeWorkflow:
    """Build a P1/P2-focused, planning-only bug bounty intake workflow."""
    endpoints = _endpoint_values_from_text(text)
    prioritized = prioritize_endpoints(endpoints)
    selected = prioritized[: max(1, top_n)]

    evidence_plan = build_evidence_requirement_plan([item.endpoint for item in selected])
    evidence_by_endpoint = {
        plan.endpoint: plan for plan in evidence_plan.endpoint_plans
    }

    intake_endpoints: list[BugBountyCaseIntakeEndpoint] = []

    for item in selected:
        profile = build_endpoint_investigation_profile(item.endpoint)
        evidence = evidence_by_endpoint.get(item.endpoint)
        requirements = evidence.requirements if evidence else ()

        intake_endpoints.append(
            BugBountyCaseIntakeEndpoint(
                endpoint=item.endpoint,
                normalized_path=item.normalized_path,
                priority_score=item.score,
                priority_band=item.band,
                p1_p2_lane=_p1_p2_lane(item.score, item.categories, tuple(signal.name for signal in item.signals)),
                categories=item.categories,
                signal_names=tuple(signal.name for signal in item.signals),
                recommended_next_steps=item.recommended_next_steps,
                investigation_tasks=tuple(
                    {
                        "title": task.title,
                        "task_type": task.task_type,
                        "priority": task.priority,
                        "agent_hint": task.agent_hint,
                        "requires_scope_guard": task.requires_scope_guard,
                        "requires_human_approval": task.requires_human_approval,
                    }
                    for task in profile.tasks
                ),
                evidence_requirements=tuple(requirement.to_dict() for requirement in requirements),
            )
        )

    lane_counts = _lane_counts(intake_endpoints)

    return BugBountyCaseIntakeWorkflow(
        kind="bug_bounty_case_intake_workflow",
        target_name=target_name,
        status="ready-for-human-manual-testing-plan" if intake_endpoints else "blocked-no-endpoints",
        endpoint_count=len(endpoints),
        selected_endpoint_count=len(intake_endpoints),
        lane_counts=lane_counts,
        top_endpoints=tuple(intake_endpoints),
        manual_testing_plan=_manual_testing_plan(intake_endpoints),
        safety=_safety_metadata(),
    )


def _endpoint_values_from_text(text: str) -> list[str]:
    normalized_text = text.replace("\\n", "\n").replace("\\r", "\n")
    mined = [endpoint.value for endpoint in mine_endpoints(normalized_text)]
    line_candidates: list[str] = []

    for line in normalized_text.splitlines():
        value = line.strip()

        if not value or value.startswith("#"):
            continue

        if value.startswith("/") or value.startswith("http://") or value.startswith("https://"):
            line_candidates.append(value)

    return sorted(set(mined + line_candidates))


def _p1_p2_lane(score: int, categories: tuple[str, ...], signal_names: tuple[str, ...]) -> str:
    signal_set = set(signal_names)
    category_set = set(categories)

    p1_signals = {
        "keyword:admin-control-plane",
        "keyword:secret-token-key",
        "keyword:billing-money",
        "keyword:tenant-project-boundary",
    }

    if score >= 75 and (signal_set & p1_signals):
        return "p1-potential-review"

    if score >= 50 or {
        "authorization-sensitive",
        "object-reference",
        "file-surface",
        "auth-flow",
    } & category_set:
        return "p2-potential-review"

    if score >= 25:
        return "watchlist"

    return "defer-low-signal"


def _lane_counts(endpoints: list[BugBountyCaseIntakeEndpoint]) -> dict[str, int]:
    lanes = {
        "p1-potential-review": 0,
        "p2-potential-review": 0,
        "watchlist": 0,
        "defer-low-signal": 0,
    }

    for endpoint in endpoints:
        lanes[endpoint.p1_p2_lane] = lanes.get(endpoint.p1_p2_lane, 0) + 1

    return lanes


def _manual_testing_plan(endpoints: list[BugBountyCaseIntakeEndpoint]) -> tuple[str, ...]:
    if not endpoints:
        return (
            "Add HAR, Burp export, JS, endpoint list, or notes containing in-scope endpoints.",
            "Confirm program authorization and scope before any manual testing.",
        )

    plan = [
        "Confirm target scope, safe-test accounts, rate limits, and allowed testing methods.",
        "Start with p1-potential-review and p2-potential-review endpoints only; defer low-signal paths.",
    ]

    for endpoint in endpoints[:5]:
        plan.append(
            f"Review {endpoint.endpoint} ({endpoint.p1_p2_lane}, score {endpoint.priority_score}) "
            "with controlled accounts and redacted request/response evidence."
        )

    plan.append("Stop if testing would access real user data, trigger payments, mutate production data, or exceed authorization.")
    plan.append("Use the evidence checklist before writing or submitting any vulnerability report.")

    return tuple(plan)


def _safety_metadata() -> dict[str, Any]:
    return {
        "planning_only": True,
        "execution_state": "not_executed",
        "network_requests": False,
        "tool_execution": False,
        "browser_execution": False,
        "provider_execution": False,
        "target_mutation": False,
        "evidence_collection": False,
        "report_submission": False,
        "vulnerability_confirmation": False,
        "requires_human_authorization_before_testing": True,
    }
