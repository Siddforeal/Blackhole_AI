# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)
[![Latest release](https://img.shields.io/github/v/release/Siddforeal/Blackhole_AI?label=release)](https://github.com/Siddforeal/Blackhole_AI/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Blackhole AI Workbench** is a local-first security research brain for authorized vulnerability research.

It helps turn rough security notes into structured observations, vulnerability pattern matches, hypotheses, next investigation steps, and report-readiness summaries.

> **Current release:** `v1.82.0`
> **Project status:** active research prototype
> **Current mode:** local-first, planning-first, human-in-the-loop
> **Long-term direction:** scope-gated AI agents that can interact with browsers, Burp Suite, curl, local tools, structured case memory, and controlled proof-of-concept workflows.

---

## Run the Demo

The fastest way to understand Blackhole is the checked-in demo case pack.

```bash
blackhole blackhole-demo-case-pack --json-output examples/blackhole-demo-case-pack.json --output-file examples/blackhole-demo-case-pack.md
```

The demo turns a synthetic local case into:

- observations
- matched vulnerability patterns
- knowledge records
- hypotheses
- next investigation steps
- a `Not report-ready` summary

Example outputs:

```text
examples/blackhole-demo-case-pack.md
examples/blackhole-demo-case-pack.json
```

---

## What Blackhole Is

Blackhole is not just a scanner. It is a research workbench designed to think through security work like a disciplined human researcher:

```text
target context
→ endpoint and surface discovery
→ hypothesis generation
→ hypothesis selection
→ investigation planning
→ action proposal
→ human decision
→ approved tool request
→ observation import
→ observation review
→ hypothesis feedback
→ confidence update proposal
→ research-state transition review
```

The goal is to help a researcher answer:

- What should I test first?
- Why is this hypothesis worth pursuing?
- What evidence do I already have?
- What evidence is missing?
- What action is safe to take next?
- What should not be executed yet?
- Is this ready for validation, reporting, or more research?
- Which assumptions are weak, stale, or unsupported?

---

## The Vision

Blackhole is being developed toward a controlled agentic security workflow where specialized agents can assist with:

| Agent Area | Intended Role |
|---|---|
| Browser agent | Navigate scoped applications, observe UI behavior, and capture browser-side evidence |
| Burp Suite agent | Help organize proxy history, requests, responses, repeater-style test plans, and evidence packets |
| Command-line agent | Prepare reviewed curl/tool commands for approved, scoped testing |
| Android/iOS static agent | Analyze mobile application artifacts, manifests, endpoints, deep links, and exposed components |
| Endpoint intelligence agent | Mine, group, rank, and prioritize endpoints |
| Hypothesis agent | Generate and refine vulnerability hypotheses |
| Evidence agent | Track what evidence is required, missing, weak, or report-ready |
| Review-gate agent | Decide whether an action is safe to continue, blocked, or requires human review |
| Report-readiness agent | Help structure human-reviewed findings without automatically submitting reports |
| PoC planning agent | Draft controlled proof-of-concept plans or code only after explicit authorization, scope checks, and human approval |

The intended future system is a live research assistant that can interact with tools, but only through explicit scope, approval, and safety gates.

---

## Current Safety Boundary

Blackhole currently remains fail-closed by design.

It does **not** automatically:

- exploit targets
- bypass authorization
- launch browsers
- execute curl commands
- run Kali tools
- mutate targets
- submit reports
- confirm vulnerabilities
- collect live evidence without approval
- generate or run proof-of-concept logic without a future explicit gate

Every risky step is represented as a local artifact first:

```text
proposal
→ review gate
→ human decision
→ approved packet
→ later execution gate
```

This makes the system suitable for building toward live automation without skipping human control.

---

## Current Brain Sequence

```text
v1.77  Blackhole Brain Architecture
v1.78  Brain Knowledge Store
v1.79  Brain Pattern Library
v1.80  Brain Pattern Knowledge Export
v1.81  Blackhole Demo Case Pack
v1.82  Product README Polish
```

The visible demo is built on top of the Brain pattern and knowledge layers:

```text
Pattern Library
→ Pattern Knowledge Export
→ Demo Case Pack
→ Human-readable investigation summary
```

## Current Capabilities

### Research Planning

Blackhole can turn rough research inputs into structured planning artifacts:

```text
notes / endpoints / source material
→ research source packet
→ hypothesis packet
→ selected hypothesis
→ investigation plan
```

### Human-Gated Action Chain

Blackhole can model action decisions before anything is executed:

```text
investigation plan
→ action proposal packet
→ action proposal review gate
→ human action decision template
→ human action decision packet
→ approved action packet
→ typed tool-request manifest
→ typed tool-request review gate
```

### Observation and Feedback Chain

Blackhole supports a research loop where observations can influence hypothesis confidence without directly mutating state:

```text
research observation packet
→ observation review gate
→ hypothesis feedback packet
→ human feedback decision packet
→ hypothesis confidence update packet
→ future research-state transition review gate
```

### Case Intelligence

Blackhole can summarize local case state, blockers, missing evidence, next safe actions, and whether validation or reporting is currently allowed.

### Report Readiness

Blackhole can organize evidence, blockers, guardrails, and report-readiness notes for human-reviewed vulnerability reports.

---

## What v1.82.0 Adds

`v1.82.0` improves the GitHub landing page and product explanation.

This release makes the project easier to understand by moving the visible demo near the top of the README, removing old release-history clutter, and explaining the current Brain sequence more clearly.

The main code behavior remains the v1.81 demo case pack:

```text
observations
→ matched vulnerability patterns
→ knowledge records
→ hypotheses
→ next investigation steps
→ report-readiness summary
```

v1.82 is a product-facing polish release. It does not add live execution, network requests, evidence collection, target mutation, report submission, or vulnerability confirmation.

## Example Workflow Shape

```text
1. Load target notes, endpoints, HAR data, mobile artifacts, or research context.
2. Build a research source packet.
3. Generate hypotheses.
4. Select one hypothesis.
5. Build an investigation plan.
6. Review proposed actions.
7. Record human decisions.
8. Build typed tool-request manifests.
9. Review whether tool requests are safe.
10. Import observations.
11. Review observations.
12. Generate hypothesis feedback.
13. Record human feedback decisions.
14. Build proposed confidence updates.
15. Prepare for a later research-state transition review.
```

---

## Quick Start

```bash
git clone https://github.com/Siddforeal/Blackhole_AI.git
cd Blackhole_AI

python -m venv .venv
source .venv/bin/activate

pip install -e .
blackhole --help
```

Legacy CLI alias:

```bash
bugintel --help
```

Check version:

```bash
blackhole version
```

---

## Example Commands

```bash
blackhole version
blackhole --help
```

Build a hypothesis confidence update packet:

```bash
blackhole brain-chat-research-hypothesis-confidence-update-packet \
  --hypothesis-file hypothesis.json \
  --decision-file feedback-decision.json \
  --json-output confidence-update.json
```

The command creates a local proposed confidence update packet only. It does not apply updates or execute tools.

---

## Design Principles

- Authorized research only
- Local-first by default
- Human-in-the-loop by default
- Planning before execution
- Evidence before claims
- Review gates before risky actions
- Scope checks before tool interaction
- No automatic vulnerability confirmation
- No automatic report submission
- No target mutation by default
- Provider/tool output is untrusted until reviewed
- PoC logic must be explicitly scoped, reviewed, and approved before use

---

## Roadmap

Blackhole is being built in stages.

Near-term:

```text
v1.19 — Research-state transition review gate
v1.20 — Persistent research-state transition packet
v1.21 — Case memory and running brain loop
v1.22 — Browser/Burp/curl adapter approval templates
v1.23 — Controlled live interaction gates
v1.24 — Human-reviewed PoC planning and generation workflow
```

Long-term:

```text
scope-gated live browser interaction
scope-gated Burp Suite workflow assistance
scope-gated command-line/curl interaction
multi-agent research planning
case memory and self-review
controlled proof-of-concept generation
report-readiness automation
human-approved validation workflows
```

---

## Important Use Notice

Blackhole AI Workbench is intended only for authorized security research, bug bounty work, private labs, internal assessments, and defensive testing.

Do not use it against systems where you do not have permission.

The project is intentionally designed around scope control, human review, safety gates, and evidence-based research decisions.
