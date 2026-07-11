# Blackhole Demo Case Pack

- Demo ID: `BLACKHOLE-DEMO-CASE-PACK-v1.81.0`
- Product version: `1.84.1`
- Demo schema version: `1.81.0`
- Legacy version alias: `1.81.0`
- Status: `demo-case-pack-local-only`
- Case: Synthetic account export boundary review
- Target label: `local-demo-api`
- Endpoint: `/api/v1/accounts/{account_id}/exports?callback_url=https://researcher.invalid/sink`
- Actor context: low-privilege viewer account in a synthetic local demo

## Case Summary

A synthetic local-only case showing how Blackhole turns observations into matched patterns, knowledge records, hypotheses, next evidence requirements, and a report-readiness summary.

## Observations

- `endpoint` — Account identifier appears in export route
  - Synthetic demo endpoint contains an account identifier and an export operation that should be scoped to the active user or tenant.
- `evidence` — Response may contain a redacted signed export URL
  - Demo notes include a placeholder signed URL value only. No real secret, token, or live response is stored.
- `input` — Export flow accepts a callback URL parameter
  - Demo input models a callback URL field for planning only. No callback is sent and no outbound interaction is attempted.

## Matched Patterns

- `authorization` / `P2` / `0.86` — Authorization boundary weakness
  - Rationale: The demo case contains an account-scoped object identifier and an export/read operation that should require boundary comparison.
  - Required next evidence: authorized scope proof, boundary comparison
- `information-disclosure` / `P2` / `0.68` — Sensitive data exposure
  - Rationale: The demo case models a redacted signed export URL, so the next safe step is to prove whether sensitive values are disclosed to the wrong actor.
  - Required next evidence: redacted sample, access-path explanation
- `ssrf` / `P2` / `0.61` — Server-side request behavior
  - Rationale: The demo case includes a callback URL input, so the next safe step is to review whether any server-side request behavior is possible inside scope.
  - Required next evidence: safe external interaction proof, impact boundary

## Next Investigation Plan

1. Confirm the tested role, account, tenant, and exact allowed scope before any live testing.
2. Perform a controlled two-account comparison only in an authorized environment.
3. Keep any sensitive value samples redacted and store only local placeholder evidence.
4. Review callback URL handling without triggering live outbound requests unless scope and human approval explicitly allow it.
5. Do not mark the case report-ready until authorization, impact boundary, and safe evidence are reviewed.

## Report-Ready Summary

Not report-ready. The demo shows a plausible research path, but it intentionally does not confirm a vulnerability. A human researcher still needs authorized boundary comparison, redacted evidence, and impact review.

## Safety

- adapter_execution_state: `not_executed`
- execution_allowed: `false`
- network_requests_allowed: `false`
- evidence_collection_allowed: `false`
- target_mutation_allowed: `false`
- report_submission_allowed: `false`
- vulnerability_confirmation_allowed: `false`
