"""
Brain decision gate for Blackhole AI Workbench.

This module converts a brain-review JSON artifact into a planning-only decision
gate. It does not call LLM providers, send requests, execute shell commands,
launch browsers, use Kali tools, mutate targets, or bypass authorization.

The decision gate is intentionally conservative: it never marks a finding as
confirmed. It only decides whether the next safe state is manual validation,
blocked, deprioritized, or needs more planning.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class DecisionBlocker:
    name: str
    severity: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class BrainDecisionGate:
    target_name: str
    focus_endpoint: str | None
    decision: str
    rationale: str
    blockers: tuple[DecisionBlocker, ...]
    required_next_steps: tuple[str, ...]
    reportable: bool = False
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_endpoint": self.focus_endpoint,
            "decision": self.decision,
            "rationale": self.rationale,
            "blockers": [blocker.to_dict() for blocker in self.blockers],
            "required_next_steps": list(self.required_next_steps),
            "reportable": self.reportable,
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_brain_decision_gate_markdown(self),
        }


def build_brain_decision_gate(brain_review_data: dict[str, Any]) -> BrainDecisionGate:
    """Build a conservative planning-only decision gate from brain-review JSON."""
    target_name = str(brain_review_data.get("target_name") or "unknown-target")
    focus_endpoint = brain_review_data.get("focus_endpoint")
    focus_endpoint = str(focus_endpoint) if focus_endpoint else None

    sections = list(brain_review_data.get("sections") or [])
    section_map = {
        str(section.get("title") or ""): str(section.get("content") or "")
        for section in sections
    }

    safety_gates = tuple(str(item) for item in brain_review_data.get("safety_gates") or [])
    blockers = tuple(_build_blockers(focus_endpoint, section_map, safety_gates))
    required_next_steps = tuple(_required_next_steps(section_map, blockers))

    decision, rationale = _decision_and_rationale(focus_endpoint, blockers, section_map)

    return BrainDecisionGate(
        target_name=target_name,
        focus_endpoint=focus_endpoint,
        decision=decision,
        rationale=rationale,
        blockers=blockers,
        required_next_steps=required_next_steps,
        reportable=False,
    )


def render_brain_decision_gate_markdown(gate: BrainDecisionGate) -> str:
    """Render the decision gate as Markdown."""
    lines = [
        f"# Blackhole Brain Decision Gate: {gate.target_name}",
        "",
        "> Planning-only decision gate. This does not confirm a vulnerability.",
        "",
        f"- Target: `{gate.target_name}`",
        f"- Focus endpoint: `{gate.focus_endpoint or 'none'}`",
        f"- Decision: `{gate.decision}`",
        f"- Reportable: `{gate.reportable}`",
        f"- Provider execution enabled: `{gate.provider_execution_enabled}`",
        f"- Execution state: `{gate.execution_state}`",
        "",
        "## Rationale",
        "",
        gate.rationale,
        "",
        "## Blockers",
        "",
    ]

    if gate.blockers:
        for blocker in gate.blockers:
            lines.append(f"- `{blocker.severity}` / `{blocker.name}` — {blocker.reason}")
    else:
        lines.append("- No blockers were detected in the review artifact.")

    lines.extend(["", "## Required Next Steps", ""])

    for step in gate.required_next_steps:
        lines.append(f"- [ ] {step}")

    lines.extend(
        [
            "",
            "## Safety Decision",
            "",
            "This gate cannot mark anything as confirmed or reportable without manually validated evidence.",
            "Use this only to decide the next safe planning or validation step.",
        ]
    )

    return "\n".join(lines).rstrip() + "\n"


def _build_blockers(
    focus_endpoint: str | None,
    section_map: dict[str, str],
    safety_gates: tuple[str, ...],
) -> list[DecisionBlocker]:
    blockers: list[DecisionBlocker] = []

    if not focus_endpoint:
        blockers.append(
            DecisionBlocker(
                name="missing-focus-endpoint",
                severity="high",
                reason="No focus endpoint was available, so Blackhole cannot select a validation target.",
            )
        )

    if "scope-confirmation" in safety_gates:
        blockers.append(
            DecisionBlocker(
                name="scope-confirmation-required",
                severity="critical",
                reason="Scope and authorization must be confirmed before any active validation.",
            )
        )

    if "controlled-accounts" in safety_gates:
        blockers.append(
            DecisionBlocker(
                name="controlled-accounts-required",
                severity="critical",
                reason="Controlled accounts or controlled objects are required before validation.",
            )
        )

    approvals = section_map.get("Human Approvals Required", "")
    if "require approval" in approvals.lower() or "approval=yes" in approvals.lower():
        blockers.append(
            DecisionBlocker(
                name="human-approval-required",
                severity="high",
                reason="The review contains approval-gated evidence collection.",
            )
        )

    evidence = section_map.get("Evidence Artifacts Needed", "")
    if not evidence.strip() or "No required artifacts" in evidence:
        blockers.append(
            DecisionBlocker(
                name="missing-evidence-plan",
                severity="medium",
                reason="No evidence artifact plan was found in the brain review.",
            )
        )

    stop_conditions = section_map.get("Stop Conditions", "")
    if not stop_conditions.strip():
        blockers.append(
            DecisionBlocker(
                name="missing-stop-conditions",
                severity="medium",
                reason="No stop conditions were found in the brain review.",
            )
        )

    return blockers


def _required_next_steps(
    section_map: dict[str, str],
    blockers: tuple[DecisionBlocker, ...] | list[DecisionBlocker],
) -> list[str]:
    steps = [
        "Confirm program scope and authorization.",
        "Confirm controlled test accounts, tenants, files, objects, or projects are available.",
        "Review and apply redaction requirements before collecting or sharing evidence.",
    ]

    blocker_names = {blocker.name for blocker in blockers}

    if "human-approval-required" in blocker_names:
        steps.append("Obtain human approval before collecting approval-gated evidence.")

    if "missing-evidence-plan" in blocker_names:
        steps.append("Create an evidence artifact plan before validation.")

    next_step = section_map.get("Next Manual Validation Step", "").strip()
    if next_step:
        steps.append("Review the suggested next manual validation step from the brain review.")

    steps.append("Keep finding status as unconfirmed until manually validated evidence exists.")

    return steps


def _decision_and_rationale(
    focus_endpoint: str | None,
    blockers: tuple[DecisionBlocker, ...] | list[DecisionBlocker],
    section_map: dict[str, str],
) -> tuple[str, str]:
    blocker_names = {blocker.name for blocker in blockers}

    if not focus_endpoint:
        return (
            "blocked",
            "No focus endpoint was available, so the case cannot safely proceed to validation.",
        )

    if "scope-confirmation-required" in blocker_names or "controlled-accounts-required" in blocker_names:
        return (
            "blocked-pending-scope-and-controls",
            "The endpoint is selected, but scope confirmation and controlled test assets are required before validation.",
        )

    if "human-approval-required" in blocker_names:
        return (
            "ready-for-human-approval",
            "The endpoint has a validation path, but approval-gated evidence collection must be approved first.",
        )

    hypotheses = section_map.get("Open Hypotheses To Review", "")
    evidence = section_map.get("Evidence Artifacts Needed", "")

    if hypotheses.strip() and evidence.strip():
        return (
            "ready-for-manual-validation",
            "The review contains hypotheses and evidence artifacts, but validation must still be performed manually.",
        )

    return (
        "needs-more-planning",
        "The review does not contain enough structured hypothesis and evidence context to proceed.",
    )
