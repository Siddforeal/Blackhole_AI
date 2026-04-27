# Architecture

BugIntel AI Workbench is designed as a human-in-the-loop, multi-agent security research platform for authorized vulnerability discovery and bug intelligence.

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

BugIntel stores security-testing evidence as redacted JSON records.

Current evidence types:

- HTTP evidence: request metadata, response headers, redacted response preview, response hash, and notes
- Browser evidence: network events, screenshot metadata, HTML snapshot previews and hashes, execution output previews, and artifact references

Browser evidence is designed to support future Playwright execution without storing raw sensitive page bodies by default. Raw response bodies and raw HTML are converted into redacted previews plus SHA-256 hashes for comparison and reproducibility.

The Browser Capture Result model acts as the bridge between a reviewed browser plan, future Playwright execution, and EvidenceStore browser records.

## Safety Model

BugIntel is designed for authorized testing only.

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

The long-term goal is a full authorized research workbench where an AI planner helps a researcher:

- map a target,
- discover endpoints,
- assign specialist agents,
- plan safe tests,
- analyze evidence,
- expand interesting branches,
- and produce high-quality vulnerability reports.
