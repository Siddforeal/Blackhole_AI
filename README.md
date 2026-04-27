# BugIntel AI Workbench

[![Tests](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml)

BugIntel AI Workbench is a human-in-the-loop security research workbench for authorized vulnerability discovery, endpoint intelligence, response analysis, and structured evidence collection.

Current version: 0.3.0

## Research Goal

This project explores AI-assisted vulnerability discovery and bug intelligence workflows for modern web and API security research.

The long-term goal is to support scope-controlled testing, endpoint mining, task-tree based research workflows, safe Kali command planning, controlled execution, response analysis, evidence storage, secret redaction, and report generation.

## Implemented Features

- Scope Guard for authorized testing boundaries
- CLI commands
- Endpoint miner for JavaScript, logs, HAR-style text, and Burp-style exports
- Safe curl planner
- Controlled curl execution with explicit approval
- HTTP response parser
- Secret and email redactor
- Structured evidence store
- Response diff analyzer
- Research task tree builder
- Passive HTML analysis for links, scripts, forms, and endpoints
- Scope-guarded website page fetcher
- JavaScript source collector
- Website Mode pipeline with endpoint merging and orchestration
- HAR traffic importer for Browser/DevTools exports
- HAR-to-orchestration workflow for captured browser traffic
- Android manifest/config analyzer
- Android permissions, components, exported components, deep links, and endpoint extraction
- iOS plist/config analyzer
- iOS bundle ID, URL schemes, associated domains, ATS, hosts, and endpoint extraction
- Browser action planner for Chromium, Chrome, and Firefox workflows
- Browser network capture, screenshot, and HTML extraction planning
- Unit tests
- GitHub Actions CI

## Planned Features

- Playwright browser traffic capture
- HAR and Burp importers
- AI planning layer
- Markdown report generator
- Finding severity scoring
- Duplicate finding detection
- Android APK static analysis
- iOS IPA/plist analysis
- Dashboard UI

## Safety Model

BugIntel AI Workbench is designed for authorized security testing only.

Every network-capable module should pass through the Scope Guard before execution.

The Scope Guard validates allowed domains, allowed schemes, allowed HTTP methods, forbidden path patterns, and human approval requirements.

The run-curl command requires explicit approval before execution.

## Ethical Use

Use this project only against your own systems, local labs, CTF environments, explicitly authorized bug bounty programs, or written-scope penetration testing engagements.

Do not use this project for unauthorized scanning, exploitation, credential attacks, denial-of-service activity, stealth, evasion, or destructive testing.

## License

MIT License.

## Browser Evidence Workflow

BugIntel v0.3.0 includes a safe browser automation foundation.

Current browser workflow:

1. Plan browser actions with Scope Guard.
2. Review the plan before execution.
3. Save future browser/Playwright capture output as redacted evidence.
4. Generate a Markdown report from the saved evidence.

Example:

    bugintel plan-browser examples/target.example.yaml https://demo.example.com/dashboard --browser chromium

    bugintel save-browser-capture examples/browser_capture_result.example.json

The `save-browser-capture` command stores browser capture output through the evidence model. It redacts sensitive previews and stores hashes for response bodies and HTML snapshots.

After saving evidence, generate a report from the saved JSON path:

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/browser-evidence-report.md

Browser execution itself is still a future step. The current implementation provides planning, capture-result normalization, redacted evidence storage, and report rendering.
