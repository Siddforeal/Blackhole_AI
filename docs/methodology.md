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
