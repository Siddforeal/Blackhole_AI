# Changelog

## v1.31.0 - Final Persistence Apply Review Gate

- Adds a final persistence apply review gate.
- Adds CLI support for `brain-chat-research-state-final-persistence-apply-review-gate`.
- Converts local write execution packet records into human-reviewable final persistence apply review items.
- Defines allowed human decisions for a later final apply decision packet.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.30.0 - Local Write Execution Packet

- Adds a local-only write execution packet.
- Adds CLI support for `brain-chat-research-state-local-write-execution-packet`.
- Converts approved human write execution decisions into local packet records.
- Prepares local packet records for a later final persistence apply review gate.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.29.0 - Human Write Execution Decision Packet

- Adds a local-only human write execution decision packet.
- Adds CLI support for `brain-chat-research-state-write-execution-decision-packet`.
- Combines write execution review gate items with explicit human write execution decisions.
- Prepares approved decision records for a later local write execution packet.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.28.0 - Write Execution Review Gate

- Adds a local-only write execution review gate.
- Adds CLI support for `brain-chat-research-state-write-execution-review-gate`.
- Converts local write packet preview items into human-reviewable write execution review items.
- Defines allowed human review decisions for the next decision packet stage.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.27.0 - Local Write Packet Preview

- Adds a local-only write packet preview.
- Adds CLI support for `brain-chat-research-state-local-write-packet-preview`.
- Converts approved human persistence write decisions into previewed write packet items.
- Prepares preview items for a later write execution review gate.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.26.0 - Human Persistence Write Decision Packet

- Adds a human persistence write decision packet.
- Adds CLI support for `brain-chat-research-state-persistence-write-decision-packet`.
- Combines a persistence write review gate with explicit human persistence write decisions.
- Prepares approved persistence write items for a later local write packet preview.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.25.0 - Persistence Write Review Gate

- Adds a local-only persistence write review gate.
- Adds CLI support for `brain-chat-research-state-persistence-write-review-gate`.
- Converts local apply preview items into human-reviewable persistence write review items.
- Defines allowed human persistence write decisions for a later explicit write decision packet.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.24.0 - Local Research-State Apply Preview

- Adds a local-only research-state transition apply preview.
- Adds CLI support for `brain-chat-research-state-transition-apply-preview`.
- Converts approved human apply decisions into before/after preview items.
- Prepares approved preview items for a later persistence write review gate.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.23.0 - Human Apply Decision Packet

- Adds a local-only human apply decision packet for research-state transition apply review gates.
- Adds CLI support for `brain-chat-research-state-transition-apply-decision-packet`.
- Combines apply review items with explicit human decisions.
- Prepares approved apply decisions for a later local apply preview.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.22.0 - Research-State Transition Apply Review Gate

- Adds a local-only apply review gate for research-state transition packets.
- Adds CLI support for `brain-chat-research-state-transition-apply-review-gate`.
- Converts local transition operations into human apply review items.
- Requires explicit human apply decisions before any persistence stage can be considered.
- Keeps all persistence, confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.21.0 - Local Research-State Transition Packet

- Adds a local-only research-state transition packet for approved human transition decisions.
- Adds CLI support for `brain-chat-research-state-transition-packet`.
- Converts approved transition candidates into local transition operations.
- Prepares transition operations for a later apply review gate without writing persistent research state.
- Keeps all confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.20.0 - Human Research-State Transition Decision Packet

- Adds a local-only human transition decision template for research-state transition review gates.
- Adds a local-only human transition decision packet for completed transition decisions.
- Adds CLI support for `brain-chat-research-state-transition-decision-template`.
- Adds CLI support for `brain-chat-research-state-transition-decision-packet`.
- Allows approved transition decisions to become ready for a later state-transition packet without directly mutating persistent research state.
- Keeps all confidence mutation, research-state mutation, execution, target interaction, evidence collection, report submission, and vulnerability confirmation disabled.


## v1.19.0 - Research-State Transition Review Gate

- Adds a local-only research-state transition review gate for proposed hypothesis confidence updates.
- Converts ready confidence update packets into pending transition candidates.
- Adds CLI support for `brain-chat-research-state-transition-review-gate`.
- Keeps transition review fail-closed: no direct hypothesis confidence mutation, selected-hypothesis mutation, investigation-plan mutation, persistent research-state mutation, execution, evidence collection, report submission, or vulnerability confirmation.
- Adds deterministic core and CLI regression coverage.


## v1.18.0 - Hypothesis Confidence Update Packet

- Adds a local-only proposed hypothesis confidence update packet.
- Converts accepted hypothesis feedback decision packets into reviewable confidence update records.
- Adds CLI support for `brain-chat-research-hypothesis-confidence-update-packet`.
- Keeps confidence updates fail-closed: no direct hypothesis mutation, selected-hypothesis mutation, investigation-plan mutation, persistent research-state mutation, execution, evidence collection, report submission, or vulnerability confirmation.
- Adds deterministic core and CLI regression coverage.


## v1.17.0 - Human Hypothesis Feedback Decision Pipeline

- Added local-only human decision template generation for hypothesis feedback proposals.
- Added local-only human feedback decision packet generation.
- Added `brain-chat-research-hypothesis-feedback-decision-template` CLI command.
- Added `brain-chat-research-hypothesis-feedback-decision-packet` CLI command.
- Added deterministic validation for accepted, rejected, changes-requested, deferred, missing, duplicate, unsafe, and incomplete feedback decisions.
- Accepted feedback only marks a later confidence-update packet as ready; it does not mutate hypothesis confidence, selection, plans, state, targets, reports, or vulnerability status.
- Added core and CLI regression coverage for the hypothesis feedback decision workflow.

## Unreleased

### Added

## v1.16.0 - Research Observation Feedback Pipeline

Released: 2026-06-12

### Added

- Local-only `brain-chat-research-observation-packet` CLI command
- Local-only `brain-chat-research-observation-review-gate` CLI command
- Local-only `brain-chat-research-hypothesis-feedback-packet` CLI command
- Deterministic normalization of imported research observations
- Observation IDs and SHA-256 observation and packet digests
- Request, action, hypothesis, artifact, signal, and source linkage
- Outcome, evidence-strength, redaction, scope, controlled-assets, and human-review validation
- Preliminary per-observation confidence effects and aggregated hypothesis impacts
- Independent packet, observation, and review-digest verification
- Observation review-gate status and per-observation review results
- Deterministic hypothesis-feedback proposals joined to the original hypothesis packet
- Proposed categorical confidence retention, promotion, and demotion
- Per-proposal and feedback-packet SHA-256 digests
- Markdown and JSON output for all three pipeline stages
- Core, CLI, forced-color, tampering, deterministic-output, status-precedence, and end-to-end pipeline tests

### Safety

- Observation import does not collect evidence or interact with targets
- Observation review does not validate vulnerabilities
- Hypothesis feedback remains proposal-only
- Source hypothesis packets are never modified
- Hypothesis confidence mutation remains disabled
- Hypothesis selection and investigation-plan mutation remain disabled
- Persistent research-state mutation remains disabled
- Command and payload generation remain disabled
- Package installation and tool execution remain disabled
- Browser, Burp Suite, curl, Kali, provider, scanner, and shell execution remain disabled
- Network and target interaction remain disabled
- Report submission and vulnerability confirmation remain disabled

## v1.15.0 - Typed Tool Request Review Gate

Released: 2026-06-12

### Added

- Local-only `brain-chat-research-typed-tool-request-review-gate` CLI command
- Typed tool-request manifest integrity and safety review core
- Manifest-kind, status, readiness, count, and source-digest validation
- SHA-256 manifest and per-request digest verification
- Deterministic request-ID, action-ID, and ordering validation
- Action-profile, tool-family, adapter-family, request-kind, and risk validation
- Adapter contract validation for allowed inputs, required outputs, and prohibited operations
- Scope, controlled-assets, observation, redaction, focus-endpoint, and runtime-gate requirement checks
- Execution-gate input and fail-closed preview consistency validation
- Per-request review results and aggregate finding counts
- Markdown and JSON review-gate outputs
- Core, CLI, forced-color, tampering, deterministic-output, and end-to-end manifest-review tests

### Safety

- Runtime approval-template readiness is separate from runtime authorization
- Command and payload generation remain disabled
- Package installation and tool execution remain disabled
- Browser, Burp Suite, curl, Kali, provider, scanner, and shell execution remain disabled
- Network and target interaction remain disabled
- Evidence collection and vulnerability validation remain disabled
- State mutation, report submission, and vulnerability confirmation remain disabled
- Every request remains non-executable
- The execution-gate compatibility preview remains fail-closed

## v1.14.0 - Research Action Decision Pipeline

Released: 2026-06-11

### Added

- Human decision templates for reviewed research action proposals
- Per-action `approved`, `rejected`, `changes-requested`, and `deferred` decisions
- Research action decision packet with coverage, consistency, reviewer, and fail-closed safety validation
- Approved-action packet containing only effectively approved actions
- Typed adapter mappings for local-file, local-artifact, scope, controlled-assets, browser, Burp Suite, shell-review, and evidence workflows
- Per-action risk, scope, controlled-asset, observation, redaction, artifact, and runtime-gate requirements
- Deterministic typed tool-request manifests compatible with the existing fail-closed execution gate
- SHA-256 request, source-packet, and manifest digests
- Optional focus-endpoint execution-gate compatibility previews
- Markdown and JSON outputs for every new stage
- Four new CLI commands:
  - `brain-chat-research-action-decision-template`
  - `brain-chat-research-action-decision-packet`
  - `brain-chat-research-approved-action-packet`
  - `brain-chat-research-typed-tool-request-manifest`

### Safety

- Human decisions authorize only downstream planning artifacts
- Command and payload generation remain disabled
- Package installation and tool execution remain disabled
- Network and target interaction remain disabled
- Evidence collection and vulnerability validation remain disabled
- State mutation, report submission, and vulnerability confirmation remain disabled
- Typed requests remain non-executable
- The execution-gate compatibility preview remains fail-closed

## v1.13.0 - Research Action Proposal Review Gate

Released: 2026-06-11

### Added

- Local-only `brain-chat-research-action-proposal-review-gate` CLI command
- Research action proposal review-gate core module
- Packet and per-proposal schema validation
- Action ID uniqueness and deterministic ordering checks
- Action-type, tool-family, approval, scope, and blocker validation
- Packet-level and per-proposal fail-closed safety validation
- Markdown and JSON output
- Core, CLI, and end-to-end workflow tests

### Safety

- Command and payload generation remain disabled
- Package installation and tool execution remain disabled
- Target interaction, evidence collection, validation, state mutation, report submission, and vulnerability confirmation remain disabled

## v1.12.0 - Research Action Proposal Packet

Released: 2026-06-11

### Added

- Local-only `brain-chat-research-action-proposal-packet` CLI command
- Research action proposal packet core module
- Deterministic action proposals derived from reviewed investigation plans
- Plan/review target and plan-count consistency checks
- Blocked states for invalid, mismatched, unsafe, or non-review-ready inputs
- Per-hypothesis proposal categories for:
  - local source review
  - local artifact review
  - scope confirmation preparation
  - controlled account preparation
  - browser observation proposal
  - Burp request review proposal
  - command-review preparation
  - evidence-plan preparation
- Markdown and JSON output support
- Unit and CLI tests for the complete proposal workflow

### Safety

- Action proposals do not generate executable commands
- Package installation remains disabled
- Tool, browser, curl, Kali, and Burp execution remain disabled
- Target interaction, evidence collection, validation, state mutation, report submission, and vulnerability confirmation remain disabled
- Human review and later approval gates remain required before any active workflow

## v1.11.0 - Research Investigation Plan Review Gate

Released: 2026-06-10

### Added

- Local-only `brain-chat-research-investigation-plan-review-gate` CLI command
- Research investigation plan review-gate core module
- Structured review status for invalid, empty, unsafe, and human-reviewable investigation plan packets
- Safety findings for top-level execution flags and per-plan validation/evidence/confirmation flags
- Human review checklist and rejected actions for investigation plan review
- Markdown and JSON output support for investigation plan review gates
- Unit and CLI tests for the research investigation plan review gate

### Safety

- Review gate does not browse, generate commands, execute tools, launch browsers, use Kali tools, send requests, collect evidence, validate findings, submit reports, write state, or confirm vulnerabilities
- Runtime execution, validation, evidence collection, report submission, and vulnerability confirmation remain false in review-gate output

- Playwright execution preview foundation
- `preview-playwright` CLI command
- Safe Playwright availability check without installing packages, downloading browsers, or launching a browser
- Browser execution preview JSON output for future browser/evidence handoff
- Safety-gated `execute_playwright_plan()` skeleton for future live browser execution
- `execute-playwright-plan` CLI command for exercising the Playwright safety gate
- `PlaywrightExecutionSafetyError` for blocked execution paths
- Safety test proving all gates passing still returns `not_implemented` until real browser launch is added
- JSON handoff test for `execute-playwright-plan --json-output`
- End-to-end CLI test for Playwright handoff JSON -> browser evidence -> Markdown report
- Browser evidence reports now render Playwright execution-output reasons
- Playwright execution request model for future browser adapter jobs
- `build-playwright-request` CLI command for creating reviewable browser job-ticket JSON
- Safe `examples/playwright_request.example.json` browser job-ticket example
- `preview-playwright-request` CLI command for previewing saved browser job-ticket JSON
- `execute-playwright-request` CLI command for safety-gated execution from saved browser job-ticket JSON
- Scope re-validation for saved Playwright request execution
- Playwright adapter context for future browser-engine integration
- Playwright adapter stub runner returning `not_implemented` capture results
- Optional artifact directory creation without browser launch or evidence capture
- Playwright artifact path planner for future screenshots, HTML snapshots, network logs, and traces
- Live browser execution remains disabled by default

## v0.3.0 - Browser Automation Foundation

Released: 2026-04-27

### Added

- Browser action planner for Chromium, Chrome, and Firefox workflows
- `plan-browser` CLI command
- `save-browser-capture` CLI command for saving future browser capture output as redacted evidence
- Browser network capture, screenshot evidence, and HTML extraction planning
- Browser evidence model for network events, screenshot metadata, HTML snapshots, and future Playwright execution output
- Browser capture result model for future Playwright-to-evidence handoff
- Redacted browser evidence storage with body/HTML previews and SHA-256 hashes
- Scope Guard enforcement for browser start URLs
- Human approval requirement preserved for browser automation planning

## v0.2.0 - Multi-mode Workbench Foundation

Released: 2026-04-27

### Added

- Evidence-to-Markdown report generator
- `generate-report` CLI command
- Analyst review checklist in generated reports
- Generated reports are ignored by Git to avoid accidental upload of private evidence
- Passive HTML analysis for Website Mode
- Scope-guarded website page fetcher
- JavaScript source collector
- Website Recon pipeline combining HTML analysis, JS endpoint mining, and multi-agent orchestration
- HAR traffic importer for Browser/DevTools and proxy exports
- Safe HAR example file using a non-HAR extension
- HAR-to-orchestration planning workflow
- Android manifest/config analyzer
- Android permission, component, exported component, deep-link, and endpoint extraction
- iOS plist/config analyzer
- iOS bundle ID, URL scheme, associated domain, ATS, host, and endpoint extraction

## v0.1.0 - BugIntel AI Workbench MVP

Initial MVP foundation for a human-in-the-loop AI-assisted vulnerability discovery and bug intelligence workbench.

### Added

- Scope Guard for authorized testing boundaries
- CLI interface
- Endpoint miner
- Safe curl planner
- Controlled curl execution with explicit approval
- HTTP response parser
- Secret and email redactor
- Structured evidence store
- Response diff analyzer
- Research task tree builder
- Example target scope files
- Local demo API
- Unit test suite
- GitHub Actions CI
- Security policy and methodology documentation

### Safety

- Out-of-scope domains are blocked
- Unsafe methods are blocked by default
- Evidence previews are redacted
- Curl execution requires explicit approval
