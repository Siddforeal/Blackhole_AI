# Changelog

## Unreleased

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
