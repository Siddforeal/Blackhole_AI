# Methodology

BugIntel AI Workbench follows a human-in-the-loop methodology for authorized vulnerability research.

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

## Playwright Preview Workflow

The Playwright preview workflow is the first v0.4.0 step toward live browser execution:

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

Even if all current gates pass in tests, the skeleton returns `status: not_implemented` and does not produce network events, screenshots, or HTML snapshots. Real browser launch must be added deliberately behind this same gate.

When the skeleton reaches the handoff path, `execute-playwright-plan --json-output` writes a capture-result JSON compatible with the browser evidence pipeline. This is useful for validating the CLI and evidence handoff before live Playwright execution exists.

The full safe handoff chain is:

1. `execute-playwright-plan --json-output` creates a future capture-result JSON.
2. `save-browser-capture` stores that JSON as redacted browser evidence.
3. `generate-report` renders the browser evidence into Markdown.
4. The report includes Playwright execution-output fields such as runner, status, and reason.
5. The current skeleton still does not launch a browser.

## Playwright Execution Request Model

Before live browser execution is implemented, BugIntel builds a reviewable execution request.

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

This command intentionally requires the scope file again. Saved request JSON can be edited, so BugIntel re-validates the start URL before applying the execution safety gate.

Default behavior is refusal because `allow_live_execution` is false. Passing `--allow-live-execution` only reaches the current `not_implemented` handoff path; it still does not launch a browser.
