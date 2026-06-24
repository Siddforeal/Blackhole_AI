"""
Brain question answering over case-intake brain handoff.

This module is local, deterministic, and planning-only. It does not send
requests, execute tools, launch browsers, call LLM providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.

It answers practical brain questions from a case_intake_brain_handoff artifact:
- what to test first
- strongest P1/P2 potential
- missing evidence
- deferred endpoints
- safe manual tests with controlled accounts
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseIntakeBrainHandoffAnswer:
    question: str
    route: str
    answer: str
    target_name: str
    focus_endpoint: str | None
    handoff_status: str
    blocked: bool
    focus_endpoint_count: int
    deferred_endpoint_count: int
    evidence_gap_count: int
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    supporting_points: tuple[str, ...]
    recommended_next_action: str
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "case-intake-brain-handoff-answerer"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "case_intake_brain_handoff_answer",
            "source": self.source,
            "question": self.question,
            "route": self.route,
            "answer": self.answer,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "handoff_status": self.handoff_status,
            "blocked": self.blocked,
            "focus_endpoint_count": self.focus_endpoint_count,
            "deferred_endpoint_count": self.deferred_endpoint_count,
            "evidence_gap_count": self.evidence_gap_count,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "supporting_points": list(self.supporting_points),
            "recommended_next_action": self.recommended_next_action,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": _safety_metadata(),
        }

    def to_markdown(self, title: str = "Case Intake Brain Handoff Answer") -> str:
        lines = [
            f"# {title}",
            "",
            "## Question",
            "",
            self.question,
            "",
            "## Answer",
            "",
            self.answer,
            "",
            "## Handoff State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Handoff status: `{self.handoff_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Focus endpoints: `{self.focus_endpoint_count}`",
            f"- Deferred endpoints: `{self.deferred_endpoint_count}`",
            f"- Evidence gaps: `{self.evidence_gap_count}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Supporting Points",
            "",
        ]

        if self.supporting_points:
            for point in self.supporting_points:
                lines.append(f"- {point}")
        else:
            lines.append("- none")

        lines.extend(
            [
                "",
                "## Recommended Next Action",
                "",
                self.recommended_next_action,
                "",
                "## Safety",
                "",
                "- This answer is local, deterministic, and planning-only.",
                "- It does not send requests, execute tools, launch browsers, call providers, collect evidence, mutate targets, submit reports, or confirm vulnerabilities.",
                "- Manual testing still requires program scope, controlled accounts, and explicit human approval.",
                "",
            ]
        )

        return "\n".join(lines)


def answer_case_intake_brain_handoff_question(
    handoff: dict[str, Any],
    question: str,
    source: str = "case-intake-brain-handoff-answerer",
) -> CaseIntakeBrainHandoffAnswer:
    """Answer a local deterministic question from a case-intake brain handoff."""
    handoff_data = handoff if isinstance(handoff, dict) else {}
    normalized = _normalize(question)
    route = _route_question(normalized)
    answer, supporting_points, focus_endpoint, recommended_next_action = _answer_for_route(handoff_data, route)

    return CaseIntakeBrainHandoffAnswer(
        question=question.strip(),
        route=route,
        answer=answer,
        target_name=str(handoff_data.get("target_name") or "bug-bounty-target"),
        focus_endpoint=focus_endpoint,
        handoff_status=str(handoff_data.get("status") or "unknown"),
        blocked=_blocked(handoff_data),
        focus_endpoint_count=len(_focus_endpoints(handoff_data)),
        deferred_endpoint_count=len(_deferred_endpoints(handoff_data)),
        evidence_gap_count=len(_evidence_gaps(handoff_data)),
        validation_allowed=False,
        runtime_execution_allowed=False,
        report_submission_allowed=False,
        vulnerability_confirmation_allowed=False,
        supporting_points=tuple(supporting_points),
        recommended_next_action=recommended_next_action,
        source=source,
    )


def _answer_for_route(
    handoff: dict[str, Any],
    route: str,
) -> tuple[str, list[str], str | None, str]:
    if str(handoff.get("kind") or "") != "case_intake_brain_handoff":
        return (
            "The handoff artifact is invalid. Provide a case_intake_brain_handoff JSON file created by case-intake-brain-handoff.",
            ["Expected kind: case_intake_brain_handoff."],
            None,
            "Regenerate the handoff from a valid bug-bounty-case-intake JSON artifact.",
        )

    if _unsafe_source(handoff):
        return (
            "The handoff artifact is unsafe for this answerer because it indicates execution, mutation, collection, submission, or confirmation.",
            ["This layer only accepts local planning-only handoff artifacts."],
            None,
            "Regenerate the handoff from a safe planning-only intake artifact.",
        )

    focus_endpoints = _focus_endpoints(handoff)
    deferred = _deferred_endpoints(handoff)
    gaps = _evidence_gaps(handoff)

    if route == "test-first":
        endpoint = _strongest_endpoint(focus_endpoints)
        if endpoint is None:
            return _no_focus_answer(handoff, route)

        endpoint_value = str(endpoint.get("endpoint") or "")
        answer = (
            f"Start with `{endpoint_value}` because it has the strongest P1/P2 review signal in the handoff. "
            "Keep this as a manual planning step only: confirm scope, use controlled accounts, avoid target mutation, "
            "and close evidence gaps before any report claim."
        )
        points = [
            _endpoint_summary(endpoint),
            *_why_focus_points(endpoint),
            *_endpoint_gap_points(endpoint_value, gaps),
        ]
        return (
            answer,
            points,
            endpoint_value,
            f"Prepare a controlled-account, read-only manual validation plan for `{endpoint_value}` and review it before any live testing.",
        )

    if route == "strongest-potential":
        endpoint = _strongest_endpoint(focus_endpoints)
        if endpoint is None:
            return _no_focus_answer(handoff, route)

        endpoint_value = str(endpoint.get("endpoint") or "")
        answer = (
            f"`{endpoint_value}` has the strongest P1/P2 potential in this handoff based on lane, score, and focus reasons."
        )
        points = [
            _endpoint_summary(endpoint),
            *_why_focus_points(endpoint),
            *_next_manual_step_points(endpoint),
        ]
        return (
            answer,
            points,
            endpoint_value,
            f"Review why-focus reasons and evidence gaps for `{endpoint_value}` before designing any manual test.",
        )

    if route == "missing-evidence":
        if not gaps:
            return (
                "No evidence gaps are recorded in the handoff artifact.",
                ["This does not mean the vulnerability is confirmed; it only means the handoff has no recorded gaps."],
                None,
                "Review scope and authorization manually before creating validation steps.",
            )

        points = [_gap_summary(gap) for gap in gaps]
        return (
            f"{len(gaps)} evidence gap item(s) are recorded before report drafting or vulnerability claims.",
            points,
            _first_endpoint_from_gaps(gaps),
            "Close scope-proof, approval, and redaction gaps before report drafting or validation execution.",
        )

    if route == "deferred":
        if not deferred:
            return (
                "No deferred endpoints are recorded in the handoff artifact.",
                ["Only focus endpoints are present in this handoff."],
                None,
                "Stay on P1/P2 focus endpoints and avoid expanding into low-signal paths.",
            )

        return (
            f"Defer {len(deferred)} endpoint(s) because the intake handoff did not classify them as P1/P2 focus endpoints.",
            [f"Deferred endpoint: `{endpoint}`" for endpoint in deferred],
            None,
            "Ignore deferred endpoints until stronger authorization, object-reference, file, auth-flow, billing, or export signals appear.",
        )

    if route == "safe-manual-tests":
        if not focus_endpoints:
            return _no_focus_answer(handoff, route)

        endpoint = _strongest_endpoint(focus_endpoints)
        endpoint_value = str(endpoint.get("endpoint") or "") if endpoint else None
        points = _safe_manual_test_points(focus_endpoints)
        return (
            "Safe manual testing is limited to controlled-account, read-only planning until explicit human approval exists.",
            points,
            endpoint_value,
            "Design the controlled-account test matrix locally, then request human review before any target interaction.",
        )

    if route == "safety":
        return (
            "This answerer is local, deterministic, and planning-only.",
            [
                "Network requests: false",
                "Tool execution: false",
                "Browser execution: false",
                "LLM/provider calls: false",
                "Evidence collection: false",
                "Target mutation: false",
                "Report submission: false",
                "Vulnerability confirmation: false",
            ],
            None,
            "Keep all next steps as reviewable plans until explicit authorization and approval are present.",
        )

    if _blocked(handoff):
        return _no_focus_answer(handoff, route)

    return (
        f"Handoff status is `{handoff.get('status')}` with {len(focus_endpoints)} focus endpoint(s), {len(deferred)} deferred endpoint(s), and {len(gaps)} evidence gap(s).",
        list(_string_list(handoff.get("brain_context_summary"))) or ["No brain context summary is recorded."],
        str(focus_endpoints[0].get("endpoint")) if focus_endpoints else None,
        "Ask a concrete handoff question: test first, strongest P1/P2 potential, missing evidence, deferred endpoints, or safe manual tests.",
    )


def _normalize(question: str) -> str:
    return " ".join(question.strip().lower().replace("_", " ").replace("-", " ").split())


def _route_question(normalized: str) -> str:
    if not normalized:
        return "status"

    if any(term in normalized for term in ("safe manual", "controlled account", "controlled accounts", "manual tests", "safe tests")):
        return "safe-manual-tests"

    if any(term in normalized for term in ("missing evidence", "evidence missing", "what evidence", "evidence gap", "evidence gaps")):
        return "missing-evidence"

    if any(term in normalized for term in ("ignore", "defer", "deferred", "low signal", "low-signal")):
        return "deferred"

    if any(term in normalized for term in ("strongest", "highest", "best", "p1/p2", "p1 p2", "impact", "potential")):
        return "strongest-potential"

    if any(term in normalized for term in ("test first", "start first", "where start", "what should i test", "test now", "first")):
        return "test-first"

    if "safe" in normalized or "safety" in normalized:
        return "safety"

    return "status"


def _no_focus_answer(
    handoff: dict[str, Any],
    route: str,
) -> tuple[str, list[str], str | None, str]:
    status = str(handoff.get("status") or "unknown")
    summary = list(_string_list(handoff.get("brain_context_summary")))
    gaps = _evidence_gaps(handoff)

    points = summary or [f"Handoff status: {status}"]
    points.extend(_gap_summary(gap) for gap in gaps[:5])

    return (
        f"No P1/P2 focus endpoint is available for `{route}` because the handoff status is `{status}`.",
        points,
        None,
        "Collect better HAR, Burp, JS, endpoint-list, or notes material and regenerate the intake and handoff artifacts.",
    )


def _focus_endpoints(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        endpoint
        for endpoint in _objects(handoff.get("focus_endpoints"))
        if str(endpoint.get("endpoint") or "")
    ]


def _deferred_endpoints(handoff: dict[str, Any]) -> list[str]:
    return [endpoint for endpoint in _string_list(handoff.get("deferred_endpoints")) if endpoint]


def _evidence_gaps(handoff: dict[str, Any]) -> list[dict[str, Any]]:
    return _objects(handoff.get("evidence_gaps"))


def _strongest_endpoint(endpoints: list[dict[str, Any]]) -> dict[str, Any] | None:
    if not endpoints:
        return None

    return max(endpoints, key=_endpoint_rank)


def _endpoint_rank(endpoint: dict[str, Any]) -> tuple[int, int]:
    lane = str(endpoint.get("lane") or "")
    lane_rank = {
        "p1-potential-review": 3,
        "p2-potential-review": 2,
        "watchlist": 1,
        "defer-low-signal": 0,
    }.get(lane, 0)

    return (lane_rank, _int(endpoint.get("priority_score")))


def _endpoint_summary(endpoint: dict[str, Any]) -> str:
    return (
        f"Endpoint `{endpoint.get('endpoint')}` is in lane `{endpoint.get('lane')}` "
        f"with score `{_int(endpoint.get('priority_score'))}` and band `{endpoint.get('priority_band') or 'unknown'}`."
    )


def _why_focus_points(endpoint: dict[str, Any]) -> list[str]:
    return [f"Why focus: {point}" for point in _string_list(endpoint.get("why_focus"))[:6]]


def _next_manual_step_points(endpoint: dict[str, Any]) -> list[str]:
    return [f"Manual step: {point}" for point in _string_list(endpoint.get("next_manual_steps"))[:4]]


def _endpoint_gap_points(endpoint_value: str, gaps: list[dict[str, Any]]) -> list[str]:
    return [
        f"Evidence gap: {_gap_summary(gap)}"
        for gap in gaps
        if str(gap.get("endpoint") or "") == endpoint_value
    ][:6]


def _gap_summary(gap: dict[str, Any]) -> str:
    endpoint = str(gap.get("endpoint") or "case")
    gap_type = str(gap.get("gap_type") or "unknown")
    description = str(gap.get("description") or "")
    required = bool(gap.get("required_before_report"))

    return f"`{endpoint}` / `{gap_type}` / required_before_report={required}: {description}"


def _first_endpoint_from_gaps(gaps: list[dict[str, Any]]) -> str | None:
    for gap in gaps:
        endpoint = str(gap.get("endpoint") or "")
        if endpoint:
            return endpoint
    return None


def _safe_manual_test_points(focus_endpoints: list[dict[str, Any]]) -> list[str]:
    points = [
        "Confirm target scope, test window, rate limits, and allowed manual testing methods before touching the target.",
        "Use only controlled accounts and synthetic objects/files created for the test.",
        "Build an account matrix locally: owner account, second controlled account, lower-privileged controlled role, and logged-out state where applicable.",
        "Keep tests read-only unless the program explicitly allows mutation and a human approves the exact step.",
        "Capture only redacted evidence after approval; do not collect real user data, secrets, payments, or production records.",
    ]

    for endpoint in focus_endpoints[:3]:
        endpoint_value = str(endpoint.get("endpoint") or "")
        categories = set(_string_list(endpoint.get("categories")))

        if {"authorization-sensitive", "object-reference"} & categories:
            points.append(
                f"For `{endpoint_value}`, plan an owned-vs-second-controlled-account authorization boundary check using only synthetic object IDs."
            )

        if "file-surface" in categories:
            points.append(
                f"For `{endpoint_value}`, use only synthetic files and verify redaction rules before saving any evidence."
            )

        if "auth-flow" in categories:
            points.append(
                f"For `{endpoint_value}`, review redirects, tokens, CSRF, MFA, and logout behavior without bypass attempts or automation."
            )

    return tuple(dict.fromkeys(points))


def _blocked(handoff: dict[str, Any]) -> bool:
    status = str(handoff.get("status") or "")
    return (
        str(handoff.get("kind") or "") != "case_intake_brain_handoff"
        or status.startswith("blocked")
        or _unsafe_source(handoff)
    )


def _unsafe_source(handoff: dict[str, Any]) -> bool:
    safety = handoff.get("safety") if isinstance(handoff.get("safety"), dict) else {}
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


def _safety_metadata() -> dict[str, Any]:
    return {
        "local_only": True,
        "deterministic": True,
        "planning_only": True,
        "network_requests": False,
        "network_interaction": False,
        "tool_execution": False,
        "browser_execution": False,
        "llm_provider_calls": False,
        "provider_execution": False,
        "target_mutation": False,
        "evidence_collection": False,
        "validation_execution": False,
        "runtime_execution_allowed": False,
        "report_submission": False,
        "vulnerability_confirmation": False,
        "requires_human_authorization_before_testing": True,
    }
