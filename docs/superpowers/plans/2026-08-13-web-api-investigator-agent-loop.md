# Blackhole Web/API Investigator Agent Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Close a headless, evidence-grounded two-account IDOR/BOLA investigation loop against the included deterministic loopback lab through one authoritative execution gateway.

**Architecture:** Raw target data exists only inside HTTP or browser workers and crosses into the rest of the system only as a `SanitizedToolOutcome`. The gateway owns revalidation, approval consumption, budgets, durable `tool.started`, credential capabilities, and outcome persistence; the model returns strict declarative decisions and never receives a network, secret, approval, or persistence capability.

**Tech Stack:** Python 3.11/3.12, SQLite, Pydantic, FastAPI/Uvicorn for the synthetic lab, httpx, Playwright, OpenAI Python SDK Responses structured outputs, pytest, coverage, and Ruff.

## Global Constraints

- Complete `2026-08-13-web-api-investigator-foundation.md` with a clean gate before starting this plan.
- Implement only on `codex/web-api-investigator-alpha`; do not push, merge, tag, release, bump version `1.84.1`, or open a pull request without separate researcher authorization.
- The only target is an explicitly scoped `http://127.0.0.1:` origin with a decimal port. Only `GET`, `HEAD`, and `OPTIONS` are representable.
- No worker call occurs without an exact, unexpired, unconsumed grant and immediate scope/budget/identity revalidation.
- Commit `tool.started` before the first network byte. Never automatically retry or replay a target action, redirect hop, or interrupted tool.
- Disable environment proxies and automatic redirects. Canonicalize and authorize every redirect, browser request, and subresource before it leaves the process.
- Inject target credentials only through a one-time gateway capability after final validation. Provider code can read only the provider-key namespace; target workers can read only the selected identity-secret namespace.
- Redact structurally before bounding or serializing. Raw bodies, headers, cookies, HTML, screenshots, storage, and network logs are never persisted, logged, exported, or sent to the model.
- `supported` and `rejected` are deterministic fixture predicates. Every other outcome is `inconclusive`; model wording cannot override the validator.
- The hidden lab mode and `FixtureOracle` never enter `ModelDecisionRequest`, prompts, events visible to the model, or workbench responses.
- New runtime code must not import `bugintel.cli`, legacy live integrations, scoped-runtime preview adapters, legacy evidence storage, legacy redaction, legacy state patching, or legacy conclusion heuristics.
- Use the official OpenAI Responses structured-output method `client.responses.parse` with the concrete `ModelDecisionEnvelope` as `text_format` behind the provider interface; pass no OpenAI-hosted or custom execution tools. Reference: https://developers.openai.com/api/docs/guides/structured-outputs
- Exact alpha ceilings from the foundation remain authoritative; adapters may lower them but never raise them.

---

## File Structure

```text
bugintel/
  cases/
    evidence.py
    export.py
    migrations/0007_tool_evidence.sql
  policy/
    gateway.py
  runtime/
    context.py
    conclusion.py
    identity_verification.py
    investigator.py
    model_provider.py
    prompts.py
    recovery.py
  tools/
    __init__.py
    results.py
    http.py
    browser.py
lab/
  __init__.py
  idor_demo/
    __init__.py
    app.py
    fixtures.py
    oracle.py
tests/
  contracts/
  lab_scenarios/
  runtime/
  tools/
```

---

### Task 12: Add the Sanitizer and Atomic Evidence Persistence

**Files:**
- Create: `bugintel/tools/__init__.py`
- Create: `bugintel/tools/results.py`
- Create: `bugintel/cases/evidence.py`
- Create: `bugintel/cases/migrations/0007_tool_evidence.sql`
- Create: `tests/tools/test_results.py`
- Create: `tests/cases/test_evidence.py`

**Interfaces:**
- Consumes: private raw worker results, `RedactionPolicy`, match-only `SecretMatcher`, `SemanticExtractor`, `SanitizedPayload`, `Database`, `EventStore`, and Foundation `CaseMemoryRepository`.
- Produces: `SanitizedToolOutcome`, `SemanticExtractor`, `ResultSanitizer.sanitize_http`, `sanitize_error`, `EvidenceRepository.commit_outcome`, and `record_failure`.

- [ ] **Step 1: Write redact-before-bound and atomicity tests**

```python
from bugintel.tools.results import RawHttpResult, ResultSanitizer


def test_sanitizer_redacts_before_bounding() -> None:
    secret = "token-that-crosses-the-boundary"
    raw = RawHttpResult(
        canonical_url="http://127.0.0.1:8080/api/orders/1048",
        method="GET",
        status_code=200,
        headers=(("Set-Cookie", secret),),
        body=(b"x" * 1995) + secret.encode("utf-8"),
        content_type="application/json",
    )
    outcome = ResultSanitizer(max_excerpt_bytes=2000).sanitize_http(
        raw,
        provenance=provenance_fixture(),
        ended_at=datetime.now(UTC),
    )
    serialized = outcome.model_dump_json()
    assert secret not in serialized
    assert "Set-Cookie" not in serialized


def test_evidence_event_and_tool_completion_roll_back_together(repository, database, outcome) -> None:
    repository.fail_after_evidence_insert = True
    with pytest.raises(SimulatedCommitFailure):
        repository.commit_outcome(outcome)
    assert database.read_one("SELECT count(*) FROM evidence")[0] == 0
    assert database.read_one("SELECT count(*) FROM events WHERE type='evidence.created'")[0] == 0


def test_opaque_configured_secret_echo_is_removed_before_bounding(provenance) -> None:
    matcher = StaticSecretMatcher(("opaque-vault-value",))
    sanitizer = ResultSanitizer(
        redaction_policy=RedactionPolicy(),
        configured_secret_matcher=matcher,
        semantic_extractor=FakeSemanticExtractor(),
        max_excerpt_bytes=2000,
    )
    raw = raw_result(json_body={"innocent_name": "prefix-opaque-vault-value-suffix"})
    serialized = sanitizer.sanitize_http(raw, provenance, datetime.now(UTC)).model_dump_json()
    assert "opaque-vault-value" not in serialized
    assert "configured_credential" in serialized


@pytest.mark.parametrize("case", [
    "cookie", "authorization", "sensitive_query", "nested_json", "tuple_value",
    "split_stream_token", "exception_text",
])
def test_result_canary_matrix(result_harness, case) -> None:
    result = result_harness.sanitize(case)
    assert result_harness.canary not in result.serialized
    assert result.raw_result_escaped is False


def test_evidence_is_append_only_uuid_named_and_hashed(evidence_repository, outcome) -> None:
    first = evidence_repository.commit_outcome(outcome)
    second = evidence_repository.commit_outcome(outcome.model_copy(update={"tool_run_id": uuid4()}))
    assert first.id != second.id
    assert first.sanitized_sha256 == sha256(
        canonical_bytes(first.sanitized_payload.model_dump(mode="json"))
    ).hexdigest()
    assert not hasattr(evidence_repository, "update")
    assert not hasattr(evidence_repository, "delete")
```

- [ ] **Step 2: Run the tests and confirm failure**

```powershell
python -m pytest tests/tools/test_results.py tests/cases/test_evidence.py -v
```

Expected: missing modules/tables.

- [ ] **Step 3: Implement the raw-to-sanitized boundary**

```python
class ResultProvenance(FrozenModel):
    action_id: UUID
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    tool_run_id: UUID
    identity_ref: UUID
    identity_label: SanitizedText
    policy_decision_id: UUID
    approval_grant_id: UUID
    started_at: AwareDatetime


class RawHttpResult(FrozenModel):
    canonical_url: str
    method: Literal["GET", "HEAD", "OPTIONS"]
    status_code: int
    headers: tuple[tuple[str, str], ...]
    body: bytes
    content_type: str


class SanitizedToolOutcome(FrozenModel):
    action_id: UUID
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    tool_run_id: UUID
    identity_ref: UUID
    identity_label: SanitizedText
    canonical_url: str
    method: str
    status_code: int | None
    content_type: str | None
    safe_headers: SanitizedPayload
    sanitized_body: SanitizedPayload
    sanitized_sha256: str
    raw_body_size: int
    semantic_fields: SanitizedPayload
    cache_ambiguity: bool
    policy_decision_id: UUID
    approval_grant_id: UUID
    started_at: AwareDatetime
    ended_at: AwareDatetime
    sanitizer_version: str = "alpha-1"


JSONScalar = str | int | float | bool | None


class SemanticExtractor(Protocol):
    def extract(
        self,
        *,
        canonical_url: str,
        status_code: int,
        content_type: str,
        sanitized_json: SanitizedPayload,
    ) -> dict[str, JSONScalar | list[JSONScalar]]:
        raise NotImplementedError
```

`ResultSanitizer.sanitize_http(raw: RawHttpResult, provenance: ResultProvenance, ended_at: datetime) -> SanitizedToolOutcome` parses the complete bounded-in-memory response, checks every primitive and exception string with both `RedactionPolicy` and the injected match-only `SecretMatcher`, replaces a configured-secret match with its category, recursively redacts, and only then creates the excerpt/subset. Production assembly obtains `VaultSecretMatcher` from the vault; it exposes `match_category(text)` only and cannot enumerate or return a credential. The HTTP worker enforces the 1 MiB transport ceiling, so the sanitizer never receives an unbounded body. Hash canonical sanitized JSON, never raw bytes. Allowlist only `content-type`, `content-length`, `cache-control`, `age`, `via`, `etag`, and `vary`, and sanitize values before storage.

After structural redaction, call the injected `SemanticExtractor` with only the sealed JSON payload and nonsecret metadata; seal its returned mapping again through `RedactionPolicy.sanitize_payload`. Define `cache_ambiguity` centrally and deterministically as `True` only when a valid positive integer `Age` is present together with either a `public`/`s-maxage` cache-control directive or a nonempty `Via`; invalid cache headers fail closed to `True`. No keyword scoring or route-specific verdict exists in the sanitizer. Task 14 supplies the only alpha extractor and its exact schema tests.

- [ ] **Step 4: Persist evidence and terminal state in one transaction**

`0007_tool_evidence.sql` creates `tool_runs`, `observations`, and immutable `evidence` rows. `commit_outcome` opens one `BEGIN IMMEDIATE` transaction, inserts the UUID-keyed canonical sanitized JSON and hash, appends `evidence.created` and `observation.created`, calls `CaseMemoryRepository.record_observation` to append the new endpoint-memory version plus `memory.updated`, and marks the tool `completed` while the investigation remains `EXECUTING`. Any evidence, event, memory, or tool update failure rolls the whole transaction back. It never changes the investigation state. After the last action, the gateway performs the single `EXECUTING -> OBSERVING` transition in a separate final transaction; intermediate outcomes therefore cannot invalidate a multi-action batch. Add SQLite triggers that abort `UPDATE` and `DELETE` on `evidence`.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/tools/test_results.py tests/cases/test_evidence.py -v
python -m pytest tests/cases tests/tools -q
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/tools bugintel/cases tests/tools tests/cases
git diff --check
git add bugintel/tools bugintel/cases/evidence.py bugintel/cases/migrations/0007_tool_evidence.sql tests/tools/test_results.py tests/cases/test_evidence.py
git commit -m "feat: persist sanitized evidence atomically"
```

### Task 13: Add the Authoritative Gateway with a Fake Worker

**Files:**
- Create: `bugintel/policy/gateway.py`
- Modify: `bugintel/cases/repository.py`
- Create: `tests/policy/test_gateway.py`
- Create: `tests/contracts/test_gateway_boundary.py`

**Interfaces:**
- Consumes: `ScopePolicy`, `ApprovalService`, `BudgetLedger`, `CaseRepository`, `EvidenceRepository`, `TargetCredentialSource`, and a registered `ToolWorker`.
- Produces: opaque `ExecutionCapability`, `ToolWorker.run`, `ExecutionGateway.execute_batch`, `authorize_redirect`, and the capability-narrowed `authorize_browser_request` used only for a browser action's approved same-origin resource envelope.

- [ ] **Step 1: Write no-approval, ordering, and import-boundary tests**

```python
def test_worker_is_never_called_without_exact_grant(gateway, fake_worker, unapproved_batch) -> None:
    with pytest.raises(ExecutionBlocked):
        gateway.execute_batch(unapproved_batch.investigation_id, grant_id=None)
    assert fake_worker.calls == []


def test_tool_started_is_committed_before_worker_call(gateway, fake_worker, granted_batch, event_store) -> None:
    fake_worker.on_call = lambda: assert_started(event_store, granted_batch.tool_run_id)
    gateway.execute_batch(granted_batch.investigation_id, granted_batch.grant.id)
    assert fake_worker.calls == [granted_batch.batch.digest]
```

In `tests/contracts/test_gateway_boundary.py`, parse imports with `ast` and fail if new runtime modules import legacy integrations, if model modules import adapters/secrets, if workers import the model, or if any module other than `policy/gateway.py` calls a worker's `run` method.

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/policy/test_gateway.py tests/contracts/test_gateway_boundary.py -v
```

Expected: missing gateway.

- [ ] **Step 3: Implement an opaque one-use capability**

```python
class ExecutionCapability(FrozenModel):
    id: UUID
    investigation_id: UUID
    tool_run_id: UUID
    action_id: UUID
    action_digest: str
    identity_ref: UUID
    identity_label: SanitizedText
    identity_secret_version: int
    scope_digest: str
    policy_decision_id: UUID
    approval_grant_id: UUID
    canonical_action: LiveAction
    credential_capability: ExecutionSecretCapability
    expires_at: datetime


class ToolWorker(Protocol):
    def run(self, capability: ExecutionCapability) -> SanitizedToolOutcome:
        raise NotImplementedError
```

Keep capability construction private to `ExecutionGateway`. A registry maps the action discriminator to a worker injected at application assembly; no global worker is importable. Add exact repository methods used below: `assert_may_start(connection, investigation_id)`, `load_scope_snapshot(connection, digest)`, `load_current_identity(connection, identity_id)`, `record_policy_block(connection, batch, action, decision)`, `record_tool_started(connection, batch, decision, identity) -> ToolRun`, and `finish_batch_observing(connection, investigation_id, batch_id, completed_action_ids)`. Foundation Tasks 6/9 persist immutable scope snapshots and expose them only through `CaseRepository`; `record_tool_started` stores the recomputed canonical `action_digest`.

- [ ] **Step 4: Implement the per-action pre-effect transaction sequence**

`execute_batch` performs, in order:

```python
batch = self._approvals.load_batch_for_grant(grant_id)
for action in batch.actions:
    with self._database.transaction() as connection:
        self._repository.assert_may_start(connection, batch.investigation_id)
        scope = self._repository.load_scope_snapshot(connection, batch.scope_digest)
        identity = self._repository.load_current_identity(connection, action.identity_ref)
        decision = self._scope.evaluate(action, scope)
        if not decision.allowed or decision.canonical_action is None:
            self._repository.record_policy_block(connection, batch, action, decision)
            raise ExecutionBlocked(decision.reason_code)
        self._approvals.assert_current_identity_version(
            connection, grant_id, identity.id, identity.secret_version
        )
        self._budgets.reserve_request(
            batch.investigation_id,
            count=1,
            connection=connection,
            now=self._clock.now(),
        )
        self._approvals.consume(
            grant_id,
            batch,
            action.id,
            now=self._clock.now(),
            connection=connection,
        )
        tool_run = self._repository.record_tool_started(
            connection, batch, decision, identity
        )
    outcome = self._run_once(batch, decision, identity, tool_run)
    self._evidence.commit_outcome(outcome)
with self._database.transaction() as connection:
    self._repository.finish_batch_observing(
        connection,
        investigation_id=batch.investigation_id,
        batch_id=batch.id,
        completed_action_ids=tuple(action.id for action in batch.actions),
    )
```

The single transaction for each action atomically revalidates stop/state, scope, identity version, approval, the 60-second batch deadline, 30-minute active deadline, 40-total request ceiling, and rolling 8-per-minute window; consumes exactly that action ID; appends `policy.allowed`; and commits `tool.started` before the worker receives a capability. `_run_once` creates the execution and one-use credential capabilities privately, invokes exactly one registered worker, and never catches an error by retrying it. The initial browser document request uses this already-reserved capability; it must not reserve the same request a second time. `authorize_browser_request(parent, method, url, resource_kind)` may derive a child capability only from a still-current `BrowserNavigationAction`, only for `GET`/`HEAD`, the approved origin, an approved resource kind, and while the action's subresource/request/byte/deadline envelope remains. Its transaction repeats state/scope/identity/budget checks, reserves exactly one additional request, appends `policy.allowed` or `policy.blocked`, and returns no credential value. On success, pass only `SanitizedToolOutcome` to `EvidenceRepository`. After every action is completed, `finish_batch_observing` verifies the exact stored batch and complete ordered action-ID set, verifies every tool row is completed, performs the only `EXECUTING -> OBSERVING` projection transition, and appends the lifecycle event in one transaction. On a sanitized failure, record `tool.failed`, pause safely, and do not call `finish_batch_observing`. On process recovery, Task 20 marks unmatched started rows `interrupted`. A successful multi-action batch proceeds sequentially; no action ID can run twice.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/policy/test_gateway.py tests/contracts/test_gateway_boundary.py -v
python -m pytest tests/cases tests/policy tests/contracts -q
git diff --check
git add bugintel/policy/gateway.py bugintel/cases/repository.py tests/policy/test_gateway.py tests/contracts/test_gateway_boundary.py
git commit -m "feat: add authoritative execution gateway"
```

### Task 14: Add the Deterministic Synthetic IDOR Lab

**Files:**
- Modify: `pyproject.toml`
- Create: `lab/__init__.py`
- Create: `lab/idor_demo/__init__.py`
- Create: `lab/idor_demo/fixtures.py`
- Create: `lab/idor_demo/oracle.py`
- Create: `lab/idor_demo/app.py`
- Create: `tests/lab_scenarios/test_idor_lab.py`

**Interfaces:**
- Consumes: a hidden `LabMode` chosen by test/launcher assembly.
- Produces: `create_lab_app(mode)`, `run_lab(host, port, mode)`, `FixtureOracle.owner_for`, `protected_subset_for`, `LabSemanticExtractor`, and stable synthetic tokens.

- [ ] **Step 1: Write exact mode and identity tests**

```python
@pytest.mark.parametrize("mode", [LabMode.VULNERABLE, LabMode.SECURE, LabMode.AMBIGUOUS])
def test_whoami_returns_fixture_subject_for_valid_tokens(mode) -> None:
    client = TestClient(create_lab_app(mode))
    assert client.get("/api/whoami", headers=auth(ACCOUNT_A_TOKEN)).json() == {"subject_id": "subject-a"}
    assert client.get("/api/whoami", headers=auth(ACCOUNT_B_TOKEN)).json() == {"subject_id": "subject-b"}
    assert client.get("/api/whoami", headers=auth("invalid")).status_code == 401


def test_secure_mode_denies_account_b_without_protected_fields() -> None:
    response = TestClient(create_lab_app(LabMode.SECURE)).get(
        "/api/orders/1048", headers=auth(ACCOUNT_B_TOKEN)
    )
    assert response.status_code == 403
    assert response.json() == {"error_code": "forbidden"}


def test_vulnerable_mode_returns_exact_account_a_fixture_to_both_accounts() -> None:
    client = TestClient(create_lab_app(LabMode.VULNERABLE))
    for token in (ACCOUNT_A_TOKEN, ACCOUNT_B_TOKEN):
        response = client.get("/api/orders/1048", headers=auth(token))
        assert response.status_code == 200
        assert protected_subset(response.json()) == PROTECTED_SUBSET


def test_ambiguous_mode_emits_exact_shared_cache_evidence() -> None:
    response = TestClient(create_lab_app(LabMode.AMBIGUOUS)).get(
        "/api/orders/1048", headers=auth(ACCOUNT_B_TOKEN)
    )
    assert response.status_code == 200
    assert response.headers["cache-control"] == "public"
    assert response.headers["age"] == "60"
    assert response.headers["via"] == "1.1 lab-cache"


@pytest.mark.parametrize(
    ("path", "status", "payload", "expected"),
    [
        ("/api/whoami", 200, {"subject_id": "subject-a"}, {"subject_id": "subject-a"}),
        ("/api/orders/1048", 200, PROTECTED_SUBSET, PROTECTED_SUBSET),
        ("/api/orders/1048", 403, {"error_code": "forbidden"}, {"error_code": "forbidden", "protected_fields_present": False}),
        ("/api/orders/1048", 200, {"object_id": "1048"}, {"normalization_valid": False}),
    ],
)
def test_lab_semantic_extractor_has_exact_schemas(extractor, redaction, path, status, payload, expected) -> None:
    actual = extractor.extract(
        canonical_url=f"http://127.0.0.1:8080{path}",
        status_code=status,
        content_type="application/json",
        sanitized_json=redaction.sanitize_payload(payload),
    )
    assert actual == expected
```

- [ ] **Step 2: Add current bounded lab dependencies**

Add without changing the package version:

```toml
"fastapi>=0.141.1,<1.0",
"uvicorn>=0.52.2,<1.0",
```

Change package discovery to `include = ["bugintel*", "lab*"]` so clean wheels can include the approved top-level lab package later.

- [ ] **Step 3: Run the tests and confirm failure**

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/lab_scenarios/test_idor_lab.py -v
```

Expected: missing lab package.

- [ ] **Step 4: Implement fixed fixtures, oracle, and binding guard**

```python
class LabMode(StrEnum):
    VULNERABLE = "vulnerable"
    SECURE = "secure"
    AMBIGUOUS = "ambiguous"


PROTECTED_SUBSET = {
    "object_id": "1048",
    "owner_subject_id": "subject-a",
    "total_minor": 2599,
    "currency": "USD",
    "item_skus": ["LAB-RED", "LAB-BLUE"],
}

ACCOUNT_A_TOKEN = "lab-account-a-token-v1"
ACCOUNT_B_TOKEN = "lab-account-b-token-v1"


def run_lab(host: str, port: int, mode: LabMode) -> None:
    if host != "127.0.0.1":
        raise ValueError("controlled lab must bind to 127.0.0.1")
    uvicorn.run(create_lab_app(mode), host=host, port=port, access_log=False)
```

Keep `FixtureOracle` in `lab/idor_demo/oracle.py`; do not expose it from an API route or place it in model context. `LabSemanticExtractor.extract` uses the exact `SemanticExtractor` signature from Task 12, reparses only the canonical URL path, and reads only `.value` from the already sealed payload. `/api/whoami` accepts only the single `subject_id` string shape; a `200 /api/orders/{id}` accepts only `object_id`, `owner_subject_id`, `total_minor`, `currency`, and string-list `item_skus`; a `403` accepts only `error_code=forbidden` and emits `protected_fields_present=False`; every other status/shape emits only `normalization_valid=False`. It normalizes observed values but cannot import or query `FixtureOracle`, so expected ownership remains unavailable to the model boundary.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/lab_scenarios/test_idor_lab.py -v
python -m pytest -q
git diff --check
git add pyproject.toml lab tests/lab_scenarios/test_idor_lab.py
git commit -m "feat: add deterministic IDOR lab"
```

### Task 15: Add the Streamed Read-Only HTTP Worker

**Files:**
- Create: `bugintel/tools/http.py`
- Modify: `bugintel/runtime/tool_protocol.py`
- Create: `tests/tools/test_http.py`
- Create: `tests/lab_scenarios/test_http_gateway.py`

**Interfaces:**
- Consumes: gateway `ExecutionCapability`, `TargetCredentialSource`, `ResultSanitizer`, `BudgetLedger`, injected `StopSignal`, and `ExecutionGateway.authorize_redirect`.
- Produces: `HttpToolWorker.run(capability) -> SanitizedToolOutcome`.

- [ ] **Step 1: Verify the action contract's exact redirect ceiling**

Confirm the Foundation plan's `HttpRequestAction` field and digest-tamper tests remain:

```python
max_redirect_hops: int = Field(default=0, ge=0, le=3)
```

The normal IDOR and `/api/whoami` actions use zero redirects. A nonzero value permits only manually followed `301`, `302`, `303`, `307`, or `308` locations whose canonicalized target remains within the approved identity, origin, method, path, time, byte, and redirect-hop envelope. Each hop receives a gateway-issued child execution capability, reserves an investigation request before the next network byte, and is counted against the single approved action's redirect ceiling; it does not consume a second top-level action ID.

- [ ] **Step 2: Write transport-boundary tests**

```python
def test_http_client_disables_environment_and_redirects(worker, transport_factory, capability) -> None:
    worker.run(capability)
    assert transport_factory.created_options == [{
        "trust_env": False,
        "follow_redirects": False,
        "cookies": {},
    }]


def test_redirect_is_reauthorized_before_second_request(worker, capability, transport) -> None:
    transport.queue_redirect("http://127.0.0.1:9090/out-of-scope")
    with pytest.raises(ExecutionBlocked):
        worker.run(capability)
    assert transport.request_count == 1


def test_credentials_are_requested_only_after_final_authorization(worker, blocked_capability, target_source) -> None:
    with pytest.raises(ExecutionBlocked):
        worker.run(blocked_capability)
    assert target_source.read_calls == []


@pytest.mark.parametrize(
    ("case", "error", "request_count"),
    [
        ("post_method", ActionContractViolation, 0),
        ("request_body", ActionContractViolation, 0),
        ("one_mib_plus_one", ResponseTooLarge, 1),
        ("after_absolute_15_seconds", ResourceInterrupted, 1),
        ("transient_503", None, 1),
        ("network_exception", SanitizedToolFailure, 1),
    ],
)
def test_http_transport_boundary_matrix(http_harness, case, error, request_count) -> None:
    result = http_harness.run(case, expected_error=error)
    assert result.request_count == request_count
    assert result.retry_count == 0
    assert result.raw_result_returned is False
    assert http_harness.secret_canary not in result.serialized_error
```

- [ ] **Step 3: Run and confirm failure**

```powershell
python -m pytest tests/tools/test_http.py tests/lab_scenarios/test_http_gateway.py -v
```

Expected: missing HTTP worker.

- [ ] **Step 4: Implement one streamed attempt per authorized hop**

```python
deadline = self._monotonic() + action.timeout_seconds
with httpx.Client(
    follow_redirects=False,
    trust_env=False,
    cookies=httpx.Cookies(),
    timeout=httpx.Timeout(connect=5.0, read=1.0, write=1.0, pool=1.0),
) as client:
    with client.stream(
        method=action.method,
        url=canonical.value,
        headers=self._headers_for(secret, action.header_profile),
    ) as response:
        body = bytearray()
        for chunk in response.iter_bytes():
            if self._monotonic() > deadline or self._stop_signal.is_set(capability.investigation_id):
                raise ResourceInterrupted("resource deadline or stop")
            self._budgets.charge_bytes(capability.investigation_id, len(chunk))
            if len(body) + len(chunk) > action.max_response_bytes:
                raise ResponseTooLarge(action.max_response_bytes)
            body.extend(chunk)
```

Define `StopSignal(Protocol)` in `bugintel/runtime/tool_protocol.py` with `is_set(investigation_id: UUID) -> bool`; Task 20 supplies the durable-backed implementation and tests, while this task uses an injected fake. The worker creates and closes a fresh client per authorized action, explicitly clears its cookie jar between redirect hops, and never shares transport state across identities. Before the first request, call `TargetCredentialSource.read(capability.credential_capability)` exactly once and build authentication headers internally. The monotonic absolute deadline enforces total resource time; the small read timeout only lets the loop recheck it. Immediately wrap the response in `RawHttpResult`, sanitize, clear the mutable body buffer, and return only `SanitizedToolOutcome`. For a redirect response, extract `Location` only inside the worker, discard it after use, call `ExecutionGateway.authorize_redirect(capability, location, hop_index)`, and use only the returned child capability's canonical action for the next request. `authorize_redirect` opens a transaction, rechecks stop/state/scope/approval/identity version and hop ceiling, reserves one request, records `policy.allowed` or `policy.blocked`, and returns no credential value.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/tools/test_http.py tests/lab_scenarios/test_http_gateway.py -v
python -m pytest tests/policy tests/tools tests/lab_scenarios -q
git diff --check
git add bugintel/tools/http.py bugintel/runtime/tool_protocol.py tests/runtime/test_tool_protocol.py tests/tools/test_http.py tests/lab_scenarios/test_http_gateway.py
git commit -m "feat: execute approved read-only HTTP actions"
```

### Task 16: Add the Approved Identity-Preflight Workflow

**Files:**
- Create: `bugintel/runtime/identity_verification.py`
- Modify: `bugintel/cases/repository.py`
- Create: `tests/runtime/test_identity_verification.py`

**Interfaces:**
- Consumes: two current `IdentityRef` values, exact scope origin, `ActionBatch`, gateway outcomes, fixture-valid subject-ID predicate, and approval invalidation.
- Produces: `IdentityVerifier.propose_preflight`, `apply_result`, verified subject/origin/secret-version metadata, `identity.verified`, and `identity.rejected`.

- [ ] **Step 1: Write valid, duplicate, invalid, and replacement tests**

```python
def test_preflight_requires_two_distinct_verified_subjects(verifier, identity_a, identity_b, scope) -> None:
    batch = verifier.propose_preflight(scope, identity_a, identity_b)
    assert [action.url for action in batch.actions] == [
        f"{scope.origins[0]}/api/whoami",
        f"{scope.origins[0]}/api/whoami",
    ]
    verified = verifier.apply_result(batch, whoami_outcomes("subject-a", "subject-b"))
    assert verified[0].verified_subject_id == "subject-a"
    assert verified[1].verified_subject_id == "subject-b"


@pytest.mark.parametrize("subjects", [("subject-a", "subject-a"), ("subject-a", None)])
def test_duplicate_or_invalid_subjects_are_rejected(verifier, batch, subjects) -> None:
    with pytest.raises(IdentityVerificationFailed):
        verifier.apply_result(batch, whoami_outcomes(*subjects))
```

Add the exact replacement proof:

```python
def test_secret_replacement_clears_verification_and_grants(identity_harness) -> None:
    case = identity_harness.verified_pair_with_grant()
    prior_version = case.identity_b.secret_version
    replaced = identity_harness.replace_secret(case.identity_b.id, "replacement-token")
    assert replaced.secret_version == prior_version + 1
    assert replaced.verified_subject_id is None
    assert replaced.verification_evidence_id is None
    assert identity_harness.unconsumed_grants(case.investigation_id) == ()
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/runtime/test_identity_verification.py -v
```

Expected: missing verifier.

- [ ] **Step 3: Implement exact preflight and apply rules**

```python
def propose_preflight(self, scope: ScopeSnapshot, first: IdentityRef, second: IdentityRef) -> ActionBatch:
    purpose = self._redaction.redact_text("verify distinct synthetic lab identities")
    expected = self._redaction.redact_text("fixture-valid subject_id")
    actions = tuple(
        HttpRequestAction(
            id=uuid4(),
            identity_ref=identity.id,
            method="GET",
            url=f"{scope.origins[0]}/api/whoami",
            header_profile=identity.header_profile,
            purpose=purpose,
            expected_observation=expected,
            timeout_seconds=15,
            max_response_bytes=16_384,
            max_redirect_hops=0,
        )
        for identity in (first, second)
    )
    return ActionBatch.create(
        investigation_id=self._investigation_id,
        scope_digest=scope.digest,
        purpose=purpose,
        actions=actions,
        max_request_count=2,
        batch_timeout_seconds=60,
        max_total_bytes=32_768,
        approval_expires_at=self._clock.now() + timedelta(minutes=5),
        created_at=self._clock.now(),
    )
```

`apply_result` accepts only two completed, cited, same-origin outcomes with `200 application/json` and a subject ID known by the lab identity predicate. It requires distinct values and current secret versions. Persist both updates and events in one transaction; on any failure persist only sanitized reason codes and pause the investigation.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/runtime/test_identity_verification.py tests/lab_scenarios/test_http_gateway.py -v
python -m pytest tests/runtime tests/cases tests/policy -q
git diff --check
git add bugintel/runtime/identity_verification.py bugintel/cases/repository.py tests/runtime/test_identity_verification.py
git commit -m "feat: verify distinct lab identities"
```

### Task 17: Add the Deterministic Conclusion Validator

**Files:**
- Modify: `bugintel/cases/repository.py`
- Create: `bugintel/runtime/conclusion.py`
- Create: `tests/runtime/test_conclusion.py`

**Interfaces:**
- Consumes: one immutable `ConclusionEvidenceSet` assembled by the repository from verified identities, the exact approved comparison batch, immutable policy/tool/evidence rows, and `FixtureOracle` through a narrow read protocol.
- Produces: `ConclusionValidator.validate(proposal: ConclusionProposal, facts: ConclusionEvidenceSet) -> Conclusion` with only exact `supported`, `rejected`, or `inconclusive` outcomes.

- [ ] **Step 1: Write exhaustive verdict-table tests**

```python
def test_supported_requires_exact_cross_account_match(validator, evidence_set) -> None:
    conclusion = validator.validate(proposal("supported", evidence_set.ids), evidence_set)
    assert conclusion.verdict == Verdict.SUPPORTED


def test_rejected_requires_exact_403_forbidden_shape(validator, secure_evidence_set) -> None:
    conclusion = validator.validate(proposal("rejected", secure_evidence_set.ids), secure_evidence_set)
    assert conclusion.verdict == Verdict.REJECTED


@pytest.mark.parametrize("mutation", [
    "same_subject",
    "missing_whoami",
    "wrong_owner",
    "account_a_not_200",
    "different_protected_subset",
    "cache_ambiguity",
    "missing_citation",
    "policy_error",
])
def test_every_incomplete_or_ambiguous_case_is_inconclusive(validator, mutated_evidence, mutation) -> None:
    assert validator.validate(proposal("supported", mutated_evidence.ids), mutated_evidence).verdict == Verdict.INCONCLUSIVE
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/runtime/test_conclusion.py -v
```

Expected: missing validator.

- [ ] **Step 3: Implement exact predicates**

```python
class ConclusionProposal(FrozenModel):
    verdict: Verdict
    cited_evidence_ids: tuple[UUID, ...]
    claim_codes: tuple[Literal[
        "distinct_verified_accounts",
        "account_a_baseline_matches_fixture",
        "account_b_read_account_a_object",
        "account_b_denied",
    ], ...]
    confidence_rationale: SanitizedText
    recommended_human_next_step: SanitizedText


class ConclusionDraft(FrozenModel):
    verdict: Verdict
    cited_evidence_ids: tuple[UUID, ...]
    claim_codes: tuple[Literal[
        "distinct_verified_accounts",
        "account_a_baseline_matches_fixture",
        "account_b_read_account_a_object",
        "account_b_denied",
    ], ...]
    confidence_rationale: str = Field(min_length=1, max_length=1000)
    recommended_human_next_step: str = Field(min_length=1, max_length=1000)


class IdentityVerificationSnapshot(FrozenModel):
    identity_id: UUID
    secret_version: int
    verified_subject_id: str
    verified_origin: str
    verification_evidence_id: UUID
    current_secret_version: int


class ComparisonOutcome(FrozenModel):
    action_id: UUID
    batch_id: UUID
    approval_grant_id: UUID
    identity_id: UUID
    canonical_url: str
    status_code: int
    content_type: str
    semantic_fields: SanitizedPayload
    cache_ambiguity: bool
    evidence_id: UUID
    policy_allowed: bool
    tool_state: Literal["completed"]


class ConclusionEvidenceSet(FrozenModel):
    investigation_id: UUID
    scope_origin: str
    comparison_batch_id: UUID
    comparison_batch_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    comparison_grant_id: UUID
    grant_batch_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    grant_state: Literal["fully_consumed"]
    comparison_action_ids: tuple[UUID, UUID]
    identity_a: IdentityVerificationSnapshot
    identity_b: IdentityVerificationSnapshot
    account_a: ComparisonOutcome
    account_b: ComparisonOutcome
    fixture_owner_subject_id: str
    fixture_object_id: str
    fixture_canonical_url: str
    fixture_protected_subset: SanitizedPayload
    available_evidence_ids: frozenset[UUID]


required_citations = {
    facts.identity_a.verification_evidence_id,
    facts.identity_b.verification_evidence_id,
    facts.account_a.evidence_id,
    facts.account_b.evidence_id,
}
identity_ok = all((
    facts.identity_a.identity_id != facts.identity_b.identity_id,
    facts.identity_a.verified_subject_id != facts.identity_b.verified_subject_id,
    facts.identity_a.verified_origin == facts.scope_origin,
    facts.identity_b.verified_origin == facts.scope_origin,
    facts.identity_a.secret_version == facts.identity_a.current_secret_version,
    facts.identity_b.secret_version == facts.identity_b.current_secret_version,
))
comparison_ok = all((
    facts.comparison_batch_digest == facts.grant_batch_digest,
    facts.grant_state == "fully_consumed",
    facts.account_a.batch_id == facts.comparison_batch_id,
    facts.account_b.batch_id == facts.comparison_batch_id,
    facts.account_a.approval_grant_id == facts.comparison_grant_id,
    facts.account_b.approval_grant_id == facts.comparison_grant_id,
    facts.comparison_action_ids == (facts.account_a.action_id, facts.account_b.action_id),
    facts.account_a.identity_id == facts.identity_a.identity_id,
    facts.account_b.identity_id == facts.identity_b.identity_id,
    facts.account_a.canonical_url == facts.account_b.canonical_url,
    facts.account_a.canonical_url == facts.fixture_canonical_url,
    facts.account_a.semantic_fields.value.get("object_id") == facts.fixture_object_id,
    facts.account_a.policy_allowed and facts.account_b.policy_allowed,
    facts.account_a.tool_state == facts.account_b.tool_state == "completed",
    required_citations <= facts.available_evidence_ids,
    required_citations <= set(proposal.cited_evidence_ids),
))
baseline_ok = all((
    facts.fixture_owner_subject_id == facts.identity_a.verified_subject_id,
    facts.account_a.status_code == 200,
    facts.account_a.content_type == "application/json",
    facts.account_a.semantic_fields.value == facts.fixture_protected_subset.value,
    not facts.account_a.cache_ambiguity,
))
supported = all((
    proposal.verdict == Verdict.SUPPORTED,
    identity_ok, comparison_ok, baseline_ok,
    facts.account_b.status_code == 200,
    facts.account_b.content_type == "application/json",
    facts.account_b.semantic_fields.value == facts.fixture_protected_subset.value,
    not facts.account_b.cache_ambiguity,
    set(proposal.claim_codes) == {
        "distinct_verified_accounts",
        "account_a_baseline_matches_fixture",
        "account_b_read_account_a_object",
    },
))

rejected = all((
    proposal.verdict == Verdict.REJECTED,
    identity_ok, comparison_ok, baseline_ok,
    facts.account_b.status_code == 403,
    facts.account_b.content_type == "application/json",
    facts.account_b.semantic_fields.value == {"error_code": "forbidden", "protected_fields_present": False},
    not facts.account_b.cache_ambiguity,
    set(proposal.claim_codes) == {
        "distinct_verified_accounts",
        "account_a_baseline_matches_fixture",
        "account_b_denied",
    },
))
```

`ConclusionEvidenceSet` has no public constructor in the controller. `CaseRepository.load_conclusion_evidence_set(investigation_id, comparison_batch_id)` joins the stored batch, its exact grant, ordered actions, tool runs, policy decisions, identity-verification evidence, and evidence rows; then the validator adds `fixture_object_id`, `fixture_canonical_url`, owner, and protected subset through the narrow oracle. Any missing/duplicate/cross-batch relation fails closed before predicate evaluation. `ConclusionValidator` computes those locals inside `validate`; no caller supplies a boolean. It rejects duplicate/unknown citation IDs before the predicate. `CLAIM_TEXT` is a fixed service-owned mapping from the four closed codes to branded sanitized sentences; model free text never becomes a factual claim. For a true exact predicate, render only those fixed claim codes and retain the sanitized rationale/next step as non-factual commentary. A proposed `inconclusive`, any proposal/predicate/claim-code mismatch, or any missing predicate stores `inconclusive` with service-owned limitation codes identifying the failed checks and no positive claim. Never import legacy `result_interpreter` or `response_diff` verdict logic.

- [ ] **Step 4: Verify 100% branch coverage and commit**

```powershell
python -m coverage run --branch --source=bugintel.runtime.conclusion -m pytest tests/runtime/test_conclusion.py
python -m coverage report --fail-under=100
python -m pytest tests/runtime/test_conclusion.py -v
git diff --check
git add bugintel/cases/repository.py bugintel/runtime/conclusion.py tests/runtime/test_conclusion.py
git commit -m "feat: validate IDOR conclusions deterministically"
```

### Task 18: Add the Sanitized Model Context and OpenAI Provider Boundary

**Files:**
- Modify: `pyproject.toml`
- Modify: `bugintel/cases/repository.py`
- Modify: `bugintel/cases/memory.py`
- Create: `bugintel/runtime/context.py`
- Create: `bugintel/runtime/prompts.py`
- Create: `bugintel/runtime/model_provider.py`
- Create: `tests/runtime/test_model_provider.py`
- Create: `tests/contracts/test_model_boundary.py`

**Interfaces:**
- Consumes: sanitized objective/messages, scope summary, labels and verified subject-presence flags, plan, hypotheses, sanitized event/evidence summaries, provider-key source, and budget ledger.
- Produces: `ModelDecisionRequest`, strict `ModelDecision`, `ModelProvider.decide`, `OpenAIModelProvider`, `ScriptedModelProvider`, `ModelContextBuilder.build`, and the exact read-only context repository surface.

- [ ] **Step 1: Write context exclusion and strict-output tests**

```python
def test_context_contains_no_secret_values_or_fixture_mode(context_builder, case_with_canaries) -> None:
    request = context_builder.build(case_with_canaries)
    serialized = request.model_dump_json()
    for canary in case_with_canaries.secret_canaries:
        assert canary not in serialized
    assert "vulnerable" not in serialized
    assert "secure" not in serialized
    assert "ambiguous" not in serialized


def test_provider_uses_structured_response_without_tools(fake_openai_client, provider, request) -> None:
    provider.decide(request)
    call = fake_openai_client.responses.parse_calls[0]
    assert call["text_format"] is ModelDecisionEnvelope
    assert call["store"] is False
    assert "tools" not in call
```

Use this provider-attempt matrix and import-boundary proof:

```python
@pytest.mark.parametrize(
    ("responses", "expected_error", "provider_calls", "model_decisions"),
    [
        ((schema_invalid(), valid_decision()), None, 2, 1),
        ((transient_error(), valid_decision()), None, 2, 1),
        ((refusal(),), ModelRefusal, 1, 0),
        ((missing_parsed(), missing_parsed()), ModelOutputInvalid, 2, 0),
        ((schema_invalid(), schema_invalid()), ModelOutputInvalid, 2, 0),
    ],
)
def test_provider_retry_and_charge_matrix(provider_harness, responses, expected_error, provider_calls, model_decisions) -> None:
    result = provider_harness.decide(responses, expected_error=expected_error)
    assert result.budget.provider_calls == provider_calls
    assert result.budget.model_decisions == model_decisions
    assert result.gateway_calls == 0


def test_provider_and_model_decision_ceilings_are_independent(provider_harness) -> None:
    provider_harness.seed_budget(provider_calls=23, model_decisions=22)
    provider_harness.decide((valid_decision(),))
    assert provider_harness.budget_snapshot() == {"provider_calls": 24, "model_decisions": 23}
    with pytest.raises(BudgetExceeded, match="provider_calls"):
        provider_harness.decide((valid_decision(),))


def test_model_provider_cannot_import_or_receive_target_secret_source() -> None:
    source = Path("bugintel/runtime/model_provider.py").read_text(encoding="utf-8")
    ast.parse(source)
    assert "TargetCredentialSource" not in source
    assert "target_secret_source" not in inspect.signature(OpenAIModelProvider).parameters
```

- [ ] **Step 2: Add the current SDK dependency**

Add without altering the package version:

```toml
"openai>=3.0.0,<4.0",
```

Install and run the tests:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/runtime/test_model_provider.py tests/contracts/test_model_boundary.py -v
```

Expected before implementation: missing modules.

- [ ] **Step 3: Implement strict decisions and sanitized request context**

Define strict variants and wrap the discriminated union in one concrete Pydantic model because the SDK parse surface requires a model class. No variant contains approval, execution status, secret reference value, raw content, network client, callable, or repository handle.

```python
class UpdatePlanDecision(FrozenModel):
    kind: Literal["update_plan"] = "update_plan"
    summary: str = Field(min_length=1, max_length=500)
    steps: tuple[str, ...] = Field(min_length=1, max_length=8)


class UpdateHypothesisDecision(FrozenModel):
    kind: Literal["update_hypothesis"] = "update_hypothesis"
    hypothesis_id: UUID | None = None
    statement: str = Field(min_length=1, max_length=500)
    status: Literal["proposed", "testing", "inconclusive"]
    cited_evidence_ids: tuple[UUID, ...] = ()


class HttpActionDraft(FrozenModel):
    kind: Literal["http_request"] = "http_request"
    identity_ref: UUID
    method: Literal["GET", "HEAD", "OPTIONS"]
    url: str
    header_profile: Literal["session_cookie", "bearer_token"]
    purpose: str = Field(min_length=1, max_length=240)
    expected_observation: str = Field(min_length=1, max_length=240)
    timeout_seconds: int = Field(ge=1, le=15)
    max_response_bytes: int = Field(ge=1, le=1_048_576)
    max_redirect_hops: int = Field(default=0, ge=0, le=3)


class BrowserActionDraft(FrozenModel):
    kind: Literal["browser_navigation"] = "browser_navigation"
    identity_ref: UUID
    start_url: str
    purpose: str = Field(min_length=1, max_length=240)
    max_top_level_navigations: Literal[1] = 1
    subresource_rule: Literal["same_origin_safe_methods"] = "same_origin_safe_methods"
    max_subresources: int = Field(ge=0, le=40)
    max_resource_bytes: int = Field(ge=1, le=1_048_576)
    max_total_bytes: int = Field(ge=1, le=5_242_880)
    timeout_seconds: int = Field(ge=1, le=15)


ActionDraft = Annotated[HttpActionDraft | BrowserActionDraft, Field(discriminator="kind")]


class ProposeActionBatchDecision(FrozenModel):
    kind: Literal["propose_action_batch"] = "propose_action_batch"
    purpose: str = Field(min_length=1, max_length=240)
    actions: tuple[ActionDraft, ...] = Field(min_length=1, max_length=4)


class ProposeConclusionDecision(FrozenModel):
    kind: Literal["propose_conclusion"] = "propose_conclusion"
    proposal: ConclusionDraft


class PauseDecision(FrozenModel):
    kind: Literal["pause"] = "pause"
    safe_reason_code: Literal[
        "needs_researcher_input",
        "insufficient_evidence",
        "model_uncertain",
    ]


class ListSavedEndpointsDecision(FrozenModel):
    kind: Literal["list_saved_endpoints"] = "list_saved_endpoints"


class RetrieveSavedEndpointDecision(FrozenModel):
    kind: Literal["retrieve_saved_endpoint"] = "retrieve_saved_endpoint"
    memory_id: UUID


class CompareSavedEndpointsDecision(FrozenModel):
    kind: Literal["compare_saved_endpoints"] = "compare_saved_endpoints"
    left_memory_id: UUID
    right_memory_id: UUID


ModelDecision = Annotated[
    UpdatePlanDecision
    | UpdateHypothesisDecision
    | ProposeActionBatchDecision
    | ProposeConclusionDecision
    | PauseDecision
    | ListSavedEndpointsDecision
    | RetrieveSavedEndpointDecision
    | CompareSavedEndpointsDecision,
    Field(discriminator="kind"),
]


class ModelDecisionRequest(FrozenModel):
    investigation_id: UUID
    objective: SanitizedText
    steering_messages: tuple[SanitizedText, ...]
    scope_summary: SanitizedPayload
    identity_labels: tuple[SanitizedText, ...]
    current_plan: Plan | None
    hypotheses: tuple[Hypothesis, ...]
    evidence_summaries: tuple[SanitizedPayload, ...]
    memory_summaries: tuple[SanitizedPayload, ...]
    recent_events: tuple[SanitizedPayload, ...]
    decision_number: int = Field(ge=1, le=24)


class ModelDecisionEnvelope(FrozenModel):
    decision: ModelDecision


class ModelProvider(Protocol):
    def decide(self, request: ModelDecisionRequest) -> ModelDecision:
        raise NotImplementedError


class ModelProviderError(RuntimeError):
    pass


class ModelRefusal(ModelProviderError):
    pass


class ModelOutputInvalid(ModelProviderError):
    pass


class TransientModelProviderError(ModelProviderError):
    pass


class PermanentModelProviderError(ModelProviderError):
    pass


class ScriptExhausted(ModelProviderError):
    pass


class ScriptedModelProvider:
    def __init__(self, decisions: Iterable[ModelDecision | BaseException]):
        self._decisions = iter(decisions)
        self.requests: list[ModelDecisionRequest] = []

    def decide(self, request: ModelDecisionRequest) -> ModelDecision:
        self.requests.append(request)
        try:
            item = next(self._decisions)
        except StopIteration as error:
            raise ScriptExhausted("no scripted decision remains") from error
        if isinstance(item, BaseException):
            raise item
        return item


class ModelContextBuilder:
    def __init__(self, repository: CaseRepository, memory: CaseMemoryRepository, budgets: BudgetLedger):
        self._repository = repository
        self._memory = memory
        self._budgets = budgets

    def build(self, investigation_id: UUID) -> ModelDecisionRequest:
        investigation = self._repository.get_investigation(investigation_id)
        return ModelDecisionRequest(
            investigation_id=investigation.id,
            objective=investigation.objective,
            steering_messages=self._repository.list_sanitized_messages(investigation_id, limit=8),
            scope_summary=self._repository.get_sanitized_scope_summary(investigation.active_scope_snapshot_id),
            identity_labels=self._repository.list_verified_identity_labels(investigation_id),
            current_plan=self._repository.get_current_plan(investigation_id),
            hypotheses=self._repository.list_hypotheses(investigation_id),
            evidence_summaries=self._repository.list_sanitized_evidence_summaries(investigation_id, limit=12),
            memory_summaries=self._memory.model_summaries(
                investigation_id, endpoint_limit=12, comparison_limit=6
            ),
            recent_events=self._repository.list_sanitized_event_summaries(investigation_id, limit=20),
            decision_number=self._budgets.snapshot(investigation_id).model_decisions + 1,
        )
```

Task 18 adds the exact bounded read methods used above to `CaseRepository`: `list_sanitized_messages(investigation_id, limit)`, `get_sanitized_scope_summary(scope_snapshot_id)`, `list_verified_identity_labels(investigation_id)`, `get_current_plan(investigation_id)`, `list_hypotheses(investigation_id)`, `list_sanitized_evidence_summaries(investigation_id, limit)`, `list_sanitized_event_summaries(investigation_id, limit)`, and `record_passive_memory_result(investigation_id, kind, payload)`. Every read verifies investigation ownership, uses a deterministic order, enforces the supplied hard maximum in SQL, and returns only branded values. `record_passive_memory_result` accepts only kind `list` or `retrieve`, a sealed payload produced by `CaseMemoryRepository`, and appends `memory.updated`; it has no worker or credential dependency. Contract tests inspect each DTO for forbidden raw/header/body/secret/mode fields.

- [ ] **Step 4: Implement the provider with Responses structured parsing**

```python
class OpenAIProviderSettings(FrozenModel):
    model_id: str
    reasoning_effort: Literal["medium"] = "medium"
    store: Literal[False] = False
    api_contract_revision: Literal["responses-structured-output-v1"] = "responses-structured-output-v1"


class OpenAIModelProvider:
    def decide(self, request: ModelDecisionRequest) -> ModelDecision:
        last_error: ModelProviderError | None = None
        for attempt in (1, 2):
            self._budgets.charge_provider_call(request.investigation_id)
            capability = self._vault.issue_provider_call_capability(
                self._provider_key_ref,
                provider_call_number=self._budgets.snapshot(request.investigation_id).provider_calls,
                expires_at=self._clock.now() + timedelta(seconds=30),
            )
            try:
                with self._provider_credentials.read(capability) as lease:
                    client = self._client_factory(api_key=lease.reveal_for_provider_call())
                    response = client.responses.parse(
                        model=self._settings.model_id,
                        input=self._prompts.messages_for(request, correction=(attempt == 2)),
                        text_format=ModelDecisionEnvelope,
                        reasoning={"effort": self._settings.reasoning_effort},
                        store=self._settings.store,
                    )
                if response.refusal:
                    raise ModelRefusal("provider_refusal")
                if response.output_parsed is None:
                    raise ModelOutputInvalid("missing_parsed_output")
                self._budgets.charge_model_decision(request.investigation_id)
                return response.output_parsed.decision
            except ModelRefusal:
                raise
            except (ModelOutputInvalid, ValidationError) as error:
                last_error = ModelOutputInvalid("invalid_structured_output")
            except TRANSIENT_OPENAI_EXCEPTIONS as error:
                last_error = TransientModelProviderError(type(error).__name__)
            except OpenAIError as error:
                raise PermanentModelProviderError(type(error).__name__) from error
            if attempt == 2:
                raise last_error
        raise AssertionError("unreachable")
```

Set `TRANSIENT_OPENAI_EXCEPTIONS` exactly to `(APITimeoutError, APIConnectionError, RateLimitError, InternalServerError)`; all other `OpenAIError` subclasses are permanent, refusal is never retried, and only structured-output/validation failure receives the correction prompt on attempt two. Exception messages are never copied into an event; only the closed safe codes shown above cross the provider boundary. Keep `investigation_id` as a UUID, not secret data, because the budget charge needs it. Provider API-key access is a separate namespace and authority from target identity-secret access: `OpenAIModelProvider.decide` mints a one-use `ProviderCallCapability` immediately before each SDK attempt and passes it only to `ProviderCredentialSource`; it may do so during planning without a live-action approval. HTTP/Browser workers cannot receive that source. Conversely, only the execution gateway can mint `ExecutionSecretCapability` after policy/approval/budget checks, and the model provider cannot receive `TargetCredentialSource`. Charge `provider_calls` before each SDK attempt; a missing/refused/invalid response consumes that call but not a valid model decision. After strict parsing succeeds, charge `model_decisions` before returning the decision. A retry never invokes the gateway and consumes a second provider-call unit; either ceiling pauses the investigation.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/runtime/test_model_provider.py tests/contracts/test_model_boundary.py -v
python -m pytest tests/runtime tests/contracts -q
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/runtime tests/runtime tests/contracts
git diff --check
git add pyproject.toml bugintel/cases/repository.py bugintel/cases/memory.py bugintel/runtime/context.py bugintel/runtime/prompts.py bugintel/runtime/model_provider.py tests/runtime/test_model_provider.py tests/contracts/test_model_boundary.py
git commit -m "feat: add sanitized OpenAI reasoning boundary"
```

### Task 19: Close the Headless Investigation Loop

**Files:**
- Create: `bugintel/runtime/investigator.py`
- Create: `tests/runtime/test_investigator.py`

**Interfaces:**
- Consumes: `CaseRepository`, `ModelProvider`, `ApprovalService`, `ExecutionGateway`, `IdentityVerifier`, `ConclusionValidator`, and `IngressFirewall`.
- Produces: `InvestigatorController.step`, `run_until_boundary`, `ControllerOutcome`, and the full service-owned state flow.

- [ ] **Step 1: Write the end-to-end headless state test with a scripted provider**

```python
def test_controller_reaches_approval_then_conclusion(harness) -> None:
    investigation = harness.create_verified_investigation(mode=LabMode.VULNERABLE)
    first = harness.controller.run_until_boundary(investigation.id)
    assert first.kind == "waiting_approval"
    assert harness.repository.get_investigation(investigation.id).state == InvestigationState.WAITING_APPROVAL

    harness.approve(first.approval_request_id)
    second = harness.controller.run_until_boundary(investigation.id)
    assert second.kind == "completed"
    assert second.conclusion.verdict == Verdict.SUPPORTED
```

Use this exact controller boundary matrix:

```python
@pytest.mark.parametrize(
    ("scenario", "boundary", "state", "verdict"),
    [
        ("secure", "completed", InvestigationState.COMPLETED, Verdict.REJECTED),
        ("ambiguous", "completed", InvestigationState.COMPLETED, Verdict.INCONCLUSIVE),
        ("invalid_model_transition", "paused", InvestigationState.PAUSED, None),
        ("model_decision_exhausted", "paused", InvestigationState.PAUSED, None),
        ("step_limit", "paused", InvestigationState.PAUSED, None),
        ("approval_rejected", "paused", InvestigationState.PAUSED, None),
        ("approval_expired", "paused", InvestigationState.PAUSED, None),
        ("approval_exhausted", "paused", InvestigationState.PAUSED, None),
        ("policy_block", "paused", InvestigationState.PAUSED, None),
        ("model_refusal", "paused", InvestigationState.PAUSED, None),
        ("provider_failure_after_retry", "paused", InvestigationState.PAUSED, None),
        ("adapter_failure", "paused", InvestigationState.PAUSED, None),
        ("redaction_failure", "paused", InvestigationState.PAUSED, None),
        ("persistence_failure", "failed", InvestigationState.FAILED, None),
    ],
)
def test_controller_boundary_matrix(harness, scenario, boundary, state, verdict) -> None:
    investigation = harness.create_scenario(scenario)
    outcome = harness.run_with_automatic_researcher_decisions(investigation.id)
    assert outcome.kind == boundary
    assert harness.repository.get_investigation(investigation.id).state == state
    assert (outcome.conclusion.verdict if outcome.conclusion else None) == verdict
    assert harness.secret_canary not in harness.persisted_events_json(investigation.id)


def test_double_persistence_failure_escapes_as_literal_safe_code(harness) -> None:
    harness.fail_primary_and_emergency_persistence()
    with pytest.raises(SafePersistenceFailure, match="^persistence_failure$"):
        harness.controller.run_until_boundary(harness.investigation_id)
    assert harness.model_provider.requests == []
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/runtime/test_investigator.py -v
```

Expected: missing controller.

- [ ] **Step 3: Implement one-decision `step` and boundary loop**

```python
def step(self, investigation_id: UUID) -> ControllerOutcome:
    investigation = self._cases.get_investigation(investigation_id)
    if investigation.state.is_terminal or investigation.state == InvestigationState.PAUSED:
        return ControllerOutcome.from_state(investigation)
    if investigation.state == InvestigationState.WAITING_APPROVAL:
        lookup = self._approvals.lookup_pending_approval(investigation_id, now=self._clock.now())
        if lookup.state == "pending":
            return ControllerOutcome.waiting_for_existing_approval(investigation_id)
        if lookup.state != "granted" or lookup.grant_id is None:
            event_type = (
                EventType.APPROVAL_REJECTED
                if lookup.state == "rejected"
                else EventType.APPROVAL_EXPIRED
            )
            return self._errors.pause(
                investigation_id,
                reason_code=f"approval_{lookup.state}",
                event_type=event_type,
            )
        self._gateway.execute_batch(investigation_id, lookup.grant_id)
        return ControllerOutcome(kind="continue")
    request = self._context.build(investigation_id)
    decision = self._provider.decide(request)
    return self._apply_decision(investigation, decision)


def run_until_boundary(self, investigation_id: UUID) -> ControllerOutcome:
    try:
        segment_id = self._budgets.begin_active_segment(investigation_id, now=self._clock.now())
    except CONTROLLER_BOUNDARY_ERRORS as error:
        return self._errors.handle(investigation_id, error)
    try:
        outcome = self._run_active_loop(investigation_id)
    except CONTROLLER_BOUNDARY_ERRORS as error:
        outcome = self._errors.handle(investigation_id, error)
    try:
        self._budgets.end_active_segment(investigation_id, segment_id, now=self._clock.now())
    except CONTROLLER_BOUNDARY_ERRORS as error:
        return self._errors.handle(investigation_id, error)
    return outcome


def _run_active_loop(self, investigation_id: UUID) -> ControllerOutcome:
    for _ in range(24):
        self._budgets.check_active_deadline(investigation_id, now=self._clock.now())
        outcome = self.step(investigation_id)
        if outcome.kind in {"waiting_approval", "paused", "completed", "stopped", "failed"}:
            return outcome
    self._cases.pause(investigation_id, reason="step_limit")
    return ControllerOutcome(kind="paused", reason="step_limit")
```

The waiting-approval branch never asks the model again: `pending` returns the existing boundary; `rejected`, `expired`, `exhausted`, or `missing` appends the matching safe approval/lifecycle event and pauses; `granted` executes the exact pending batch, whose gateway performs the one final `EXECUTING -> OBSERVING` transition after all outcome commits. The next loop iteration builds model context from the new evidence and durable case memory, and the controller does not perform that transition a second time. `run_until_boundary` opens a persisted active segment before its loop and closes it through the error router; Task 10's computed `active_deadline` is the authoritative remaining investigation deadline. `ModelContextBuilder.build` always includes bounded endpoint/comparison summaries. `_apply_decision` wires passive decisions exactly: `list_saved_endpoints` records `memory.model_summaries(...)`; `retrieve_saved_endpoint` calls `memory.retrieve(investigation_id, memory_id)` and records its sealed allowlisted model payload; `compare_saved_endpoints` calls `memory.compare(investigation_id, left_id, right_id)`. The next context sees the resulting `memory.updated` event/comparison. These operations require no approval and cannot call a worker or credential source. Every returned model string is untrusted; `_apply_decision` passes it through `RedactionPolicy` and obtains a sealed `SanitizedText` before constructing or persisting a domain model/event. It converts `ConclusionDraft` into `ConclusionProposal` only after sanitizing rationale/next step; factual claims are closed service-owned codes. A detector match pauses with a safe category and never persists the raw model value. Plan/hypothesis changes append their matching events. A `ProposeActionBatchDecision` carries only drafts, so after sanitization the service generates each action UUID, validates the current identity/profile, evaluates every action against the active scope, derives `max_request_count` and `max_total_bytes`, fixes `batch_timeout_seconds=60` and expiry at `min(now + 5 minutes, BudgetLedger.active_deadline(...))`, and calls `ActionBatch.create`. If any pre-approval policy decision blocks, persist `policy.blocked` and pause; otherwise persist each `policy.allowed`, `tool.proposed`, and `approval.requested`, then move to `WAITING_APPROVAL` without executing. Contract tests reject any model fields named `id`, `digest`, `scope_digest`, `approval`, `approved`, `executed`, `state`, `credential`, or arbitrary headers/body/script. A conclusion proposal always passes through `ConclusionValidator` before `investigation.completed`. Every service mutation from Tasks 16-20 appends the matching exact `EventType`, including identity, message, memory, approval, policy, lifecycle, and tool outcomes.

```python
def _apply_passive_memory_decision(self, investigation_id: UUID, decision: ModelDecision) -> bool:
    if isinstance(decision, ListSavedEndpointsDecision):
        summaries = self._memory.model_summaries(
            investigation_id, endpoint_limit=12, comparison_limit=6
        )
        payload = self._redaction.sanitize_payload({
            "items": [item.model_dump(mode="json") for item in summaries]
        })
        self._cases.record_passive_memory_result(investigation_id, "list", payload)
        return True
    if isinstance(decision, RetrieveSavedEndpointDecision):
        payload = self._memory.model_payload(investigation_id, decision.memory_id)
        self._cases.record_passive_memory_result(investigation_id, "retrieve", payload)
        return True
    if isinstance(decision, CompareSavedEndpointsDecision):
        self._memory.compare(
            investigation_id, decision.left_memory_id, decision.right_memory_id
        )
        return True
    return False
```

`_apply_decision` calls this helper before any live-action branch and returns `ControllerOutcome(kind="continue")` when it returns true. Tests assert all three decisions perform zero gateway, worker, approval, and credential calls; cross-investigation IDs pause with `memory_boundary_error`.

Define `CONTROLLER_BOUNDARY_ERRORS` and `ControllerErrorRouter` exactly:

```python
CONTROLLER_BOUNDARY_ERRORS = (
    ExecutionBlocked,
    ApprovalExpired,
    ApprovalRejected,
    ApprovalConsumed,
    BudgetExceeded,
    ModelRefusal,
    ModelOutputInvalid,
    TransientModelProviderError,
    PermanentModelProviderError,
    ScriptExhausted,
    SanitizedToolFailure,
    ResourceInterrupted,
    RedactionFailure,
    MemoryBoundaryError,
    PersistenceError,
)
```

The closed mapping is: `ExecutionBlocked -> (policy.blocked, policy_blocked)`, `ApprovalExpired -> (approval.expired, approval_expired)`, `ApprovalRejected -> (approval.rejected, approval_rejected)`, `ApprovalConsumed -> (approval.expired, approval_exhausted)`, `BudgetExceeded -> (investigation.paused, the exception's closed BudgetReason enum)`, `ModelRefusal -> (investigation.paused, model_refusal)`, `ModelOutputInvalid/TransientModelProviderError/PermanentModelProviderError/ScriptExhausted -> (investigation.paused, model_provider_error)`, `SanitizedToolFailure/ResourceInterrupted -> (tool.failed or tool.interrupted, tool_failure)`, `RedactionFailure -> (investigation.paused, redaction_failure)`, and `MemoryBoundaryError -> (investigation.paused, memory_boundary_error)`. `handle` writes only the mapped event/reason and a `PAUSED` projection in one transaction, never exception text. `PersistenceError`—including its `SanitizedPersistenceError` subtype—uses a fresh emergency transaction to append `investigation.failed` with `persistence_failure` and set `FAILED`; if that also fails it raises `SafePersistenceFailure("persistence_failure")` to the launcher, which logs only that literal and never builds model context. No other exception is swallowed.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/runtime/test_investigator.py -v
python -m pytest tests/runtime tests/policy tests/cases tests/lab_scenarios -q
git diff --check
git add bugintel/runtime/investigator.py tests/runtime/test_investigator.py
git commit -m "feat: close the headless investigation loop"
```

### Task 20: Add Stop, Steering, Restart, and Orphan Recovery

**Files:**
- Create: `bugintel/runtime/recovery.py`
- Modify: `bugintel/runtime/investigator.py`
- Create: `tests/runtime/test_recovery.py`

**Interfaces:**
- Consumes: durable events/tool rows, safe-boundary controller, ingress firewall, and approval invalidation.
- Produces: `RecoveryService.reconcile`, `request_stop`, `resume`, `submit_message`, and `edit_objective`.

- [ ] **Step 1: Write crash and safe-boundary tests**

```python
def test_reconcile_marks_started_tool_interrupted_without_worker_call(harness) -> None:
    tool_run = harness.insert_orphaned_started_tool()
    harness.recovery.reconcile()
    assert harness.repository.get_tool_run(tool_run.id).state == ToolRunState.INTERRUPTED
    assert harness.worker.calls == []


def test_objective_edit_waits_for_active_tool_and_invalidates_grants(harness) -> None:
    investigation = harness.executing_investigation()
    harness.controller.edit_objective(investigation.id, "compare order access only")
    assert harness.repository.get_investigation(investigation.id).pending_objective is not None
    harness.finish_active_tool_as_interrupted()
    assert harness.repository.get_investigation(investigation.id).state == InvestigationState.PLANNING
    assert harness.approvals.unconsumed_for(investigation.id) == []
```

Use this exact recovery/control matrix:

```python
@pytest.mark.parametrize("case", [
    "durable_stop_before_signal", "new_start_after_stop", "stop_reaches_terminal",
    "resume_paused_to_planning", "resume_expires_grant", "secret_bearing_steering",
])
def test_recovery_and_control_matrix(harness, case) -> None:
    result = harness.exercise_control(case)
    assert result.expected_state_reached is True
    assert result.unexpected_worker_starts == 0
    assert harness.secret_canary not in result.persisted_json
    assert harness.secret_canary not in result.event_json


def test_projection_corruption_blocks_startup(harness) -> None:
    investigation = harness.completed_investigation()
    harness.database.execute_for_test(
        "UPDATE investigation_projections SET state='planning' WHERE id=?",
        (str(investigation.id),),
    )
    with pytest.raises(ProjectionIntegrityError):
        harness.recovery.reconcile()
    assert harness.worker.calls == []
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/runtime/test_recovery.py -v
```

Expected: missing recovery service/methods.

- [ ] **Step 3: Implement reconciliation and controller controls**

```python
def reconcile(self) -> RecoveryReport:
    with self._database.transaction() as connection:
        orphaned = self._cases.list_tool_runs(connection, state=ToolRunState.STARTED)
        for run in orphaned:
            self._cases.mark_interrupted_and_pause(
                connection,
                run.id,
                run.investigation_id,
                reason="service_restart",
            )
        self._budgets.close_orphaned_active_segments(connection, now=self._clock.now())
        self._cases.rebuild_and_verify_projections(connection)
    return RecoveryReport(interrupted_tool_ids=tuple(run.id for run in orphaned))
```

`mark_interrupted_and_pause` appends both tool/lifecycle events and updates both projections in the same transaction. `rebuild_and_verify_projections` replays ordered lifecycle/tool events into memory, compares every durable projection, and raises `ProjectionIntegrityError` without starting the controller if any value differs. `request_stop` commits stop intent before signalling the shared `StopSignal`, blocks new gateway starts, and ends with investigation `STOPPED`; any uncertain active tool becomes `INTERRUPTED`. `resume` accepts only `PAUSED`, invalidates expired grants, and returns to `PLANNING`. `submit_message` and `edit_objective` call `IngressFirewall.inspect` before any persistence.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/runtime/test_recovery.py tests/runtime/test_investigator.py -v
python -m pytest tests/runtime tests/cases tests/policy -q
git diff --check
git add bugintel/runtime/recovery.py bugintel/runtime/investigator.py tests/runtime/test_recovery.py
git commit -m "feat: recover investigations without replay"
```

### Task 21: Add the Fully Intercepted Playwright Worker

**Files:**
- Modify: `pyproject.toml`
- Create: `bugintel/tools/browser.py`
- Create: `tests/tools/test_browser.py`
- Create: `tests/lab_scenarios/test_browser_gateway.py`

**Interfaces:**
- Consumes: gateway capability, route authorizer, target credential source, budget ledger, sanitizer, and in-memory `FrameSink`.
- Produces: `BrowserToolWorker.run(capability) -> SanitizedToolOutcome`; inject `FrameSink` into the worker constructor so it conforms to the gateway's `ToolWorker` protocol.

- [ ] **Step 1: Bound the browser dependency and write isolation tests**

Change the existing browser extra to:

```toml
"playwright>=1.62.1,<2.0",
```

Write tests around an injected fake Playwright driver:

```python
def test_browser_context_is_ephemeral_and_locked_down(worker, fake_playwright, capability) -> None:
    worker.run(capability)
    options = fake_playwright.context_options
    assert options["service_workers"] == "block"
    assert options["accept_downloads"] is False
    assert options["java_script_enabled"] is False
    assert options["permissions"] == []
    assert options["storage_state"] is None


def test_every_request_is_authorized_before_continue(worker, fake_playwright, capability) -> None:
    fake_playwright.queue_request("http://127.0.0.1:9090/escape", method="GET")
    worker.run(capability)
    assert fake_playwright.last_route_action == "abort"


def test_initial_document_uses_existing_reservation(worker, fake_playwright, capability, ledger) -> None:
    before = ledger.request_count(capability.investigation_id)
    fake_playwright.queue_document(capability.canonical_action.url)
    worker.run(capability)
    assert ledger.request_count(capability.investigation_id) == before


@pytest.mark.parametrize(
    ("case", "expected_action"),
    [
        ("account-a-context", "fulfill"),
        ("account-b-context", "fulfill"),
        ("popup", "close"),
        ("download", "cancel"),
        ("websocket", "close"),
        ("service-worker", "block"),
        ("cross-origin-resource", "abort"),
        ("post-resource", "abort"),
        ("fortieth-subresource", "abort"),
        ("resource-over-1-mib", "abort"),
        ("navigation-over-5-mib", "abort"),
        ("after-15-second-deadline", "abort"),
    ],
)
def test_browser_boundary_matrix(browser_harness, case, expected_action) -> None:
    result = browser_harness.run(case)
    assert result.route_action == expected_action
    assert result.raw_html_persisted is False
    assert result.storage_state_persisted is False
    assert result.network_log_persisted is False


def test_snapshot_buffer_is_erased_after_frame_delivery(browser_harness) -> None:
    result = browser_harness.run("snapshot")
    assert result.frame_sink_deliveries == 1
    assert result.worker_snapshot_buffer == bytearray(len(result.delivered_frame))
```

`browser_harness.run(case)` uses two fixed identity capabilities and an injected bounded transport. It asserts one top-level navigation, no proxy, no persistent profile, and one additional ledger reservation for every fulfilled subresource. The initial document uses the reservation already made by `execute_batch`. Each permitted subresource has an independent 1 MiB decompressed ceiling, charges streamed chunks into the navigation's 5 MiB total, and aborts before fulfillment when either ceiling would be crossed.

- [ ] **Step 2: Install Chromium and observe missing implementation**

```powershell
python -m pip install -e ".[dev,browser]"
python -m playwright install chromium
python -m pytest tests/tools/test_browser.py tests/lab_scenarios/test_browser_gateway.py -v
```

Expected: missing browser worker.

- [ ] **Step 3: Implement locked-down context and routing**

```python
browser = playwright.chromium.launch(
    headless=True,
    args=[
        "--no-proxy-server",
        "--disable-extensions",
        "--disable-background-networking",
        "--disable-component-update",
        "--disable-default-apps",
        "--disable-sync",
        "--metrics-recording-only",
        "--no-first-run",
        "--host-resolver-rules=MAP * ~NOTFOUND",
    ],
)
context = browser.new_context(
    accept_downloads=False,
    java_script_enabled=False,
    service_workers="block",
    permissions=[],
    storage_state=None,
)
context.route("**/*", lambda route, request: self._intercept_and_fulfill(capability, route, request))
page = context.new_page()
page.on("popup", lambda popup: popup.close())
page.route_web_socket("**/*", lambda socket: socket.close())
```

Chromium is never allowed to connect directly to the lab, and JavaScript is disabled for the alpha. `_intercept_and_fulfill` aborts non-HTTP(S), WebSockets, popups, downloads, disallowed methods, cross-origin URLs, and every resource kind except `document`, `stylesheet`, `image`, and `font`. Its entire callback is wrapped in `try/except BaseException`; an exception attempts `route.abort("blockedbyclient")`, records only a safe failure code, and never falls through to continuation. For the first main-frame document it uses the existing capability and reservation. For every later document redirect or subresource it calls `authorize_browser_request`; a rejected child is aborted before any socket opens. The interceptor then uses the same fresh-client, `trust_env=False`, no-cookie-jar, absolute-deadline bounded transport primitive built in Task 15, reads at most 1 MiB decompressed per resource and 5 MiB across the navigation, and calls `route.fulfill` with only status, allowlisted `content-type`/`cache-control`, a newly computed `content-length`, and bounded bytes. It never forwards `Set-Cookie`, `Content-Encoding`, credentials, arbitrary response headers, or a body over the remaining allowance. A redirect is handled as another gateway-authorized candidate rather than by Playwright or `httpx` auto-following it. Zero the mutable response buffer immediately after `route.fulfill`; the browser receives no unmediated target response.

Before `page.goto`, revalidate the exact top-level URL, issue the target credential capability, and prepare authentication headers inside the bounded transport only. Take only an in-memory JPEG/PNG snapshot for `FrameSink`, clear its `bytearray` after delivery, and close the identity-specific context in `finally`. Derive evidence from the bounded, sanitized transport subset, never DOM/HTML, storage state, console output, or network logs.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/tools/test_browser.py tests/lab_scenarios/test_browser_gateway.py -v
python -m pytest tests/tools tests/policy tests/lab_scenarios -q
git diff --check
git add pyproject.toml bugintel/tools/browser.py tests/tools/test_browser.py tests/lab_scenarios/test_browser_gateway.py
git commit -m "feat: add intercepted local browser worker"
```

### Task 22: Add the Sanitized Case Exporter

**Files:**
- Create: `bugintel/cases/export.py`
- Create: `tests/cases/test_export.py`

**Interfaces:**
- Consumes: database-listed sanitized project/investigation/event/evidence/conclusion rows.
- Produces: `CaseExporter.export(investigation_id, output_directory) -> ExportManifest` and one UUID-named ZIP.

- [ ] **Step 1: Write allowlist, traversal, collision, and manifest tests**

```python
def test_export_contains_only_fixed_members(exporter, investigation_id, tmp_path) -> None:
    result = exporter.export(investigation_id, tmp_path)
    with ZipFile(result.path) as archive:
        assert set(archive.namelist()) == {
            "case.json",
            "events.jsonl",
            "evidence.jsonl",
            "conclusion.json",
            "manifest.json",
        }


def test_manifest_is_recomputed_from_written_members(exporter, investigation_id, tmp_path) -> None:
    result = exporter.export(investigation_id, tmp_path)
    assert verify_export(result.path).valid is True
    assert result.manifest.record_count == actual_record_count(result.path)
```

Use this exact export-safety matrix:

```python
def test_immediate_exports_are_uuid_named_and_distinct(exporter, investigation_id, tmp_path) -> None:
    first = exporter.export(investigation_id, tmp_path)
    second = exporter.export(investigation_id, tmp_path)
    assert first.path != second.path
    UUID(first.path.stem)
    UUID(second.path.stem)


@pytest.mark.parametrize("member", [
    "../escape", "/absolute", "C:/absolute", "nested/../../escape",
    "legacy_artifact.json", "case.db", "raw-response.bin", "link",
])
def test_export_builder_rejects_non_allowlisted_member(export_harness, member) -> None:
    with pytest.raises(ExportIntegrityError):
        export_harness.build_with_extra_member(member, symlink=(member == "link"))


def test_publish_refuses_existing_name_and_database_directory(export_harness) -> None:
    with pytest.raises(FileExistsError):
        export_harness.publish_to_preexisting_destination()
    with pytest.raises(ExportPathError):
        export_harness.publish_inside_database_directory()
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/cases/test_export.py -v
```

Expected: missing exporter.

- [ ] **Step 3: Implement fixed-member construction and atomic no-overwrite publication**

```python
MEMBERS = (
    "case.json",
    "events.jsonl",
    "evidence.jsonl",
    "conclusion.json",
    "manifest.json",
)


def _publish_without_overwrite(temp_path: Path, final_path: Path) -> None:
    os.link(temp_path, final_path)
    temp_path.unlink()
```

Build member bytes only from repository methods returning sanitized records. Hash the exact non-manifest bytes, write those members, write `manifest.json`, reopen the temporary ZIP, reject any member outside `MEMBERS`, recompute hashes/counts, then use a same-directory hard link for atomic no-overwrite publication. On any error, delete the temporary file and leave no final file.

- [ ] **Step 4: Run the agent-loop completion gate and commit**

```powershell
python -m pytest tests/cases tests/policy tests/runtime tests/tools tests/contracts tests/lab_scenarios -q
python -m coverage run --branch --source=bugintel.cases,bugintel.policy,bugintel.runtime,bugintel.tools -m pytest tests/cases tests/policy tests/runtime tests/tools tests/contracts tests/lab_scenarios
python -m coverage report --fail-under=90
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases bugintel/policy bugintel/runtime bugintel/tools lab tests/cases tests/policy tests/runtime tests/tools tests/contracts tests/lab_scenarios
python -m ruff format --check bugintel/cases bugintel/policy bugintel/runtime bugintel/tools lab tests/cases tests/policy tests/runtime tests/tools tests/contracts tests/lab_scenarios
git diff --check
git add bugintel/cases/export.py tests/cases/test_export.py
git commit -m "feat: export sanitized investigation bundles"
```

## Agent Loop Completion Gate

Run the included lab in each hidden mode through `ScriptedModelProvider` and the real HTTP gateway. The gate requires exact `supported`, `rejected`, and `inconclusive` outcomes; zero unapproved or out-of-scope attempts; zero secret canaries in all persisted/model-visible surfaces; no worker import outside the gateway; at least 90% new-runtime branch coverage; and 100% branch coverage for policy, approval, secret, evidence, and conclusion validation.

Record the critical-module result separately so aggregate coverage cannot hide a missed branch:

```powershell
python -m coverage run --branch --source=bugintel.policy.scope,bugintel.policy.approval,bugintel.cases.secrets,bugintel.cases.redaction,bugintel.cases.evidence,bugintel.runtime.conclusion -m pytest tests/policy/test_scope.py tests/policy/test_approval.py tests/cases/test_secrets.py tests/cases/test_redaction.py tests/cases/test_evidence.py tests/runtime/test_conclusion.py
python -m coverage report --fail-under=100
git status --short
```

The worktree must be clean before starting the Workbench plan.
