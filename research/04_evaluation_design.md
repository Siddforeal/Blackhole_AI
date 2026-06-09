# Evaluation Design: Blackhole_AI

Status: planning only, not final paper text.

## Purpose

The evaluation should test whether Blackhole_AI improves vulnerability research planning quality compared with weaker or less structured workflows.

The evaluation should not test whether Blackhole_AI autonomously discovers vulnerabilities.

## Main comparison

The first study should compare three workflows:

### Baseline A: Manual notes

A researcher reviews the same case and writes investigation notes manually.

### Baseline B: Direct LLM assistance

A researcher asks a general-purpose LLM for help using normal chat-style prompts, without Blackhole_AI's structured workflow or safety gates.

### System under study: Blackhole_AI

The same case is processed through Blackhole_AI's structured workflow, producing research packets, hypotheses, evidence requirements, safety blockers, validation plans, and report-readiness decisions.

## Evaluation cases

The evaluation should use controlled and safe cases.

Possible case sources:

- intentionally vulnerable local labs
- toy API or web scenarios created for the study
- sanitized historical vulnerability-research notes
- public CVE or advisory descriptions converted into planning tasks
- synthetic bug bounty-style scenarios with known evidence gaps

The first evaluation should avoid live production targets.

## Candidate number of cases

A realistic first study may use:

- 8 to 12 cases for an initial workshop/preprint paper
- 15 to 25 cases for a stronger conference-style version

## Main metrics

### M1: Evidence completeness

Does the workflow identify the evidence needed to validate or reject the finding?

Examples:

- baseline behavior
- affected component
- reproduction steps
- request/response samples
- screenshots
- logs
- negative controls
- authorization checks
- impact evidence
- cleanup steps

### M2: Safety discipline

Does the workflow avoid unsafe, unauthorized, destructive, privacy-risky, or out-of-scope actions?

### M3: Overclaim control

Does the workflow avoid calling a finding confirmed, critical, exploitable, or report-ready before sufficient evidence exists?

### M4: Validation plan quality

Does the workflow produce a clear, reproducible, and reviewable validation plan?

### M5: Blocker identification

Does the workflow clearly identify missing evidence, assumptions, unresolved questions, and reasons the finding is not yet reportable?

### M6: Research usefulness

Does the workflow help the researcher decide what to do next without replacing human judgment?

## Scoring approach

Each output should be scored using a predefined rubric.

Possible score range:

- 0 = absent or harmful
- 1 = very weak
- 2 = incomplete
- 3 = acceptable
- 4 = strong
- 5 = excellent

The scoring rubric must be written before running the evaluation.

## Evidence collection

For each case and workflow, preserve:

- input case description
- prompt or workflow configuration
- generated output
- scoring notes
- final score
- reviewer comments
- observed unsafe suggestions, if any
- observed unsupported claims, if any

## Ethical boundary

The evaluation should not require:

- testing live third-party targets
- exploiting real systems
- accessing real user data
- bypassing authorization
- destructive testing
- automatic report submission

## Expected paper claim

The strongest defensible claim would be:

Blackhole_AI improves structure, evidence discipline, safety awareness, and validation planning in controlled vulnerability-research planning tasks.

## Claims not supported by this evaluation

This evaluation would not prove that Blackhole_AI:

- discovers more real vulnerabilities
- replaces expert researchers
- is a complete autonomous pentesting system
- is better than commercial scanners
- guarantees safe behavior in all situations
