# Roadmap

> Historical note: the versioned sections below describe the original early roadmap. Many items listed as planned were later implemented. See **Current Direction After v1.28.0** for the active roadmap.

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

## Current Direction After v1.28.0

The current pipeline now has a write execution review gate for local write packet preview items. The next stage is a human write execution decision packet. Stored-state writes remain disabled until a later separate write path is intentionally introduced and reviewed.
## v1.19.0 Current Direction

The feedback loop now has an explicit human decision packet stage. The next major direction is an approved confidence-update packet and a research-state transition review gate, preserving fail-closed behavior until a human-reviewed transition boundary approves state changes.

## v1.20.0 Current Direction

The current pipeline now has a human transition decision template and decision packet. The next stage is a separate state-transition packet that remains local-only and reviewable before any persistent write is introduced.

## v1.21.0 Current Direction

The current pipeline now has a local research-state transition packet. The next stage is a transition apply review gate that can review local operations before any persistent write is introduced.

## v1.22.0 Current Direction

The current pipeline now has a local apply review gate for research-state transition operations. The next stage is a human apply decision packet that can approve, reject, request changes, or defer each local operation before any persistence preview is introduced.

## v1.23.0 Current Direction

The current pipeline now records explicit human apply decisions for local transition operations. The next stage is a local apply preview that can show the exact proposed stored-state changes before any persistent write path is introduced.

## v1.24.0 Current Direction

The current pipeline now has a local apply preview for approved human apply decisions. The next stage is a persistence write review gate that can inspect previewed changes before any stored-state write path is introduced.
