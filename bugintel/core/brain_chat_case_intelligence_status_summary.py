"""
Brain chat case intelligence status summary.

This module summarizes local case state across the evidence, approval,
validation, step-review, and execution-gate proposal chain. It is an
intelligence/status layer only. It does not execute tools, collect evidence,
send requests, call providers, mutate targets, submit reports, or confirm
vulnerabilities.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CaseChainPosition:
    stage: str
    status: str
    ready: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "status": self.status,
            "ready": self.ready,
        }


@dataclass(frozen=True)
class BrainChatCaseIntelligenceStatusSummary:
    target_name: str
    focus_endpoint: str | None
    current_stage: str
    current_status: str
    blocked: bool
    validation_allowed: bool
    runtime_execution_allowed: bool
    report_submission_allowed: bool
    vulnerability_confirmation_allowed: bool
    safest_next_action: str
    blockers: tuple[str, ...]
    missing_evidence: tuple[str, ...]
    chain_position: tuple[CaseChainPosition, ...]
    evidence_counts: dict[str, int]
    planning_only: bool = True
    execution_state: str = "not_executed"
    source: str = "brain-chat-case-intelligence-status-summary"

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_case_intelligence_status_summary",
            "source": self.source,
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "current_stage": self.current_stage,
            "current_status": self.current_status,
            "blocked": self.blocked,
            "validation_allowed": self.validation_allowed,
            "runtime_execution_allowed": self.runtime_execution_allowed,
            "report_submission_allowed": self.report_submission_allowed,
            "vulnerability_confirmation_allowed": self.vulnerability_confirmation_allowed,
            "safest_next_action": self.safest_next_action,
            "blockers": list(self.blockers),
            "missing_evidence": list(self.missing_evidence),
            "chain_position": [item.to_dict() for item in self.chain_position],
            "evidence_counts": dict(self.evidence_counts),
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "safety": {
                "local_only": True,
                "planning_only": True,
                "network_interaction": False,
                "target_mutation": False,
                "tool_execution": False,
                "browser_execution": False,
                "llm_provider_calls": False,
                "provider_execution": False,
                "evidence_collection": False,
                "validation_execution": False,
                "runtime_execution_allowed": False,
                "report_submission": False,
                "vulnerability_confirmation": False,
            },
        }

    def to_markdown(self, title: str = "Brain Chat Case Intelligence Status Summary") -> str:
        lines = [
            f"# {title}",
            "",
            "## Current State",
            "",
            f"- Target: `{self.target_name}`",
            f"- Focus endpoint: `{self.focus_endpoint or 'none'}`",
            f"- Current stage: `{self.current_stage}`",
            f"- Current status: `{self.current_status}`",
            f"- Blocked: `{self.blocked}`",
            f"- Validation allowed: `{self.validation_allowed}`",
            f"- Runtime execution allowed: `{self.runtime_execution_allowed}`",
            f"- Report submission allowed: `{self.report_submission_allowed}`",
            f"- Vulnerability confirmation allowed: `{self.vulnerability_confirmation_allowed}`",
            "",
            "## Safest Next Action",
            "",
            self.safest_next_action,
            "",
            "## Blockers",
            "",
        ]

        if self.blockers:
            for item in self.blockers:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Missing Evidence", ""])
        if self.missing_evidence:
            for item in self.missing_evidence:
                lines.append(f"- {item}")
        else:
            lines.append("- none")

        lines.extend(["", "## Chain Position", ""])
        for item in self.chain_position:
            lines.append(f"- {item.stage}: `{item.status}` ready=`{item.ready}`")

        lines.extend(["", "## Evidence Counts", ""])
        for key, value in sorted(self.evidence_counts.items()):
            lines.append(f"- {key}: `{value}`")

        lines.extend(
            [
                "",
                "## Safety",
                "",
                "- This summary is local and planning-only.",
                "- It does not execute validation, collect evidence, send requests, submit reports, or confirm vulnerabilities.",
                "",
            ]
        )

        return "\n".join(lines)


def build_case_intelligence_status_summary(
    *,
    session: Any | None = None,
    checklist: Any | None = None,
    evidence_review_gate: Any | None = None,
    approval_request: Any | None = None,
    approval_decision: Any | None = None,
    validation_plan: Any | None = None,
    step_review_gate: Any | None = None,
    step_approval_request: Any | None = None,
    step_approval_decision: Any | None = None,
    execution_gate_proposal: Any | None = None,
    execution_gate_review_packet: Any | None = None,
    source: str = "brain-chat-case-intelligence-status-summary",
) -> BrainChatCaseIntelligenceStatusSummary:
    artifacts = (
        ("session", session),
        ("evidence-checklist", checklist),
        ("evidence-review-gate", evidence_review_gate),
        ("evidence-approval-request", approval_request),
        ("evidence-approval-decision", approval_decision),
        ("approved-validation-plan", validation_plan),
        ("validation-step-review-gate", step_review_gate),
        ("validation-step-approval-request", step_approval_request),
        ("validation-step-approval-decision", step_approval_decision),
        ("execution-gate-proposal", execution_gate_proposal),
        ("execution-gate-proposal-review", execution_gate_review_packet),
    )

    target_name, focus_endpoint = _target_and_focus(artifacts)
    chain_position = tuple(_chain_positions(artifacts))
    current = _latest_position(chain_position)

    blockers = tuple(_collect_blockers(artifacts, checklist))
    missing_evidence = tuple(_missing_evidence(checklist))
    evidence_counts = _evidence_counts(checklist)

    runtime_execution_allowed = False
    report_submission_allowed = False
    vulnerability_confirmation_allowed = False
    validation_allowed = _validation_allowed(validation_plan, step_review_gate, step_approval_request, step_approval_decision)

    blocked = bool(blockers) or _status_is_blocked(current.status) or bool(missing_evidence)

    return BrainChatCaseIntelligenceStatusSummary(
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        current_stage=current.stage,
        current_status=current.status,
        blocked=blocked,
        validation_allowed=validation_allowed,
        runtime_execution_allowed=runtime_execution_allowed,
        report_submission_allowed=report_submission_allowed,
        vulnerability_confirmation_allowed=vulnerability_confirmation_allowed,
        safest_next_action=_safest_next_action(
            current_stage=current.stage,
            current_status=current.status,
            blocked=blocked,
            missing_evidence=missing_evidence,
            blockers=blockers,
            validation_allowed=validation_allowed,
            runtime_execution_allowed=runtime_execution_allowed,
        ),
        blockers=blockers,
        missing_evidence=missing_evidence,
        chain_position=chain_position,
        evidence_counts=evidence_counts,
        source=source,
    )


def _to_dict(obj: Any) -> dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "to_dict"):
        try:
            data = obj.to_dict()
            if isinstance(data, dict):
                return data
        except TypeError:
            pass
    return {}


def _target_and_focus(artifacts: tuple[tuple[str, Any | None], ...]) -> tuple[str, str | None]:
    for _, artifact in reversed(artifacts):
        data = _to_dict(artifact)
        target = data.get("target_name") or data.get("target")
        if target:
            return str(target), _string_or_none(data.get("focus_endpoint"))

    session = dict(artifacts).get("session")
    turns = getattr(session, "turns", None)
    if turns:
        latest = turns[-1]
        target = getattr(latest, "target_name", None)
        focus = getattr(latest, "focus_endpoint", None)
        if target:
            return str(target), _string_or_none(focus)

    return "unknown", None


def _chain_positions(artifacts: tuple[tuple[str, Any | None], ...]) -> list[CaseChainPosition]:
    positions: list[CaseChainPosition] = []
    for stage, artifact in artifacts:
        if artifact is None:
            continue

        data = _to_dict(artifact)
        status = _status_from_data(stage, data)
        ready = _ready_from_data(status, data)
        positions.append(CaseChainPosition(stage=stage, status=status, ready=ready))

    if not positions:
        positions.append(CaseChainPosition(stage="case", status="no-local-case-artifacts", ready=False))

    return positions


def _latest_position(chain_position: tuple[CaseChainPosition, ...]) -> CaseChainPosition:
    return chain_position[-1] if chain_position else CaseChainPosition("case", "no-local-case-artifacts", False)


def _status_from_data(stage: str, data: dict[str, Any]) -> str:
    for key in (
        "review_status",
        "proposal_status",
        "request_status",
        "plan_status",
        "gate_status",
        "approval_status",
        "decision",
        "status",
    ):
        value = data.get(key)
        if value not in (None, ""):
            return str(value)

    if stage == "evidence-checklist":
        complete = data.get("complete")
        if complete is True:
            return "complete"
        if complete is False:
            return "incomplete"

    if stage == "session":
        execution_state = data.get("execution_state")
        if execution_state:
            return str(execution_state)
        return "loaded"

    return "present"


def _ready_from_data(status: str, data: dict[str, Any]) -> bool:
    for key in (
        "design_review_ready",
        "execution_gate_proposal_ready",
        "effective_step_approval_granted",
        "step_review_ready",
        "validation_allowed",
        "effective_approval_granted",
        "validation_approval_ready",
        "complete",
        "reportable",
    ):
        value = data.get(key)
        if isinstance(value, bool):
            return value

    return status.startswith("ready-")


def _status_is_blocked(status: str) -> bool:
    normalized = status.lower()
    return (
        normalized.startswith("blocked")
        or "blocked" in normalized
        or "pending" in normalized
        or normalized in {"incomplete", "not_executed", "no-local-case-artifacts"}
    )


def _collect_blockers(
    artifacts: tuple[tuple[str, Any | None], ...],
    checklist: Any | None,
) -> list[str]:
    blockers: list[str] = []
    for _, artifact in artifacts:
        data = _to_dict(artifact)
        for key in ("blockers", "blocking_reasons"):
            value = data.get(key)
            if isinstance(value, list):
                blockers.extend(str(item) for item in value)
            elif isinstance(value, tuple):
                blockers.extend(str(item) for item in value)

    missing = _missing_evidence(checklist)
    if missing:
        blockers.append(f"{len(missing)} evidence item(s) are still missing.")

    return list(dict.fromkeys(item for item in blockers if item))


def _missing_evidence(checklist: Any | None) -> list[str]:
    if checklist is None:
        return []

    items = _checklist_items(checklist)
    missing: list[str] = []
    for item in items:
        label = item.get("label") or item.get("name")
        status = item.get("status")
        if label and status == "missing":
            missing.append(str(label))
    return missing


def _checklist_items(checklist: Any) -> list[dict[str, Any]]:
    data = _to_dict(checklist)
    for key in ("items", "evidence_items", "checklist"):
        value = data.get(key)
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]

    raw_items = getattr(checklist, "items", None)
    if raw_items:
        result = []
        for item in raw_items:
            result.append(
                {
                    "label": getattr(item, "label", None),
                    "status": getattr(item, "status", None),
                }
            )
        return result

    return []


def _evidence_counts(checklist: Any | None) -> dict[str, int]:
    default = {
        "total": 0,
        "missing": 0,
        "collected": 0,
        "review-needed": 0,
        "blocked": 0,
    }
    if checklist is None:
        return default

    data = _to_dict(checklist)
    counts = data.get("counts")
    if isinstance(counts, dict):
        merged = dict(default)
        for key, value in counts.items():
            try:
                merged[str(key)] = int(value)
            except (TypeError, ValueError):
                pass
        return merged

    items = _checklist_items(checklist)
    result = dict(default)
    result["total"] = len(items)
    for item in items:
        status = str(item.get("status", "missing"))
        result[status] = result.get(status, 0) + 1
    return result


def _validation_allowed(*artifacts: Any | None) -> bool:
    for artifact in reversed(artifacts):
        data = _to_dict(artifact)
        value = data.get("validation_allowed")
        if isinstance(value, bool):
            return value
    return False


def _safest_next_action(
    *,
    current_stage: str,
    current_status: str,
    blocked: bool,
    missing_evidence: tuple[str, ...],
    blockers: tuple[str, ...],
    validation_allowed: bool,
    runtime_execution_allowed: bool,
) -> str:
    if missing_evidence:
        return "Collect or mark the missing local evidence items before requesting validation or approval."

    if blockers:
        return "Resolve the listed blockers before advancing the case chain."

    if not validation_allowed:
        return "Keep validation disabled and advance only through local review or approval packets."

    if not runtime_execution_allowed:
        return "Keep runtime execution disabled; use local planning and human review only."

    if blocked:
        return f"Review `{current_stage}` status `{current_status}` and resolve blocked state before continuing."

    return "Continue with local human review; do not execute, collect evidence, submit reports, or confirm vulnerabilities from this summary."


def _string_or_none(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value)
