"""
Brain chat evidence checklist status importer.

This module imports local status metadata for evidence checklist items.
It does not collect evidence, execute tools, send requests, call providers,
mutate targets, or confirm vulnerabilities.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from bugintel.core.brain_chat_evidence_checklist import (
    BrainChatEvidenceChecklist,
    build_brain_chat_evidence_checklist,
)
from bugintel.core.brain_chat_session import BrainChatSession


@dataclass(frozen=True)
class EvidenceChecklistStatusImport:
    statuses: dict[str, str]
    notes: dict[str, str]
    unmatched_labels: tuple[str, ...]
    source_file: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_checklist_status_import",
            "source_file": self.source_file,
            "statuses": dict(self.statuses),
            "notes": dict(self.notes),
            "unmatched_labels": list(self.unmatched_labels),
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
                "vulnerability_confirmation": False,
            },
        }


@dataclass(frozen=True)
class EvidenceChecklistStatusImportResult:
    imported: EvidenceChecklistStatusImport
    checklist: BrainChatEvidenceChecklist

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": "brain_chat_evidence_checklist_status_import_result",
            "imported": self.imported.to_dict(),
            "checklist": self.checklist.to_dict(),
        }


def import_evidence_checklist_status_file(
    session: BrainChatSession,
    status_file: Path,
) -> EvidenceChecklistStatusImportResult:
    if not status_file.exists():
        raise FileNotFoundError(f"Evidence checklist status JSON not found: {status_file}")

    data = json.loads(status_file.read_text(encoding="utf-8"))
    return import_evidence_checklist_status_data(
        session,
        data,
        source_file=str(status_file),
    )


def import_evidence_checklist_status_data(
    session: BrainChatSession,
    data: dict[str, Any],
    source_file: str | None = None,
) -> EvidenceChecklistStatusImportResult:
    base = build_brain_chat_evidence_checklist(session)
    valid_labels = {item.label for item in base.items}

    statuses: dict[str, str] = {}
    notes: dict[str, str] = {}
    unmatched: list[str] = []

    for item in _iter_status_items(data):
        label = str(item.get("label", "")).strip()
        if not label:
            continue

        if label not in valid_labels:
            unmatched.append(label)
            continue

        if "status" in item:
            statuses[label] = str(item["status"])
        if "notes" in item:
            notes[label] = str(item["notes"])

    imported = EvidenceChecklistStatusImport(
        statuses=statuses,
        notes=notes,
        unmatched_labels=tuple(unmatched),
        source_file=source_file,
    )
    checklist = build_brain_chat_evidence_checklist(
        session,
        item_statuses=statuses,
        item_notes=notes,
    )

    return EvidenceChecklistStatusImportResult(imported=imported, checklist=checklist)


def _iter_status_items(data: dict[str, Any]) -> list[dict[str, Any]]:
    if isinstance(data.get("items"), list):
        return [item for item in data["items"] if isinstance(item, dict)]

    items = []
    for label, value in data.items():
        if isinstance(value, dict):
            item = {"label": label}
            item.update(value)
            items.append(item)
        elif isinstance(value, str):
            items.append({"label": label, "status": value})
    return items
