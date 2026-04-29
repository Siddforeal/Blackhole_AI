# Methodology

Blackhole AI Workbench follows a human-in-the-loop methodology for authorized vulnerability research.

## Workflow

1. Define target scope.
2. Mine endpoints from passive inputs such as JavaScript, HTML, HAR, logs, and Burp exports.
3. Build a task tree from discovered attack surfaces.
4. Plan safe commands through Scope Guard.
5. Execute only explicitly approved actions.
6. Parse HTTP responses.
7. Redact sensitive data.
8. Save structured evidence.
9. Compare responses for interesting security signals.
10. Generate research notes and report material.

## Browser Evidence Workflow

Browser automation should follow the same safety pattern as command execution:

1. Validate the browser start URL through Scope Guard.
2. Build a reviewable browser action plan.
3. Require human approval before execution.
4. Capture browser-observed network events.
5. Save screenshot metadata and artifact references.
6. Save redacted HTML snapshot previews and hashes.
7. Save execution output previews from future Playwright runs.
8. Normalize browser execution output into a Browser Capture Result.
9. Save browser capture output with `save-browser-capture`.
10. Store evidence as redacted JSON for later reporting and validation.

Browser evidence should avoid saving raw secrets, raw tokens, raw private HTML, or raw sensitive response bodies by default. Instead, it should preserve enough metadata, previews, and hashes to support reproducible analysis.

## Current MVP Capabilities

- Scope validation
- Endpoint mining
- Task-tree generation
- Safe curl planning
- Controlled curl execution
- HTTP response parsing
- Evidence storage
- Browser evidence storage
- Secret redaction
- Response-diff analysis

## Browser Evidence Command Workflow

The browser evidence workflow can be exercised with the safe example capture result:

    bugintel plan-browser examples/target.example.yaml https://demo.example.com/dashboard --browser chromium

    bugintel save-browser-capture examples/browser_capture_result.example.json

    bugintel generate-report data/evidence/demo-lab/<saved-browser-evidence>.json --output reports/browser-evidence-report.md

The example capture result represents the output shape expected from a future Playwright/browser execution adapter. It should be treated as a handoff file, not as proof that live browser automation has executed.

## Deterministic Research Planner

The research planner converts existing browser evidence into structured research hypotheses and recommendations:

    bugintel plan-research browser-evidence.json --json-output research-plan.json --markdown-output research-plan.md

The planner is intentionally offline and deterministic. It does not call an LLM, execute shell commands, launch a browser, or send network requests.

Current hypothesis categories include:

1. API authorization review.
2. Object-level authorization review.
3. Sensitive-surface review.
4. Error-handling review.
5. Browser artifact review.

Planner output should be treated as a manual review guide, not as a confirmed vulnerability. Each recommendation must still be validated using authorized test accounts, Scope Guard, and read-only checks before any report is prepared.

### Safe LLM Prompt Packaging

A deterministic research plan can be converted into a reviewable prompt package:

    bugintel build-llm-prompt research-plan.json --json-output llm-prompt.json --markdown-output llm-prompt.md

This packaging step is intentionally offline. It does not call OpenAI, Anthropic, local models, or any other LLM provider. It does not read API keys, send network requests, execute shell commands, or run browser actions.

The prompt package includes:

1. A system prompt with authorization and safety rules.
2. A user prompt containing the deterministic research plan.
3. Safety notes for human review.
4. Basic redaction for common sensitive patterns such as emails, JWTs, API-key-like values, passwords, and AWS access key IDs.

The package is a bridge for future optional provider integration. It should be reviewed before any model receives it.

### LLM Prompt Safety Audit

Prompt packages should be audited locally before any future provider receives them:

    bugintel audit-llm-prompt llm-prompt.json --json-output llm-prompt-audit.json --markdown-output llm-prompt-audit.md

The audit does not call an LLM provider, read API keys, send network requests, or execute commands. It inspects the prompt package text and produces a local safety report.

Audit statuses:

1. `pass`: no local findings detected.
2. `review`: medium-severity findings detected.
3. `blocked`: high-severity findings detected.

Current checks include sensitive values such as emails, JWT-like tokens, bearer tokens, API-key-like assignments, passwords, secrets, generic tokens, and AWS access key IDs. It also flags risky prompt instructions such as prompt-injection language, safety-bypass requests, credential theft instructions, and destructive-action instructions.

A clean audit is only a helper signal. It should not be treated as a formal data-loss guarantee.

### Disabled LLM Provider Stub

The disabled provider stub can consume a prompt package and return a structured disabled result:

    bugintel run-llm-provider llm-prompt.json --json-output llm-provider-result.json

This command is intentionally non-operational as a model runner. It does not call any provider, read API keys, send prompts over the network, or execute generated actions. It exists to validate result shape and future integration boundaries.

### UFO Startup Intro

The terminal intro can be shown with:

    bugintel intro

Running `bugintel` with no command shows the UFO startup screen. This is a human-facing UX layer only and should not be used as part of machine-readable workflows.

## Playwright Preview Workflow

The Playwright preview workflow is part of the v0.10.0 path toward live browser execution:

    bugintel preview-playwright examples/target.example.yaml https://demo.example.com/dashboard --browser chromium --json-output reports/playwright-preview.json

This command:

1. Loads the authorized target scope.
2. Builds a browser plan through Scope Guard.
3. Checks whether the optional Playwright Python package is importable.
4. Produces a safe execution preview JSON.
5. Does not launch a browser.
6. Does not install Playwright.
7. Does not download browser binaries.
8. Keeps live execution disabled by default.

## Playwright Execution Safety Gate

The safety-gated Playwright execution skeleton defines the future adapter boundary:

    execute_playwright_plan(plan, task_name, config)

The function currently does not launch a browser. It exists to enforce the required safety checks before live browser execution is implemented.

It blocks execution when:

1. The browser plan is out of scope or otherwise blocked.
2. `allow_live_execution` is false.
3. The optional Playwright package is missing.

When blocked, it raises `PlaywrightExecutionSafetyError`. Future live execution should be implemented behind this same gate, not beside it.

The CLI safety-gate command is:

    bugintel execute-playwright-plan examples/target.example.yaml https://demo.example.com/dashboard

Expected default behavior is refusal, because `allow_live_execution` is false unless explicitly requested.

Real adapter routing is also opt-in. The real Playwright adapter path requires both:

1. `--allow-live-execution`
2. `--use-real-adapter`

Without `--use-real-adapter`, the safety-gated execution path continues to use the adapter stub.

For local validation, prefer a temporary `127.0.0.1` HTTP server and a scope file that only allows that local host. A successful real-adapter smoke test should produce:

1. `status: completed`
2. At least one browser-observed network event.
3. One screenshot artifact.
4. One HTML snapshot artifact.
5. A capture-result JSON that can be passed into `save-browser-capture`.

When the handoff path writes a capture-result JSON, it remains compatible with the browser evidence pipeline.

The full safe handoff chain is:

1. `execute-playwright-plan --json-output` creates a future capture-result JSON.
2. `save-browser-capture` stores that JSON as redacted browser evidence.
3. `generate-report` renders the browser evidence into Markdown.
4. The report includes Playwright execution-output fields such as runner, status, and reason.
5. The current skeleton still does not launch a browser.

## Playwright Execution Request Model

Before live browser execution is implemented, Blackhole builds a reviewable execution request.

The request contains:

1. Target name.
2. Task name.
3. Start URL.
4. Browser label.
5. Execution config.
6. Planned browser actions.
7. Planned artifact paths for screenshot, HTML, network log, and trace output.

This request is the future adapter input. It is safe because building it does not create files, does not install Playwright, and does not launch a browser.

The CLI command is:

    bugintel build-playwright-request examples/target.example.yaml https://demo.example.com/dashboard --task-name "Capture Dashboard" --json-output reports/playwright-request.json

Use this command when you want to review the future browser job before attempting any execution workflow.

A safe example request lives at:

    examples/playwright_request.example.json

Treat this example as a request format reference, not as evidence of browser execution.

To preview a saved request:

    bugintel preview-playwright-request examples/playwright_request.example.json --json-output reports/playwright-request-preview.json

This command is useful when the request has already been created and you want to review the execution preview without reloading the original scope file.

To execute a saved request through the safety gate:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml

This command intentionally requires the scope file again. Saved request JSON can be edited, so Blackhole re-validates the start URL before applying the execution safety gate.

Default behavior is refusal because `allow_live_execution` is false. Passing only `--allow-live-execution` keeps the stub route by default.

To route a saved request through the real adapter, use:

    bugintel execute-playwright-request examples/playwright_request.example.json examples/target.example.yaml --allow-live-execution --use-real-adapter

## Browser Artifact Loading

The artifact-loading command converts existing planned artifact files into a browser capture result:

    bugintel load-browser-artifacts examples/playwright_request.example.json --json-output reports/browser-capture-result.json

It reads the artifact paths from the saved request JSON. Supported inputs are:

1. `network.json` for browser-observed network events.
2. `page.html` for the HTML snapshot.
3. `screenshot.png` for screenshot metadata and SHA-256 hashing.

The output is compatible with the browser evidence workflow:

    bugintel save-browser-capture reports/browser-capture-result.json

This command does not execute Playwright or launch a browser.

## Playwright Adapter Context

The adapter context is the internal package that will later be handed to the real Playwright engine.

It contains:

1. The Playwright execution request.
2. Planned artifact paths.
3. Whether the artifact directory was created.
4. Safety notes confirming no browser launch or capture happened.
5. A flag showing browser launch is not implemented yet.

Creating the context is safe. It does not launch a browser. Optional directory creation creates only the planned artifact folder, not screenshots, HTML, network logs, or traces.

## Playwright Adapter Stub Runner

The adapter stub runner is the placeholder for the future real Playwright engine.

Current behavior:

1. Accepts a Playwright adapter context.
2. Returns a browser capture result.
3. Sets execution status to `not_implemented`.
4. Preserves artifact path metadata.
5. Confirms no browser launch is implemented.
6. Produces no network events, screenshots, HTML snapshots, or traces.

This lets Blackhole test the future adapter-to-evidence handoff before real browser execution is added.

## Endpoint Investigation Profiles

Blackhole can turn one discovered endpoint into a planning-only investigation profile.

Example:

    blackhole endpoint-investigation "/api/accounts/123/users/{id}/permissions" --json-output /tmp/endpoint-profile.json

The profile is designed to help the future orchestrator and specialist agents decide what to inspect next.

The generated plan may include:

- method policy review
- parameter and schema review
- error and oracle review
- authorization boundary planning
- tenant isolation review
- object reference mutation planning
- identifier source mapping
- file surface safety review
- session/auth-flow review
- evidence and report checklist

The output is a reviewable plan only. It does not run curl, launch browsers, call LLM providers, make network requests, mutate targets, or bypass authorization.

