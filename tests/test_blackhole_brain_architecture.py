from __future__ import annotations

from bugintel.brain.architecture import build_blackhole_brain_architecture_spec
from bugintel.brain.interfaces import (
    ConfidenceEngine,
    GraphEngine,
    KnowledgeStore,
    MemoryStore,
    PatternEngine,
    PlannerEngine,
    ReasoningEngine,
)


def test_blackhole_brain_architecture_spec_defines_core_brain_contracts() -> None:
    spec = build_blackhole_brain_architecture_spec()
    data = spec.to_dict()

    assert data["kind"] == "blackhole_brain_architecture_spec"
    assert data["architecture_id"] == "BLACKHOLE-BRAIN-ARCHITECTURE-v1.77.0"
    assert data["version"] == "1.77.0"
    assert data["status"] == "architecture-foundation-local-only"

    entity_types = {entity["entity_type"] for entity in data["entities"]}
    assert "Workspace" in entity_types
    assert "Investigation" in entity_types
    assert "Target" in entity_types
    assert "Endpoint" in entity_types
    assert "Evidence" in entity_types
    assert "Fact" in entity_types
    assert "Hypothesis" in entity_types
    assert "Finding" in entity_types
    assert "Pattern" in entity_types

    contract_names = {contract["name"] for contract in data["service_contracts"]}
    assert "KnowledgeStore" in contract_names
    assert "MemoryStore" in contract_names
    assert "PatternEngine" in contract_names
    assert "ConfidenceEngine" in contract_names
    assert "ReasoningEngine" in contract_names
    assert "PlannerEngine" in contract_names
    assert "GraphEngine" in contract_names


def test_blackhole_brain_architecture_preserves_no_execution_safety() -> None:
    data = build_blackhole_brain_architecture_spec().to_dict()

    assert data["adapter_execution_state"] == "not_executed"
    assert data["can_execute_now"] is False
    assert data["execution_allowed"] is False
    assert data["validation_allowed"] is False
    assert data["runtime_execution_allowed"] is False
    assert data["tool_execution_allowed"] is False
    assert data["browser_execution_allowed"] is False
    assert data["network_requests_allowed"] is False
    assert data["evidence_collection_allowed"] is False
    assert data["target_mutation_allowed"] is False
    assert data["report_submission_allowed"] is False
    assert data["vulnerability_confirmation_allowed"] is False
    assert data["planning_only"] is True
    assert data["dry_run_only"] is True


def test_blackhole_brain_architecture_pipeline_is_ordered() -> None:
    data = build_blackhole_brain_architecture_spec().to_dict()
    stages = [stage["name"] for stage in data["pipeline"]]

    assert stages == [
        "Discovery",
        "Evidence Review",
        "Fact Extraction",
        "Hypothesis Generation",
        "Pattern Matching",
        "Confidence Scoring",
        "Planning",
        "Decision",
        "Knowledge Update",
    ]


def test_blackhole_brain_architecture_markdown_is_human_readable() -> None:
    markdown = build_blackhole_brain_architecture_spec().to_markdown()

    assert "# Blackhole Brain Architecture" in markdown
    assert "## Entities" in markdown
    assert "## Pipeline" in markdown
    assert "## Service contracts" in markdown
    assert "network_requests_allowed: `false`" in markdown
    assert "vulnerability_confirmation_allowed: `false`" in markdown


def test_blackhole_brain_interfaces_are_importable() -> None:
    assert KnowledgeStore is not None
    assert MemoryStore is not None
    assert PatternEngine is not None
    assert ConfidenceEngine is not None
    assert ReasoningEngine is not None
    assert PlannerEngine is not None
    assert GraphEngine is not None
