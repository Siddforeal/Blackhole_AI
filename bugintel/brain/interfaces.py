from __future__ import annotations

from typing import Protocol

from bugintel.brain.models import BrainEntity, BrainHypothesis, BrainRelationship


class KnowledgeStore(Protocol):
    def add_entity(self, entity: BrainEntity) -> None: ...
    def add_relationship(self, relationship: BrainRelationship) -> None: ...
    def find_similar_entities(self, entity: BrainEntity, *, limit: int = 10) -> tuple[BrainEntity, ...]: ...


class MemoryStore(Protocol):
    def remember(self, key: str, value: dict) -> None: ...
    def recall(self, key: str) -> dict | None: ...


class PatternEngine(Protocol):
    def match_patterns(self, entity: BrainEntity) -> tuple[str, ...]: ...


class ConfidenceEngine(Protocol):
    def score_hypothesis(self, hypothesis: BrainHypothesis) -> float: ...


class ReasoningEngine(Protocol):
    def generate_hypotheses(self, entities: tuple[BrainEntity, ...]) -> tuple[BrainHypothesis, ...]: ...


class PlannerEngine(Protocol):
    def build_plan(self, hypotheses: tuple[BrainHypothesis, ...]) -> dict: ...


class GraphEngine(Protocol):
    def neighbors(self, entity_id: str) -> tuple[BrainRelationship, ...]: ...
