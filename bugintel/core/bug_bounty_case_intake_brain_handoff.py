"""
Case intake brain handoff for Blackhole AI Workbench.

This module is planning-only. It does not send requests, execute shell commands,
launch browsers, call LLM providers, mutate targets, collect evidence, submit
reports, or confirm vulnerabilities.

It converts a bug-bounty-case-intake workflow JSON into a brain-readable case
context for later local reasoning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainFocusEndpoint:
    endpoint: str
    lane: str
    priority_score: int
    priority_band: str
    categories: tuple[str, ...]
    why_focus: tuple[str, ...]
    next_manual_steps: tuple[str, ...]
    evidence_requirement_names: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["categories"] = list(self.categories)
        data["why_focus"] = list(self.why_focus)
        data["next_manual_steps"] = list(self.next_manual_steps)
        data["evidence_requirement_names"] = list(self.evidence_requirement_names)
        data["planning_only"] = True
        data["execution_state"] = "not_executed"
        return data


@dataclass(frozen=True)
class CaseIntakeBrainEvidenceGap:
    endpoint: str
    gap_type: str
    description: str
    required_before_report: bool

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["planning_only"] = True
        data["execution_state"] = "not_executed"
        return data


@dataclass(frozen=True)
class CaseIntakeBrainHandoff:
    kind: str
    source_kind: str
    target_name: str
    status: str
    focus_endpoint_count: int
    deferred_endpoint_count: int
    focus_endpoints: tuple[CaseIntakeBrainFocusEndpoint, ...]
    deferred_endpoints: tuple[str, ...]
    evidence_gaps: tuple[CaseIntakeBrainEvidenceGap, ...]
    brain_questions: tuple[str, ...]
    brain_context_summary: tuple[str, ...]
    safety: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "source_kind": self.source_kind,
            "target_name": self.target_name,
            "status": self.status,
            "focus_endpoint_count": self.focus_endpoint_count,
            "deferred_endpoint_count": self.deferred_endpoint_count,
            "focus_endpoints": [endpoint.to_dict() for endpoint in self.focus_endpoints],
            "deferred_endpoints": list(self.deferred_endpoints),
            "evidence_gaps": [gap.to_dict() for gap in self.evidence_gaps],
            "brain_questions": list(self.brain_questions),
            "brain_context_summary": list(self.brain_context_summary),
            "safety": dict(self.safety),
            "planning_only": True,
            "execution_state": "not_executed",
        }


def build_case_intake_brain_handoff(intake_workflow: dict[str, Any]) -> CaseIntakeBrainHandoff:
    """Convert a bug-bounty-case-intake workflow into a brain-readable handoff."""
    source_kind = str(intake_workflow.get("kind") or "")
    target_name = str(intake_workflow.get("target_name") or "bug-bounty-target")
    top_endpoints = _objects(intake_workflow.get("top_endpoints"))
    source_safety = intake_workflow.get("safety") if isinstance(intake_workflow.get("safety"), dict) else {}

    if source_kind != "bug_bounty_case_intake_workflow":
        return _blocked_handoff(
            target_name=target_name,
            source_kind=source_kind,
            status="blocked-invalid-case-intake-workflow",
            reason="Input is not a bug_bounty_case_intake_workflow artifact.",
        )

    if _unsafe_source(source_safety):
        return _blocked_handoff(
            target_name=target_name,
            source_kind=source_kind,
            status="blocked-unsafe-case-intake-workflow",
            reason="Source intake workflow reports execution, target mutation, provider use, evidence collection, report submission, or vulnerability confirmation.",
        )

    focus_raw = [
        endpoint
        for endpoint in top_endpoints
        if str(endpoint.get("p1_p2_lane") or endpoint.get("lane") or "") in {"p1-potential-review", "p2-potential-review"}
    ]
    deferred_raw = [str(endpoint.get("endpoint") or "") for endpoint in top_endpoints if endpoint not in focus_raw]

    focus_endpoints = tuple(_focus_endpoint(endpoint) for endpoint in focus_raw)
    evidence_gaps = tuple(gap for endpoint in focus_raw for gap in _evidence_gaps(endpoint))

    status = "ready-for-brain-case-context" if focus_endpoints else "blocked-no-p1-p2-focus-endpoints"

    return CaseIntakeBrainHandoff(
        kind="case_intake_brain_handoff",
        source_kind=source_kind,
        target_name=target_name,
        status=status,
        focus_endpoint_count=len(focus_endpoints),
        deferred_endpoint_count=len([endpoint for endpoint in deferred_raw if endpoint]),
        focus_endpoints=focus_endpoints,
        deferred_endpoints=tuple(endpoint for endpoint in deferred_raw if endpoint),
        evidence_gaps=evidence_gaps,
        brain_questions=_brain_questions(focus_endpoints, evidence_gaps),
        brain_context_summary=_context_summary(target_name, focus_endpoints, evidence_gaps),
        safety=_safety_metadata(),
    )


def _focus_endpoint(endpoint: dict[str, Any]) -> CaseIntakeBrainFocusEndpoint:
    endpoint_value = str(endpoint.get("endpoint") or "")
    lane = str(endpoint.get("p1_p2_lane") or endpoint.get("lane") or "unknown")
    score = _int(endpoint.get("priority_score"))
    band = str(endpoint.get("priority_band") or "")
    categories = tuple(_string_list(endpoint.get("categories")))
    signal_names = tuple(_string_list(endpoint.get("signal_names")))
    next_steps = tuple(_string_list(endpoint.get("recommended_next_steps")))
    requirements = _objects(endpoint.get("evidence_requirements"))
    requirement_names = tuple(str(item.get("name") or "") for item in requirements if item.get("name"))

    return CaseIntakeBrainFocusEndpoint(
        endpoint=endpoint_value,
        lane=lane,
        priority_score=score,
        priority_band=band,
        categories=categories,
        why_focus=_why_focus(lane, score, categories, signal_names),
        next_manual_steps=next_steps,
        evidence_requirement_names=requirement_names,
    )


def _why_focus(
    lane: str,
    score: int,
    categories: tuple[str, ...],
    signal_names: tuple[str, ...],
) -> tuple[str, ...]:
    reasons: list[str] = []

    if lane == "p1-potential-review":
        reasons.append("Marked as P1-potential by the intake workflow.")
    elif lane == "p2-potential-review":
        reasons.append("Marked as P2-potential by the intake workflow.")

    if score >= 75:
        reasons.append("High static priority score suggests critical manual review value.")
    elif score >= 50:
        reasons.append("High static priority score suggests meaningful manual review value.")

    if "authorization-sensitive" in categories:
        reasons.append("Authorization-sensitive surface; check owned-vs-foreign access boundaries.")

    if "object-reference" in categories:
        reasons.append("Object-reference pattern; map identifiers and test only controlled objects.")

    if "file-surface" in categories:
        reasons.append("File surface; use synthetic files and avoid real user data.")

    if "auth-flow" in categories:
        reasons.append("Authentication/session surface; review redirects, tokens, CSRF, MFA, and logout behavior.")

    if any("billing" in signal for signal in signal_names):
        reasons.append("Billing or invoice signal; keep testing read-only and avoid real charges.")

    return tuple(dict.fromkeys(reasons))


def _evidence_gaps(endpoint: dict[str, Any]) -> tuple[CaseIntakeBrainEvidenceGap, ...]:
    endpoint_value = str(endpoint.get("endpoint") or "")
    requirements = _objects(endpoint.get("evidence_requirements"))

    gaps: list[CaseIntakeBrainEvidenceGap] = [
        CaseIntakeBrainEvidenceGap(
            endpoint=endpoint_value,
            gap_type="scope-proof",
            description="Confirm program scope, authorization, controlled accounts, and safe-testing constraints before manual testing.",
            required_before_report=True,
        )
    ]

    for requirement in requirements:
        name = str(requirement.get("name") or "")
        if requirement.get("redaction_required"):
            gaps.append(
                CaseIntakeBrainEvidenceGap(
                    endpoint=endpoint_value,
                    gap_type="redaction-required",
                    description=f"Evidence requirement '{name}' needs token, cookie, identifier, and user-data redaction.",
                    required_before_report=True,
                )
            )

        if requirement.get("human_approval_required"):
            gaps.append(
                CaseIntakeBrainEvidenceGap(
                    endpoint=endpoint_value,
                    gap_type="human-approval-required",
                    description=f"Evidence requirement '{name}' needs explicit human approval before active validation.",
                    required_before_report=True,
                )
            )

    return tuple(gaps)


def _brain_questions(
    focus_endpoints: tuple[CaseIntakeBrainFocusEndpoint, ...],
    evidence_gaps: tuple[CaseIntakeBrainEvidenceGap, ...],
) -> tuple[str, ...]:
    if not focus_endpoints:
        return (
            "Why did the intake workflow find no P1/P2 focus endpoints?",
            "What additional HAR, Burp, JS, endpoint-list, or notes should be collected?",
            "Which low-signal endpoints should be ignored until stronger evidence appears?",
        )

    questions = [
        "Which focus endpoint should be manually tested first, and why?",
        "Which endpoint has the strongest P1/P2 potential based on authorization, object-reference, file, auth-flow, billing, or export signals?",
        "What exact evidence is missing before any report claim can be written?",
        "Which endpoints should be deferred because they are low-signal or unsafe to test now?",
        "What manual tests can be performed with controlled accounts and without target mutation?",
    ]

    if evidence_gaps:
        questions.append("Which evidence gaps must be closed before report drafting?")

    return tuple(questions)


def _context_summary(
    target_name: str,
    focus_endpoints: tuple[CaseIntakeBrainFocusEndpoint, ...],
    evidence_gaps: tuple[CaseIntakeBrainEvidenceGap, ...],
) -> tuple[str, ...]:
    if not focus_endpoints:
        return (
            f"Target {target_name} has no P1/P2 focus endpoints in the intake workflow.",
            "Brain should request more input material before planning manual testing.",
        )

    top = focus_endpoints[0]
    return (
        f"Target {target_name} has {len(focus_endpoints)} P1/P2 focus endpoint(s).",
        f"Top focus endpoint is {top.endpoint} with lane {top.lane} and score {top.priority_score}.",
        f"There are {len(evidence_gaps)} evidence gap item(s) to consider before report drafting.",
        "All next steps remain planning-only and require human authorization before manual testing.",
    )


def _blocked_handoff(target_name: str, source_kind: str, status: str, reason: str) -> CaseIntakeBrainHandoff:
    gap = CaseIntakeBrainEvidenceGap(
        endpoint="",
        gap_type="blocked-input",
        description=reason,
        required_before_report=True,
    )

    return CaseIntakeBrainHandoff(
        kind="case_intake_brain_handoff",
        source_kind=source_kind,
        target_name=target_name,
        status=status,
        focus_endpoint_count=0,
        deferred_endpoint_count=0,
        focus_endpoints=(),
        deferred_endpoints=(),
        evidence_gaps=(gap,),
        brain_questions=("What valid case-intake workflow artifact should be provided?",),
        brain_context_summary=(reason,),
        safety=_safety_metadata(),
    )


def _unsafe_source(safety: dict[str, Any]) -> bool:
    unsafe_keys = (
        "network_requests",
        "tool_execution",
        "browser_execution",
        "provider_execution",
        "target_mutation",
        "evidence_collection",
        "report_submission",
        "vulnerability_confirmation",
    )

    return any(bool(safety.get(key)) for key in unsafe_keys)


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


def _objects(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    return [item for item in value if isinstance(item, dict)]


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []

    return [str(item) for item in value if str(item)]


def _int(value: Any) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return 0
