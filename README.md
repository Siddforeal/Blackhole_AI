# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)
[![Latest release](https://img.shields.io/github/v/release/Siddforeal/Blackhole_AI?label=release)](https://github.com/Siddforeal/Blackhole_AI/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**Blackhole AI Workbench** is a local-first, human-in-the-loop security research workbench for authorized vulnerability research, bug bounty investigation, endpoint intelligence, evidence planning, and report-readiness review.

It helps researchers turn fragmented notes, endpoints, hypotheses, evidence, and review decisions into a structured local case workflow.

> **Current state:** Blackhole is a planning-oriented, human-controlled research workbench. Its long-term roadmap is an agentic security research, vulnerability validation, and controlled exploitation framework with scope-gated command-line, browser, Burp Suite, Kali/tooling, evidence, proof-of-concept generation, and autonomous research-loop capabilities.

**Current release:** `v1.18.0`

**Project status:** active research prototype

---

## What Blackhole Does

Blackhole organizes security research into safe, reviewable local artifacts:

```text
endpoints / notes / evidence
→ local research state
→ deterministic planning
→ case chat
→ session memory
→ dashboard
→ review packet
→ report-readiness support
```

It helps answer practical workflow questions:

- Which endpoint should I focus on first?
- What is blocking validation?
- What evidence is missing?
- Is this reportable yet?
- What should I not do yet?

---

## Core Capabilities

| Area | What Blackhole Provides |
|---|---|
| Endpoint intelligence | Endpoint grouping, prioritization, investigation profiles, and validation planning |
| Case memory | Local research state, saved chat sessions, summaries, dashboards, and review packets |
| Brain chat | Deterministic local answers about focus, blockers, approvals, evidence, safety, and reportability |
| Evidence planning | Required evidence lists, redaction needs, controlled-object matrices, and blocker tracking |
| Review gates | Provider review, apply-preview review, export-bundle review, dashboard review, and report-readiness checks |
| Report support | Human-reviewed skeletons, finding draft packets, and report-readiness packets |

---

## Core Principles

- Authorized research only
- Local-first by default
- Planning-first by default; controlled execution only through explicit scope, approval, and safety gates
- Human approval before risky actions
- Provider output is untrusted until reviewed
- No automatic vulnerability confirmation
- No automatic report submission
- No target mutation by default
- Evidence before severity or impact claims

---

## Current Safety Model

Blackhole currently does **not** automatically:

- call LLM providers
- execute curl commands
- launch browsers
- run Kali tools
- mutate targets
- bypass authorization
- confirm vulnerabilities
- submit reports

Every provider/tool/browser/execution-oriented workflow is represented as a reviewable plan,
gate, packet, or checklist until a human explicitly validates the next step.

---

## Current Workflow Highlights

### Endpoint and Evidence Planning

Blackhole can organize endpoints and evidence into structured research artifacts:

```text
endpoint list
→ orchestration
→ research state
→ endpoint priority
→ attack surface groups
→ validation runbooks
→ evidence requirements
```

### Case Chat and Provider Review Pipeline

Blackhole supports a safety-gated case-chat workflow that treats external or provider-generated
text as untrusted planning input:

```text
case-chat-prompt-package
→ case-chat-provider-gate
→ case-chat-provider-dry-run
→ case-chat-provider-result-import
→ case-chat-provider-result-review
→ case-chat-suggestion-action-plan
→ case-chat-action-plan-apply-preview
→ case-chat-action-plan-apply-preview-review
→ case-chat-reviewed-apply-packet
→ case-chat-reviewed-apply-packet-export-bundle
→ case-chat-export-bundle-review-gate
→ case-chat-export-bundle-report-readiness-review
```

### Report Readiness

The current release can review whether a gated export bundle is ready to support a human-written
report draft.

It separates report-ready support notes, blockers, missing evidence, unsafe items, artifact
problems, overclaim risks, safety blockers, final checklist items, and report guardrails.

It still does **not** generate or submit reports automatically.

---

### Case Intelligence and Approval Chain

The latest release line adds a local case-intelligence layer on top of the evidence and approval chain.

Chain:

- evidence checklist
- evidence status import
- evidence review gate
- approval request
- approval decision import
- approved validation plan
- validation step review gate
- validation step approval request
- validation step approval decision import
- execution gate proposal
- execution gate proposal review
- case intelligence status summary

This layer explains the current case stage, blockers, missing evidence, safest next action, and whether validation, runtime execution, report submission, or vulnerability confirmation are allowed.

## Research Planning and Action Review Chain

```text
research source packet
→ hypothesis packet
→ hypothesis selection
→ investigation plan
→ investigation plan review gate
→ action proposal packet
→ action proposal review gate
→ human action decision template
→ human action decision packet
→ approved-action packet
→ typed tool-request manifest
→ typed tool-request review gate
→ future exact-action runtime approval template
→ fail-closed execution-gate compatibility preview
→ imported research observation packet
→ observation integrity and safety review gate
→ proposed hypothesis feedback packet
→ future human feedback decision
→ future research-state transition gate
```

The action proposal review gate validates structure, action IDs, tool-family mappings, approval and scope requirements, blockers, ordering, and fail-closed execution flags. The v1.14.0 pipeline then records explicit human decisions, selects effectively approved actions, normalizes typed adapter requests, assigns deterministic digests, and builds a compatibility preview for the existing execution gate.

The v1.15.0 typed tool-request review gate verifies request and manifest digests, deterministic identities and ordering, action profiles, adapter contracts, focus-endpoint requirements, fail-closed execution flags, and execution-gate preview consistency before a future exact-action runtime approval template may be created.

The v1.16.0 observation feedback pipeline imports user-provided research observations, normalizes and digests each observation, verifies packet and observation integrity, validates source linkage, redaction, scope, controlled assets, human review, and preliminary hypothesis-impact calculations, and then creates deterministic proposed confidence feedback against the original hypothesis packet.
The v1.18.0 human hypothesis feedback decision pipeline adds an explicit human decision boundary after proposed hypothesis feedback. It creates a local decision template, records accepted/rejected/changes-requested/deferred decisions, and produces a deterministic feedback decision packet. Accepted decisions only enable a later confidence-update packet stage; they do not directly mutate hypothesis confidence or persistent research state.


The feedback packet may propose retaining, promoting, or demoting categorical hypothesis confidence, but it never changes the source hypothesis packet, hypothesis selection, investigation plans, or persistent research state.

Human approval in this chain authorizes only the next planning artifact. It does not authorize command or payload generation, package installation, tool execution, network or target interaction, evidence collection, vulnerability validation, state mutation, report submission, or vulnerability confirmation.

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

The legacy CLI name is also kept for compatibility:

```bash
bugintel --help
```

---

## Minimal Demo

```bash
cat > /tmp/blackhole-endpoints.txt <<'EOF'
/api/accounts/123/users/{id}/permissions
/api/files/{id}/download
/api/status
EOF

blackhole orchestrate /tmp/blackhole-endpoints.txt \
  --target demo \
  --json-output /tmp/orchestration.json

blackhole research-state /tmp/orchestration.json \
  --output-file /tmp/research-state.md \
  --json-output /tmp/research-state.json
```

---

## Example: Report-Readiness Review

```bash
blackhole case-chat-export-bundle-report-readiness-review \
  --review-gate /tmp/export-bundle-review-gate.json \
  --output /tmp/report-readiness.md \
  --json-output /tmp/report-readiness.json
```

This produces a planning-only readiness review. It does not generate a report, submit a report,
call providers, execute tools, or confirm a vulnerability.

---

## Documentation

| Document | Purpose |
|---|---|
| [CLI Reference](docs/cli-reference.md) | Commands and examples |
| [Feature Reference](docs/feature-reference.md) | Full feature list |
| [Methodology](docs/methodology.md) | Research workflow and methodology |
| [Safety Model](docs/safety-model.md) | Safety guarantees and boundaries |
| [Architecture](docs/architecture.md) | Internal design |
| [Threat Model](docs/threat_model.md) | Misuse and risk analysis |
| [Limitations](docs/limitations.md) | Current limitations |

---

## Release History

The current release is `v1.18.0`.

Full release notes and historical versions are available on the [GitHub releases page](https://github.com/Siddforeal/Blackhole_AI/releases).

## Ethical Use

Use Blackhole only on systems you own, local labs, CTFs, written-scope penetration tests, or
explicitly authorized bug bounty programs.

Do not use it for unauthorized scanning, exploitation, credential theft, persistence, stealth,
denial-of-service activity, destructive testing, or accessing private data.

---

## License

MIT License.
