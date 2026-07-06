from __future__ import annotations

from bugintel.brain.models import (
    BrainArchitectureSpec,
    BrainEntity,
    BrainMemoryLayer,
    BrainPipelineStage,
    BrainRelationship,
    BrainServiceContract,
)


def build_blackhole_brain_architecture_spec() -> BrainArchitectureSpec:
    entities = (
        BrainEntity("entity-workspace", "Workspace", "Container for investigations, targets, and knowledge."),
        BrainEntity("entity-investigation", "Investigation", "A single authorized research case."),
        BrainEntity("entity-target", "Target", "Program, application, organization, or scoped target."),
        BrainEntity("entity-asset", "Asset", "Host, app, API, mobile package, repository, or service."),
        BrainEntity("entity-endpoint", "Endpoint", "URL, route, method, function, handler, or API operation."),
        BrainEntity("entity-observation", "Observation", "Raw noticed behavior or parsed input."),
        BrainEntity("entity-evidence", "Evidence", "Reviewed artifact supporting or contradicting a claim."),
        BrainEntity("entity-fact", "Fact", "Normalized assertion derived from evidence."),
        BrainEntity("entity-hypothesis", "Hypothesis", "Testable vulnerability or attack-path theory."),
        BrainEntity("entity-finding", "Finding", "Validated security issue candidate."),
        BrainEntity("entity-report", "Report", "Human-reviewable vulnerability report package."),
        BrainEntity("entity-pattern", "Pattern", "Reusable vulnerability pattern or heuristic."),
    )

    relationships = (
        BrainRelationship("Target", "owns", "Asset", rationale="Targets contain scoped assets."),
        BrainRelationship("Asset", "exposes", "Endpoint", rationale="Assets expose endpoints and handlers."),
        BrainRelationship("Endpoint", "produces", "Observation", rationale="Endpoint analysis creates observations."),
        BrainRelationship("Observation", "supports", "Evidence", rationale="Reviewed observations become evidence."),
        BrainRelationship("Evidence", "derives", "Fact", rationale="Evidence supports normalized facts."),
        BrainRelationship("Fact", "supports", "Hypothesis", rationale="Facts support or contradict hypotheses."),
        BrainRelationship("Hypothesis", "supports", "Finding", rationale="Hypotheses support finding candidates."),
        BrainRelationship("Finding", "produces", "Report", rationale="Findings produce report drafts."),
        BrainRelationship("Pattern", "suggests", "Hypothesis", rationale="Reusable patterns suggest hypotheses."),
    )

    pipeline = (
        BrainPipelineStage("Discovery", "raw_input", "observation", "Parse scoped inputs into normalized observations.", False),
        BrainPipelineStage("Evidence Review", "observation", "evidence", "Convert observations into reviewed evidence.", True),
        BrainPipelineStage("Fact Extraction", "evidence", "fact", "Normalize evidence into reusable facts.", True),
        BrainPipelineStage("Hypothesis Generation", "fact", "hypothesis", "Generate testable vulnerability theories.", True),
        BrainPipelineStage("Pattern Matching", "hypothesis", "pattern_match", "Match against reusable vulnerability patterns.", True),
        BrainPipelineStage("Confidence Scoring", "hypothesis", "confidence_score", "Score hypotheses from evidence and history.", True),
        BrainPipelineStage("Planning", "confidence_score", "investigation_plan", "Create prioritized investigation plans.", True),
        BrainPipelineStage("Decision", "investigation_plan", "human_review_request", "Route risky actions to human review.", True),
        BrainPipelineStage("Knowledge Update", "decision", "knowledge", "Persist lessons, outcomes, and reusable patterns.", True),
    )

    memory_layers = (
        BrainMemoryLayer("Working Memory", "session", ("active target", "active hypotheses", "open questions"), "Temporary context for the current interaction."),
        BrainMemoryLayer("Case Memory", "investigation", ("evidence", "facts", "hypotheses", "timeline"), "Persistent memory for one investigation."),
        BrainMemoryLayer("Knowledge Memory", "cross-case", ("patterns", "techniques", "historical outcomes"), "Reusable security knowledge across investigations."),
        BrainMemoryLayer("Model Context", "runtime", ("retrieved knowledge", "planner instructions", "safety constraints"), "Context supplied to model providers later."),
    )

    service_contracts = (
        BrainServiceContract("KnowledgeStore", "Persist and retrieve reusable cross-case knowledge.", ("BrainEntity", "BrainRelationship"), ("similar entities", "knowledge facts"), ("local-first", "no execution")),
        BrainServiceContract("MemoryStore", "Persist working and case memory.", ("case update",), ("case state",), ("append-only history", "human reviewable")),
        BrainServiceContract("PatternEngine", "Match facts and hypotheses to vulnerability patterns.", ("facts", "hypotheses"), ("pattern matches",), ("deterministic", "explainable")),
        BrainServiceContract("ConfidenceEngine", "Score hypotheses from evidence and history.", ("hypothesis", "evidence", "history"), ("confidence score",), ("bounded score", "explainable reasons")),
        BrainServiceContract("ReasoningEngine", "Generate hypotheses and decisions from facts.", ("facts", "patterns", "memory"), ("hypotheses", "decisions"), ("planning-only", "no confirmation")),
        BrainServiceContract("PlannerEngine", "Create prioritized investigation plans.", ("hypotheses", "scope", "safety"), ("plan",), ("human approval before execution",)),
        BrainServiceContract("GraphEngine", "Represent relationships between entities.", ("entities", "relationships"), ("neighbors", "paths"), ("traceable", "serializable")),
    )

    extension_points = (
        "Local SQLite knowledge store",
        "Graph-backed relationship store",
        "Embedding similarity index",
        "Pattern library loaders",
        "LLM provider adapters",
        "Local model adapters",
        "Burp Suite adapter",
        "Browser automation adapter",
        "Report generation adapter",
        "Accepted or rejected report feedback importer",
    )

    return BrainArchitectureSpec(
        architecture_id="BLACKHOLE-BRAIN-ARCHITECTURE-v1.77.0",
        version="1.77.0",
        status="architecture-foundation-local-only",
        purpose=(
            "Define the canonical Blackhole Brain domain model, reasoning pipeline, memory hierarchy, "
            "service contracts, and extension points for future intelligence-layer releases."
        ),
        entities=entities,
        relationships=relationships,
        pipeline=pipeline,
        memory_layers=memory_layers,
        service_contracts=service_contracts,
        extension_points=extension_points,
    )
