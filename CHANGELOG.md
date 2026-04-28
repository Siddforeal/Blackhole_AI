# Changelog

## Unreleased

### Added

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
