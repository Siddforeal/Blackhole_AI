"""
Evidence workspace builder for Blackhole AI Workbench.

This module creates local, planning-only evidence workspace manifests and folder
layouts. It does not send requests, execute shell commands against targets,
launch browsers, call LLM providers, mutate targets, or bypass authorization.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import re


@dataclass(frozen=True)
class EvidenceWorkspaceFile:
    path: str
    purpose: str
    content: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class EvidenceWorkspaceEndpoint:
    index: int
    endpoint: str
    slug: str
    priority_score: int
    priority_band: str
    attack_surface_groups: tuple[str, ...]
    requirement_names: tuple[str, ...]
    files: tuple[EvidenceWorkspaceFile, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "endpoint": self.endpoint,
            "slug": self.slug,
            "priority_score": self.priority_score,
            "priority_band": self.priority_band,
            "attack_surface_groups": list(self.attack_surface_groups),
            "requirement_names": list(self.requirement_names),
            "files": [item.to_dict() for item in self.files],
        }


@dataclass(frozen=True)
class EvidenceWorkspaceManifest:
    target_name: str
    workspace_root: str
    endpoint_count: int
    endpoints: tuple[EvidenceWorkspaceEndpoint, ...]
    files: tuple[EvidenceWorkspaceFile, ...]
    planning_only: bool = True
    execution_state: str = "not_executed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "target_name": self.target_name,
            "workspace_root": self.workspace_root,
            "endpoint_count": self.endpoint_count,
            "planning_only": self.planning_only,
            "execution_state": self.execution_state,
            "files": [item.to_dict() for item in self.files],
            "endpoints": [endpoint.to_dict() for endpoint in self.endpoints],
        }


def build_evidence_workspace_manifest(
    orchestration_data: dict[str, Any],
    workspace_root: str | Path,
) -> EvidenceWorkspaceManifest:
    """Build a local evidence workspace manifest from orchestration JSON."""
    root_path = Path(workspace_root)
    target_name = str(orchestration_data.get("target_name") or "blackhole-target")

    evidence_plan = orchestration_data.get("evidence_requirement_plan") or {}
    endpoint_plans = evidence_plan.get("endpoint_plans") or []

    endpoints: list[EvidenceWorkspaceEndpoint] = []

    for index, endpoint_plan in enumerate(endpoint_plans, start=1):
        endpoint = str(endpoint_plan.get("endpoint") or f"endpoint-{index}")
        slug = f"{index:03d}-{slugify_endpoint(endpoint)}"
        endpoint_dir = f"endpoints/{slug}"

        requirements = endpoint_plan.get("requirements") or []
        requirement_names = tuple(str(item.get("name")) for item in requirements if item.get("name"))

        groups = tuple(str(item) for item in endpoint_plan.get("attack_surface_groups") or [])

        files = (
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/README.md",
                purpose="Endpoint evidence summary and handling notes.",
                content=_endpoint_readme(endpoint_plan, requirement_names),
            ),
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/checklist.md",
                purpose="Evidence collection checklist generated from requirements.",
                content=_endpoint_checklist(endpoint_plan, requirement_names),
            ),
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/notes.md",
                purpose="Human researcher notes for observations and validation decisions.",
                content=_endpoint_notes(endpoint_plan),
            ),
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/requests/.gitkeep",
                purpose="Directory placeholder for redacted request samples.",
            ),
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/responses/.gitkeep",
                purpose="Directory placeholder for redacted response samples.",
            ),
            EvidenceWorkspaceFile(
                path=f"{endpoint_dir}/screenshots/.gitkeep",
                purpose="Directory placeholder for approved screenshots.",
            ),
        )

        endpoints.append(
            EvidenceWorkspaceEndpoint(
                index=index,
                endpoint=endpoint,
                slug=slug,
                priority_score=int(endpoint_plan.get("priority_score") or 0),
                priority_band=str(endpoint_plan.get("priority_band") or "info"),
                attack_surface_groups=groups,
                requirement_names=requirement_names,
                files=files,
            )
        )

    top_files = (
        EvidenceWorkspaceFile(
            path="README.md",
            purpose="Workspace overview and safety notes.",
            content=_workspace_readme(target_name, endpoints),
        ),
        EvidenceWorkspaceFile(
            path="manifest.json",
            purpose="Machine-readable evidence workspace manifest.",
        ),
        EvidenceWorkspaceFile(
            path="redaction-checklist.md",
            purpose="Global redaction checklist before report submission.",
            content=_redaction_checklist(),
        ),
        EvidenceWorkspaceFile(
            path="report-notes.md",
            purpose="Draft report notes and triage decisions.",
            content=_report_notes(target_name),
        ),
    )

    return EvidenceWorkspaceManifest(
        target_name=target_name,
        workspace_root=str(root_path),
        endpoint_count=len(endpoints),
        endpoints=tuple(endpoints),
        files=top_files,
    )


def materialize_evidence_workspace(manifest: EvidenceWorkspaceManifest) -> None:
    """Create the local workspace files described by the manifest."""
    root = Path(manifest.workspace_root)
    root.mkdir(parents=True, exist_ok=True)

    import json

    for file in manifest.files:
        path = root / file.path
        path.parent.mkdir(parents=True, exist_ok=True)

        if file.path == "manifest.json":
            path.write_text(json.dumps(manifest.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        else:
            path.write_text(file.content, encoding="utf-8")

    for endpoint in manifest.endpoints:
        for file in endpoint.files:
            path = root / file.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(file.content, encoding="utf-8")


def slugify_endpoint(endpoint: str) -> str:
    """Create a stable readable folder slug from an endpoint path or URL."""
    value = endpoint.lower()
    value = re.sub(r"^https?://", "", value)
    value = value.replace("{", "").replace("}", "")
    value = re.sub(r"[^a-z0-9]+", "-", value)
    value = value.strip("-")
    value = re.sub(r"-+", "-", value)

    if not value:
        return "endpoint"

    return value[:90]


def _workspace_readme(target_name: str, endpoints: list[EvidenceWorkspaceEndpoint]) -> str:
    lines = [
        f"# Blackhole Evidence Workspace: {target_name}",
        "",
        "This workspace is local and planning-only.",
        "",
        "Safety rules:",
        "",
        "- Do not store live secrets, cookies, tokens, API keys, or private customer data.",
        "- Store only redacted request and response samples.",
        "- Use controlled accounts and authorized targets only.",
        "- Keep raw exploit attempts out of this folder unless explicitly approved and sanitized.",
        "",
        "Endpoint folders:",
        "",
    ]

    for endpoint in endpoints:
        lines.append(f"- `{endpoint.slug}` — {endpoint.priority_band} / {endpoint.priority_score} — `{endpoint.endpoint}`")

    lines.append("")
    return "\n".join(lines)


def _endpoint_readme(endpoint_plan: dict[str, Any], requirement_names: tuple[str, ...]) -> str:
    endpoint = endpoint_plan.get("endpoint", "unknown-endpoint")
    score = endpoint_plan.get("priority_score", 0)
    band = endpoint_plan.get("priority_band", "info")
    groups = ", ".join(endpoint_plan.get("attack_surface_groups") or []) or "none"

    return "\n".join(
        [
            f"# Endpoint Evidence: {endpoint}",
            "",
            f"- Priority: {band} / {score}",
            f"- Attack surface groups: {groups}",
            "",
            "Evidence requirements:",
            "",
            *[f"- [ ] {name}" for name in requirement_names],
            "",
        ]
    )


def _endpoint_checklist(endpoint_plan: dict[str, Any], requirement_names: tuple[str, ...]) -> str:
    endpoint = endpoint_plan.get("endpoint", "unknown-endpoint")

    lines = [
        f"# Evidence Checklist: {endpoint}",
        "",
        "Before collecting evidence:",
        "",
        "- [ ] Confirm target is in scope.",
        "- [ ] Confirm account/test data is controlled.",
        "- [ ] Confirm action is non-destructive or explicitly approved.",
        "- [ ] Confirm redaction plan is ready.",
        "",
        "Requirements:",
        "",
    ]

    for name in requirement_names:
        lines.append(f"- [ ] {name}")

    lines.append("")
    lines.append("After collection:")
    lines.append("")
    lines.append("- [ ] Redact secrets, tokens, cookies, emails, and identifiers.")
    lines.append("- [ ] Confirm no private customer data is included.")
    lines.append("- [ ] Link evidence to a clear impact statement.")
    lines.append("")

    return "\n".join(lines)


def _endpoint_notes(endpoint_plan: dict[str, Any]) -> str:
    endpoint = endpoint_plan.get("endpoint", "unknown-endpoint")

    return "\n".join(
        [
            f"# Research Notes: {endpoint}",
            "",
            "Observations:",
            "",
            "- ",
            "",
            "Validation decision:",
            "",
            "- ",
            "",
            "Report impact notes:",
            "",
            "- ",
            "",
        ]
    )


def _redaction_checklist() -> str:
    return "\n".join(
        [
            "# Redaction Checklist",
            "",
            "- [ ] Cookies redacted",
            "- [ ] Authorization headers redacted",
            "- [ ] API keys and tokens redacted",
            "- [ ] Emails/user identifiers redacted where needed",
            "- [ ] Customer/private data excluded",
            "- [ ] Screenshots reviewed before sharing",
            "- [ ] Request/response samples sanitized",
            "",
        ]
    )


def _report_notes(target_name: str) -> str:
    return "\n".join(
        [
            f"# Report Notes: {target_name}",
            "",
            "Summary:",
            "",
            "- ",
            "",
            "Impact:",
            "",
            "- ",
            "",
            "Steps to reproduce:",
            "",
            "1. ",
            "",
            "Evidence references:",
            "",
            "- ",
            "",
        ]
    )
