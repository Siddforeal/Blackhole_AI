"""
AI brain interface for Blackhole AI Workbench.

This module creates a deterministic, planning-only AI brain plan from research
state / case memory. It does not call LLM providers, send requests, execute
shell commands, launch browsers, mutate targets, or bypass authorization.

This is the bridge between structured case memory and the future LLM-powered
Blackhole reasoning brain.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class BrainAction:
    name: str
    endpoint: str | None
    phase: str
    rationale: str
    produces_artifact: str | None = None
    human_approval_required: bool = False
    blocked_by: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["blocked_by"] = list(self.blocked_by)
        return data


@dataclass(frozen=True)
class BrainFocusItem:
    endpoint: str
    priority_score: int
    priority_band: str
    triage_state: str
    reason: str
    hypotheses: tuple[str, ...]
    required_artifacts: tuple[str, ...]
    next_actions: tuple[BrainAction, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "endpoint": self.endpoint,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "triage_state": self.triage_state,
            "reason": self.reason,
            "hypotheses": list(self.hypotheses),
            "required_artifacts": list(self.required_artifacts),
            "next_actions": [action.to_dict() for action in self.next_actions],
            "planning_only": True,
            "execution_state": "not_executed",
        }


@dataclass(frozen=True)
class AIBrainPlan:
    target_name: str
    focus_queue: tuple[BrainFocusItem, ...]
    global_actions: tuple[BrainAction, ...]
    safety_gates: tuple[str, ...]
    provider_execution_enabled: bool = False
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "focus_queue": [item.to_dict() for item in self.focus_queue],
            "global_actions": [action.to_dict() for action in self.global_actions],
            "safety_gates": list(self.safety_gates),
            "provider_execution_enabled": self.provider_execution_enabled,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "markdown": render_ai_brain_plan_markdown(self),
        }


def build_ai_brain_plan(research_state_data: dict[str, Any]) -> AIBrainPlan:
    """Build a deterministic planning-only brain plan from research state JSON."""
    target_name = str(research_state_data.get("target_name") or "unknown-target")
    endpoints = list(research_state_data.get("endpoints") or [])

    focus_items = [_build_focus_item(endpoint) for endpoint in endpoints]
    focus_items.sort(key=_focus_sort_key)

    return AIBrainPlan(
        target_name=target_name,
        focus_queue=tuple(focus_items),
        global_actions=tuple(_global_actions(research_state_data)),
        safety_gates=tuple(_safety_gates()),
    )


def render_ai_brain_plan_markdown(plan: AIBrainPlan) -> str:
    """Render the AI brain plan as Markdown."""
    lines = [
        f"# Blackhole AI Brain Plan: {plan.target_name}",
        "",
        "> Planning-only AI brain interface. No LLM provider, browser, curl, Kali, or network execution is performed.",
        "",
        f"- Target: `{plan.target_name}`",
        f"- Focus items: `{len(plan.focus_queue)}`",
        f"- Provider execution enabled: `{plan.provider_execution_enabled}`",
        f"- Execution state: `{plan.execution_state}`",
        "",
        "## Safety Gates",
        "",
    ]

    for gate in plan.safety_gates:
        lines.append(f"- [ ] {gate}")

    lines.extend(["", "## Global Actions", ""])

    for action in plan.global_actions:
        blocked = ", ".join(action.blocked_by) or "none"
        lines.append(
            f"- `{action.phase}` — {action.name}: {action.rationale} "
            f"(approval={'yes' if action.human_approval_required else 'no'}, blocked_by={blocked})"
        )

    lines.extend(["", "## Focus Queue", ""])

    for index, item in enumerate(plan.focus_queue, start=1):
        lines.append(f"### {index}. `{item.endpoint}`")
        lines.append("")
        lines.append(f"- Priority: `{item.priority_band}` / `{item.priority_score}`")
        lines.append(f"- Triage state: `{item.triage_state}`")
        lines.append(f"- Reason: {item.reason}")
        lines.append("")
        lines.append("Hypotheses:")
        for hypothesis in item.hypotheses:
            lines.append(f"- `{hypothesis}`")
        lines.append("")
        lines.append("Required artifacts:")
        for artifact in item.required_artifacts:
            lines.append(f"- `{artifact}`")
        lines.append("")
        lines.append("Next actions:")
        for action in item.next_actions:
            blocked = ", ".join(action.blocked_by) or "none"
            lines.append(
                f"- `{action.phase}` — {action.name}: {action.rationale} "
                f"(artifact={action.produces_artifact or 'none'}, "
                f"approval={'yes' if action.human_approval_required else 'no'}, "
                f"blocked_by={blocked})"
            )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def _build_focus_item(endpoint_state: dict[str, Any]) -> BrainFocusItem:
    endpoint = str(endpoint_state.get("endpoint") or "unknown-endpoint")
    priority_score = int(endpoint_state.get("priority_score") or 0)
    priority_band = str(endpoint_state.get("priority_band") or "info")
    triage_state = str(endpoint_state.get("triage_state") or "watchlist")

    hypotheses = tuple(
        str(item.get("name"))
        for item in endpoint_state.get("hypotheses", [])
        if item.get("name")
    )

    artifacts = tuple(
        str(item.get("name"))
        for item in endpoint_state.get("artifacts", [])
        if item.get("name")
    )

    next_actions = tuple(_next_actions_for_endpoint(endpoint_state))

    return BrainFocusItem(
        endpoint=endpoint,
        priority_score=priority_score,
        priority_band=priority_band,
        triage_state=triage_state,
        reason=_focus_reason(priority_band, triage_state, hypotheses),
        hypotheses=hypotheses,
        required_artifacts=artifacts,
        next_actions=next_actions,
    )


def _focus_sort_key(item: BrainFocusItem) -> tuple[int, int, str]:
    triage_rank = {
        "ready-for-manual-validation": 0,
        "queued": 1,
        "watchlist": 2,
        "deprioritized": 3,
    }.get(item.triage_state, 2)

    return (triage_rank, -item.priority_score, item.endpoint)


def _focus_reason(priority_band: str, triage_state: str, hypotheses: tuple[str, ...]) -> str:
    if triage_state == "ready-for-manual-validation":
        return "High-signal endpoint with open hypotheses and planned evidence artifacts."
    if triage_state == "queued":
        return "Medium-priority endpoint worth reviewing after high-signal items."
    if triage_state == "deprioritized":
        return "Low-signal endpoint; keep in memory but avoid spending time unless new evidence appears."
    if hypotheses:
        return "Endpoint has hypotheses but not enough priority to lead the queue."
    return "Endpoint is retained for context."


def _next_actions_for_endpoint(endpoint_state: dict[str, Any]) -> list[BrainAction]:
    endpoint = str(endpoint_state.get("endpoint") or "unknown-endpoint")
    triage_state = str(endpoint_state.get("triage_state") or "watchlist")
    artifacts = list(endpoint_state.get("artifacts") or [])
    hypotheses = list(endpoint_state.get("hypotheses") or [])

    actions: list[BrainAction] = [
        BrainAction(
            name="Review endpoint memory",
            endpoint=endpoint,
            phase="analysis",
            rationale="Read endpoint priority, attack-surface groups, hypotheses, and planned artifacts before validation.",
            blocked_by=("scope-confirmation",),
        )
    ]

    if triage_state == "deprioritized":
        actions.append(
            BrainAction(
                name="Keep low-signal route on watchlist",
                endpoint=endpoint,
                phase="triage",
                rationale="Avoid spending validation time unless later evidence shows sensitive behavior.",
                produces_artifact="low-signal-deprioritization-note",
                blocked_by=("new-evidence-required",),
            )
        )
        return actions

    if hypotheses:
        actions.append(
            BrainAction(
                name="Select strongest open hypothesis",
                endpoint=endpoint,
                phase="analysis",
                rationale="Choose the hypothesis most likely to prove a real security boundary violation.",
                blocked_by=("manual-review",),
            )
        )

    approval_artifact = _first_approval_artifact(artifacts)

    if approval_artifact:
        actions.append(
            BrainAction(
                name="Prepare approval-gated evidence collection",
                endpoint=endpoint,
                phase="evidence-planning",
                rationale="A planned artifact requires human approval before collection.",
                produces_artifact=str(approval_artifact.get("name")),
                human_approval_required=True,
                blocked_by=("human-approval", "redaction-plan"),
            )
        )

    non_approval_artifact = _first_non_approval_artifact(artifacts)

    if non_approval_artifact:
        actions.append(
            BrainAction(
                name="Prepare non-executing artifact notes",
                endpoint=endpoint,
                phase="evidence-planning",
                rationale="Create or update notes/checklists that do not require active target interaction.",
                produces_artifact=str(non_approval_artifact.get("name")),
                blocked_by=("redaction-plan",),
            )
        )

    actions.append(
        BrainAction(
            name="Update research state after manual validation",
            endpoint=endpoint,
            phase="state-update",
            rationale="After the human researcher validates or rejects the hypothesis, update triage state, artifacts, and decisions.",
            blocked_by=("manual-validation-result",),
        )
    )

    return actions


def _first_approval_artifact(artifacts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for artifact in artifacts:
        if artifact.get("human_approval_required"):
            return artifact
    return None


def _first_non_approval_artifact(artifacts: list[dict[str, Any]]) -> dict[str, Any] | None:
    for artifact in artifacts:
        if not artifact.get("human_approval_required"):
            return artifact
    return None


def _global_actions(research_state_data: dict[str, Any]) -> list[BrainAction]:
    decisions = list(research_state_data.get("decisions") or [])
    decision_names = {str(item.get("name")) for item in decisions}

    actions = [
        BrainAction(
            name="Confirm scope and authorization",
            endpoint=None,
            phase="preflight",
            rationale="No research action should move forward until the target and test data are confirmed in scope.",
            human_approval_required=True,
            blocked_by=("program-scope", "controlled-accounts"),
        ),
        BrainAction(
            name="Review approval-gated artifacts",
            endpoint=None,
            phase="preflight",
            rationale="Identify artifacts that require human approval before collection.",
            human_approval_required=True,
            blocked_by=("human-approval",),
        ),
    ]

    if "prioritize-high-signal-endpoints" in decision_names:
        actions.append(
            BrainAction(
                name="Focus high-signal endpoints first",
                endpoint=None,
                phase="triage",
                rationale="Prioritize critical/high endpoints before low-signal routes.",
                blocked_by=("scope-confirmation",),
            )
        )

    return actions


def _safety_gates() -> list[str]:
    return [
        "scope-confirmation",
        "controlled-accounts",
        "human-approval",
        "redaction-plan",
        "manual-validation-result",
        "no-llm-provider-execution",
        "no-network-execution",
        "no-browser-execution",
        "no-shell-execution",
    ]
