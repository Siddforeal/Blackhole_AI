# Blackhole AI Workbench

[![Tests](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml/badge.svg)](https://github.com/Siddforeal/Blackhole_AI/actions/workflows/tests.yml)

Blackhole AI Workbench is a human-in-the-loop security research workbench for authorized vulnerability discovery, endpoint intelligence, response analysis, and structured evidence collection.

Current version: 1.21.0

## Research Goal

This project explores AI-assisted vulnerability discovery and bug intelligence workflows for modern web and API security research.

The long-term goal is an interactive, human-controlled AI security research environment that can reason over target context, operate approved command-line, browser, Burp Suite, Kali, and analysis tools, perform controlled proof-of-concept validation, capture observations and evidence, update persistent research state, and support evidence-backed reporting.

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

### Case Timeline Builder

Blackhole can create a planning-only case timeline from local Blackhole artifacts:

    blackhole case-timeline /tmp/blackhole-safe-brain-demo --output-file /tmp/case-timeline.md --json-output /tmp/case-timeline.json

The timeline builder reads known local artifacts such as:

- orchestration JSON
- research-state JSON
- AI brain plan
- brain prompt package
- brain review
- brain decision gate
- human approval packet
- tool request manifest
- tool execution gate
- brain-chat session
- research-state update plan
- research-state apply result

It creates a chronological summary of what happened in the case.

This command is local-only and planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Research State Patch Applier

Blackhole can apply a research-state update plan to a local copy of research-state JSON:

    blackhole research-state-apply /tmp/research-state.json --update-plan /tmp/research-state-update.json --output-file /tmp/research-state.updated.json

It can also write a full apply result JSON:

    blackhole research-state-apply /tmp/research-state.json --update-plan /tmp/research-state-update.json --output-file /tmp/research-state.updated.json --result-json ./research-state-apply-result.json

The applier updates a local copy only.

It can apply planned changes for:

- endpoint triage state
- hypothesis status
- artifact status
- validation notes

This command is local-only and planning-safe. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Research State Update Planner

Blackhole can create a planning-only update plan for research-state JSON after manual validation:

    blackhole research-state-update /tmp/research-state.json --endpoint "/api/accounts/123/users/{id}/permissions" --validation-result supported --note "Validated with controlled accounts." --output-file ./research-state-update.md

It can also write structured JSON:

    blackhole research-state-update /tmp/research-state.json --endpoint "/api/accounts/123/users/{id}/permissions" --validation-result needs-more-evidence --json-output ./research-state-update.json

Supported validation results:

- supported
- rejected
- needs-more-evidence
- deprioritize

The update planner proposes changes for:

- endpoint triage state
- hypothesis status
- artifact status
- validation notes

The command is planning-only. It does not mutate research-state files automatically, call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, or bypass authorization.

### Brain Chat Session Memory

Blackhole can persist local brain-chat turns into a session JSON file:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo --session /tmp/blackhole-chat-session.json
    blackhole brain-chat "status" --state-dir /tmp/blackhole-safe-brain-demo --session /tmp/blackhole-chat-session.json

The session file stores:

- question
- answer
- target name
- focus endpoint
- decision state
- approval status
- execution gate
- execution allowed flag
- timestamp

This is local, deterministic, and planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Deterministic Brain Chat

Blackhole can answer simple local questions from saved brain-state artifacts:

    blackhole brain-chat "hello" --state-dir /tmp/blackhole-safe-brain-demo

It can also write structured JSON:

    blackhole brain-chat "status" --state-dir /tmp/blackhole-safe-brain-demo --json-output ./brain-chat.json

The brain-chat command reads existing planning artifacts such as:

- AI brain plan
- brain decision gate
- human approval packet
- tool execution gate

It can answer planning-only questions like:

- hello
- status
- what should we do next?
- why this endpoint?
- can we execute?

The current implementation is deterministic and local. It does not call an LLM provider.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Tool Execution Gate

Blackhole can create a planning-only execution gate from tool-request-manifest JSON:

    blackhole tool-execution-gate /tmp/tool-request-manifest.json --output-file ./tool-execution-gate.md

It can also write structured JSON:

    blackhole tool-execution-gate /tmp/tool-request-manifest.json --output-file ./tool-execution-gate.md --json-output ./tool-execution-gate.json

The Tool Execution Gate is the final safety checkpoint before any future human-approved execution layer.

It records:

- target name
- focus endpoint
- gate decision
- execution allowed flag
- gate items
- required confirmations
- provider execution status
- execution state

The gate fails closed by default. Execution remains disabled until a future explicit human-approved execution layer exists.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, bypass authorization, or execute tools.

### Tool Request Manifest

Blackhole can create a planning-only tool request manifest from brain-approval JSON:

    blackhole tool-request-manifest /tmp/brain-approval.json --output-file ./tool-request-manifest.md

It can also write structured JSON:

    blackhole tool-request-manifest /tmp/brain-approval.json --output-file ./tool-request-manifest.md --json-output ./tool-request-manifest.json

The Tool Request Manifest converts approval requirements into reviewable future tool/action requests.

It records:

- target name
- focus endpoint
- source approval status
- requested tool/action family
- purpose
- human approval requirement
- blocked-by safety gates
- expected artifact
- execution allowed flag

Execution remains disabled. This command does not execute tools.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Human Approval Packet

Blackhole can create a planning-only human approval packet from brain-decision JSON:

    blackhole brain-approval /tmp/brain-decision.json --output-file ./brain-approval.md

It can also write structured JSON:

    blackhole brain-approval /tmp/brain-decision.json --output-file ./brain-approval.md --json-output ./brain-approval.json

The Human Approval Packet turns a brain decision into a human-reviewable approval checklist before any future tool/browser/curl execution is allowed.

It records:

- source decision
- approval status
- approval-required flag
- focus endpoint
- approval items
- human checklist
- reportability status
- provider execution status

The packet is intentionally conservative. It keeps reportability false until manually validated evidence exists.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Brain Decision Gate

Blackhole can create a planning-only decision gate from brain-review JSON:

    blackhole brain-decision /tmp/brain-review.json --output-file ./brain-decision.md

It can also write structured JSON:

    blackhole brain-decision /tmp/brain-review.json --output-file ./brain-decision.md --json-output ./brain-decision.json

The Brain Decision Gate reads a brain review and decides the next safe state:

- blocked
- blocked-pending-scope-and-controls
- ready-for-human-approval
- ready-for-manual-validation
- needs-more-planning

It also records:

- focus endpoint
- decision rationale
- blockers
- required next steps
- reportability status
- provider execution status

The gate is intentionally conservative. It never marks a vulnerability as confirmed or reportable without manually validated evidence.

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### Brain Review / Reasoning Draft

Blackhole can create a planning-only reasoning review from a brain-prompt JSON package:

    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md

It can also write structured JSON:

    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md --json-output ./brain-review.json

The Brain Review layer is the first deterministic reasoning-output layer after the LLM Brain Prompt Package.

Current safe brain flow:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json
    blackhole research-state /tmp/orchestration.json --json-output /tmp/research-state.json
    blackhole ai-brain /tmp/research-state.json --json-output /tmp/ai-brain-plan.json
    blackhole brain-prompt /tmp/ai-brain-plan.json --json-output /tmp/brain-prompt.json
    blackhole brain-review /tmp/brain-prompt.json --output-file ./brain-review.md --json-output ./brain-review.json

Generated brain reviews include:

- recommended focus endpoint
- why the endpoint is high signal
- open hypotheses to review
- evidence artifacts needed
- human approvals required
- safety gates still blocking execution
- next manual validation step
- stop conditions
- research state updates after validation

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### LLM Brain Prompt Package

Blackhole can create a provider-ready, planning-only prompt package from AI brain JSON:

    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md

It can also write structured JSON:

    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md --json-output ./brain-prompt.json

The LLM Brain Prompt Package is the bridge between deterministic AI brain planning and future provider-gated LLM reasoning.

It packages:

- system instructions
- developer safety requirements
- structured user context from the AI brain plan
- assistant task instructions
- focus endpoint
- safety gates
- provider execution status

The generated prompt package is provider-ready, but Blackhole does not call an LLM provider yet.

Current flow:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json
    blackhole research-state /tmp/orchestration.json --json-output /tmp/research-state.json
    blackhole ai-brain /tmp/research-state.json --json-output /tmp/ai-brain-plan.json
    blackhole brain-prompt /tmp/ai-brain-plan.json --output-file ./brain-prompt.md --json-output ./brain-prompt.json

This command is planning-only. It does not call LLM providers, send requests, execute shell commands, launch browsers, use Kali tools, mutate targets, or bypass authorization.

### AI Brain Interface

Blackhole can create a planning-only AI brain plan from research-state JSON:

    blackhole ai-brain /tmp/research-state.json --output-file ./ai-brain-plan.md

It can also write structured JSON:

    blackhole ai-brain /tmp/research-state.json --output-file ./ai-brain-plan.md --json-output ./ai-brain-plan.json

The AI Brain Interface is the first deterministic brain layer for Blackhole.

It reads structured case memory and decides:

- which endpoint to focus on first
- why the endpoint matters
- which hypotheses are open
- which artifacts are required
- which actions require human approval
- which safety gates block execution
- what the next planning action should be

The current AI brain is deterministic and planning-only. It does not call LLM providers yet.

Generated brain plans include:

- focus queue
- endpoint priority
- triage state
- hypotheses
- required artifacts
- next actions
- global actions
- safety gates
- provider execution status

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, use Kali tools, mutate targets, or bypass authorization.

### Research State / Case Memory

Blackhole can create planning-only research state from orchestration JSON:

    blackhole research-state /tmp/orchestration.json --output-file ./research-state.md

It can also write structured JSON:

    blackhole research-state /tmp/orchestration.json --output-file ./research-state.md --json-output ./research-state.json

Research state is the base layer for the future Blackhole AI brain.

It stores:

- target name
- endpoint memory
- endpoint priority
- attack-surface groups
- triage state
- hypotheses
- planned evidence artifacts
- redaction requirements
- approval requirements
- global decisions

Example endpoint states include:

- ready-for-manual-validation
- queued
- watchlist
- deprioritized

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Validation Runbook Builder

Blackhole can create a safe manual validation runbook from orchestration JSON:

    blackhole validation-runbook /tmp/orchestration.json --output-file ./validation-runbook.md

It can also write structured JSON:

    blackhole validation-runbook /tmp/orchestration.json --output-file ./validation-runbook.md --json-output ./validation-runbook.json

The runbook helps answer:

- what should be validated first
- which endpoint requires approval
- what evidence should be collected
- what must be redacted
- when the researcher should stop
- how to make a reportability decision

Generated runbooks include:

- global safety rules
- endpoint priority
- attack-surface groups
- validation phases
- expected evidence artifacts
- redaction requirements
- human approval requirements
- stop conditions

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Report Draft Builder

Blackhole can create a safe report draft skeleton from orchestration JSON:

    blackhole report-draft /tmp/orchestration.json --output-file ./report-draft.md

It can also write structured JSON:

    blackhole report-draft /tmp/orchestration.json --output-file ./report-draft.md --json-output ./report-draft.json

The draft includes sections for:

- Summary
- Scope and Authorization
- Priority Triage
- Attack Surface Grouping
- Evidence Requirements
- Validation Notes
- Impact
- Steps to Reproduce
- Evidence References
- Safety and Redaction Checklist

The report draft is a skeleton only. It must be filled with manually validated evidence before submission.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Evidence Workspace Builder

Blackhole can create a local evidence workspace from orchestration JSON:

    blackhole evidence-workspace /tmp/orchestration.json --output-dir ./case-demo

The workspace builder creates a local folder structure for safe, organized research evidence.

Example output structure:

    case-demo/
    ├── README.md
    ├── manifest.json
    ├── redaction-checklist.md
    ├── report-notes.md
    └── endpoints/
        └── 001-api-accounts-123-users-id-permissions/
            ├── README.md
            ├── checklist.md
            ├── notes.md
            ├── requests/
            ├── responses/
            └── screenshots/

The generated files help organize:

- endpoint evidence summaries
- evidence checklists
- researcher notes
- redacted request samples
- redacted response samples
- approved screenshots
- global redaction checklist
- report notes

This command is local-only and planning-only. It does not send requests, execute shell commands against targets, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Evidence Requirements Planning

Blackhole can plan what evidence is needed to validate and report findings safely:

    blackhole evidence-requirements endpoints.txt --json-output /tmp/evidence-requirements.json

Evidence requirements help the researcher understand what proof artifacts are needed before active testing.

Example requirements include:

- scope-and-authorization-proof
- baseline-request-response-sample
- redaction-checklist
- controlled-account-role-matrix
- authorization-decision-diff
- identifier-source-map
- owned-foreign-random-response-matrix
- safe-test-file-manifest
- file-access-control-evidence
- integration-secret-redaction-proof
- integration-boundary-evidence
- low-signal-deprioritization-note

Blackhole orchestration also includes evidence requirements in JSON and terminal output:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

This helps prioritize not only what to inspect first, but also what proof is needed for safe validation and report writing.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Attack Surface Grouping

Blackhole can group endpoint inventories into planning-only attack-surface buckets:

    blackhole attack-surface endpoints.txt --json-output /tmp/attack-surface.json

Attack-surface groups help organize research around meaningful security areas.

Example groups include:

- identity-access
- tenant-project-boundary
- file-surface
- auth-flow
- billing-money
- integration-webhook
- secret-token-key
- object-reference
- parameter-heavy
- low-signal
- general-api

Blackhole orchestration also includes attack-surface groups in JSON and terminal output:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

This helps the researcher see which endpoint clusters deserve focused review.

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Priority-Aware Orchestration

Blackhole orchestration now includes endpoint priority scoring in the generated plan and terminal output.

Example:

    blackhole orchestrate endpoints.txt --target demo --json-output /tmp/orchestration.json

The orchestration output includes:

- task tree expansion
- specialist agent assignments
- endpoint priority scores
- score bands such as critical, high, medium, low, and info
- top scoring signals for each endpoint

This helps prioritize high-value endpoints before any active testing.

Priority-aware orchestration is still planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

### Endpoint Priority Scoring

Blackhole can score a single endpoint using planning-only security heuristics:

    blackhole endpoint-priority "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-priority.json

Blackhole can also rank endpoint inventories from a text file:

    blackhole prioritize-endpoints endpoints.txt --json-output /tmp/prioritized-endpoints.json

Priority scoring helps focus manual research on endpoints that look more security-sensitive.

Signals include:

- authorization-sensitive routes
- object references
- file upload/download surfaces
- authentication/session flows
- billing/payment/invoice routes
- integrations/webhooks/OAuth callbacks
- token/key/secret routes
- low-signal public/static/status routes

This command is planning-only. It does not send requests, execute shell commands, launch browsers, call LLM providers, mutate targets, or bypass authorization.

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

Blackhole v0.59.0 includes a safe browser automation foundation.

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

The v0.59.0 foundation adds a safe Playwright execution preview command. It does not launch a browser. It validates scope, checks whether the optional Playwright package is available, and writes a JSON preview that can later feed execution/evidence workflows.

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

## v0.60.0 - Case Chat Suggestion Action Plan

The provider suggestion action plan bridge converts reviewed provider suggestions into safe local manual next steps.

It is designed for the end of the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan

The output keeps provider suggestions untrusted until they are mapped against local evidence. The generated plan clearly marks what can be manually investigated, what needs additional evidence, and what must be rejected or avoided.

This feature keeps Blackhole deterministic and local-first by default. It does not execute provider suggestions or confirm vulnerabilities automatically.

## v0.61.0 - Case Chat Action Plan Apply Preview

The action plan apply preview bridge turns a reviewed suggestion action plan into safe local update candidates.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview

The output previews what could be added to local case memory and research state, while keeping blocked actions separate until a human closes evidence gaps or safety concerns.

This feature is intentionally non-mutating. It does not write state, execute tools, call providers, or confirm vulnerabilities.

## v0.62.0 - Case Chat Apply Preview Reviewer

The apply preview reviewer checks a v0.61.0 apply preview before any future state-write workflow exists.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review

The output helps a human researcher decide whether apply-preview candidates should remain planning notes, be deduplicated, be blocked, or require more evidence.

This feature is intentionally non-mutating. It does not write state, execute tools, call providers, or confirm vulnerabilities.

## v0.63.0 - Case Chat Reviewed Apply Packet

The reviewed apply packet turns a v0.62.0 apply-preview review into a final human approval packet.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet

The output helps a human decide what can remain as approved planning notes, what must be deduplicated, what stays blocked, and what requires more evidence or safer wording.

This feature is intentionally non-mutating. It does not write state, execute tools, call providers, or confirm vulnerabilities.

## v0.64.0 - Reviewed Apply Packet Export Bundle

The reviewed apply packet export bundle builds a local bundle manifest from a v0.63.0 reviewed apply packet.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle

The output packages the packet recommendation, section counts, included local artifact references, human review checklist, report guardrails, and safety metadata into a reviewable manifest.

This feature is intentionally non-mutating. It does not write case memory, write research state, execute tools, call providers, or confirm vulnerabilities.

## v0.65.0 - Export Bundle Review Gate

The export bundle review gate checks a v0.64.0 export bundle before it is used in reports or future workflows.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate

The output audits artifact references, packet risk counts, evidence gaps, overclaim risks, safety metadata, human review checklist items, and report guardrails.

This feature is intentionally non-mutating. It does not write case memory, write research state, execute tools, call providers, or confirm vulnerabilities.

## v0.66.0 - Export Bundle Report Readiness Review

The export bundle report readiness review checks a v0.65.0 review gate before using a bundle to support human report drafting.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate
    → case-chat-export-bundle-report-readiness-review

The output separates report-supporting notes from blockers, missing evidence, unsafe or rejected items, artifact problems, overclaim risks, safety blockers, final checklist items, and report guardrails.

This feature is intentionally non-mutating. It does not generate reports, submit reports, write state, execute tools, call providers, or confirm vulnerabilities.

## v0.67.0 - Report Readiness Finding Draft Packet

The report readiness finding draft packet converts a v0.66.0 report-readiness review into safe structured support for human report writing.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate
    → case-chat-export-bundle-report-readiness-review
    → case-chat-report-readiness-finding-draft-packet

The output prepares title candidates, evidence checklist items, reproduction placeholders, impact and severity guardrails, blocked claims, do-not-claim-yet items, final human writing checklist items, and safety metadata.

This feature is intentionally non-mutating. It does not generate reports, submit reports, write state, execute tools, call providers, or confirm vulnerabilities.

## v0.68.0 - Finding Draft Packet Review Gate

The finding draft packet review gate checks a v0.67.0 finding draft packet before human report writing.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate
    → case-chat-export-bundle-report-readiness-review
    → case-chat-report-readiness-finding-draft-packet
    → case-chat-finding-draft-packet-review-gate

The output reviews title quality, evidence checklist completeness, reproduction placeholder gaps, wording guardrails, blocked claims, do-not-claim-yet items, safety metadata, and whether the packet is safe only as human writing support.

This feature is intentionally non-mutating. It does not generate reports, submit reports, write state, execute tools, call providers, or confirm vulnerabilities.

## v0.69.0 - Human Report Skeleton Packet

The human report skeleton packet converts a v0.68.0 finding draft packet review gate into safe report section placeholders for human writing.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate
    → case-chat-export-bundle-report-readiness-review
    → case-chat-report-readiness-finding-draft-packet
    → case-chat-finding-draft-packet-review-gate
    → case-chat-human-report-skeleton-packet

The output prepares Summary, Impact, Steps to Reproduce, Evidence, Affected Assets, Severity Rationale, Remediation, Blocked Claims / Do Not Claim, and Human final-writing checklist sections.

This feature is intentionally non-mutating. It does not generate final reports, submit reports, write state, execute tools, call providers, or confirm vulnerabilities.

## v0.70.0 - Human Report Skeleton Review Gate

The human report skeleton review gate checks a v0.69.0 human report skeleton packet before a human turns it into a report.

It extends the case-chat provider workflow:

    case-chat-prompt-package
    → case-chat-provider-gate
    → case-chat-provider-dry-run
    → case-chat-provider-result-import
    → case-chat-provider-result-review
    → case-chat-suggestion-action-plan
    → case-chat-action-plan-apply-preview
    → case-chat-action-plan-apply-preview-review
    → case-chat-reviewed-apply-packet
    → case-chat-reviewed-apply-packet-export-bundle
    → case-chat-export-bundle-review-gate
    → case-chat-export-bundle-report-readiness-review
    → case-chat-report-readiness-finding-draft-packet
    → case-chat-finding-draft-packet-review-gate
    → case-chat-human-report-skeleton-packet
    → case-chat-human-report-skeleton-review-gate

The output reviews section completeness, blocker leakage, evidence mapping gaps, impact and severity risk, blocked/do-not-claim items, safety metadata, and whether the skeleton is safe only as human writing support.

This feature is intentionally non-mutating. It does not generate final reports, submit reports, write state, execute tools, call providers, or confirm vulnerabilities.

## v0.71.0 - Brain Chat Question Router

The brain chat question router makes `brain-chat` understand more natural phrasing while remaining deterministic and local-only.

It routes questions such as:

    What is blocking validation?
    Why can't we test?
    What approvals are missing?
    What evidence do we need?
    What endpoint should I start with?
    Which endpoint is highest priority?
    Can we execute?
    Is this reportable?

The router maps these questions to existing safe answer types: focus, blockers, approvals, evidence, execution, reportability, status, next steps, and help.

This feature does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.72.0 - Brain State Export Builder

The brain state export builder removes the manual copy/rename step required by `brain-chat`.

It exports generated brain artifacts into the numbered state directory layout expected by `brain-chat`:

    03-ai-brain.json
    06-brain-decision.json
    07-brain-approval.json
    09-tool-execution-gate.json

This makes the local brain-chat workflow easier to use after building:

    ai-brain
    brain-prompt
    brain-review
    brain-decision
    brain-approval
    tool-request-manifest
    tool-execution-gate
    brain-state-export
    brain-chat

This feature is local-only and file-copy-only. It does not execute tools, call providers, send requests, launch browsers, mutate targets, or confirm vulnerabilities.

## v0.73.0 - Brain Chat Demo Flow

The brain chat demo flow runs the local planning-only chain from an endpoints file to a ready-to-use `brain-chat` state directory.

It creates the core artifacts needed to understand how Blackhole works:

    endpoints.txt
    → orchestration
    → research-state
    → ai-brain
    → brain-prompt
    → brain-review
    → brain-decision
    → brain-approval
    → tool-request-manifest
    → tool-execution-gate
    → brain-state-export
    → brain-chat-ready state directory

This feature is designed for first-run demos and onboarding. It does not execute tools, call providers, send requests, launch browsers, mutate targets, or confirm vulnerabilities.

## v0.74.0 - Brain Chat Case Directory Discovery

The brain-chat case directory discovery release improves the local chat user experience.

`brain-chat` can now use:

    blackhole brain-chat "What should I test first?" --case-dir /tmp/case

or, from inside a case directory containing `brain/`:

    blackhole brain-chat "What should I test first?"

This removes the need to always pass `--state-dir /tmp/case/brain` after using `brain-chat-demo-flow`.

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.75.0 - Brain Chat Case Session Auto-Save

The brain-chat case session auto-save release makes local chat history automatic when using a case directory.

After this release:

    blackhole brain-chat "What should I test first?" --case-dir /tmp/case

automatically appends the turn to:

    /tmp/case/brain-chat-session.json

And from inside a case directory:

    cd /tmp/case
    blackhole brain-chat "What should I test first?"

automatically appends the turn to:

    ./brain-chat-session.json

Explicit `--session` remains the manual override. Explicit `--state-dir` remains session-neutral unless `--session` is also provided.

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.76.0 - Brain Chat Session Summary Command

The brain-chat session summary command makes saved local chat history easier to review.

It can summarize:

    /tmp/case/brain-chat-session.json

or, from inside a case directory:

    ./brain-chat-session.json

The summary reports total turns, latest question, latest focus endpoint, latest decision, approval status, execution gate, repeated questions, and a suggested next question.

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.77.0 - Brain Chat Session Next-Step Planner

The brain-chat session next-step planner turns saved local chat history into an actionable planning packet.

It reads a brain-chat session and produces:

    next safe question
    current focus endpoint
    current blocker
    next evidence list
    do-not-do-yet list
    safety metadata

This makes saved chat history actionable instead of only descriptive.

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.78.0 - Brain Chat Case Dashboard

The brain-chat case dashboard combines saved local chat history with the next-step planner into one case overview.

It reports:

    target
    focus endpoint
    latest question
    session turn count
    decision
    approval status
    execution gate
    execution allowed flag
    reportable flag
    current blocker
    next question
    next evidence list
    repeated questions
    safety metadata

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.79.0 - Brain Chat Case Dashboard Review Packet

The brain-chat case dashboard review packet turns dashboard state into a safe local review packet.

It blocks reportability from dashboard state alone and requires local validation evidence before any report or vulnerability claim.

The packet includes:

    focus endpoint
    reportability status
    execution status
    blockers
    required evidence
    safe next action
    rejected actions
    safety metadata

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.80.0 - Brain Chat Smart Next Question Rotation

Brain-chat summaries and dashboards now suggest less repetitive next questions.

Before this release, repeated questions could cause the suggested next question to stay stuck on:

    What is blocking validation?

The new deterministic rotation prefers useful unasked or less-repeated questions:

    What approvals are missing?
    What is blocking validation?
    What evidence do we need?
    Can we execute?
    Is this reportable?
    What should I not do yet?

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.81.0 - Brain Chat Case Dashboard Review Packet CLI

The brain-chat case dashboard review packet CLI exposes the v0.79 review-packet core feature as a user-facing command.

The command can read a local brain-chat session and produce:

    blockers
    required evidence
    safe next action
    rejected actions
    Markdown output
    JSON output
    safety metadata

This closes the workflow gap between the dashboard and the review packet.

This feature remains deterministic and local-only. It does not add provider calls, execution, network interaction, report generation, or vulnerability confirmation.

## v0.82.0 - Brain Chat Evidence Checklist Tracker

The brain-chat evidence checklist tracker turns review-packet required evidence into a local checklist.

It tracks evidence items with deterministic statuses:

    missing
    collected
    review-needed
    blocked

The checklist reports total, missing, collected, review-needed, and blocked evidence counts.

This feature remains deterministic and local-only. It does not collect evidence, call providers, execute tools, send requests, generate reports, or confirm vulnerabilities.

## v0.83.0 - Evidence Checklist Status Importer

The evidence checklist status importer updates local checklist status metadata from a JSON file.

It supports deterministic evidence statuses:

    missing
    collected
    review-needed
    blocked

The importer can update statuses and notes, report unmatched labels, and produce an updated local checklist.

This feature remains deterministic and local-only. It does not collect evidence, call providers, execute tools, send requests, generate reports, or confirm vulnerabilities.

## v0.84.0 - Evidence Checklist Review Gate

The evidence checklist review gate reviews local checklist readiness and returns a deterministic gate status.

It can decide whether the checklist is:

    blocked
    needs-review
    ready-for-validation-approval

The review gate reports blockers, review reasons, approval requirements, evidence counts, and safety metadata.

This feature remains deterministic and local-only. It does not collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.85.0 - Evidence Checklist Approval Request Packet

The evidence checklist approval request packet turns review-gate state into a local human approval request.

It stays blocked when the checklist review gate is:

    blocked
    needs-review

It becomes ready only when the gate is:

    ready-for-validation-approval

The approval request reports blockers, required human checks, allowed actions after approval, rejected actions without approval, and safety metadata.

This feature remains deterministic and local-only. It does not grant approval, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.86.0 - Evidence Approval Decision Importer

The evidence approval decision importer records a local human reviewer decision for an approval request packet.

Supported decisions:

    approved
    rejected
    changes-requested

An approved decision becomes effective only when the approval request is ready for human approval and the underlying review gate is ready for validation approval.

This feature remains deterministic and local-only. It does not grant side-effectful approval, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.87.0 - Evidence Approved Validation Plan Builder

The evidence approved validation plan builder creates a local validation-plan packet from an approval decision.

A plan is ready only when effective approval is granted.

If approval is blocked or premature, the plan remains:

    blocked-pending-effective-approval

If effective approval is granted, the plan becomes:

    ready-for-manual-validation-planning

This feature remains deterministic and local-only. It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.88.0 - Validation Plan Step Review Gate

The validation plan step review gate reviews local validation-plan steps before any future execution layer exists.

It classifies planned steps as:

    allowed-for-manual-review
    needs-scope-check
    rejected-unsafe

The gate can remain blocked when effective approval is missing, require scope review for sensitive steps, or reject unsafe validation language.

This feature remains deterministic and local-only. It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.89.0 - Validation Step Approval Request Packet

The validation step approval request packet turns a ready validation step review gate into a local human approval request.

It stays blocked when the step review gate is:

    blocked-pending-approved-validation-plan
    needs-scope-check
    blocked-unsafe-validation-step

It becomes ready only when the step review gate is ready for manual step review.

This feature remains deterministic and local-only. It does not grant approval, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.90.0 - Validation Step Approval Decision Importer

The validation step approval decision importer records a local human reviewer decision for validation-step approval.

Supported decisions:

    approved
    rejected
    changes-requested

An approved decision becomes effective only when the validation step approval request is ready, step review is ready, validation is allowed, and reviewed steps exist for approval.

This feature remains deterministic and local-only. It does not grant side-effectful approval, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.91.0 - Validation Step Execution Gate Proposal

The validation step execution gate proposal builds a local proposal for what a future execution gate would require.

It stays blocked unless effective validation-step approval exists.

Even when ready, it only describes required safeguards for a future gate. It does not create an execution gate, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.92.0 - Execution Gate Proposal Review Packet

The execution gate proposal review packet reviews a local execution-gate proposal before any future execution-gate design.

Review statuses:

    blocked-pending-effective-step-approval
    needs-human-review
    ready-for-execution-gate-design-review

The packet reviews effective step approval, proposal readiness, proposed requirements, runtime guards, blockers, and human-review items.

This feature remains deterministic and local-only. It does not create an execution gate, execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.93.0 - Case Intelligence Status Summary

The case intelligence status summary is the first case-intelligence layer.

It summarizes local state across the evidence, approval, validation, step-review, and execution-gate proposal chain.

The summary reports the current stage, latest status, blockers, missing evidence, safest next action, chain position, and whether validation, runtime execution, report submission, or vulnerability confirmation are allowed.

This feature remains deterministic and local-only. It does not execute validation, collect evidence, call providers, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.94.0 - Case Intelligence Question Answerer

The case intelligence question answerer answers local deterministic questions from the case intelligence status summary.

It can explain blockers, missing evidence, safest next action, validation state, runtime execution state, report-submission state, vulnerability-confirmation state, chain position, and safety posture.

This feature remains deterministic and local-only. It does not call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.95.0 - Case Intelligence Question Set Runner

The case intelligence question set runner runs a bundled set of deterministic local questions against the case intelligence status summary.

The default set covers current status, blockers, missing evidence, safest next action, validation state, runtime execution state, report-submission state, vulnerability-confirmation state, chain position, and safety posture.

This feature remains deterministic and local-only. It does not call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.96.0 - Case Intelligence Briefing Export

The case intelligence briefing export creates one local deterministic briefing packet from the case intelligence status summary and question-set answers.

The briefing combines case state, current status, missing evidence, blockers, safest next action, chain position, evidence counts, question-set answers, and safety metadata.

This feature remains deterministic and local-only. It does not call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.97.0 - Case Intelligence Briefing Review Gate

The case intelligence briefing review gate reviews a local briefing export and classifies it as blocked, needing human review, or ready for human case review.

The gate checks missing evidence, blockers, unsafe permission flags, runtime/reporting/confirmation state, briefing completeness, human review items, required human checks, rejected actions, and safety metadata.

This feature remains deterministic and local-only. It does not call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.98.0 - Case Intelligence Human Review Request

The case intelligence human review request turns a briefing review gate into a clean local request packet for human review.

The packet includes review request status, human-review readiness, missing evidence checklist, blockers checklist, required human checks, requested human decision options, rejected actions, and explicit no-approval-granted safety metadata.

This feature remains deterministic and local-only. It does not grant approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v0.99.0 - Case Intelligence Human Review Decision Importer

The case intelligence human review decision importer imports a local human-review decision for the case-intelligence human-review request.

Supported decisions are approved-for-human-case-review, changes-requested, and rejected. Approval becomes effective only when the human-review request is ready, the case-review gate is ready, and unsafe flags remain disabled.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.0.0 - Case Intelligence Human Review Decision Gate

The case intelligence human review decision gate reviews an imported human-review decision and classifies the next local state.

Gate statuses are blocked-pending-effective-human-review, changes-requested, rejected, and ready-for-human-case-review.

The gate verifies whether approval is effective or only typed in JSON, whether the human-review request and case-review gate are ready, whether unsafe flags remain disabled, what exact local next step is allowed, and what actions remain rejected.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.1.0 - Human Case Review Packet

The human case review packet turns a case-intelligence human-review decision gate into a clean local packet for human case review.

The packet reports whether human case review can begin, whether the path is blocked, changes-requested, rejected, or ready, what the human should review, what blockers or missing evidence remain, what local-only next step is allowed, and what actions remain rejected.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.2.0 - Human Case Review Packet Review Gate

The human case review packet review gate reviews a local human case-review packet before any future human case-review decision step.

The gate classifies packet review state as blocked-pending-human-case-review-packet, changes-requested, rejected, or ready-for-human-case-review.

It verifies packet status, human case-review readiness, effective approval state, decision blockers, missing evidence, blocker checklist, required human checks, unsafe flags, allowed local next step, and rejected actions.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.3.0 - Human Case Review Decision Request

The human case review decision request turns a reviewed human case-review packet into a local request packet for a future human decision.

The request says whether a human case-review decision can be requested, whether the path is blocked, changes-requested, rejected, or ready, what decision options are allowed, what the reviewer must check before deciding, what blockers remain, what local-only next step is allowed, and what actions remain rejected.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.4.0 - Human Case Review Decision Importer

The human case review decision importer imports a local reviewer decision for a human case-review decision request.

It supports approved-for-next-local-planning-gate, changes-requested, and rejected decisions. Approval only becomes effective when the decision request is ready and unsafe flags remain disabled. Blocked requests only allow rejected or changes-requested outcomes.

This feature remains deterministic and local-only. It does not grant side-effectful approval, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.5.0 - Human Case Review Decision Gate

The human case review decision gate reviews an imported human case-review decision and determines whether the case can move to the next local planning gate.

It classifies imported decisions as blocked, changes-requested, rejected, or ready for the next local planning gate. Even when ready, this gate does not authorize validation, runtime execution, evidence collection, report submission, or vulnerability confirmation.

This feature remains deterministic and local-only. It does not grant runtime execution, call LLM providers, execute validation, collect evidence, execute tools, send requests, submit reports, or confirm vulnerabilities.

## v1.6.0 - Research Source Packet

The research source packet turns local, user-provided research sources into a deterministic planning packet.

It normalizes source metadata, identifies source gaps, derives likely attack surfaces, and produces research questions for later hypothesis planning. This is the first local research-brain layer.

This feature remains deterministic and local-only. It does not browse the web, call LLM providers, execute tools, send requests, collect evidence, submit reports, or confirm vulnerabilities.

## v1.7.0 - Research Hypothesis Packet

The research hypothesis packet turns a ready local research source packet into deterministic bug-hunting hypotheses.

It converts derived attack surfaces into structured hypotheses with hypothesis type, rationale, local review questions, evidence needed, allowed local checks, rejected actions, priority, confidence, and tags.

This feature remains deterministic and local-only. It does not browse the web, call LLM providers, generate commands, execute tools, send requests, collect evidence, validate findings, submit reports, or confirm vulnerabilities.

## v1.8.0 - Research Hypothesis Type Refinement

This release refines research hypothesis classification for authorization and administrative access-control surfaces.

Authorization-oriented surfaces such as `Authorization and administrative access control` now resolve to `authorization-admin-boundary` instead of being caught by the broader authentication/session classifier.

The authentication/session classifier now matches explicit authentication concepts such as authentication, OAuth, session, JWT, and token.

Safety defaults remain unchanged: local-only, deterministic, no web browsing, no network interaction, no command generation, no tool execution, no evidence collection, no validation, no report submission, and no vulnerability confirmation.

## v1.9.0 - Research Hypothesis Selection Packet

The research hypothesis selection packet ranks and selects the strongest local-only hypotheses for deeper investigation planning.

It turns a ready research hypothesis packet into selected hypotheses with selection rank, selection score, selection reason, primary hypothesis ID, evidence needed, allowed local checks, tags, and selection gaps.

This feature remains deterministic and local-only. It does not browse the web, call LLM providers, generate commands, execute tools, send requests, collect evidence, validate findings, submit reports, or confirm vulnerabilities.

## Research Action Decision Pipeline

Version 1.14.0 extends the reviewed research-planning chain:

```text
action proposal packet
→ action proposal review gate
→ human decision template
→ action decision packet
→ approved-action packet
→ typed tool-request manifest
→ fail-closed execution-gate compatibility preview
```

The decision packet validates reviewer identity, decision coverage, source consistency, planning-only state, and fail-closed safety fields.

The approved-action packet includes only effectively approved actions and normalizes tool families, adapter families, request kinds, risks, scope requirements, controlled assets, expected artifacts, and downstream blockers.

The typed tool-request manifest creates deterministic, non-executable adapter requests with allowed inputs, required outputs, prohibited operations, request identifiers, and SHA-256 digests.

Human approval permits only construction of the next planning artifact. It does not authorize command generation, package installation, tool execution, network interaction, evidence collection, vulnerability validation, state mutation, report submission, or vulnerability confirmation.

## Typed Tool Request Review Gate

Version 1.15.0 adds a fail-closed integrity and safety review between the typed tool-request manifest and any future exact-action runtime approval artifact.

```text
typed tool-request manifest
→ typed tool-request review gate
→ future exact-action runtime approval template
→ later runtime authorization and adapter review
```

The review gate validates:

- manifest kind, status, readiness, and request counts
- SHA-256 manifest and per-request digests
- deterministic request IDs, action IDs, and ordering
- action profiles, tool families, adapter families, request kinds, and risks
- adapter allowed inputs, required outputs, and prohibited operations
- scope, controlled-assets, focus-endpoint, observation, redaction, and runtime-gate requirements
- execution-gate input and preview consistency
- packet, request, and safety flags remain fail-closed

A successful review produces `ready-for-runtime-approval-template`. This status permits only creation of another local planning artifact.

It does not authorize command or payload generation, package installation, tool execution, network or target interaction, evidence collection, vulnerability validation, state mutation, report submission, or vulnerability confirmation.

## Research Observation Feedback Pipeline

Version 1.16.0 adds a deterministic, local-only observation feedback pipeline.

Pipeline:

- research observation packet
- observation review gate
- hypothesis feedback packet
- future human feedback decision
- future research-state transition gate

The observation packet normalizes imported observations, deterministic observation IDs, source linkage, evidence strength, scope status, controlled-assets status, redaction status, human-review state, preliminary confidence effects, and SHA-256 digests.

The observation review gate independently verifies packet integrity, observation integrity, source linkage, redaction, scope, controlled assets, human review, fail-closed safety fields, and aggregate hypothesis-impact calculations.

The hypothesis feedback packet joins verified observation impacts to the original hypothesis packet and creates proposal-only confidence feedback.

Version 1.16.0 does not modify hypothesis packets, hypothesis selection, investigation plans, approved actions, persistent research state, targets, reports, or vulnerability status.

Command generation, payload generation, package installation, tool execution, browser execution, Burp Suite execution, Kali execution, network interaction, evidence collection, vulnerability validation, report submission, and vulnerability confirmation remain disabled.

## v1.17.0 Human Hypothesis Feedback Decision Pipeline

Version 1.19.0 adds a local-only human decision boundary for proposed hypothesis feedback.

The pipeline adds:

- hypothesis feedback decision template
- hypothesis feedback decision packet
- accepted/rejected/changes-requested/deferred decision handling
- deterministic decision digests
- fail-closed safety fields for confidence, selection, plan, state, runtime, target, report, and vulnerability mutation

Accepted feedback decisions only mark a later confidence-update packet as ready. They do not directly change hypothesis confidence, hypothesis selection, investigation plans, approved actions, persistent research state, targets, reports, or vulnerability status.


## v1.18.0 Hypothesis Confidence Update Packet

The hypothesis confidence update packet converts accepted human feedback decision packets into proposed confidence update records. It remains local-only and fail-closed. It does not mutate the source hypothesis packet or persistent research state.

## v1.19.0 Research-State Transition Review Gate

The research-state transition review gate converts ready hypothesis confidence update packets into pending transition candidates. It requires a later explicit human transition decision before any state-transition packet can be created.

## v1.20.0 Human Research-State Transition Decision Packet

The transition decision template converts a ready research-state transition review gate into pending human decisions. The transition decision packet validates completed human decisions and marks approved candidates as ready for a later state-transition packet.

This stage is local-only and non-mutating. It does not update hypothesis confidence or persistent research state.

## v1.21.0 Local Research-State Transition Packet

The local research-state transition packet converts approved human transition decisions into local transition operations. These operations describe proposed hypothesis confidence changes but do not write persistent research state.

A later apply review gate is required before any persistence step can be considered.
