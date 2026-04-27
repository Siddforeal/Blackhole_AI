# Threat Model

BugIntel AI Workbench is designed to reduce risk during AI-assisted security testing.

## Main Risks

- Testing outside authorized scope
- Accidentally storing secrets
- Executing unsafe commands
- Confusing false positives with real vulnerabilities
- Over-automation without human validation

## Mitigations

- Scope Guard blocks out-of-scope domains, schemes, methods, and forbidden paths.
- Secret Redactor removes common sensitive values from stored evidence.
- `run-curl` requires explicit `--yes` before execution.
- Evidence is stored as structured JSON for manual review.
- The tool is designed for human-in-the-loop operation.
