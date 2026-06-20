# Architecture

Blackhole AI Workbench is designed as a human-in-the-loop, multi-agent security research platform for authorized vulnerability discovery and bug intelligence.

## Core Idea

The workbench breaks a target into a structured research tree.

Each discovered endpoint, browser flow, mobile artifact, or source-code route can be expanded into smaller specialist tasks handled by dedicated agents.

Active testing must pass through the Scope Guard and explicit human approval.

## High-Level Flow

1. Define authorized target scope.
2. Collect passive inputs such as URLs, JavaScript, HAR files, Burp exports, logs, APK/IPA metadata, or source code.
3. Mine endpoints and attack-surface signals.
4. Build a task tree.
5. Assign specialist agents to each node.
6. Plan safe commands or browser actions.
7. Require human approval before active execution.
8. Parse outputs and save redacted evidence.
9. Expand interesting nodes into deeper tasks.
10. Generate reports and validation checklists.

## Major Modes

### Website Mode

Purpose:

- Crawl or review web pages.
- Collect JavaScript sources.
- Mine frontend endpoints.
- Identify login flows, forms, dashboards, exports, admin routes, and integration paths.

Planned agents:

- recon_agent
- endpoint_agent
- browser_agent
- source_agent

### API Mode

Purpose:

- Build endpoint inventory.
- Plan baseline requests.
- Compare own, candidate, blocked, and random-ID responses.
- Detect interesting access-control patterns.
- Support IDOR/BOLA and authorization workflow research.

Planned agents:

- endpoint_agent
- authz_agent
- curl_agent
- report_agent

### Kali Mode

Purpose:

- Plan and run safe command-line research tasks.
- Execute only after Scope Guard approval and explicit human approval.
- Parse command output into structured evidence.

Current support:

- Safe curl planning
- Controlled curl execution

Future support:

- jq/httpx integration
- carefully approved nuclei/template workflows
- local parsing utilities

### Browser Mode

Purpose:

- Interact with real websites through browser automation.
- Capture network traffic.
- Save screenshots and HAR-style evidence.
- Observe frontend behavior that static parsing may miss.

Current support:

- Browser action planning for Chromium, Chrome, and Firefox labels
- Scope Guard validation for browser start URLs
- Human approval requirement preservation
- Planned network capture, screenshot capture, and HTML extraction steps
- Browser evidence records for network events, screenshot metadata, HTML snapshots, and future Playwright execution output
- Browser capture result model that maps future browser execution output into evidence storage

Planned support:

- Playwright execution workflow
- Chrome-compatible browser traffic capture
- Firefox-compatible workflow later
- HAR export/import

### Source Code Mode

Purpose:

- Analyze source code, frontend bundles, and configuration files.
- Extract routes and endpoints.
- Find authz-sensitive paths.
- Identify possible secret patterns.
- Map route handlers to API surfaces.

Planned support:

- grep/ripgrep-based code search
- route extraction
- source endpoint mining
- code-path notes

### Android Mode

Purpose:

- Analyze Android APK-related artifacts.
- Extract mobile API endpoints.
- Review AndroidManifest.xml.
- Identify deep links and exported components.
- Detect Firebase/config references.

Planned support:

- Manifest parser
- endpoint extraction
- Firebase/config review
- deep-link mapping

### iOS Mode

Purpose:

- Analyze iOS IPA/plist-related artifacts.
- Extract URL schemes.
- Discover API hosts.
- Review mobile configuration files.

Planned support:

- plist parser
- URL scheme extractor
- API host discovery
- mobile config review

## Agent Model

Current and planned agents:

- recon_agent: passive website and target intelligence
- endpoint_agent: endpoint categorization and task expansion
- curl_agent: safe curl planning and execution
- authz_agent: authorization workflow planning
- browser_agent: browser and network capture workflows
- source_agent: source-code and route analysis
- android_agent: Android static analysis
- ios_agent: iOS static analysis
- report_agent: evidence-to-report generation

## Evidence Model

Blackhole stores security-testing evidence as redacted JSON records.

Current evidence types:

- HTTP evidence: request metadata, response headers, redacted response preview, response hash, and notes
- Browser evidence: network events, screenshot metadata, HTML snapshot previews and hashes, execution output previews, and artifact references

Browser evidence is designed to support future Playwright execution without storing raw sensitive page bodies by default. Raw response bodies and raw HTML are converted into redacted previews plus SHA-256 hashes for comparison and reproducibility.

The Browser Capture Result model acts as the bridge between a reviewed browser plan, future Playwright execution, and EvidenceStore browser records.

## Safety Model

Blackhole is designed for authorized testing only.

All network-capable actions should follow this flow:

Scope Guard -> Plan -> Human Approval -> Execute -> Parse -> Redact -> Store Evidence -> Expand Task Tree

The system should not perform destructive actions, denial-of-service testing, credential attacks, stealth, evasion, persistence, or out-of-scope testing.

## Current Implementation

Implemented:

- Scope Guard
- Endpoint Miner
- Task Tree
- Agent Registry
- Orchestrator Planner
- Safe Curl Planner
- Controlled Curl Execution
- HTTP Parser
- Response Diff Analyzer
- Secret Redactor
- Evidence Store
- Browser Evidence Model
- Evidence Report Generator
- CLI
- Unit Tests
- GitHub Actions

## Future Direction

The project is evolving from a planning-oriented workbench into the controlled interactive agent runtime described below.

## Interactive Agent Runtime Direction

The long-term runtime is intended to be agentic but controlled. The AI research brain should be able to inspect local files and source code, propose and critique command-line actions, install approved dependencies, interact with approved browser, DevTools, Burp Suite, Kali, and analysis-tool adapters, generate controlled proof-of-concept validation, observe results, and update persistent research state.

Side-effectful actions must remain scope-aware, auditable, interruptible, and subject to risk-appropriate human approval.

```text
reason
→ propose action
→ classify scope and risk
→ obtain approval when required
→ execute through a controlled adapter
→ capture and redact observations
→ update research state
→ critique the result
→ select the next action
```

## Research Action Decision Bridge

Version 1.14.0 connects reviewed research actions to the existing execution-gate architecture without granting runtime authority.

```text
reviewed action proposals
→ explicit human decisions
→ effective planning approval
→ normalized approved actions
→ typed adapter requests
→ execution-gate compatibility input
→ fail-closed gate preview
```

The bridge separates human planning decisions, approved-action normalization, typed request preparation, and runtime authorization.

No v1.14.0 artifact grants runtime authorization. Browser, Burp Suite, shell, Kali, evidence, and other runtime-oriented requests remain blocked by scope, focus-endpoint, controlled-asset, human-approval, observation, redaction, and execution-gate requirements.

## Typed Tool Request Review Boundary

Version 1.15.0 adds a dedicated integrity and safety boundary after typed request generation and before any future exact-action runtime approval artifact.

```text
approved research actions
→ typed tool-request manifest
→ digest and contract verification
→ focus-endpoint and execution-gate consistency review
→ runtime approval-template readiness
→ later exact-action approval and adapter review
```

The review boundary independently reconstructs manifest and request digests, validates deterministic identity and ordering, verifies action profiles and adapter contracts, and rebuilds the existing execution-gate preview from its compatibility input.

A successful review indicates only that a future runtime approval template may be created. It does not make any request executable and does not grant command generation, package installation, network access, target interaction, evidence collection, validation, state mutation, report submission, or vulnerability confirmation.

## Research Observation Feedback Boundary

Version 1.16.0 adds a local feedback boundary between imported research observations and any future persistent research-state transition.

Pipeline:

- external or manually recorded observation
- normalization and deterministic observation identity
- observation and packet digest generation
- independent integrity and safety review
- verified preliminary hypothesis impacts
- proposed hypothesis-confidence feedback
- future human decision
- future state-transition review

The boundary separates observation import, observation normalization, independent observation review, hypothesis-feedback proposal generation, and future persistent state mutation.

Observation import accepts user-provided facts and artifacts but performs no collection. Observation normalization assigns deterministic identities and computes preliminary effects. Observation review independently verifies integrity, linkage, safety, redaction, scope, controlled assets, and impact consistency.

Hypothesis feedback joins verified impacts to the original hypothesis packet and records current confidence, proposed confidence, evidence direction, aggregate confidence delta, linked observation IDs, required human review, and deterministic proposal digests.

A ready feedback packet means only that a human feedback-review artifact may be created. It does not update hypothesis confidence, reorder selected hypotheses, alter investigation plans, authorize execution, collect additional evidence, validate a vulnerability, or mutate persistent research state.

## v1.17.0 Human Feedback Decision Boundary

Version 1.19.0 adds a human decision boundary after proposed hypothesis feedback. The boundary converts proposal-only feedback into explicit local human decisions, then emits a deterministic decision packet. Accepted decisions are still not state mutation; they only allow a later confidence-update packet to be prepared and reviewed by a future transition gate.

This preserves the local-first architecture: no command generation, no runtime execution, no target interaction, no evidence collection, no report submission, and no vulnerability confirmation occur in this stage.


## v1.18.0 Confidence Update Boundary

Accepted feedback decisions do not directly modify hypothesis confidence. The confidence update packet is an intermediate review artifact that prepares proposed updates for a later research-state transition review gate.

All mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.19.0 Research-State Transition Review Boundary

Proposed confidence updates do not directly modify persistent research state. The transition review gate is an intermediate review artifact that requires explicit human transition decision before any later state-transition packet.

All mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.20.0 Human Transition Decision Boundary

A transition review gate must be converted into a human transition decision template before a transition decision packet can be built. The decision packet can mark approved candidates as ready for a later state-transition packet, but still does not write persistent state.

All mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.21.0 Local Transition Packet Boundary

The local transition packet is the first artifact that describes concrete local transition operations, such as proposed hypothesis confidence field updates. It remains non-mutating and requires a later apply review gate before persistence can be considered.

All mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.22.0 Apply Review Gate Boundary

The apply review gate is a non-mutating review stage between local transition operations and any later persistence stage. It turns local transition operations into human apply review items.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.23.0 Human Apply Decision Boundary

The human apply decision packet records explicit human decisions for apply review items. It prepares approved items for a later local apply preview.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.24.0 Local Apply Preview Boundary

The local apply preview is a non-mutating stage between approved human apply decisions and any later persistence write review gate. It shows proposed before/after field changes only.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.25.0 Persistence Write Review Gate Boundary

The persistence write review gate is a non-mutating stage between local apply preview and any later explicit write decision packet. It converts previewed before/after field changes into human-reviewable records.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.26.0 Human Persistence Write Decision Packet Boundary

The human persistence write decision packet is a non-mutating stage between persistence write review gate and any later local write packet preview. It records explicit human decisions and keeps approved items reviewable.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.27.0 Local Write Packet Preview Boundary

The local write packet preview is a non-mutating stage between human persistence write decision packet and any later write execution review gate. It converts approved decision records into preview-only write packet records.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.28.0 Write Execution Review Gate Boundary

The write execution review gate is a non-mutating stage between local write packet preview and any later human write execution decision packet. It converts preview records into human-reviewable review records.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.29.0 Human Write Execution Decision Packet Boundary

The human write execution decision packet is a non-mutating stage between write execution review gate and any later local write execution packet. It records explicit human decisions and preserves source review context.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.30.0 Local Write Execution Packet Boundary

The local write execution packet is a non-mutating stage between the human write execution decision packet and any later final persistence apply review gate. It preserves approved human decisions as local write packet records.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.31.0 Final Persistence Apply Review Gate Boundary

The final persistence apply review gate is a non-mutating stage between the local write execution packet and any later human final apply decision packet. It preserves proposed stored-state field writes as review items.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.32.0 Human Final Apply Decision Packet Boundary

The human final apply decision packet is a non-mutating stage between the final persistence apply review gate and any later final local apply preview. It records explicit human decisions.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.33.0 Final Local Apply Preview Boundary

The final local apply preview is a non-mutating stage between the human final apply decision packet and any later final apply execution review gate. It preserves approved final apply decisions as final local preview records.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.

## v1.34.0 Final Apply Execution Review Gate Boundary

The final apply execution review gate is a non-mutating stage between the final local apply preview and any later human final apply execution decision packet. It exposes final local preview records for explicit human execution review.

All persistence, mutation, execution, network, evidence collection, report submission, and vulnerability confirmation flags remain disabled.
