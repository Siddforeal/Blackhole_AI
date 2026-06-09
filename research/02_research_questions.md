# Research Questions: Blackhole_AI

Status: planning only, not final paper text.

## Working paper direction

Evidence-gated human-in-the-loop AI assistance for vulnerability research planning.

## Main research question

Can a structured, safety-gated, human-in-the-loop AI workflow improve vulnerability research planning compared with unstructured manual notes or direct LLM assistance?

## Candidate research questions

### RQ1: Evidence completeness

Does Blackhole_AI help researchers identify more complete evidence requirements for vulnerability investigations?

Examples of evidence requirements include:

- baseline behavior
- affected component
- reproduction steps
- request and response samples
- logs
- screenshots
- negative controls
- authorization boundary checks
- impact proof
- cleanup steps
- responsible disclosure notes

### RQ2: Safety discipline

Does Blackhole_AI reduce unsafe, destructive, unauthorized, privacy-risky, or out-of-scope suggested actions compared with direct LLM assistance?

### RQ3: Overclaim control

Does Blackhole_AI reduce premature claims such as calling a finding confirmed, critical, exploitable, or report-ready before sufficient evidence exists?

### RQ4: Validation planning

Does Blackhole_AI produce more reproducible and reviewable validation plans than manual notes or direct LLM assistance?

### RQ5: Blocker identification

Does Blackhole_AI more clearly identify missing evidence, unresolved assumptions, and reasons why a finding is not yet reportable?

## Current strongest RQ set

The strongest first-paper research questions are likely:

1. RQ1: Evidence completeness
2. RQ2: Safety discipline
3. RQ3: Overclaim control
4. RQ4: Validation planning

RQ5 may be merged into RQ1 or RQ3 later.

## Claims to avoid

This study should not claim that Blackhole_AI:

- discovers more vulnerabilities
- replaces expert researchers
- performs autonomous exploitation
- is a full penetration testing agent
- is better than all scanners
- guarantees safe research behavior

## Evaluation implication

Each research question must be tested using controlled cases, predefined scoring criteria, and comparison baselines.
