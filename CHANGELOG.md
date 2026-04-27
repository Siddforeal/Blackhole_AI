# Changelog

## Unreleased

### Added

- Evidence-to-Markdown report generator
- `generate-report` CLI command
- Analyst review checklist in generated reports
- Generated reports are ignored by Git to avoid accidental upload of private evidence

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
