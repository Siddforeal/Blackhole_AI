# Publication Roadmap: Blackhole_AI Research

Status: planning only, not final paper text.

## Purpose

This file defines a realistic roadmap for turning Blackhole_AI into a publishable cybersecurity research paper.

The goal is to avoid rushing into writing before the research contribution, evaluation, and evidence are ready.

## Current research direction

Evidence-gated human-in-the-loop AI assistance for vulnerability research planning.

## Main publication idea

The first paper should study whether a structured, safety-gated AI-assisted workflow improves vulnerability research planning compared with unstructured manual notes and direct LLM assistance.

The paper should focus on:

- evidence completeness
- safety discipline
- overclaim control
- validation planning quality
- blocker identification
- responsible disclosure readiness

## What the first paper should not be

The first paper should not claim that Blackhole_AI:

- is a complete autonomous security researcher
- replaces human experts
- discovers more real-world vulnerabilities
- performs autonomous exploitation
- is better than all vulnerability scanners
- guarantees safe behavior in every situation

## Minimum milestones before writing the paper

Before drafting the paper, the project should have:

1. stable minimum research prototype
2. finalized research questions
3. finalized scoring rubric
4. safe case-study dataset
5. defined baselines
6. completed evaluation runs
7. recorded outputs for each workflow
8. scored results
9. honest limitations
10. ethics and safety discussion

## Suggested development-to-paper path

### Phase 1: Research foundation

Create and review planning files:

- research direction
- research questions
- minimum prototype
- evaluation design
- scoring rubric
- case study plan
- ethics and safety plan
- publication roadmap
- related work map

Estimated duration:

- 2 to 3 weeks

### Phase 2: Minimum research prototype freeze

Choose one stable version of Blackhole_AI for evaluation.

The evaluated version should support the core workflow needed for the paper.

Estimated duration:

- 1 to 2 months, depending on development status

### Phase 3: Case-study dataset

Create controlled evaluation cases.

Initial target:

- 8 to 12 cases for preprint or workshop
- 15 to 25 cases for stronger conference version

Estimated duration:

- 3 to 5 weeks

### Phase 4: Evaluation execution

Run each case through:

1. manual notes workflow
2. direct LLM assistance workflow
3. Blackhole_AI workflow

Preserve all outputs and scoring notes.

Estimated duration:

- 4 to 6 weeks

### Phase 5: Results analysis

Analyze:

- per-metric scores
- qualitative differences
- unsafe suggestions
- overclaims
- missing evidence
- usefulness
- limitations

Estimated duration:

- 2 to 3 weeks

### Phase 6: Paper drafting

Only after evaluation results exist, draft the paper.

Estimated duration:

- 3 to 5 weeks

### Phase 7: Preprint or workshop submission

Prepare:

- paper PDF
- artifact package
- anonymized evaluation data if needed
- appendix
- ethics statement
- reproducibility notes

Estimated duration:

- 2 to 4 weeks

## Realistic timeline

### Fast but risky

3 to 4 months.

This may be enough for an early preprint if the evaluation is small and the prototype stabilizes quickly.

### Realistic first serious version

5 to 7 months.

This is the most realistic timeline for a useful preprint or workshop submission.

### Strong conference version

8 to 12 months or more.

This would require stronger evaluation, more cases, better baselines, and cleaner artifact packaging.

## Venue strategy

### Stage 1: Preprint

Release a careful preprint only after evaluation results exist.

Possible platform:

- arXiv

Purpose:

- strengthen PhD applications
- make the research visible
- get feedback

### Stage 2: Workshop paper

Target a security or AI-security workshop.

Possible types:

- AI and security workshop
- usable security workshop
- security automation workshop
- cyber reasoning or AI-assisted security venue

Purpose:

- publish a focused first version
- receive reviewer feedback
- build academic credibility

### Stage 3: Main conference or journal extension

After improving evaluation, consider a stronger submission.

Possible venue types:

- security conference
- systems security conference
- AI-for-security workshop or conference
- cybersecurity journal

Purpose:

- mature the work into a stronger academic contribution

## Submission readiness checklist

The paper is not ready until the following are true:

- the research question is narrow and testable
- the evaluated prototype is stable
- all cases are safe and documented
- baseline outputs are collected
- Blackhole_AI outputs are collected
- scoring rubric is finalized before scoring
- results are honestly analyzed
- limitations are clearly stated
- related work is properly cited
- ethics and safety are clearly explained
- no private bug bounty data is exposed
- no unsupported claims are made

## Current decision

Do not write or submit the paper yet.

Continue building Blackhole_AI while developing the research foundation.

The next major research step is to create a related-work map using real papers and sources.
