# Blackhole Brain Architecture

This document defines the Chapter 2 architecture direction for Blackhole_AI.

## Goal

Blackhole should evolve from a workflow toolkit into a security research intelligence platform.

The brain is not a model. The brain is the structured system that provides knowledge, memory, reasoning, planning, confidence scoring, pattern matching, evidence correlation, and human review boundaries.

Models can plug into this system later.

## Core pipeline

Discovery -> Observation -> Evidence -> Fact -> Hypothesis -> Pattern Match -> Confidence Score -> Investigation Plan -> Human Decision -> Knowledge Update

## Memory hierarchy

Working Memory:
- active session context
- current hypotheses
- current unanswered questions

Case Memory:
- one investigation
- evidence
- facts
- timeline
- hypotheses
- report readiness

Knowledge Memory:
- cross-case reusable patterns
- vulnerability techniques
- historical outcomes
- lessons learned

Model Context:
- retrieved knowledge
- planner instructions
- safety constraints

## Service contracts

Future releases should implement these services behind stable interfaces:

- KnowledgeStore
- MemoryStore
- PatternEngine
- ConfidenceEngine
- ReasoningEngine
- PlannerEngine
- GraphEngine

## Safety invariants

The brain architecture remains local-first and planning-first.

By default it does not:

- execute curl
- call subprocess
- send network requests
- execute tools
- launch browsers
- call providers
- collect evidence
- mutate targets
- submit reports
- confirm vulnerabilities
