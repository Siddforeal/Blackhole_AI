"""Research investigation plan packet builder.

v1.10.0 milestone:
selected research hypothesis -> local-only investigation plan.

This module is intentionally planning-only. It does not generate commands,
execute tools, interact with targets, browse, collect evidence, validate a
finding, confirm a vulnerability, or submit a report.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


SAFETY_FLAGS: dict[str, bool] = {
    "web_browsing": False,
    "network_interaction": False,
    "command_generation": False,
    "tool_execution": False,
    "browser_execution": False,
    "curl_execution": False,
    "kali_execution": False,
    "burp_execution": False,
    "target_interaction": False,
    "evidence_collection": False,
    "validation_execution": False,
    "report_submission": False,
    "vulnerability_confirmation": False,
}


REJECTED_ACTIONS: list[dict[str, str]] = [
    {
        "action": "Generate shell, curl, browser, Burp, or Kali commands",
        "reason": "The investigation plan packet is local-only planning and must not produce executable testing steps.",
    },
    {
        "action": "Interact with a target or live service",
        "reason": "Target interaction belongs to a later explicitly approved validation stage.",
    },
    {
        "action": "Collect evidence",
        "reason": "This packet can list evidence requirements, but it must not collect or claim evidence.",
    },
    {
        "action": "Validate exploitability",
        "reason": "Validation is gated separately and remains disabled here.",
    },
    {
        "action": "Confirm a vulnerability",
        "reason": "The packet preserves hypotheses as hypotheses until later evidence-backed review.",
    },
    {
        "action": "Submit or prepare a final report as confirmed",
        "reason": "Report submission and confirmation require validated evidence and human approval.",
    },
]


@dataclass(frozen=True)
class InvestigationTemplate:
    focus: str
    investigation_phases: tuple[str, ...]
    review_questions: tuple[str, ...]
    evidence_requirements: tuple[str, ...]
    local_only_checks: tuple[str, ...]


TEMPLATES: dict[str, InvestigationTemplate] = {
    "worker-execution-trust-boundary": InvestigationTemplate(
        focus="Agent, runner, worker, deployment, package, job, or execution trust boundary.",
        investigation_phases=(
            "Map execution entry points and the product components that can influence worker-side behavior.",
            "Separate trusted administrator intent from data supplied by packages, imports, jobs, webhooks, templates, or deployment metadata.",
            "Review staging, unpacking, templating, variable expansion, environment construction, and script-selection logic before execution.",
            "Identify whether untrusted data can cross from control-plane state into worker-side execution context.",
            "Define later proof requirements without performing validation or claiming exploitability.",
        ),
        review_questions=(
            "Which actor or artifact can influence the worker/deployment input?",
            "Where does data cross from a control-plane object into worker-side execution?",
            "Are package names, paths, references, templates, variables, or hooks normalized and confined before use?",
            "Is the behavior intended script execution, or can untrusted data replace a trusted executable/script?",
            "Which product-level permissions and preconditions must be proven later?",
        ),
        evidence_requirements=(
            "Source references for worker/deployment entry points.",
            "Data-flow notes from attacker-influenced artifact to execution-sensitive decision.",
            "Trust-boundary notes explaining expected confinement or authorization assumptions.",
            "Human-reviewed impact hypothesis that does not claim confirmation.",
        ),
        local_only_checks=(
            "Review source, docs, local fixtures, or existing offline artifacts only.",
            "Keep runtime validation and target interaction blocked.",
            "Keep any future executable proof separate from this planning packet.",
        ),
    ),
    "input-to-filesystem-trust-boundary": InvestigationTemplate(
        focus="Import, export, archive, package, migration, upload, extraction, or filesystem write trust boundary.",
        investigation_phases=(
            "Map parsing and unpacking paths from input artifact to filesystem destination.",
            "Identify canonicalization, traversal, symlink, hardlink, overwrite, extraction-order, and cleanup controls.",
            "Trace whether untrusted names, metadata, archive entries, or package references reach write/copy/move/delete operations.",
            "Separate helper-level unsafe behavior from real product workflow reachability.",
            "Define later proof requirements without creating payloads or performing validation.",
        ),
        review_questions=(
            "Which parser accepts attacker-controlled paths, names, metadata, or archive entries?",
            "Is destination confinement enforced before every filesystem operation?",
            "Can helper-level behavior be reached through a real product workflow?",
            "Which role can provide the artifact: unauthenticated user, ordinary user, package contributor, admin, or local operator?",
            "What non-destructive later proof would demonstrate durable impact?",
        ),
        evidence_requirements=(
            "Source references for parser, extractor, importer, or filesystem sink code.",
            "Canonical destination-root and path-normalization notes.",
            "Product reachability notes for the real workflow.",
            "Human-reviewed impact hypothesis that does not claim confirmation.",
        ),
        local_only_checks=(
            "Review local source/static artifacts only.",
            "Do not generate traversal payloads in this packet.",
            "Keep runtime validation and evidence collection blocked.",
        ),
    ),
    "authorization-admin-boundary": InvestigationTemplate(
        focus="Authorization, administrative access control, RBAC, tenant, ownership, or permission boundary.",
        investigation_phases=(
            "Map roles, permissions, ownership checks, tenant context, and server-side authorization gates.",
            "Identify actions where UI restrictions may differ from backend enforcement.",
            "Trace whether object identifiers, tenant IDs, role fields, permission flags, or admin context can be influenced by request data.",
            "Separate authentication presence from authorization correctness.",
            "Define later proof requirements without sending requests or validating access.",
        ),
        review_questions=(
            "Which role is expected to perform the sensitive action?",
            "Where is the server-side authorization decision made?",
            "Can object ownership, tenant context, role context, or permission state be influenced by caller-controlled data?",
            "Are administrative APIs protected by both route-level and object-level checks?",
            "What later safe validation would distinguish intended access from privilege escalation?",
        ),
        evidence_requirements=(
            "Source references for route handlers, controllers, middleware, policies, or permission checks.",
            "Role/permission matrix notes.",
            "Object ownership and tenant-boundary notes.",
            "Human-reviewed impact hypothesis that does not claim confirmation.",
        ),
        local_only_checks=(
            "Review docs, source, and existing local artifacts only.",
            "Do not propose authenticated A/B request testing in this packet.",
            "Keep validation blocked pending explicit human approval.",
        ),
    ),
}


DEFAULT_TEMPLATE = InvestigationTemplate(
    focus="Selected hypothesis requiring local-only investigation planning.",
    investigation_phases=(
        "Map the selected attack surface and trust boundary.",
        "Identify attacker-influenced input and trusted sink assumptions.",
        "List product-level reachability questions.",
        "List evidence requirements for later human-approved validation.",
    ),
    review_questions=(
        "What is the trusted boundary?",
        "What input may be attacker-controlled?",
        "What sink, security decision, or trust assumption could be affected?",
        "What proof would be needed later without overclaiming now?",
    ),
    evidence_requirements=(
        "Source or documentation references.",
        "Data-flow notes.",
        "Reachability notes.",
        "Human-reviewed impact hypothesis with no confirmation claim.",
    ),
    local_only_checks=(
        "Review local artifacts only.",
        "Keep all execution, target interaction, evidence collection, and validation blocked.",
    ),
)


def load_json(path: str | Path) -> dict[str, Any]:
    """Load a JSON object from disk."""

    with Path(path).open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return data


def write_json(path: str | Path, data: dict[str, Any]) -> None:
    """Write a deterministic JSON object."""

    Path(path).write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown(path: str | Path, text: str) -> None:
    """Write markdown output."""

    Path(path).write_text(text, encoding="utf-8")


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _clean_text(value: Any, default: str = "") -> str:
    if isinstance(value, str) and value.strip():
        return value.strip()
    if value is None:
        return default
    text = str(value).strip()
    return text if text else default


def _first_text(*values: Any, default: str = "") -> str:
    for value in values:
        text = _clean_text(value)
        if text:
            return text
    return default


def _target_name(selection_packet: dict[str, Any]) -> str:
    source_packet = selection_packet.get("source_packet")
    source_packet = source_packet if isinstance(source_packet, dict) else {}

    return _first_text(
        selection_packet.get("target_name"),
        source_packet.get("target_name"),
        selection_packet.get("target"),
        default="unknown-target",
    )


def _selected_hypotheses(selection_packet: dict[str, Any]) -> list[dict[str, Any]]:
    for key in (
        "selected_hypotheses",
        "selected",
        "hypotheses_selected",
        "ranked_selected_hypotheses",
    ):
        value = selection_packet.get(key)
        items = _as_list(value)
        if items and all(isinstance(item, dict) for item in items):
            return list(items)

    hypotheses = selection_packet.get("hypotheses")
    if isinstance(hypotheses, list):
        selected = [item for item in hypotheses if isinstance(item, dict) and item.get("selected")]
        if selected:
            return selected

    primary = selection_packet.get("primary_hypothesis")
    if isinstance(primary, dict):
        return [primary]

    return []


def _hypothesis_id(hypothesis: dict[str, Any], index: int) -> str:
    return _first_text(
        hypothesis.get("hypothesis_id"),
        hypothesis.get("id"),
        hypothesis.get("hypothesis"),
        default=f"HYP-{index:03d}",
    )


def _hypothesis_type(hypothesis: dict[str, Any]) -> str:
    return _first_text(
        hypothesis.get("hypothesis_type"),
        hypothesis.get("type"),
        hypothesis.get("category"),
        default="generic-research-hypothesis",
    )


def _hypothesis_title(hypothesis: dict[str, Any], fallback_id: str) -> str:
    return _first_text(
        hypothesis.get("title"),
        hypothesis.get("surface"),
        hypothesis.get("name"),
        hypothesis.get("description"),
        default=fallback_id,
    )


def _hypothesis_priority(hypothesis: dict[str, Any]) -> str:
    return _first_text(hypothesis.get("priority"), hypothesis.get("risk"), default="unknown")


def _hypothesis_confidence(hypothesis: dict[str, Any]) -> str:
    return _first_text(hypothesis.get("confidence"), default="unknown")


def _hypothesis_score(hypothesis: dict[str, Any]) -> int | None:
    score = hypothesis.get("score")
    if isinstance(score, bool):
        return None
    if isinstance(score, int):
        return score
    if isinstance(score, float):
        return int(score)
    if isinstance(score, str) and score.strip().isdigit():
        return int(score.strip())
    return None


def _hypothesis_tags(hypothesis: dict[str, Any]) -> list[str]:
    raw_tags = hypothesis.get("tags")
    if isinstance(raw_tags, str):
        return [tag.strip() for tag in raw_tags.split(",") if tag.strip()]
    return [_clean_text(tag) for tag in _as_list(raw_tags) if _clean_text(tag)]


def _hypothesis_evidence_needed(hypothesis: dict[str, Any]) -> list[str]:
    for key in ("evidence_needed", "evidence_requirements", "required_evidence"):
        items = [_clean_text(item) for item in _as_list(hypothesis.get(key)) if _clean_text(item)]
        if items:
            return items
    return []


def _template_for(hypothesis_type: str) -> InvestigationTemplate:
    return TEMPLATES.get(hypothesis_type, DEFAULT_TEMPLATE)


def _build_plan_for_hypothesis(hypothesis: dict[str, Any], index: int) -> dict[str, Any]:
    hid = _hypothesis_id(hypothesis, index)
    htype = _hypothesis_type(hypothesis)
    template = _template_for(htype)
    existing_evidence = _hypothesis_evidence_needed(hypothesis)

    evidence_requirements = list(template.evidence_requirements)
    for item in existing_evidence:
        if item not in evidence_requirements:
            evidence_requirements.append(item)

    return {
        "hypothesis_id": hid,
        "hypothesis_type": htype,
        "title": _hypothesis_title(hypothesis, hid),
        "priority": _hypothesis_priority(hypothesis),
        "confidence": _hypothesis_confidence(hypothesis),
        "score": _hypothesis_score(hypothesis),
        "tags": _hypothesis_tags(hypothesis),
        "focus": template.focus,
        "plan_status": "ready-for-human-review",
        "investigation_allowed": True,
        "validation_allowed": False,
        "evidence_collection_allowed": False,
        "vulnerability_confirmation_allowed": False,
        "investigation_phases": list(template.investigation_phases),
        "review_questions": list(template.review_questions),
        "evidence_requirements": evidence_requirements,
        "local_only_checks": list(template.local_only_checks),
        "blocked_until_later_gate": [
            "runtime validation",
            "target interaction",
            "command generation",
            "browser execution",
            "curl execution",
            "Kali execution",
            "Burp execution",
            "evidence collection",
            "vulnerability confirmation",
            "report submission",
        ],
    }


def build_research_investigation_plan_packet(
    selection_packet: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic local-only investigation plan packet."""

    selected = _selected_hypotheses(selection_packet)
    plans = [_build_plan_for_hypothesis(hypothesis, index) for index, hypothesis in enumerate(selected, start=1)]

    selection_status = _first_text(selection_packet.get("selection_status"), default="unknown")
    selected_count = len(plans)
    plan_status = "ready-for-human-review" if selected_count else "blocked-no-selected-hypotheses"

    packet = {
        "kind": "brain_chat_research_investigation_plan_packet",
        "target_name": _target_name(selection_packet),
        "packet_status": plan_status,
        "selection_status": selection_status,
        "investigation_plan_status": plan_status,
        "selected_count": selected_count,
        "plan_count": selected_count,
        "primary_hypothesis_id": _first_text(
            selection_packet.get("primary_hypothesis_id"),
            plans[0]["hypothesis_id"] if plans else "",
            default="",
        ),
        "hypothesis_plan_ids": [plan["hypothesis_id"] for plan in plans],
        "plans": plans,
        "allowed_local_next_steps_count": 2 if plans else 0,
        "allowed_local_next_steps": [
            "Review the investigation plan packet for completeness and scope alignment.",
            "Prepare a separate human approval request before any validation or evidence collection.",
        ]
        if plans
        else [],
        "rejected_actions_count": len(REJECTED_ACTIONS),
        "rejected_actions": REJECTED_ACTIONS,
        "safety_flags": dict(SAFETY_FLAGS),
    }

    return packet


def render_research_investigation_plan_packet_markdown(packet: dict[str, Any]) -> str:
    """Render a human-readable markdown packet."""

    lines: list[str] = [
        "# Research Investigation Plan Packet",
        "",
        f"- kind: `{packet.get('kind', '')}`",
        f"- target_name: `{packet.get('target_name', '')}`",
        f"- packet_status: `{packet.get('packet_status', '')}`",
        f"- selection_status: `{packet.get('selection_status', '')}`",
        f"- investigation_plan_status: `{packet.get('investigation_plan_status', '')}`",
        f"- selected_count: `{packet.get('selected_count', 0)}`",
        f"- primary_hypothesis_id: `{packet.get('primary_hypothesis_id', '')}`",
        "",
        "## Safety",
        "",
    ]

    safety_flags = packet.get("safety_flags", {})
    if isinstance(safety_flags, dict):
        for name in sorted(safety_flags):
            lines.append(f"- {name}: `{str(bool(safety_flags[name])).lower()}`")

    lines.extend(["", "## Plans", ""])

    plans = packet.get("plans", [])
    if isinstance(plans, list) and plans:
        for plan in plans:
            if not isinstance(plan, dict):
                continue
            lines.extend(
                [
                    f"### {plan.get('hypothesis_id', '')} - {plan.get('hypothesis_type', '')}",
                    "",
                    f"- title: {plan.get('title', '')}",
                    f"- priority: `{plan.get('priority', '')}`",
                    f"- confidence: `{plan.get('confidence', '')}`",
                    f"- score: `{plan.get('score', '')}`",
                    f"- plan_status: `{plan.get('plan_status', '')}`",
                    f"- validation_allowed: `{str(bool(plan.get('validation_allowed'))).lower()}`",
                    f"- evidence_collection_allowed: `{str(bool(plan.get('evidence_collection_allowed'))).lower()}`",
                    f"- vulnerability_confirmation_allowed: `{str(bool(plan.get('vulnerability_confirmation_allowed'))).lower()}`",
                    "",
                    "#### Investigation phases",
                    "",
                ]
            )
            for item in _as_list(plan.get("investigation_phases")):
                lines.append(f"- {item}")
            lines.extend(["", "#### Review questions", ""])
            for item in _as_list(plan.get("review_questions")):
                lines.append(f"- {item}")
            lines.extend(["", "#### Evidence requirements for later gated validation", ""])
            for item in _as_list(plan.get("evidence_requirements")):
                lines.append(f"- {item}")
            lines.extend(["", "#### Blocked until later gate", ""])
            for item in _as_list(plan.get("blocked_until_later_gate")):
                lines.append(f"- {item}")
            lines.append("")
    else:
        lines.append("No selected hypotheses were available for investigation planning.")
        lines.append("")

    lines.extend(["## Rejected actions", ""])
    for item in _as_list(packet.get("rejected_actions")):
        if isinstance(item, dict):
            lines.append(f"- {item.get('action', '')}: {item.get('reason', '')}")

    lines.append("")
    return "\n".join(lines)


def build_packet_from_file(
    selection_file: str | Path,
    output_file: str | Path | None = None,
    json_output: str | Path | None = None,
) -> dict[str, Any]:
    """Load a selection packet, build the plan packet, and optionally write outputs."""

    selection_packet = load_json(selection_file)
    packet = build_research_investigation_plan_packet(selection_packet)

    if output_file is not None:
        write_markdown(output_file, render_research_investigation_plan_packet_markdown(packet))

    if json_output is not None:
        write_json(json_output, packet)

    return packet


__all__ = [
    "SAFETY_FLAGS",
    "REJECTED_ACTIONS",
    "build_packet_from_file",
    "build_research_investigation_plan_packet",
    "render_research_investigation_plan_packet_markdown",
]
