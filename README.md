# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)
[![Latest release](https://img.shields.io/github/v/release/Siddforeal/Blackhole_AI?label=release)](https://github.com/Siddforeal/Blackhole_AI/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Blackhole AI Workbench** is an in-progress agentic security research system for authorized vulnerability research, bug bounty investigation, evidence planning, browser-assisted analysis, Burp Suite workflows, command-line research, and human-reviewed proof-of-concept development.

Blackhole is being built as a local-first AI research brain: it breaks a target into hypotheses, plans investigation steps, reviews evidence, decides what is safe to do next, and routes work through small task-focused agents.

> **Current release:** `v1.68.0`
> **Project status:** active research prototype
> **Current mode:** local-first, planning-first, human-in-the-loop
> **Long-term direction:** scope-gated AI agents that can interact with browsers, Burp Suite, curl, local tools, structured case memory, and controlled proof-of-concept workflows.

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

## What v1.35.0 Adds

`v1.35.0` adds the **Human Final Apply Execution Decision Packet** stage.

Accepted human feedback decisions can now be converted into proposed confidence update records:

```text
final apply execution review gate
→ human final apply execution decision packet
→ later final apply execution packet
```

This still does **not** write persistent research state. It combines final apply execution review items with explicit human final apply execution decisions before any final apply execution packet or stored-state write path is considered.

---

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

## What v1.36.0 Adds

Version 1.36.0 adds a practical bug bounty case intake workflow.

The new `bug-bounty-case-intake` command connects endpoint mining, endpoint priority scoring, endpoint investigation planning, and evidence requirement planning into one P1/P2-focused human workflow.

Input can be HAR text, Burp exports, JavaScript, endpoint lists, or notes. Output includes top endpoints, P1/P2 potential lanes, investigation tasks, evidence requirements, and a manual testing plan.

This still does **not** send requests, execute tools, launch browsers, call providers, collect evidence, submit reports, mutate targets, or confirm vulnerabilities.
