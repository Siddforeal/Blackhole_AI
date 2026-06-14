# Roadmap

> Historical note: the versioned sections below describe the original early roadmap. Many items listed as planned were later implemented. See **Current Direction After v1.19.0** for the active roadmap.

BugIntel AI Workbench is being developed as a human-in-the-loop research prototype for AI-assisted vulnerability discovery and bug intelligence.

## v0.1.0 - MVP Foundation

Completed:

- Scope Guard
- CLI
- Endpoint miner
- Safe curl planner
- Controlled curl execution
- HTTP response parser
- Secret redaction
- Evidence store
- Response diff analyzer
- Research task tree
- Unit tests
- GitHub Actions CI

## v0.2.0 - Report Intelligence

Planned:

- Markdown report generator
- Evidence-to-report conversion
- Report quality scoring
- Severity reasoning
- CWE/category mapping
- Finding templates for common web/API issues

## v0.3.0 - Browser and Proxy Evidence

Planned:

- Playwright browser traffic capture
- HAR importer
- Burp Suite export importer
- JavaScript source collection
- Browser-observed endpoint mining

## v0.4.0 - AI Planning Layer

Planned:

- Human-in-the-loop AI task planner
- Task-tree expansion
- Finding hypothesis generation
- Manual validation checklist generation
- False-positive reduction workflow

## v0.5.0 - Mobile Security Modules

Planned:

- Android APK endpoint extraction
- Android manifest analysis
- Firebase/config discovery
- iOS plist and URL scheme analysis
- Mobile API surface mapping

## v1.0.0 - Research Workbench

Goal:

A full research workbench for authorized web, API, browser, and mobile vulnerability intelligence with structured evidence, AI-assisted planning, and report generation.

## Current Direction After v1.19.0

Blackhole is moving from a structured planning workbench toward an interactive,
human-controlled security research agent.

Planned capabilities include:

- critical target and trust-boundary reasoning
- command-line and workspace interaction
- approved package installation
- browser, DevTools, console, and network interaction
- Burp Suite request and response workflows
- scope-aware Kali and security-tool adapters
- controlled proof-of-concept generation and validation
- observation capture and research-state updates
- multi-agent coordination
- a future specialized security-research LLM

These capabilities must remain scope-controlled, auditable, interruptible, and
subject to risk-appropriate human approval.

## v1.19.0 Current Direction

The feedback loop now has an explicit human decision packet stage. The next major direction is an approved confidence-update packet and a research-state transition review gate, preserving fail-closed behavior until a human-reviewed transition boundary approves state changes.
