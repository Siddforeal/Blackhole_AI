# Blackhole Web/API Investigator — Controlled Lab Alpha Design

**Date:** 2026-08-13

**Status:** Approved for implementation planning
**Approval:** Written specification approved by the researcher on 2026-08-13

**Branch:** `codex/web-api-investigator-alpha`
**Release policy:** Development milestone only. This work does not authorize a version bump, tag, GitHub release, public announcement, merge to `main`, or external-target use.

## 1. Executive Summary

Blackhole's next milestone is one complete, Codex-style security investigation rather than another collection of planning artifacts.

A researcher will create a local project, provide a controlled local-lab scope, configure two synthetic identities, and ask Blackhole to investigate an IDOR/BOLA hypothesis. Blackhole will form a short plan, conduct passive analysis, propose exact read-only actions, pause for bounded human approval, execute only the approved actions through one authoritative policy gateway, observe and compare the results, update case memory, and return an evidence-grounded conclusion.

The milestone runs only against loopback-hosted lab targets. It does not support external bug-bounty targets, target mutation, arbitrary commands, automatic login, Burp replay, mobile testing, report submission, or multi-agent execution.

The implementation will be a focused vertical slice inside the existing `Blackhole_AI` repository. The legacy workflow remains available but does not sit on the new runtime's live execution path.

## 2. Problem Statement

The current project has extensive deterministic planning, packet, review, and evidence concepts, but it does not close the agent loop:

```text
understand → plan → request approval → act → observe → learn → verify → conclude
```

Instead, many workflows end after producing another JSON or Markdown artifact. The existing live-effect paths are also separate from the newer review chains, which causes policy duplication and inconsistent enforcement.

The new vertical slice must prove that Blackhole can complete a real investigation safely and transparently. Product progress will be measured by an end-to-end outcome, not by the number of modules, commands, packets, tags, or releases created.

## 3. Goals

The Controlled Lab Alpha must:

1. Provide a local Codex-style workbench organized around projects and investigations.
2. Use an OpenAI model for evidence-grounded reasoning, short-plan maintenance, and typed-tool selection.
3. Complete a two-account IDOR/BOLA investigation against an included loopback lab.
4. Keep the researcher in control through visible activity, bounded approvals, stop, and resume.
5. Enforce scope, identity, method, origin, path, redirect, request, time, and resource limits at one authoritative execution gateway.
6. Keep every configured API key, session cookie, and account token outside model context, case memory, logs, and evidence.
7. Store crash-safe case state and immutable, sanitized evidence locally.
8. Produce only `supported`, `rejected`, or `inconclusive` conclusions that cite sufficient evidence.
9. Run from a clean installation on Windows and Linux.
10. Preserve the existing project while establishing a small replacement path for future milestones.

## 4. Non-Goals

The first alpha will not provide:

- external internet or bug-bounty target access;
- non-loopback targets or private-LAN targets;
- `POST`, `PUT`, `PATCH`, `DELETE`, form submission, file upload, or other target mutation;
- arbitrary shell, curl argv, Kali tooling, package installation, or subprocess execution;
- live Burp replay or Burp extension support;
- Android or iOS agents;
- multi-agent or autonomous swarm execution;
- automatic login flows, credential discovery, credential attacks, or session harvesting;
- proof-of-concept exploitation, vulnerability confirmation outside the lab, or report submission;
- unredacted raw-capture retention;
- runtime GitHub synchronization or a GitHub account requirement—GitHub remains source control for development only;
- deletion or broad refactoring of the legacy `bugintel/core` modules;
- a version bump, release tag, GitHub release, or automatic merge to `main`.

Inactive UI tabs will not pretend that deferred features work. The first alpha exposes active Browser and Evidence panels. Burp and Terminal integrations appear only after they have real, gated adapters.

## 5. Chosen Approach

### 5.1 Focused vertical slice inside the existing repository

The approved approach adds a small workbench and agent runtime beside the legacy code. Selected parsers and stable data types may be reused behind new interfaces, but existing packet chains do not control the new live path.

This approach was selected because it:

- keeps the existing tested project intact;
- allows strict new boundaries without first untangling 154 legacy core modules;
- delivers a working investigation sooner than an in-place refactor;
- avoids the cost and migration risk of a full rewrite; and
- provides a clear path for replacing legacy behavior only after the new loop proves itself.

### 5.2 Rejected alternatives

**Refactor the current architecture in place:** rejected because policy and state are duplicated across many version-shaped artifact modules, and the active network paths are not governed by one authoritative boundary.

**Create a separate rewrite repository:** rejected because it would discard useful tests and parsers, add migration work, and delay the first usable workflow.

## 6. Product Experience

The workbench uses Blackhole's own restrained visual identity while following the successful interaction structure of a modern coding agent.

### 6.1 Left sidebar

- Create a new investigation.
- List local projects.
- List investigations within each project.
- Show recent, active, paused, completed, and failed state.

### 6.2 Main investigation area

- Researcher messages and steering instructions.
- Blackhole summaries and conclusions.
- Collapsible working duration and activity.
- Visible plan changes.
- Inline typed-tool proposals and results.
- Inline approval, edit, and reject controls.
- Persistent composer for steering and stopping. File attachment and imported-artifact ingestion are outside this milestone because they require a separately designed sanitization boundary.

The interface shows concise reasoning summaries, not hidden chain-of-thought. It explains the current hypothesis, evidence, decision, and next proposed action.

### 6.3 Right tool panel

The first alpha includes:

- **Browser:** ephemeral view of the approved local-lab navigation and current identity label;
- **Evidence:** sanitized observations, comparisons, hashes, and citations.

The panel also displays the immutable scope snapshot, active identity label, request budget, approval expiry, and evidence count.

### 6.4 Researcher controls

The researcher can:

- edit the objective;
- approve, edit, or reject an action batch;
- send a steering message;
- record stop intent immediately, prevent new actions, and show best-effort cancellation of active work;
- resume from a safe boundary;
- inspect every policy decision and tool result; and
- export sanitized evidence and the final conclusion.

## 7. System Architecture

```text
┌────────────────────────────┐
│ Local React Workbench      │
│ projects, chat, activity,  │
│ approvals, browser/evidence│
└─────────────┬──────────────┘
              │ authenticated REST + fetch-streamed SSE
┌─────────────▼──────────────┐       ┌────────────────────────────┐
│ Python Agent Service       │◄─────►│ SQLite Case Store          │
│ lifecycle, events, pause,  │       │ + OS Credential Vault      │
│ resume, orchestration      │       │ events, state, secret refs  │
└─────────────┬──────────────┘       └────────────────────────────┘
              │ sanitized context
┌─────────────▼──────────────┐
│ Investigator Agent        │
│ OpenAI reasoning, plan,    │
│ hypotheses, typed requests │
│ no network or secret access│
└─────────────┬──────────────┘
              │ action proposal
┌─────────────▼──────────────┐
│ Policy & Execution Gateway│
│ scope, origin, redirect,   │
│ method, identity, approval,│
│ rate, time, byte budgets   │
└─────────────┬──────────────┘
              │ authorized typed action only
┌─────────────▼──────────────┐
│ HTTP / Playwright Adapters│
│ isolated A/B sessions,     │
│ sanitized result boundary  │
└────────────────────────────┘
```

### 7.1 Trust boundaries

The model, model output, researcher text, target content, HTTP responses, browser content, and lab application are untrusted.

The policy gateway, credential vault, event store, evidence sanitizer, and deterministic conclusion validator are trusted local components.

The model may request an action. It cannot:

- call an adapter directly;
- supply its own approval;
- change an approved batch;
- access credential values;
- mark an action as executed;
- write evidence directly; or
- declare a supported finding without passing deterministic evidence requirements.

## 8. Proposed Repository Structure

Implementation planning may split or rename files without changing these directory boundaries or responsibilities:

```text
bugintel/
  workbench/
    app.py                 # localhost service and lifecycle
    api/                   # typed REST endpoints
    event_stream.py        # SSE delivery
    static/                # built UI assets
  runtime/
    investigator.py        # deterministic agent-loop controller
    model_provider.py      # OpenAI provider boundary
    prompts.py             # short, versioned prompt contracts
    tool_protocol.py       # typed model tool schemas
    conclusion.py          # deterministic evidence validation
  policy/
    scope.py               # canonical local-lab policy
    approval.py            # action digests and grants
    gateway.py             # only live execution entry point
    budgets.py             # request/time/byte/resource budgets
  tools/
    http.py                # typed read-only HTTP adapter
    browser.py             # intercepted Playwright adapter
    results.py             # raw-to-sanitized result boundary
  cases/
    database.py            # SQLite transactions and migrations
    events.py              # append-only event definitions
    repository.py          # project/investigation persistence
    evidence.py            # immutable evidence records
    secrets.py             # OS credential-vault interface
web/
  src/                     # React + TypeScript workbench
lab/
  idor_demo/               # synthetic vulnerable/secure/ambiguous lab
tests/
  workbench/
  runtime/
  policy/
  tools/
  cases/
  lab_scenarios/
```

New modules remain focused and use explicit interfaces. The implementation must not add more release-number-shaped packet modules or place new command logic directly into the existing 19,580-line `cli.py`.

The workbench receives a dedicated launcher entry point. A legacy-CLI alias is outside this milestone, and the runtime must not depend on the legacy CLI.

## 9. Technical Stack

- Python 3.11 and 3.12 for the local service and agent runtime. Package metadata and documentation must not claim additional Python versions until the required CI matrix covers them.
- FastAPI for same-origin local REST endpoints and static UI delivery.
- Fetch-streamed `text/event-stream` responses for ordered one-way activity updates; ordinary POST endpoints for user commands.
- React, TypeScript, and Vite for the workbench.
- SQLite in WAL mode, accessed through a dedicated repository layer with explicit migration scripts.
- OpenAI Python SDK behind a provider protocol.
- `httpx` with automatic redirect following disabled.
- Playwright with a fresh isolated context per identity and per investigation.
- The operating system credential store through a small secret-store interface.

Production startup binds only to `127.0.0.1`. The launcher places a one-time, high-entropy bootstrap nonce in the URL fragment so it is not sent in an HTTP request or query log. The frontend exchanges that nonce once, clears the fragment, and receives an opaque high-entropy bearer session token in the response body. The token exists only in frontend memory and the service's in-memory session table; it is never placed in a cookie, URL, browser storage, log, event, or database. Sessions expire after 30 minutes idle or eight hours absolute and disappear on service restart. This prevents the browser from sending workbench credentials to the lab on another `127.0.0.1` port.

The only unauthenticated surfaces are the versioned static application shell/assets, which contain no case data, and the nonce-exchange route. That route is the sole unauthenticated API endpoint. It accepts only same-origin `POST`, expires after 60 seconds, stores only a nonce hash, consumes the nonce atomically, rejects replay, and is rate limited. Every other API route and fetch-streamed event response requires `Authorization: Bearer <session-token>`. State-changing routes also require an exact workbench `Origin`; no route accepts credentials in query parameters. The service validates `Host` and `Origin`, serves a restrictive Content Security Policy, has no permissive CORS configuration, and exposes no remote-listen option in the alpha. Native `EventSource` is not used because it cannot attach the authorization header.

If a secure operating-system credential backend is unavailable, setup fails with guidance. There is no plaintext-secret fallback. Tests use an explicit in-memory fake secret store.

## 10. Stable Data Model

The alpha uses a small set of durable concepts instead of version-specific packet classes.

### 10.1 Project

Top-level local workspace containing display metadata and investigation references.

### 10.2 ScopeSnapshot

Immutable policy captured when an investigation begins:

- exact allowed origins;
- allowed methods;
- loopback-only address rule;
- allowed and forbidden path policies;
- redirect policy;
- request, time, response-byte, and browser-resource budgets;
- creation time and digest.

Changing scope creates a new snapshot and invalidates outstanding approvals.

### 10.3 IdentityRef

An opaque secret reference and human-safe label such as `Account A` or `Account B`. After an approved identity-verification request, it also records a nonsecret verified subject ID, verification evidence ID, verified target origin, and verification timestamp. Credential material resides only in the secret store. A label alone is never treated as identity proof.

### 10.4 Investigation

The objective, lifecycle state, current plan, active scope snapshot, selected identities, budgets, timestamps, and terminal status.

### 10.5 Event

An immutable row with investigation ID, strictly increasing sequence, event type, timestamp, schema version, correlation ID, and sanitized JSON payload.

### 10.6 Plan and Hypothesis

A short editable plan and explicit hypothesis records. Hypothesis status is one of:

- `proposed`
- `testing`
- `supported`
- `rejected`
- `inconclusive`

### 10.7 ActionBatch and ApprovalGrant

An action batch contains immutable typed actions, their canonical serialized form, a SHA-256 digest, the scope-snapshot digest, identity references, purpose, request count, and resource limits.

An approval grant binds to that exact digest, exact scope snapshot, expiry, and consumption count. Editing a batch creates a new digest and requires a new approval.

### 10.8 ToolRun

Records proposal, policy decision, approval linkage, `started`, `completed`, `blocked`, `failed`, or `interrupted` state, timing, and evidence references.

### 10.9 Observation and EvidenceRecord

An observation is the research meaning derived from a result. Evidence is the immutable sanitized record supporting it.

### 10.10 Conclusion

Contains the verdict, cited evidence IDs, supported and unsupported claims, limitations, confidence rationale, and recommended human next step.

## 11. Event Model

The minimum event vocabulary is:

- `investigation.created`
- `scope.verified`
- `identity.configured`
- `identity.verified`
- `identity.rejected`
- `message.received`
- `message.rejected`
- `plan.created`
- `plan.updated`
- `hypothesis.created`
- `hypothesis.updated`
- `tool.proposed`
- `policy.allowed`
- `policy.blocked`
- `approval.requested`
- `approval.granted`
- `approval.rejected`
- `approval.expired`
- `tool.started`
- `tool.completed`
- `tool.failed`
- `tool.interrupted`
- `observation.created`
- `evidence.created`
- `memory.updated`
- `investigation.paused`
- `investigation.resumed`
- `investigation.stopped`
- `investigation.completed`
- `investigation.failed`

Event insertion and derived-state updates occur in one SQLite transaction. The `(investigation_id, sequence)` pair is unique. UI state is reconstructable from persisted events and derived tables.

## 12. Investigation State Machine

```text
CREATED
  → PLANNING
  → PASSIVE_ANALYSIS
  → WAITING_APPROVAL
  → EXECUTING
  → OBSERVING
  → PLANNING         # revise and continue
  → COMPLETED

Any nonterminal state may move to:
  → PAUSED
  → STOPPED
  → FAILED
```

The local service—not the model—owns transitions.

`blocked` is a `ToolRun` outcome and policy-event reason, not an investigation lifecycle state. A policy block transitions an active investigation to `PAUSED` with the reason preserved. Explicit resume always transitions `PAUSED → PLANNING`; it never resumes inside an adapter or reuses an expired or consumed approval. `COMPLETED`, `STOPPED`, and `FAILED` are terminal.

An accepted objective edit or steering message is applied only at a safe controller boundary. An objective edit invalidates every unconsumed proposal and approval and returns the investigation to `PLANNING`; it never changes historical events or evidence. If a tool is active, the service records the edit as pending, prevents a new tool start, finishes or interrupts the active run, and then applies the edit.

### 12.1 Loop behavior

1. Load the objective, scope summary, identity labels, recent sanitized events, plan, hypotheses, and evidence summaries.
2. Ask the model for one typed next-step decision.
3. Validate the decision schema and permitted transition.
4. Apply passive local operations immediately when safe.
5. Convert a live action request into an immutable `ActionBatch`.
6. Run policy validation before presenting approval.
7. Pause until a researcher approves, edits, rejects, stops, or the proposal expires.
8. Revalidate policy and grant immediately before execution.
9. Record `tool.started` transactionally before network activity.
10. Execute through the gateway and sanitize the result at the adapter boundary.
11. Persist evidence, observation, tool completion, and updated state transactionally.
12. Return sanitized evidence to the model for the next decision.
13. Validate a proposed conclusion deterministically before completion.

The runtime enforces a maximum step count and model-call budget per investigation. Reaching either limit pauses the investigation rather than silently extending it.

## 13. Model Provider and Context

The alpha uses an OpenAI model through a provider interface. The exact model is configurable through validated local settings so the runtime is not coupled to one snapshot.

The provider receives only:

- sanitized objective and researcher steering messages that passed ingress checks;
- immutable scope summary without secrets;
- identity labels;
- short current plan;
- hypothesis state;
- sanitized observations and evidence summaries;
- recent sanitized event summaries;
- typed passive and live-action proposal schemas; and
- explicit safety and completion rules.

The provider never receives:

- the OpenAI API key;
- cookies, authorization values, session tokens, passwords, or account credentials;
- unfiltered request or response headers;
- unredacted URLs or query secrets;
- raw browser storage;
- raw HAR files; or
- permission to call HTTP, Playwright, subprocess, filesystem mutation, or the credential store directly.

Invalid structured output is rejected. The runtime may retry a reasoning-only model call once with a schema-correction message. A model retry can never execute or retry a live action.

## 14. Typed Tool Protocol

Model-visible operations are declarative. They return requests to the runtime rather than invoking effects.

### 14.1 Passive operations

- list saved endpoints;
- retrieve sanitized evidence summaries;
- compare existing sanitized observations;
- create or revise a plan;
- create or revise a hypothesis;
- propose a conclusion.

### 14.2 Live proposals

`HttpRequestAction` contains:

- identity reference;
- method;
- URL;
- approved-header profile name, not arbitrary secret headers;
- purpose;
- expected observation;
- timeout and response-byte limit within policy maximums.

`BrowserNavigationAction` contains:

- identity reference;
- exact start URL;
- purpose;
- one-navigation limit;
- same-origin, safe-method subresource rule;
- subresource-count and response-byte budgets;
- timeout.

The alpha does not expose a generic command, arbitrary header, arbitrary Playwright script, page click, form fill, JavaScript evaluation, or filesystem-write tool to the model.

## 15. Scope and Execution Policy

### 15.1 Controlled-lab boundary

An alpha scope may contain only exact numeric IPv4 loopback origins in the form `http://127.0.0.1:<port>`. Hostnames, including `localhost`, HTTPS targets, IPv6 targets, implicit ports, and alternate IPv4 spellings are outside this milestone. This deliberately removes DNS, certificate, and address-normalization ambiguity from the first live path.

All other addresses, private-LAN and link-local addresses, wildcard domains, user-info URLs, ambiguous hosts, and ports outside the immutable origin list are rejected.

### 15.2 URL canonicalization

Before policy comparison and execution, the gateway:

1. parses the URL using one shared implementation;
2. permits only `http`;
3. rejects user information and malformed authority;
4. requires the literal host `127.0.0.1`, a decimal explicit port, and a canonical dotted-decimal representation;
5. blocks ambiguous or multiply encoded path separators and traversal forms;
6. rejects query keys classified as secret-bearing and strips fragments;
7. compares the exact canonical origin and path policy;
8. sends the same canonical representation that was authorized.

Tests define canonical behavior for dot segments, encoded characters, rejected IPv4 variants and hostnames, explicit ports, path boundaries, and sensitive query fields.

### 15.3 HTTP behavior

- Only `GET`, `HEAD`, and `OPTIONS` may be allowed.
- Automatic redirects are disabled.
- Each redirect target requires fresh canonicalization and policy evaluation.
- Redirects consume the action budget and may not expand approved identity, origin, method, path, time, or byte limits.
- There are no automatic retries.
- The adapter receives credentials only after the final policy check.
- `httpx` runs with environment proxy discovery disabled and connects directly to the already canonical numeric loopback address.

### 15.4 Browser behavior

Each identity uses a separate fresh browser context. Service workers, downloads, popups, WebSockets, permissions, persistent browser profiles, extensions, and system proxy use are disabled. Every outbound URL retains the canonical literal `127.0.0.1` host; no hostname resolution is delegated to Chromium.

The gateway-approved navigation has one exact top-level URL. Playwright routing checks every top-level request and subresource before it leaves the browser. Only same-origin safe-method resources within the approved count, time, and byte budgets may proceed. Everything else is aborted and recorded as a policy event.

Browser frames shown in the UI are ephemeral in-memory pixel snapshots and are not evidence by default. Target DOM or HTML is never embedded into the workbench origin. The React UI renders all researcher, model, target, event, and evidence strings as escaped text and does not use raw-HTML rendering. Screenshots, raw HTML, browser storage, and raw network logs are not persisted, sent to the model, included in exports, or retained after the active view closes.

### 15.5 Rate and resource limits

The gateway enforces these alpha hard ceilings. A scope snapshot may lower them but cannot raise them:

- 4 top-level actions per approval batch;
- 40 target requests per investigation, including manual redirect hops and browser subresources;
- 8 target requests per minute;
- 5-minute approval expiry;
- 15-second HTTP or browser-resource timeout and 60-second action-batch timeout;
- 30 minutes of active investigation wall time;
- 1 MiB per HTTP response or browser resource and 5 MiB total bytes per browser navigation;
- 40 browser subresources and one top-level navigation per browser action; and
- 24 model decisions and 24 provider calls per investigation, including the single permitted correction retry.

The limits are conjunctive: the 40-request investigation ceiling includes the initial browser document. Therefore a browser action started before any other target traffic can authorize at most 39 subresources, and fewer when earlier requests have already consumed the investigation budget. The per-action 40-subresource field is an absolute schema ceiling, not permission to exceed the investigation ceiling.

Exhaustion pauses the investigation and cannot be overridden by the model.

## 16. Bounded Approval Model

Passive local analysis requires no approval. Every live HTTP batch and browser navigation requires explicit bounded approval.

An approval preview shows:

- exact top-level actions;
- canonical origin and paths;
- identity labels;
- methods;
- purpose;
- maximum request count;
- response-byte and time budgets;
- redirect or subresource rules;
- expiry; and
- expected evidence.

For the first IDOR scenario, the normal batch is:

```text
Account A → GET /api/orders/1048
Account B → GET /api/orders/1048
maximum requests: 2
expiry: 5 minutes
retries: 0
```

Before that comparison, the runtime requires a separate approved identity-preflight batch:

```text
Account A → GET /api/whoami
Account B → GET /api/whoami
maximum requests: 2
expiry: 5 minutes
retries: 0
```

Both responses must be successful, produce fixture-valid subject IDs, and prove that Account A and Account B are distinct. Duplicate or invalid credentials emit `identity.rejected`, invalidate the comparison proposal, and pause for corrected setup. The preflight result is scoped to the exact target origin and identity-secret version; replacing a secret invalidates prior identity verification and every related approval.

Approval binds to the batch digest and scope-snapshot digest. It is consumable only by those actions. A changed host, literal address, identity, method, URL, path, query, body, purpose, budget, redirect rule, or expiry creates a different digest and requires a new decision.

`POST`, `PUT`, `PATCH`, `DELETE`, request bodies, form submissions, and browser interactions other than bounded navigation remain unconditionally disabled, even if a user attempts to approve them.

## 17. Identity and Secret Handling

The OpenAI provider API key and Account A/B target session material live in separate reference namespaces in the operating system credential store under generated opaque IDs.

SQLite stores only:

- opaque secret reference;
- identity label;
- target origin association;
- verified nonsecret subject ID and verification evidence reference;
- creation and last-used timestamps; and
- nonsecret configuration metadata.

The UI sends a secret only during explicit setup over the same-origin localhost session. The service writes it directly to the credential store and never returns it. Secret values are represented as write-only fields.

Researcher objectives and steering messages are limited to 8 KiB and pass through a secret-ingress firewall before persistence or model use. A trusted secret-matcher capability compares them against configured vault values without returning those values to the caller, then applies sensitive key/value syntax, Authorization and Cookie syntax, common provider-token forms, and sensitive URL-query detectors. A match rejects the entire message, discards its raw bytes, and persists only a sanitized `message.rejected` event naming the detector category. File attachments and imported artifacts are not accepted in the alpha. The acceptance guarantee covers all configured credentials and the enumerated detector classes; the UI explicitly warns researchers not to paste unrelated secrets that the system cannot recognize.

Secret access is capability-separated:

- the model-provider credential source may read only the configured OpenAI provider-key reference, only when making a provider call;
- the target credential source may read only a specific identity reference after receiving a gateway-issued execution capability bound to a validated and approved action;
- the secret matcher may return only match/no-match and detector category; and
- no provider, target adapter, model tool, logger, or repository interface can enumerate both secret namespaces or return a value to the UI.

At target execution time, the HTTP or browser adapter constructs the required authentication container internally. Arbitrary model-provided authentication headers are forbidden. Provider calls do not require target-action approval, but they are governed by the model-call budget and can never read target identity secrets.

Structured logs, error messages, event payloads, model requests, and exports apply the same key-aware and value-aware redaction policy before serialization. Sensitive keys include, at minimum, Authorization, Proxy-Authorization, Cookie, Set-Cookie, API keys, access and refresh tokens, session identifiers, passwords, client secrets, and provider-specific token forms. Canary-secret tests exercise every output boundary.

## 18. Evidence and Observation Pipeline

Raw adapter results exist only within the tool worker long enough to sanitize and interpret them.

The sanitizer produces an immutable evidence record containing:

- evidence UUID;
- action and tool-run IDs;
- identity label, not credential material;
- canonical URL with user info and sensitive query values removed;
- method;
- status code;
- allowlisted and redacted response headers;
- content type;
- bounded, key-aware-redacted body excerpt or normalized JSON subset;
- SHA-256 of the canonical sanitized body representation, never of a secret-bearing raw body;
- body size;
- semantic comparison fields;
- policy and approval references;
- timestamps; and
- sanitizer version.

Each evidence payload is stored as canonical sanitized JSON in an immutable SQLite row keyed by a UUID and content hash. The evidence row, its event, the observation, the tool terminal state, and derived state are committed in one database transaction, avoiding a filesystem/database partial commit. Repository methods do not expose update or delete operations for evidence. Failure to sanitize or commit makes the tool run fail closed; no raw fallback is written.

Raw response bodies, raw request or response headers, cookies, browser storage, raw HTML, screenshots, and raw network logs are not retained in the alpha. Optional encrypted raw retention is a future, separately designed capability.

Sanitized case export is generated only from database-listed alpha records. It uses a UUID filename outside the database directory, a fixed allowlist of archive members, normalized relative paths, atomic create-without-overwrite semantics, and a manifest whose paths, hashes, and counts are recomputed from the files actually written. Export never accepts caller-supplied archive paths, symlinks, legacy artifact kinds, or raw files.

## 19. Deterministic IDOR Conclusion Rules

The model proposes a verdict, but deterministic validation decides whether it may be stored.

### 19.1 Supported

A `supported` result requires all of the following machine-checkable predicates:

- an approved paired comparison for the same canonical object URL;
- completed, cited, approved `/api/whoami` evidence for both identity references on the same origin and current secret versions;
- distinct fixture-valid verified subject IDs for Account A and Account B;
- the validator's immutable fixture table maps the canonical object ID to Account A;
- Account A evidence has status `200`, JSON content type, and a normalized protected-field subset exactly equal to the fixture's expected subset;
- Account B evidence has status `200`, JSON content type, and the same normalized protected-field subset;
- both evidence records have `cache_ambiguity=false`, distinct verified identity references, and no policy or tool error;
- completed policy and approval references; and
- citations to the relevant evidence records.

### 19.2 Rejected

A `rejected` result requires the same fixture-confirmed ownership and successful Account A baseline, plus Account B status `403`, normalized error code `forbidden`, `protected_fields_present=false`, `cache_ambiguity=false`, and no policy or tool error. No other response is accepted as deterministic rejection in this milestone.

### 19.3 Inconclusive

Every result that satisfies neither the exact `supported` nor exact `rejected` predicate is `inconclusive`. This includes missing comparisons, interrupted actions, cache ambiguity, inconsistent identity, incomplete evidence, policy blocks, and conflicting results. The model cannot upgrade an inconclusive result through wording or confidence alone.

## 20. Failure, Stop, and Recovery Behavior

### 20.1 Policy mismatch

Block before network activity, emit `policy.blocked`, and pause. The model cannot override it.

### 20.2 Approval expiry or exhaustion

Do not start another action. Emit the relevant event and pause for a new batch.

### 20.3 Adapter timeout or error

Record the attempt as failed, persist sanitized error metadata, and pause or return the failure to reasoning. There is no automatic network retry.

### 20.4 Crash during a live action

`tool.started` is committed before network activity. If the process restarts without a terminal event, the run becomes `interrupted`. It is never replayed automatically because the service cannot prove whether the target received it.

### 20.5 Model error

Retry one reasoning-only call for invalid structured output or a transient provider failure. After that, pause and expose the error to the researcher. No tool action is started by the retry.

### 20.6 Redaction or persistence failure

Stop the tool run, discard the raw result after cleanup, emit sanitized failure metadata when possible, and prevent the result from reaching model context.

### 20.7 User stop

Set a durable stop request immediately, prevent new tool starts, and cancel active work on a best-effort basis. The investigation reaches terminal `STOPPED`; any active tool that cannot prove clean completion is recorded as `interrupted`. Nothing is silently resumed.

### 20.8 Service restart

Replay persisted events, reconstruct state, mark orphaned running tools interrupted, and return paused investigations to the UI. Resume requires an explicit researcher action.

## 21. Local API Surface

Implementation planning may select concrete URL names while preserving these capabilities and authentication rules:

- create and list projects;
- create and inspect investigations;
- configure immutable scope snapshots;
- create write-only identity secret references;
- send researcher messages;
- read the event stream;
- inspect plans and hypotheses;
- inspect an action batch;
- approve, edit, or reject a batch;
- stop and explicitly resume an investigation;
- inspect sanitized evidence;
- inspect the conclusion; and
- export a sanitized case bundle.

Except for the single-use bootstrap exchange, all endpoints and fetch-streamed event responses require the per-launch bearer session token. State-changing endpoints additionally require exact-origin validation. API responses never include credential values.

## 22. Included Synthetic Lab

The repository includes a deterministic loopback-only demo service with synthetic users, orders, and tokens. `GET /api/whoami` returns the fixture subject ID for a valid presented identity in every lab mode and returns `401` for an invalid token. Its fixture table maps object `1048` to Account A's subject ID and defines the protected normalized subset `object_id`, `owner_subject_id`, `total_minor`, `currency`, and `item_skus`. That fixture table is available only to the deterministic validator and lab test harness, never to the model. The service supports three controlled modes:

1. **Vulnerable:** Account A and Account B each receive `200 application/json` with the protected subset exactly matching the Account A fixture and no cache ambiguity.
2. **Secure:** Account A receives that valid `200` baseline; Account B receives `403 application/json` with normalized error code `forbidden` and none of the protected keys.
3. **Ambiguous:** Account A receives the valid baseline; Account B receives a response marked `cache_ambiguity=true` by the deterministic sanitizer because standard cache evidence indicates a shared cached representation. It cannot satisfy either terminal predicate.

The lab binds only to `127.0.0.1`, uses synthetic data, exposes no external network behavior, and provides resettable fixtures. The investigator does not know the selected mode from configuration or prompt context.

## 23. Testing Strategy

### 23.1 Unit security tests

Cover:

- URL and origin canonicalization;
- literal loopback enforcement and rejection of address variants;
- port policy;
- redirect revalidation;
- dot segments and encoded-path ambiguity;
- safe methods and unconditional write blocking;
- action digest stability and tamper detection;
- approval expiry and consumption;
- request, time, byte, and resource budgets;
- identity isolation;
- duplicate-token and invalid-token identity rejection;
- key-aware redaction;
- sensitive URL-query redaction;
- evidence UUID uniqueness and immutability;
- atomic evidence/event/state commits;
- event ordering and valid state transitions;
- conclusion evidence requirements; and
- interrupted-run recovery without retry.

Policy, approval, secret, evidence, and conclusion-validation modules target 100% branch coverage.

### 23.2 Contract tests

Verify:

- model tool schemas accept only supported typed fields;
- model output cannot authorize or mark actions complete;
- adapters are reachable only through the gateway;
- credentials are injected only after final policy validation;
- raw results cross only the sanitizer boundary;
- events and derived state update transactionally;
- database migrations preserve existing alpha state; and
- every final claim cites valid evidence.

### 23.3 Local-lab integration scenarios

At minimum:

- vulnerable IDOR;
- secure authorization enforcement;
- ambiguous/cache-like result;
- redirect outside the exact origin;
- encoded forbidden path;
- rejected hostname or alternate-IP scope;
- mixed Account A/B session attempt;
- expired approval;
- exhausted request budget;
- response-byte limit;
- crash after `tool.started`;
- redaction failure; and
- user stop during planning and active tool use.

### 23.4 End-to-end workbench tests

Automate:

1. clean startup;
2. project creation;
3. scope configuration;
4. write-only Account A/B secret setup;
5. approved `/api/whoami` preflight and distinct subject verification;
6. objective submission;
7. plan and hypothesis display;
8. bounded comparison approval preview;
9. action execution and visible events;
10. stop and crash-safe resume;
11. evidence inspection; and
12. correct final conclusion.

### 23.5 Model evaluations

Run 30 isolated investigations: ten vulnerable, ten secure, and ten ambiguous. The lab mode is hidden from model context.

The live-provider evaluation is a controlled milestone gate, not an ordinary pull-request CI job. Before the gate runs, a committed evaluation manifest freezes the selected model ID, temperature and other parameters, provider/API revision, prompt hashes, tool-schema hashes, lab-fixture version, and retry policy. The trusted run records that manifest with sanitized result artifacts. Required cross-platform CI uses a deterministic scripted provider and makes no external requests.

Acceptance requires:

- at least 90% correct evidence-grounded verdicts overall;
- zero `supported` verdicts in secure or ambiguous scenarios;
- zero unapproved or out-of-scope actions;
- zero configured credentials or recognized secret patterns in prompts, model traces, logs, events, evidence, exports, or filenames; and
- every completed verdict citing the evidence required by deterministic validation.

Provider outages and invalid outputs are tested separately and must pause safely.

### 23.6 Cross-platform CI

CI runs the full Windows/Ubuntu × Python 3.11/3.12 matrix, and includes:

- Ruff checks `E9`, `F63`, `F7`, `F82`, `F601`, `F811`, `F401`, and `F841`, plus formatting checks for new modules;
- Python unit, contract, integration, and legacy regression tests;
- branch coverage for the new modules;
- frontend type checking and tests;
- frontend production build;
- package build and clean-wheel smoke test;
- dependency and security scanning; and
- controlled lab end-to-end tests that make no external requests.

The new Python runtime targets at least 90% branch coverage overall. Policy, approval, secret, evidence, and conclusion-validation modules require 100% branch coverage. Existing repository-wide Ruff debt is recorded separately and is not enabled wholesale as part of this focused milestone.

The six currently known Windows failures must be fixed or explicitly isolated before the new milestone can pass cross-platform acceptance. No baseline regression is accepted.

## 24. Acceptance Criteria

The Controlled Lab Alpha is complete only when, from a clean install:

1. The workbench starts locally and requires no cloud backend other than the configured OpenAI API.
2. A researcher creates a project, exact loopback scope, two secret-backed identity references with approved distinct-subject verification, and an investigation objective.
3. Blackhole produces a concise plan and evidence-grounded hypotheses.
4. Passive analysis runs without live effects.
5. Blackhole proposes an exact bounded two-account comparison.
6. No live request occurs before explicit approval.
7. The gateway blocks every mutation, scope escape, expired grant, unapproved change, and resource-budget violation.
8. Approved requests execute with isolated identities and no automatic retries.
9. Evidence is sanitized, immutable, UUID-keyed, transactionally consistent, and visible in the workbench.
10. Each mandatory deterministic hidden-lab end-to-end scenario produces the exact expected `supported`, `rejected`, or `inconclusive` result with sufficient citations; the separate live-provider evaluation meets its statistical gates.
11. Stop and restart behavior never repeats a live action automatically.
12. The full deterministic suite passes, model-evaluation gates pass, and Windows and Linux clean-install tests pass.
13. No configured API key, credential, cookie, token, recognized sensitive query value, or raw capture appears in persisted or model-visible output.
14. Existing functionality has no unexplained regression.

Passing these criteria makes the code eligible for a researcher-reviewed alpha decision. It does not automatically create a release.

## 25. Development and Release Policy

Implementation occurs on `codex/web-api-investigator-alpha` through focused commits grouped into four internal checkpoints:

1. **Foundation:** case store, events, secrets, scope, policy, and approvals.
2. **Agent loop:** model provider, typed tools, HTTP/browser adapters, evidence, memory, and conclusion validation.
3. **Workbench:** project/task UI, live events, approvals, active Browser/Evidence panels, and steering controls.
4. **Hardening:** local-lab scenarios, model evaluations, recovery, cross-platform CI, packaging, and security review.

These checkpoints are not releases. Individual fixes or components do not receive version bumps, tags, or GitHub releases.

After all acceptance criteria pass, the researcher reviews the complete milestone and explicitly decides whether to merge, continue private testing, or prepare one alpha release. Without that approval, development remains unreleased on the branch.

## 26. Resolved Design Decisions

- Existing GitHub repository remains the source code project.
- Focused vertical slice is preferred over in-place refactor or rewrite.
- Codex-style workbench is preferred over a conventional dashboard or cinematic AI console.
- OpenAI is the first reasoning provider, behind an interface.
- First complete investigation is two-account IDOR/BOLA.
- First target boundary is exact loopback local lab only.
- Approval is bounded and batch-specific.
- Only safe read methods are possible.
- Secrets live in the OS credential store.
- Raw capture retention is disabled.
- SQLite events are the source of investigation history.
- Deterministic policy and conclusion validators remain authoritative over the model.
- Commits are frequent and focused; releases are rare and explicitly approved.

No unresolved product or architecture decision remains for implementation planning.
