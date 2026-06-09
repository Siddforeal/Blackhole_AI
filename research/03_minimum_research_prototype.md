# Minimum Research Prototype: Blackhole_AI

Status: planning only, not final paper text.

## Purpose

Blackhole_AI is still under active development. The first research paper should not evaluate the entire long-term system.

Instead, the first paper should evaluate a minimum stable research prototype.

## Research prototype boundary

The minimum research prototype should focus on vulnerability research planning, not autonomous testing or exploitation.

The prototype should transform unstructured or semi-structured vulnerability-research context into:

1. structured research sources
2. attack-surface or hypothesis candidates
3. selected high-priority hypotheses
4. evidence requirements
5. validation-plan requirements
6. safety blockers
7. report-readiness decisions

## Minimum input types

The prototype should support at least one or more of the following safe input types:

- target description
- endpoint list
- source notes
- bug bounty scope summary
- sanitized vulnerability investigation notes
- local lab scenario description
- public CVE or advisory summary converted into a planning task

## Minimum output artifacts

The minimum prototype should produce reviewable artifacts such as:

- research source packet
- research hypothesis packet
- hypothesis selection packet
- evidence checklist
- safety/blocker analysis
- validation plan review
- report-readiness or not-ready decision

## What is outside the first prototype

The first paper should not require:

- autonomous browser execution
- live target testing
- Kali command execution
- destructive validation
- real exploitation
- real customer data handling
- automatic report submission
- fully autonomous bug discovery
- completed Android or iOS testing modes

These features may be part of the broader Blackhole_AI roadmap, but they are not required for the first research paper.

## Main evaluation claim

The minimum prototype should be evaluated on whether it improves planning quality, evidence discipline, safety discipline, validation readiness, and overclaim control.

## Why this boundary is important

This boundary keeps the first paper academically defensible.

It avoids overclaiming that Blackhole_AI is a complete autonomous security researcher.

It allows the research to evaluate one stable, measurable contribution while the larger project continues development.
