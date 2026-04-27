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

### Playwright Execution Preview

The v0.4.0 foundation adds a safe Playwright execution preview command. It does not launch a browser. It validates scope, checks whether the optional Playwright package is available, and writes a JSON preview that can later feed execution/evidence workflows.

Example:

    bugintel preview-playwright examples/target.example.yaml https://demo.example.com/dashboard --browser chromium --json-output reports/playwright-preview.json

The preview keeps live execution disabled by default.

### Playwright Execution Safety Gate

BugIntel now includes a safety-gated `execute_playwright_plan()` skeleton for future live browser execution.

The skeleton does not launch a browser yet. It blocks execution unless:

1. The browser plan was approved by Scope Guard.
2. `allow_live_execution=True` is explicitly set after human approval.
3. The optional Playwright Python package is available.

If any gate fails, execution raises `PlaywrightExecutionSafetyError`.

You can exercise the safety gate from the CLI:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard

By default, this command blocks with a safety message. Passing `--allow-live-execution` only passes the explicit opt-in gate; the command still does not launch a browser until real Playwright execution is implemented.

The command can also write a future capture-result handoff JSON when the skeleton reaches the handoff stage:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

In the current skeleton, this handoff remains `status: not_implemented`.

The safe handoff chain is:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

    bugintel save-browser-capture reports/playwright-capture-result.json

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/playwright-browser-report.md

This validates the evidence/report pipeline before live browser execution is implemented.

### Playwright Execution Request Model

BugIntel also has a pre-execution request model for future Playwright jobs.

Human meaning: this is a browser job ticket. It records the target, task, start URL, browser type, config, planned actions, and artifact paths before any browser is launched.

The artifact planner prepares future paths like:

    artifacts/browser/<target>/<task>/screenshot.png
    artifacts/browser/<target>/<task>/page.html
    artifacts/browser/<target>/<task>/network.json
    artifacts/browser/<target>/<task>/trace.zip

Creating this request does not create files and does not launch a browser.

You can create a request JSON from the CLI:

    bugintel build-playwright-request examples/target.example.yaml https://demo.example.com/dashboard --task-name "Capture Dashboard" --json-output reports/playwright-request.json

Human meaning: this gives you a reviewable browser job ticket before execution exists.

A safe example request is included at:

    examples/playwright_request.example.json

This file is a sample request shape only. It is not browser evidence and does not mean a browser was launched.
