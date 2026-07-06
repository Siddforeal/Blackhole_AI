from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BrainSafety:
    adapter_execution_state: str = "not_executed"
    can_execute_now: bool = False
    execution_allowed: bool = False
    validation_allowed: bool = False
    runtime_execution_allowed: bool = False
    tool_execution_allowed: bool = False
    browser_execution_allowed: bool = False
    network_requests_allowed: bool = False
    evidence_collection_allowed: bool = False
    target_mutation_allowed: bool = False
    report_submission_allowed: bool = False
    vulnerability_confirmation_allowed: bool = False
    planning_only: bool = True
    dry_run_only: bool = True

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass(frozen=True)
class BrainEntity:
    entity_id: str
    entity_type: str
    title: str
    summary: str = ""
    tags: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "entity_id": self.entity_id,
            "entity_type": self.entity_type,
            "title": self.title,
            "summary": self.summary,
            "tags": list(self.tags),
        }


@dataclass(frozen=True)
class BrainRelationship:
    source_id: str
    relationship_type: str
    target_id: str
    confidence: float = 1.0
    rationale: str = ""

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass(frozen=True)
class BrainPipelineStage:
    name: str
    input_kind: str
    output_kind: str
    responsibility: str
    persistent: bool

    def to_dict(self) -> dict:
        return self.__dict__.copy()


@dataclass(frozen=True)
class BrainMemoryLayer:
    name: str
    lifetime: str
    stores: tuple[str, ...]
    purpose: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "lifetime": self.lifetime,
            "stores": list(self.stores),
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class BrainServiceContract:
    name: str
    responsibility: str
    inputs: tuple[str, ...]
    outputs: tuple[str, ...]
    invariants: tuple[str, ...]

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "inputs": list(self.inputs),
            "outputs": list(self.outputs),
            "invariants": list(self.invariants),
        }


@dataclass(frozen=True)
class BrainArchitectureSpec:
    architecture_id: str
    version: str
    status: str
    purpose: str
    entities: tuple[BrainEntity, ...]
    relationships: tuple[BrainRelationship, ...]
    pipeline: tuple[BrainPipelineStage, ...]
    memory_layers: tuple[BrainMemoryLayer, ...]
    service_contracts: tuple[BrainServiceContract, ...]
    extension_points: tuple[str, ...]
    safety: BrainSafety = field(default_factory=BrainSafety)

    def to_dict(self) -> dict:
        return {
            "kind": "blackhole_brain_architecture_spec",
            "architecture_id": self.architecture_id,
            "version": self.version,
            "status": self.status,
            "purpose": self.purpose,
            "entities": [x.to_dict() for x in self.entities],
            "relationships": [x.to_dict() for x in self.relationships],
            "pipeline": [x.to_dict() for x in self.pipeline],
            "memory_layers": [x.to_dict() for x in self.memory_layers],
            "service_contracts": [x.to_dict() for x in self.service_contracts],
            "extension_points": list(self.extension_points),
            **self.safety.to_dict(),
        }

    def to_markdown(self) -> str:
        lines = [
            "# Blackhole Brain Architecture",
            "",
            f"- Architecture ID: `{self.architecture_id}`",
            f"- Version: `{self.version}`",
            f"- Status: `{self.status}`",
            "",
            "## Purpose",
            "",
            self.purpose,
            "",
            "## Entities",
            "",
        ]
        for entity in self.entities:
            lines.append(f"- `{entity.entity_type}` - {entity.title}")

        lines += ["", "## Pipeline", ""]
        for index, stage in enumerate(self.pipeline, start=1):
            lines.append(f"{index}. `{stage.name}`: `{stage.input_kind}` -> `{stage.output_kind}`")

        lines += ["", "## Service contracts", ""]
        for contract in self.service_contracts:
            lines.append(f"- `{contract.name}` - {contract.responsibility}")

        lines += [
            "",
            "## Safety",
            "",
            "- adapter_execution_state: `not_executed`",
            "- can_execute_now: `false`",
            "- execution_allowed: `false`",
            "- network_requests_allowed: `false`",
            "- evidence_collection_allowed: `false`",
            "- target_mutation_allowed: `false`",
            "- report_submission_allowed: `false`",
            "- vulnerability_confirmation_allowed: `false`",
            "",
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class BrainHypothesis:
    hypothesis_id: str
    title: str
    description: str
    vulnerability_class: str
    confidence: float
    priority: str
    status: str = "proposed"
    supporting_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    contradicting_evidence_ids: tuple[str, ...] = field(default_factory=tuple)
    required_next_evidence: tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> dict:
        return {
            "hypothesis_id": self.hypothesis_id,
            "title": self.title,
            "description": self.description,
            "vulnerability_class": self.vulnerability_class,
            "confidence": self.confidence,
            "priority": self.priority,
            "status": self.status,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "contradicting_evidence_ids": list(self.contradicting_evidence_ids),
            "required_next_evidence": list(self.required_next_evidence),
        }
