# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/bugintel-ai-workbench/actions/workflows/tests.yml)

Blackhole AI Workbench is a human-in-the-loop security research workbench for authorized vulnerability discovery, endpoint intelligence, response analysis, and structured evidence collection.

Current version: 0.10.0

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

Blackhole AI Workbench is designed for authorized security testing only.

Every network-capable module should pass through the Scope Guard before execution.

The Scope Guard validates allowed domains, allowed schemes, allowed HTTP methods, forbidden path patterns, and human approval requirements.

The run-curl command requires explicit approval before execution.

## Ethical Use

Use this project only against your own systems, local labs, CTF environments, explicitly authorized bug bounty programs, or written-scope penetration testing engagements.

Do not use this project for unauthorized scanning, exploitation, credential attacks, denial-of-service activity, stealth, evasion, or destructive testing.

## License

MIT License.

## Research Planner Workflow

Blackhole includes a deterministic research planner that turns existing browser evidence into structured hypotheses and recommendations.

Example:

    bugintel plan-research /tmp/browser-evidence-sample.json --json-output /tmp/research-plan.json --markdown-output /tmp/research-plan.md

The planner does not call an LLM, does not execute commands, and does not make network requests. It only analyzes existing evidence.

Example output categories include:

    api-authorization
    object-authorization
    sensitive-surface-review
    error-handling
    browser-evidence-review

Use the output as a manual research guide. Confirm every hypothesis with authorized, in-scope testing before treating it as a finding.

### Safe LLM Prompt Package

Blackhole can convert a deterministic research plan into a reviewable LLM prompt package:

    bugintel build-llm-prompt /tmp/research-plan.json --json-output /tmp/llm-prompt.json --markdown-output /tmp/llm-prompt.md

This command does not call an LLM provider, does not read API keys, does not make network requests, and does not execute commands. It only creates a redacted system/user prompt package for human review.

Use this package as an optional bridge to a future LLM provider. Treat any future LLM output as suggestions only, not confirmed findings.

### LLM Prompt Safety Audit

Blackhole can audit a prompt package locally before provider use:

    bugintel audit-llm-prompt /tmp/llm-prompt.json --json-output /tmp/llm-prompt-audit.json --markdown-output /tmp/llm-prompt-audit.md

The audit is fully local. It scans for common sensitive values and risky prompt instructions, then returns `pass`, `review`, or `blocked`.

Current checks include:

    emails
    JWT-like tokens
    bearer tokens
    API-key-like assignments
    passwords/secrets/tokens
    AWS access key IDs
    prompt-injection style instructions
    safety-bypass instructions
    credential theft or destructive-action instructions

### Endpoint Investigation Profiles

Blackhole can expand a single endpoint into a planning-only investigation profile:

    blackhole endpoint-investigation "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-profile.json

The command classifies the endpoint and creates a reviewable task plan for specialist agents.

Example task categories include:

- baseline and method policy review
- parameter and schema review
- authorization boundary planning
- tenant isolation review
- object reference mutation planning
- file surface safety review
- auth-flow review
- evidence and report checklist

This command does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Disabled LLM Provider Stub

Blackhole includes a disabled-by-default provider stub:

    bugintel run-llm-provider /tmp/llm-prompt.json --json-output /tmp/llm-provider-result.json

The current provider does not call OpenAI, Anthropic, local models, or any network API. It returns a structured disabled result so future provider integration can be added behind explicit opt-in gates.

### UFO Startup Intro

Blackhole includes an optional terminal UFO startup screen:

    bugintel intro

Running `bugintel` with no command also shows the UFO loading screen. Normal commands remain separate and should be used for scripted workflows.

## Browser Evidence Workflow

Blackhole v0.10.0 includes a safe browser automation foundation.

Install optional Playwright support with:

    pip install -e ".[browser]"

Then install browser binaries when you are ready to run real Playwright locally:

    python -m playwright install chromium


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

The v0.10.0 foundation adds a safe Playwright execution preview command. It does not launch a browser. It validates scope, checks whether the optional Playwright package is available, and writes a JSON preview that can later feed execution/evidence workflows.

Example:

    bugintel preview-playwright examples/target.example.yaml https://demo.example.com/dashboard --browser chromium --json-output reports/playwright-preview.json

The preview keeps live execution disabled by default.

### Playwright Execution Safety Gate

Blackhole now includes a safety-gated `execute_playwright_plan()` skeleton for future live browser execution.

The skeleton does not launch a browser yet. It blocks execution unless:

1. The browser plan was approved by Scope Guard.
2. `allow_live_execution=True` is explicitly set after human approval.
3. The optional Playwright Python package is available.

If any gate fails, execution raises `PlaywrightExecutionSafetyError`.

You can exercise the safety gate from the CLI:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard

By default, this command blocks with a safety message. Passing `--allow-live-execution` only passes the explicit opt-in gate; the command still does not launch a browser until real Playwright execution is implemented.

The command can also write a capture-result handoff JSON when the safety gates pass:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

By default, this still routes through the adapter stub. To opt into the real Playwright adapter route, pass both gates explicitly:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --use-real-adapter --json-output reports/playwright-capture-result.json

Real adapter routing requires:

1. Scope Guard approval.
2. `--allow-live-execution`.
3. `--use-real-adapter`.
4. The optional Playwright Python package to be installed and importable.

A safe local smoke test can be run against a temporary `127.0.0.1` HTTP server. Use a local scope file that only allows `http://127.0.0.1`, then run:

    bugintel execute-playwright-plan /tmp/bugintel-local-scope.yaml http://127.0.0.1:8765/dashboard.html --task-name "local real adapter smoke" --allow-live-execution --use-real-adapter --json-output /tmp/bugintel-real-playwright-success.json

Expected successful local result:

    status: completed
    loaded_network_events: >= 1
    loaded_screenshots: 1
    loaded_html_snapshots: 1

The safe handoff chain is:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard --allow-live-execution --json-output reports/playwright-capture-result.json

    bugintel save-browser-capture reports/playwright-capture-result.json

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/playwright-browser-report.md

This validates the evidence/report pipeline before live browser execution is implemented.

### Playwright Execution Request Model

Blackhole also has a pre-execution request model for future Playwright jobs.

A Playwright request records the target, task, start URL, browser type, config, planned actions, and artifact paths before execution.

The artifact planner prepares future paths like:

    artifacts/browser/<target>/<task>/screenshot.png
    artifacts/browser/<target>/<task>/page.html
    artifacts/browser/<target>/<task>/network.json
    artifacts/browser/<target>/<task>/trace.zip

Creating this request does not create files and does not launch a browser.

You can create a request JSON from the CLI:

    bugintel build-playwright-request examples/target.example.yaml https://demo.example.com/dashboard --task-name "Capture Dashboard" --json-output reports/playwright-request.json

This creates a reviewable Playwright request before live execution is implemented.

A safe example request is included at:

    examples/playwright_request.example.json

This file is a sample request shape only. It is not browser evidence and does not mean a browser was launched.

You can preview a saved request JSON:

    bugintel preview-playwright-request examples/playwright_request.example.json --json-output reports/playwright-request-preview.json

This reads the Playwright request and generates an execution preview without launching a browser.

You can also pass a saved request through the execution safety gate:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml

This re-checks the saved request against scope, then blocks by default because live execution is disabled.

To route a saved request through the real Playwright adapter, both opt-in flags must be passed:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --use-real-adapter

To test the future handoff path:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --json-output reports/playwright-request-capture-result.json

In the current skeleton, this still does not launch a browser. It only reaches the safe `not_implemented` handoff path when the safety gates pass.

### Browser Artifact Loading

Blackhole can load planned browser artifacts from a saved Playwright request and convert them into a browser capture result JSON.

Expected artifact paths come from the request JSON:

    artifacts/browser/<target>/<task>/network.json
    artifacts/browser/<target>/<task>/page.html
    artifacts/browser/<target>/<task>/screenshot.png

Example:

    bugintel load-browser-artifacts examples/playwright_request.example.json --json-output reports/browser-capture-result.json

Then save the capture result as redacted evidence:

    bugintel save-browser-capture reports/browser-capture-result.json

This command does not launch a browser. It only reads artifact files that already exist.

### Playwright Adapter Context

Blackhole now has an internal Playwright adapter context.

The adapter context carries the request and planned artifact paths toward the browser adapter.

By default it does not create files. It can optionally create only the artifact directory, but it still does not launch a browser, capture network traffic, save screenshots, save HTML, or create traces.

### Playwright Adapter Stub Runner

Blackhole now has a stub runner for the future Playwright adapter.

The adapter stub returns `status: not_implemented` as a browser capture result.

It proves the adapter can hand results into the evidence pipeline shape, but it still does not launch a browser, capture network traffic, save screenshots, save HTML, or create traces.
