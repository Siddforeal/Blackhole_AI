# Blackhole Web/API Investigator Workbench Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deliver the authenticated local Codex-style workbench for creating, steering, approving, observing, stopping, resuming, and completing the controlled-lab investigation.

**Architecture:** A FastAPI service bound only to `127.0.0.1` exposes authenticated REST and fetch-streamed `text/event-stream` endpoints over the SQLite-backed controller. A React/TypeScript single-page app holds its bearer token only in memory, renders all untrusted strings as escaped text, and shows only real Browser and Evidence panels backed by the completed agent loop.

**Tech Stack:** FastAPI 0.141, Uvicorn 0.52, Pydantic, React 19.2, TypeScript 7, Vite 8, Vitest 4, Testing Library, Playwright Test, and Node 24.

## Global Constraints

- Complete the Foundation and Agent Loop plans with clean gates before this plan.
- Implement only on `codex/web-api-investigator-alpha`; do not push, merge, tag, release, bump version `1.84.1`, open a pull request, or add release notes without separate researcher authorization.
- Bind production only to `127.0.0.1`; expose no remote-listen option, permissive CORS, wildcard host, or query-string credential.
- Static shell/assets and the single-use bootstrap exchange are the only unauthenticated surfaces. Every case API and event stream requires an in-memory bearer token.
- Bootstrap nonce: 32 random bytes, base64url, fragment only, stored server-side as SHA-256, 60-second expiry, atomic single use, rate limited, and never logged.
- Session token: 32 random bytes, response body only, frontend/server memory only, 30-minute idle expiry, eight-hour absolute expiry, cleared on service restart, and never placed in a cookie, URL, localStorage, sessionStorage, IndexedDB, log, event, or database.
- Every state-changing route requires an exact workbench `Origin`; validate `Host`; serve a restrictive CSP; use no native `EventSource` because it cannot attach the authorization header.
- FastAPI request models containing provider or identity secrets are write-only and never reused as response models. API responses never contain a secret value, raw target data, fixture oracle, hidden lab mode, or model chain-of-thought.
- The SQLite event store is the only history source. Streaming may wake readers but cannot own or invent state; commit events before notifying clients.
- Target DOM/HTML/JavaScript never executes in the workbench origin. Render untrusted text through normal React text nodes; never use `dangerouslySetInnerHTML`.
- Browser frames are bounded in-memory image bytes served through an authenticated endpoint, converted to a temporary blob URL, and revoked after replacement/unmount. They are never persisted or evidence.
- Do not show fake Burp, Terminal, mobile, multi-agent, or external-target controls. The active right panel contains Browser and Evidence only.
- Keep each UI component focused and accessible: semantic controls, keyboard focus, status text, labels, and visible approval/stop state.
- Node must satisfy `>=22.12.0`; commit `.nvmrc` with `24` and the generated `package-lock.json`.

---

## File Structure

```text
bugintel/workbench/
  __init__.py
  app.py
  auth.py
  launcher.py
  services.py
  supervisor.py
  event_stream.py
  browser_view.py
  api/
    __init__.py
    dependencies.py
    schemas.py
    bootstrap.py
    projects.py
    scopes.py
    identities.py
    investigations.py
    messages.py
    actions.py
    evidence.py
    conclusions.py
    exports.py
    browser.py
    events.py
  static/                 # generated production assets; populated in Hardening
tools/export_openapi.py
web/
  .nvmrc
  package.json
  package-lock.json
  index.html
  tsconfig.json
  vite.config.ts
  vitest.config.ts
  openapi.json
  src/
    main.tsx
    App.tsx
    api/
    state/
    components/
    styles/
  e2e/
tests/workbench/
```

---

### Task 23: Add Secure Bootstrap, Session Authentication, and the Local Launcher

**Files:**
- Modify: `pyproject.toml`
- Create: `bugintel/workbench/__init__.py`
- Create: `bugintel/workbench/auth.py`
- Create: `bugintel/workbench/services.py`
- Create: `bugintel/workbench/app.py`
- Create: `bugintel/workbench/launcher.py`
- Create: `bugintel/workbench/api/__init__.py`
- Create: `bugintel/workbench/api/dependencies.py`
- Create: `bugintel/workbench/api/bootstrap.py`
- Create: `tests/workbench/conftest.py`
- Create: `tests/workbench/test_auth.py`
- Create: `tests/workbench/test_app_security.py`
- Create: `tests/workbench/test_launcher.py`

**Interfaces:**
- Consumes: assembled repositories/controller/gateway/vault through `WorkbenchServices`, injected UTC/monotonic clocks, and injected randomness.
- Produces: `WorkbenchAuthority`, `SessionManager.create_bootstrap`, `exchange`, `authenticate`, `create_app(services, sessions, static_dir, authority)`, and `blackhole-workbench` entry point.

- [ ] **Step 1: Write nonce, token, and cross-port leakage tests**

```python
def test_bootstrap_is_single_use_and_expires_after_60_seconds(clock, sessions) -> None:
    bootstrap = sessions.create_bootstrap()
    token = sessions.exchange(bootstrap.nonce)
    assert sessions.authenticate(token.value).authenticated is True
    with pytest.raises(BootstrapRejected):
        sessions.exchange(bootstrap.nonce)
    clock.advance(seconds=61)
    expired = sessions.create_bootstrap()
    clock.advance(seconds=61)
    with pytest.raises(BootstrapRejected):
        sessions.exchange(expired.nonce)


def test_exchange_sets_no_cookie_and_token_never_appears_in_url(client, bootstrap) -> None:
    response = client.post(
        "/api/bootstrap/exchange",
        json={"nonce": bootstrap.nonce},
        headers={"Origin": "http://127.0.0.1:8765"},
    )
    assert "set-cookie" not in response.headers
    assert response.json()["session_token"] not in str(response.request.url)


def test_concurrent_exchange_has_exactly_one_winner(sessions, bootstrap) -> None:
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: capture_exchange(sessions, bootstrap.nonce), range(2)))
    assert sum(result.succeeded for result in results) == 1


@pytest.mark.parametrize("path", ["/docs", "/redoc", "/openapi.json"])
def test_framework_documentation_surfaces_are_disabled(client, path) -> None:
    assert client.get(path).status_code == 404


@pytest.mark.parametrize(
    ("headers", "expected_status"),
    [
        ({"Host": "127.0.0.1:9999", "Origin": "http://127.0.0.1:8765"}, 400),
        ({"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:9999"}, 403),
        ({"Host": "127.0.0.1:8765"}, 403),
    ],
)
def test_bootstrap_exchange_rejects_wrong_authority(client, bootstrap, headers, expected_status) -> None:
    response = client.post("/api/bootstrap/exchange", json={"nonce": bootstrap.nonce}, headers=headers)
    assert response.status_code == expected_status


@pytest.mark.parametrize("query", ["key=x", "token=x", "session=x", "auth=x", "ToKeN=x"])
def test_credential_like_query_parameters_are_rejected(client, query) -> None:
    response = client.get(f"/?{query}", headers={"Host": "127.0.0.1:8765"})
    assert response.status_code == 400


def test_session_idle_absolute_and_restart_boundaries(clock, sessions, random_bytes) -> None:
    idle = sessions.exchange(sessions.create_bootstrap().nonce).value
    clock.advance(minutes=30)
    with pytest.raises(SessionRejected, match="expired"):
        sessions.authenticate(idle)

    absolute = sessions.exchange(sessions.create_bootstrap().nonce).value
    for _ in range(15):
        clock.advance(minutes=29)
        sessions.authenticate(absolute)
    clock.advance(minutes=45)
    with pytest.raises(SessionRejected, match="expired"):
        sessions.authenticate(absolute)

    restarted = SessionManager(clock=clock, random_bytes=random_bytes)
    with pytest.raises(SessionRejected, match="invalid"):
        restarted.authenticate(absolute)


def test_diagnostics_and_security_headers_contain_no_secrets(client, sessions, bootstrap, caplog) -> None:
    response = client.post(
        "/api/bootstrap/exchange",
        json={"nonce": bootstrap.nonce},
        headers={"Host": "127.0.0.1:8765", "Origin": "http://127.0.0.1:8765"},
    )
    token = response.json()["session_token"]
    diagnostic = repr(sessions.diagnostic_state())
    captured = caplog.text
    assert bootstrap.nonce not in diagnostic + captured
    assert token not in diagnostic + captured
    assert "set-cookie" not in response.headers
    assert "access-control-allow-origin" not in response.headers
    assert response.headers["cache-control"] == "no-store"
    assert "default-src 'self'" in response.headers["content-security-policy"]
```

`tests/workbench/conftest.py` fixes `WorkbenchAuthority(port=8765)`, creates `TestClient(app, base_url="http://127.0.0.1:8765")`, injects `FakeClock`, deterministic 32-byte `random_bytes`, a temporary static directory containing only `index.html`, and defines `capture_exchange` as a `try/except BootstrapRejected` wrapper returning `ExchangeAttempt(succeeded: bool)`. It also mounts a test-only `/api/_protected` route with `Depends(require_session)`; the matrix below is executable through that route:

```python
@pytest.mark.parametrize(
    ("authorization", "status"),
    [(None, 401), ("Bearer invalid", 401), ("Basic abc", 401)],
)
def test_protected_dependency_rejects_absent_or_invalid_bearer(protected_client, authorization, status) -> None:
    headers = {} if authorization is None else {"Authorization": authorization}
    assert protected_client.get("/api/_protected", headers=headers).status_code == status


def test_static_shell_is_public_but_contains_no_case_data(client) -> None:
    response = client.get("/", headers={"Host": "127.0.0.1:8765"})
    assert response.status_code == 200
    assert response.text == "<main id=\"root\"></main>"
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/workbench/test_auth.py tests/workbench/test_app_security.py tests/workbench/test_launcher.py -v
```

Expected: missing workbench package.

- [ ] **Step 3: Implement hash-only bootstrap and memory-only sessions**

```python
class WorkbenchAuthority(FrozenModel):
    host: Literal["127.0.0.1"] = "127.0.0.1"
    port: int = Field(ge=1, le=65535)

    @property
    def origin(self) -> str:
        return f"http://{self.host}:{self.port}"

    @property
    def host_header(self) -> str:
        return f"{self.host}:{self.port}"


class Clock(Protocol):
    def now(self) -> datetime:
        raise NotImplementedError


class BootstrapSecret(FrozenModel):
    nonce: str = Field(min_length=43, max_length=43, repr=False)


class SessionSecret(FrozenModel):
    value: str = Field(min_length=43, max_length=43, repr=False)


class SessionRecord(FrozenModel):
    issued_at: AwareDatetime
    last_seen_at: AwareDatetime

    @classmethod
    def create(cls, now: datetime) -> "SessionRecord":
        return cls(issued_at=now, last_seen_at=now)


class AuthenticatedSession(FrozenModel):
    authenticated: Literal[True] = True
    issued_at: AwareDatetime
    session_digest: bytes = Field(repr=False)


class SessionManager:
    NONCE_TTL = timedelta(seconds=60)
    IDLE_TTL = timedelta(minutes=30)
    ABSOLUTE_TTL = timedelta(hours=8)

    def __init__(self, clock: Clock, random_bytes: Callable[[int], bytes]):
        self._clock = clock
        self._random_bytes = random_bytes
        self._lock = threading.Lock()
        self._failed_exchanges: deque[datetime] = deque(maxlen=5)
        self._sessions: dict[bytes, SessionRecord] = {}
        self._bootstrap_hash: bytes | None = None
        self._bootstrap_expires_at: datetime | None = None

    def create_bootstrap(self) -> BootstrapSecret:
        nonce = urlsafe_b64encode(self._random_bytes(32)).rstrip(b"=").decode("ascii")
        with self._lock:
            self._bootstrap_hash = sha256(nonce.encode("ascii")).digest()
            self._bootstrap_expires_at = self._clock.now() + self.NONCE_TTL
        return BootstrapSecret(nonce=nonce)

    def exchange(self, nonce: str) -> SessionSecret:
        with self._lock:
            self._prune_failed_exchanges()
            if len(self._failed_exchanges) >= 5:
                raise BootstrapRejected("bootstrap rate limited")
            candidate = sha256(nonce.encode("ascii")).digest()
            if self._bootstrap_hash is None or not compare_digest(candidate, self._bootstrap_hash):
                self._failed_exchanges.append(self._clock.now())
                raise BootstrapRejected("invalid bootstrap")
            if self._bootstrap_expires_at is None or self._clock.now() >= self._bootstrap_expires_at:
                self._consume_bootstrap()
                raise BootstrapRejected("expired bootstrap")
            self._consume_bootstrap()
            token = urlsafe_b64encode(self._random_bytes(32)).rstrip(b"=").decode("ascii")
            self._sessions[sha256(token.encode("ascii")).digest()] = SessionRecord.create(self._clock.now())
            self._failed_exchanges.clear()
            return SessionSecret(value=token)

    def authenticate(self, token: str) -> AuthenticatedSession:
        candidate = sha256(token.encode("ascii", errors="ignore")).digest()
        with self._lock:
            matched = next((digest for digest in self._sessions if compare_digest(candidate, digest)), None)
            record = None if matched is None else self._sessions[matched]
            now = self._clock.now()
            if record is None:
                raise SessionRejected("invalid")
            if now - record.last_seen_at >= self.IDLE_TTL or now - record.issued_at >= self.ABSOLUTE_TTL:
                del self._sessions[matched]
                raise SessionRejected("expired")
            self._sessions[matched] = record.model_copy(update={"last_seen_at": now})
            return AuthenticatedSession(authenticated=True, issued_at=record.issued_at, session_digest=matched)

    def validate(self, session: AuthenticatedSession) -> None:
        with self._lock:
            record = self._sessions.get(session.session_digest)
            now = self._clock.now()
            if record is None or now - record.last_seen_at >= self.IDLE_TTL or now - record.issued_at >= self.ABSOLUTE_TTL:
                self._sessions.pop(session.session_digest, None)
                raise SessionRejected("expired")

    def diagnostic_state(self) -> dict[str, int | bool]:
        with self._lock:
            return {"bootstrap_configured": self._bootstrap_hash is not None, "session_count": len(self._sessions)}

    def _prune_failed_exchanges(self) -> None:
        boundary = self._clock.now() - timedelta(seconds=60)
        while self._failed_exchanges and self._failed_exchanges[0] <= boundary:
            self._failed_exchanges.popleft()

    def _consume_bootstrap(self) -> None:
        self._bootstrap_hash = None
        self._bootstrap_expires_at = None

    def clear(self) -> None:
        with self._lock:
            self._bootstrap_hash = None
            self._bootstrap_expires_at = None
            self._failed_exchanges.clear()
            self._sessions.clear()
```

Never add `__repr__` or logging that prints `BootstrapSecret`/`SessionSecret`. Mark their Pydantic fields `repr=False`.

- [ ] **Step 4: Implement security middleware and sole unauthenticated API route**

`create_app` constructs `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` and receives the exact `WorkbenchAuthority` selected by the launcher. Register the bootstrap and authenticated API routers first, mount only `static/assets` at `/assets`, and register `GET /` last to return `static/index.html`; never mount the whole static directory at `/`, because that would shadow `/api`. Middleware requires `Host == authority.host_header`, requires `Origin == authority.origin` for every state-changing request including bootstrap exchange, rejects any query parameter whose lowercase key is `key`, `token`, `session`, or `auth`, and attaches:

```python
CONTENT_SECURITY_POLICY = (
    "default-src 'self'; script-src 'self'; style-src 'self'; "
    "img-src 'self' blob:; connect-src 'self'; object-src 'none'; "
    "frame-src 'none'; base-uri 'none'; form-action 'none'"
)
```

The exchange route is `POST /api/bootstrap/exchange`, permits at most five failed exchange attempts in a rolling 60-second process-local window, and returns `{session_token, idle_expires_in_seconds, absolute_expires_in_seconds}` without setting a cookie. A successful exchange atomically consumes the nonce before creating the session and clears failure history. Middleware applies `Cache-Control: no-store`, `Pragma: no-cache`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, and the CSP to bootstrap and authenticated API responses. Validation and exception handlers return only `{error_code, correlation_id}` and never echo request bodies, URLs, secrets, or exception text. Uvicorn runs with `access_log=False`; the app's structured logger records only method, templated route name, status, correlation ID, and safe error code after redaction. Tests send canaries in malformed JSON/query/error paths and assert absence from captured stdout/stderr/log records.

Use these exact dependency boundaries so later routers cannot bypass authentication or origin validation:

```python
def require_session(
    authorization: Annotated[str | None, Header()] = None,
    sessions: SessionManager = Depends(get_sessions),
) -> AuthenticatedSession:
    scheme, separator, value = (authorization or "").partition(" ")
    if separator != " " or scheme != "Bearer" or not value:
        raise HTTPException(status_code=401, detail="unauthorized")
    return sessions.authenticate(value)


def require_exact_origin(
    request: Request,
    authority: WorkbenchAuthority = Depends(get_authority),
) -> None:
    if request.headers.get("origin") != authority.origin:
        raise HTTPException(status_code=403, detail="origin_rejected")


Authenticated = Annotated[AuthenticatedSession, Depends(require_session)]
ExactOrigin = Annotated[None, Depends(require_exact_origin)]
```

- [ ] **Step 5: Implement launcher socket ownership and script entry point**

Open and bind an IPv4 socket to `("127.0.0.1", 0)` before application assembly, derive `WorkbenchAuthority(port=socket.getsockname()[1])`, pass that authority to `create_app`, pass the already-bound socket to Uvicorn to avoid a port-selection race, create a bootstrap, and open:

```python
url = f"http://127.0.0.1:{port}/#bootstrap={quote(bootstrap.nonce, safe='')}"
webbrowser.open(url)
```

Do not accept a `--host` option. Add to `pyproject.toml` without changing the version:

```toml
blackhole-workbench = "bugintel.workbench.launcher:main"
```

`WorkbenchServices` is an immutable composition object containing the already-built Foundation/Agent Loop services. `launcher.main` selects `%LOCALAPPDATA%/Blackhole/cases.db` on Windows or `$XDG_DATA_HOME/blackhole/cases.db` (falling back to `~/.local/share/blackhole/cases.db`) with owner-only directory permissions, opens/migrates it, validates the OS keyring/provider-key reference, calls `RecoveryService.reconcile()`, resolves packaged `bugintel.workbench/static` with `importlib.resources`, and installs an app lifespan that closes workers/sessions/database state. Tasks 24-27 extend the composition root when their setup, result, frame, and event services exist. No plaintext provider-key CLI flag exists; setup uses `python -m bugintel.workbench.launcher configure-provider-key`, which prompts with `getpass`, writes to the provider namespace, and prints only the opaque reference.

`blackhole-workbench --check` performs offline static/migration/keyring readiness and exits without binding or opening a browser. `--check-browser` additionally launches/closes Chromium and emits the exact install command when absent. Production starts Uvicorn with access logs disabled and the already-bound socket.

The composition and launcher use these exact callable interfaces; `build_services` is the only function allowed to construct adapters:

```python
@dataclass(frozen=True, slots=True)
class WorkbenchServices:
    database: Database
    cases: CaseRepository
    events: EventStore
    evidence: EvidenceRepository
    memory: CaseMemoryRepository
    vault: KeyringCredentialVault
    provider_credentials: ProviderCredentialSource
    credentials: TargetCredentialSource
    scope_policy: ScopePolicy
    budgets: BudgetLedger
    approvals: ApprovalService
    result_sanitizer: ResultSanitizer
    http_worker: HttpToolWorker
    browser_worker: BrowserToolWorker
    gateway: ExecutionGateway
    controller: InvestigatorController
    recovery: RecoveryService
    identity_verifier: IdentityVerifier
    conclusion_validator: ConclusionValidator
    model_provider: OpenAIModelProvider
    exporter: CaseExporter
    ingress: IngressFirewall


def build_services(database_path: Path, provider_ref: SecretRef) -> WorkbenchServices:
    database = Database.open(database_path)
    events = EventStore(database)
    cases = CaseRepository(database=database, events=events)
    memory = CaseMemoryRepository(database=database, events=events)
    vault = KeyringCredentialVault.open()
    provider_credentials = vault.provider_source()
    target_credentials = vault.target_source()
    matcher = vault.secret_matcher()
    redaction = RedactionPolicy(configured_secret_matcher=matcher)
    ingress = IngressFirewall(matcher=matcher, policy=redaction)
    scope_policy = ScopePolicy()
    budgets = BudgetLedger(database=database, scope_repository=cases, clock=SystemClock())
    approvals = ApprovalService(database=database, repository=cases, clock=SystemClock())
    semantic_extractor = LabSemanticExtractor()
    result_sanitizer = ResultSanitizer(
        redaction_policy=redaction,
        configured_secret_matcher=matcher,
        semantic_extractor=semantic_extractor,
        max_excerpt_bytes=2_000,
    )
    evidence = EvidenceRepository(
        database=database,
        events=events,
        memory=memory,
    )
    stop_signal = DurableStopSignal(cases)
    gateway = ExecutionGateway.unsealed(
        database=database,
        repository=cases,
        evidence=evidence,
        scope_policy=scope_policy,
        budgets=budgets,
        approvals=approvals,
        credential_vault=vault,
        workers={},
        clock=SystemClock(),
    )
    http_worker = HttpToolWorker(
        target_credentials=target_credentials,
        sanitizer=result_sanitizer,
        budgets=budgets,
        redirect_authorizer=gateway,
        stop_signal=stop_signal,
    )
    browser_worker = BrowserToolWorker(
        target_credentials=target_credentials,
        sanitizer=result_sanitizer,
        budgets=budgets,
        route_authorizer=gateway,
        stop_signal=stop_signal,
        frame_sink=DiscardingFrameSink(),
    )
    gateway.install_registry_once({
        "http_request": http_worker,
        "browser_navigation": browser_worker,
    })
    identity_verifier = IdentityVerifier(
        cases=cases,
        approvals=approvals,
        redaction=redaction,
        lab_subject_validator=LabSubjectValidator(),
        clock=SystemClock(),
    )
    conclusion_validator = ConclusionValidator(
        repository=cases,
        fixture_oracle=FixtureOracle(),
        redaction=redaction,
    )
    model_provider = OpenAIModelProvider(
        settings=OpenAIProviderSettings(model_id="gpt-5.6-sol"),
        provider_key_ref=provider_ref,
        vault=vault,
        provider_credentials=provider_credentials,
        budgets=budgets,
        prompts=InvestigatorPrompts(),
        client_factory=OpenAI,
        clock=SystemClock(),
    )
    controller = InvestigatorController(
        cases=cases,
        memory=memory,
        context=ModelContextBuilder(repository=cases, memory=memory, budgets=budgets),
        model_provider=model_provider,
        approvals=approvals,
        gateway=gateway,
        identity_verifier=identity_verifier,
        conclusion_validator=conclusion_validator,
        ingress=ingress,
        redaction=redaction,
        budgets=budgets,
        clock=SystemClock(),
    )
    recovery = RecoveryService(
        database=database,
        cases=cases,
        approvals=approvals,
        budgets=budgets,
        stop_signal=stop_signal,
        clock=SystemClock(),
    )
    return WorkbenchServices(
        database=database, cases=cases, events=events, evidence=evidence, memory=memory,
        vault=vault, provider_credentials=provider_credentials, credentials=target_credentials,
        scope_policy=scope_policy, budgets=budgets, approvals=approvals,
        result_sanitizer=result_sanitizer, http_worker=http_worker,
        browser_worker=browser_worker, gateway=gateway, controller=controller,
        recovery=recovery, identity_verifier=identity_verifier,
        conclusion_validator=conclusion_validator, model_provider=model_provider,
        exporter=CaseExporter(cases=cases, events=events, evidence=evidence), ingress=ingress,
    )


def create_app(
    services: WorkbenchServices,
    sessions: SessionManager,
    static_dir: Traversable,
    authority: WorkbenchAuthority,
) -> FastAPI:
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    app.state.services = services
    app.state.sessions = sessions
    app.state.authority = authority
    app.add_middleware(WorkbenchSecurityMiddleware, authority=authority)
    app.include_router(bootstrap_router())
    app.mount("/assets", StaticFiles(directory=static_dir.joinpath("assets")), name="assets")
    app.add_api_route("/", lambda: FileResponse(static_dir.joinpath("index.html")), methods=["GET"])
    return app
def run_server(sock: socket.socket, app: FastAPI) -> None:
    uvicorn.Server(uvicorn.Config(app, access_log=False)).run(sockets=[sock])
```

- [ ] **Step 6: Verify and commit**

```powershell
python -m pytest tests/workbench/test_auth.py tests/workbench/test_app_security.py tests/workbench/test_launcher.py -v
python -m pytest tests/workbench tests/runtime tests/policy tests/cases -q
git diff --check
git add pyproject.toml bugintel/workbench tests/workbench/test_auth.py tests/workbench/test_app_security.py tests/workbench/test_launcher.py
git commit -m "feat: secure the local workbench session"
```

### Task 24: Add Project, Scope, Identity, Investigation, and Message APIs

**Files:**
- Modify: `bugintel/workbench/services.py`
- Create: `bugintel/workbench/api/schemas.py`
- Create: `bugintel/workbench/api/projects.py`
- Create: `bugintel/workbench/api/scopes.py`
- Create: `bugintel/workbench/api/identities.py`
- Create: `bugintel/workbench/api/investigations.py`
- Create: `bugintel/workbench/api/messages.py`
- Modify: `bugintel/workbench/app.py`
- Create: `tests/workbench/test_projects_api.py`
- Create: `tests/workbench/test_scope_identity_api.py`
- Create: `tests/workbench/test_investigations_api.py`
- Create: `tests/workbench/test_messages_api.py`

**Interfaces:**
- Consumes: repositories, `ScopePolicy`, credential vault, `IdentityVerifier`, controller/supervisor, ingress firewall, and authenticated/exact-origin dependencies.
- Produces: typed REST routes for the first half of the approved local API.

The exact route surface is:

```text
GET  /api/projects
POST /api/projects
GET  /api/projects/{project_id}
POST /api/projects/{project_id}/scopes
POST /api/projects/{project_id}/identities
PUT  /api/identities/{identity_id}/secret
POST /api/projects/{project_id}/investigations
GET  /api/investigations/{investigation_id}
POST /api/investigations/{investigation_id}/messages
GET  /api/investigations/{investigation_id}/plan
GET  /api/investigations/{investigation_id}/hypotheses
POST /api/investigations/{investigation_id}/identity-preflight
```

- [ ] **Step 1: Write authentication and response-secrecy tests**

```python
def test_every_case_route_requires_bearer(client) -> None:
    for method, path in [
        ("GET", "/api/projects"),
        ("POST", "/api/projects"),
        ("GET", "/api/projects/00000000-0000-0000-0000-000000000001"),
        ("POST", "/api/projects/00000000-0000-0000-0000-000000000001/scopes"),
        ("POST", "/api/projects/00000000-0000-0000-0000-000000000001/identities"),
        ("POST", "/api/projects/00000000-0000-0000-0000-000000000001/investigations"),
    ]:
        assert client.request(method, path).status_code == 401


def test_identity_secret_is_write_only(auth_client, project) -> None:
    response = auth_client.post(
        f"/api/projects/{project.id}/identities",
        json={"label": "Account A", "origin": "http://127.0.0.1:8080", "header_profile": "bearer_token", "secret": "canary-secret"},
    )
    assert response.status_code == 201
    assert "canary-secret" not in response.text
    assert "secret" not in response.json()


@pytest.mark.parametrize(
    "payload",
    [
        {"origin": "http://localhost:8080", "path_prefix": "/api/", "methods": ["GET"]},
        {"origin": "http://127.0.0.1:8080", "path_prefix": "/", "methods": ["POST"]},
        {"origin": "http://127.0.0.1:8080", "path_prefix": "/api/../admin", "methods": ["GET"]},
        {"origin": "https://example.com", "path_prefix": "/api/", "methods": ["GET"]},
    ],
)
def test_scope_api_rejects_non_lab_or_unsafe_forms(auth_client, project, payload) -> None:
    assert auth_client.post(f"/api/projects/{project.id}/scopes", json=payload).status_code == 422


def test_replacing_identity_secret_increments_version_without_returning_either_value(auth_client, identity) -> None:
    response = auth_client.put(
        f"/api/identities/{identity.id}/secret",
        json={"secret": "replacement-canary"},
    )
    assert response.status_code == 200
    assert response.json()["secret_version"] == identity.secret_version + 1
    assert "replacement-canary" not in response.text


@pytest.mark.parametrize("size,status", [(8192, 201), (8193, 422)])
def test_message_utf8_limit_is_exact(auth_client, investigation, size, status) -> None:
    body = "x" * size
    response = auth_client.post(f"/api/investigations/{investigation.id}/messages", json={"content": body})
    assert response.status_code == status


```

The request matrix additionally asserts: every mutation with a missing or wrong `Origin` returns `403`; configured-secret ingress returns `422` with `error_code == "configured_secret_rejected"`; the persisted message contains only that safe category; and identity-preflight creation returns a waiting-approval batch containing exactly two `GET /api/whoami` actions and performs zero network calls.

- [ ] **Step 2: Run and confirm missing routers**

```powershell
python -m pytest tests/workbench/test_projects_api.py tests/workbench/test_scope_identity_api.py tests/workbench/test_investigations_api.py tests/workbench/test_messages_api.py -v
```

Expected: 404 or import failures.

- [ ] **Step 3: Define separate request and response schemas**

```python
class IdentitySecretCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    label: str = Field(min_length=1, max_length=80)
    origin: str
    header_profile: Literal["session_cookie", "bearer_token"]
    secret: SecretStr


class IdentityResponse(FrozenModel):
    id: UUID
    label: str
    origin: str
    header_profile: str
    secret_version: int
    verified_subject_id: str | None
    verification_evidence_id: UUID | None


class ProjectCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=120)


class ScopeCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    origin: AnyHttpUrl
    path_prefix: str = Field(min_length=1, max_length=256)
    methods: frozenset[Literal["GET", "HEAD", "OPTIONS"]]


class InvestigationCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective: str = Field(min_length=1, max_length=8192)
    identity_ids: tuple[UUID, UUID]


class MessageCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    content: str = Field(min_length=1, max_length=8192)


class ObjectiveEdit(BaseModel):
    model_config = ConfigDict(extra="forbid")
    objective: str = Field(min_length=1, max_length=8192)
```

Define response-only frozen DTOs with the exact persisted public fields: `ProjectResponse(id, name, created_at)`, `ScopeResponse(id, project_id, origin, path_prefix, methods, digest)`, `InvestigationResponse(id, project_id, objective, identity_ids, state, created_at, updated_at)`, and `MessageResponse(id, investigation_id, role, content: SanitizedText, created_at)`. Do not inherit a response model from a secret-bearing request model.

- [ ] **Step 4: Implement routes through the setup service only**

Every route requires `Authenticated`; mutation routes also require `ExactOrigin`. Routers accept models and return response DTOs; they do not access SQLite or adapters. Secret routes call `SecretStr.get_secret_value()` once at the `WorkbenchSetupService` vault boundary, overwrite the local reference after storing, and return only `IdentityResponse`. Message routes call the ingress firewall before `append_message`.

Approved identity verification uses two calls: create/write identities, then `POST /api/investigations/{id}/identity-preflight` to create the exact batch; the user grants that batch through Task 25.

The composition service has these exact signatures:

```python
class WorkbenchSetupService(Protocol):
    def list_projects(self) -> tuple[Project, ...]: ...
    def create_project(self, body: ProjectCreate) -> Project: ...
    def get_project(self, project_id: UUID) -> Project: ...
    def create_scope(self, project_id: UUID, body: ScopeCreate) -> ScopeSnapshot: ...
    def create_identity(self, project_id: UUID, body: IdentitySecretCreate, plaintext: str) -> IdentityRef: ...
    def replace_identity_secret(self, identity_id: UUID, plaintext: str) -> IdentityRef: ...
    def create_investigation(self, project_id: UUID, body: InvestigationCreate) -> Investigation: ...
    def get_investigation(self, investigation_id: UUID) -> Investigation: ...
    def append_message(self, investigation_id: UUID, content: SanitizedText) -> Message: ...
    def get_plan(self, investigation_id: UUID) -> Plan | None: ...
    def list_hypotheses(self, investigation_id: UUID) -> tuple[Hypothesis, ...]: ...
```

Task 24 adds `setup: WorkbenchSetupService` to `WorkbenchServices` and constructs its concrete implementation from the existing repository, vault, scope policy, approval service, and ingress firewall.

The route wiring is exact:

| Route | Service call | Response/status |
|---|---|---|
| `GET /api/projects` | `setup.list_projects()` | `list[ProjectResponse]`, 200 |
| `POST /api/projects` | `setup.create_project(body)` | `ProjectResponse`, 201 |
| `GET /api/projects/{project_id}` | `setup.get_project(project_id)` | `ProjectResponse`, 200 |
| `POST /api/projects/{project_id}/scopes` | `setup.create_scope(project_id, body)` | `ScopeResponse`, 201 |
| `POST /api/projects/{project_id}/identities` | `setup.create_identity(project_id, body, plaintext)` | `IdentityResponse`, 201 |
| `PUT /api/identities/{identity_id}/secret` | `setup.replace_identity_secret(identity_id, plaintext)` | `IdentityResponse`, 200 |
| `POST /api/projects/{project_id}/investigations` | `setup.create_investigation(project_id, body)` | `InvestigationResponse`, 201 |
| `GET /api/investigations/{investigation_id}` | `setup.get_investigation(investigation_id)` | `InvestigationResponse`, 200 |
| `POST /api/investigations/{investigation_id}/messages` | `decision = ingress.inspect(body.content)`; reject with safe category or `setup.append_message(investigation_id, decision.sanitized_text)` | `MessageResponse`, 201 or safe 422 |
| `GET /api/investigations/{investigation_id}/plan` | `setup.get_plan(investigation_id)` | `PlanResponse`, 200 or 404 |
| `GET /api/investigations/{investigation_id}/hypotheses` | `setup.list_hypotheses(investigation_id)` | `list[HypothesisResponse]`, 200 |
| `POST /api/investigations/{investigation_id}/identity-preflight` | `identity_verifier.propose_preflight(investigation_id)` | `ActionBatchResponse`, 201 |

The secret handler is implemented exactly at the boundary:

```python
@router.post("/api/projects/{project_id}/identities", response_model=IdentityResponse, status_code=201)
def create_identity(
    project_id: UUID,
    body: IdentitySecretCreate,
    _: Authenticated,
    __: ExactOrigin,
    services: WorkbenchServices = Depends(get_services),
) -> IdentityResponse:
    plaintext = body.secret.get_secret_value()
    try:
        identity = services.setup.create_identity(project_id, body, plaintext)
    finally:
        plaintext = ""
    return IdentityResponse.model_validate(identity)


@router.post("/api/investigations/{investigation_id}/identity-preflight", response_model=ActionBatchResponse, status_code=201)
def create_identity_preflight(
    investigation_id: UUID,
    _: Authenticated,
    __: ExactOrigin,
    services: WorkbenchServices = Depends(get_services),
) -> ActionBatchResponse:
    batch = services.identity_verifier.propose_preflight(investigation_id)
    return ActionBatchResponse.from_domain(batch)
```

Register `projects`, `scopes`, `identities`, `investigations`, and `messages` routers exactly once in `create_app`.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/workbench/test_projects_api.py tests/workbench/test_scope_identity_api.py tests/workbench/test_investigations_api.py tests/workbench/test_messages_api.py -v
python -m pytest tests/workbench tests/runtime tests/cases tests/policy -q
git diff --check
git add bugintel/workbench/services.py bugintel/workbench/api bugintel/workbench/app.py tests/workbench/test_projects_api.py tests/workbench/test_scope_identity_api.py tests/workbench/test_investigations_api.py tests/workbench/test_messages_api.py
git commit -m "feat: expose controlled investigation setup API"
```

### Task 25: Add Action, Approval, Steering, Stop, and Resume APIs

**Files:**
- Modify: `bugintel/policy/approval.py`
- Modify: `bugintel/workbench/services.py`
- Create: `bugintel/workbench/supervisor.py`
- Create: `bugintel/workbench/api/actions.py`
- Modify: `bugintel/workbench/api/investigations.py`
- Modify: `bugintel/workbench/app.py`
- Create: `tests/workbench/test_actions_api.py`
- Create: `tests/workbench/test_controls_api.py`

**Interfaces:**
- Consumes: controller, approval service, gateway, recovery controls, and per-investigation single-flight supervisor.
- Produces: action-batch preview, approve/edit/reject, start/advance, stop, resume, and objective-edit APIs.

- [ ] **Step 1: Write exact-preview and single-flight tests**

```python
def test_action_preview_contains_every_approval_binding(auth_client, pending_batch) -> None:
    preview = auth_client.get(f"/api/action-batches/{pending_batch.id}").json()
    assert set(preview) >= {
        "id", "digest", "scope_digest", "actions", "identity_labels",
        "purpose", "max_request_count", "batch_timeout_seconds",
        "max_total_bytes", "approval_expires_at", "expected_evidence",
    }


def test_edit_creates_new_digest_and_cannot_reuse_grant(auth_client, granted_batch) -> None:
    edited = auth_client.post(
        f"/api/action-batches/{granted_batch.id}/edit",
        json={
            "expected_digest": granted_batch.digest,
            "purpose": "compare only order 1048",
            "actions": [action.model_dump(mode="json") for action in granted_batch.actions],
        },
    ).json()
    assert edited["digest"] != granted_batch.digest
    assert edited["status"] == "waiting_approval"


@pytest.mark.parametrize(
    ("operation", "fixture_name", "expected_status", "expected_batch_status"),
    [
        ("approve", "expired_batch", 409, "expired"),
        ("approve", "granted_batch", 409, "granted"),
        ("reject", "pending_batch", 200, "rejected"),
        ("approve_without_origin", "pending_batch", 403, "waiting_approval"),
    ],
)
def test_approval_transition_matrix(request, auth_client, operation, fixture_name, expected_status, expected_batch_status) -> None:
    batch = request.getfixturevalue(fixture_name)
    headers = {"Origin": ""} if operation == "approve_without_origin" else {"Origin": WORKBENCH_ORIGIN}
    verb = "approve" if operation == "approve_without_origin" else operation
    response = auth_client.post(
        f"/api/action-batches/{batch.id}/{verb}",
        json={"digest": batch.digest},
        headers=headers,
    )
    assert response.status_code == expected_status
    assert auth_client.get(f"/api/action-batches/{batch.id}").json()["status"] == expected_batch_status


def test_concurrent_advance_has_one_accepted_request(auth_client, investigation, blocking_controller) -> None:
    path = f"/api/investigations/{investigation.id}/advance"
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = sorted(pool.map(lambda _: auth_client.post(path).status_code, range(2)))
    assert statuses == [202, 409]
    blocking_controller.release()


def test_stop_during_tool_is_durable_and_resume_is_explicit(auth_client, active_tool_investigation) -> None:
    investigation = active_tool_investigation
    assert auth_client.post(f"/api/investigations/{investigation.id}/stop").status_code == 202
    investigation.wait_until_idle()
    assert investigation.event_types[-2:] == ["tool.interrupted", "investigation.stopped"]
    assert auth_client.post(f"/api/investigations/{investigation.id}/advance").status_code == 409
    assert auth_client.post(f"/api/investigations/{investigation.id}/resume").status_code == 200
    assert investigation.reload().state == "planning"


def test_objective_edit_invalidates_pending_approval(auth_client, investigation, pending_batch) -> None:
    response = auth_client.patch(
        f"/api/investigations/{investigation.id}/objective",
        json={"objective": "Compare only order 1048"},
    )
    assert response.status_code == 200
    assert auth_client.get(f"/api/action-batches/{pending_batch.id}").json()["status"] == "superseded"
```

`blocking_controller` uses two `threading.Event` objects: `advance()` sets `entered`, waits on `release`, and returns `ControllerOutcome(state=InvestigationState.PLANNING)`. `active_tool_investigation` exposes `wait_until_idle()`, `event_types`, and `reload()` over the real SQLite repositories plus a gateway worker that waits for its cancellation token. A separate parameterized control test asserts `resume` returns `409` from `planning`, `waiting_approval`, and `complete`; only `paused` returns `200` and becomes `planning`.

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/workbench/test_actions_api.py tests/workbench/test_controls_api.py -v
```

Expected: missing routes/supervisor.

- [ ] **Step 3: Implement a per-investigation single-flight supervisor**

```python
class FailureRecorder(Protocol):
    def record_interrupted(self, investigation_id: UUID, safe_code: str) -> None:
        raise NotImplementedError

    def record_failed(self, investigation_id: UUID, safe_code: str) -> None:
        raise NotImplementedError


class InvestigationSupervisor:
    def __init__(self, failures: FailureRecorder) -> None:
        self._failures = failures
        self._tasks: dict[UUID, asyncio.Task[ControllerOutcome]] = {}

    def start(self, investigation_id: UUID, factory: Callable[[], ControllerOutcome]) -> None:
        active = self._tasks.get(investigation_id)
        if active is not None and not active.done():
            raise InvestigationAlreadyRunning(investigation_id)
        task = asyncio.create_task(asyncio.to_thread(factory))
        self._tasks[investigation_id] = task
        task.add_done_callback(lambda finished: self._finish(investigation_id, finished))

    def _finish(self, investigation_id: UUID, finished: asyncio.Task[ControllerOutcome]) -> None:
        try:
            finished.result()
        except asyncio.CancelledError:
            self._failures.record_interrupted(investigation_id, "controller_cancelled")
        except Exception:
            self._failures.record_failed(investigation_id, "controller_failed")
        finally:
            self._tasks.pop(investigation_id, None)

    async def request_stop(self, investigation_id: UUID, recovery: RecoveryService, gateway: ExecutionGateway) -> None:
        await asyncio.to_thread(recovery.request_stop, investigation_id)
        gateway.request_cancellation(investigation_id)

    async def shutdown(self, recovery: RecoveryService, gateway: ExecutionGateway) -> None:
        active = tuple(self._tasks)
        for investigation_id in active:
            await self.request_stop(investigation_id, recovery, gateway)
        if not self._tasks:
            return
        _, pending = await asyncio.wait(tuple(self._tasks.values()), timeout=15.0)
        for task in pending:
            investigation_id = next(key for key, value in self._tasks.items() if value is task)
            self._failures.record_interrupted(investigation_id, "shutdown_timeout")
```

`FailureRecorder` exposes only `record_interrupted(investigation_id, safe_code)` and `record_failed(investigation_id, safe_code)`; it persists the corresponding sanitized event without receiving the exception object. The callback consumes every task result so asyncio never logs raw exception context.

`InvestigationSupervisor.request_stop` first calls the synchronous controller's durable `request_stop`, then signals the gateway's thread-safe cancellation token for that investigation. HTTP checks it between streamed chunks; Playwright route/resource callbacks check it before continuation. Never call `Task.cancel()` on the `to_thread` wrapper: cooperative cancellation owns the worker lifetime. `_finish` removes ownership only after the worker actually returns. Shutdown records a sanitized `shutdown_timeout` for any thread still active after 15 seconds and process teardown performs no further action starts.

- [ ] **Step 4: Implement exact action/control routes**

Provide authenticated/exact-origin routes:

```text
GET  /api/action-batches/{batch_id}
POST /api/action-batches/{batch_id}/approve
POST /api/action-batches/{batch_id}/edit
POST /api/action-batches/{batch_id}/reject
POST /api/investigations/{investigation_id}/advance
POST /api/investigations/{investigation_id}/stop
POST /api/investigations/{investigation_id}/resume
PATCH /api/investigations/{investigation_id}/objective
```

Approval delegates to `ApprovalService`; advance delegates to the supervisor/controller; no route calls an adapter. Editing reconstructs and revalidates a new strict batch rather than patching canonical JSON.

Use exact status codes and dependencies:

```python
@router.post("/api/action-batches/{batch_id}/approve", response_model=ActionBatchResponse)
def approve_batch(
    batch_id: UUID,
    body: ApprovalDecision,
    _: Authenticated,
    __: ExactOrigin,
    services: WorkbenchServices = Depends(get_services),
) -> ActionBatchResponse:
    return services.controls.grant_batch(batch_id, body.digest)


@router.post("/api/investigations/{investigation_id}/advance", status_code=202)
async def advance(
    investigation_id: UUID,
    _: Authenticated,
    __: ExactOrigin,
    services: WorkbenchServices = Depends(get_services),
    supervisor: InvestigationSupervisor = Depends(get_supervisor),
) -> None:
    supervisor.start(investigation_id, lambda: services.controller.advance(investigation_id))


@router.post("/api/investigations/{investigation_id}/stop", status_code=202)
async def stop(
    investigation_id: UUID,
    _: Authenticated,
    __: ExactOrigin,
    services: WorkbenchServices = Depends(get_services),
    supervisor: InvestigationSupervisor = Depends(get_supervisor),
) -> None:
    await supervisor.request_stop(investigation_id, services.recovery, services.gateway)
```

`ApprovalDecision` is a strict request with `digest: str` matching `^[0-9a-f]{64}$`. `ActionBatchEdit` is strict with `expected_digest`, `purpose: str` (1..240), and `actions: tuple[LiveAction, ...]` (1..4); the ingress firewall brands purpose before reconstruction. The service boundary and route wiring are exact:

```python
class ActionControlService(Protocol):
    def get_batch(self, batch_id: UUID) -> ActionBatchResponse: ...
    def grant_batch(self, batch_id: UUID, expected_digest: str) -> ActionBatchResponse: ...
    def replace_batch(self, batch_id: UUID, edit: ActionBatchEdit) -> ActionBatchResponse: ...
    def reject_batch(self, batch_id: UUID, expected_digest: str) -> ActionBatchResponse: ...
    def resume(self, investigation_id: UUID) -> InvestigationResponse: ...
    def edit_objective(self, investigation_id: UUID, body: ObjectiveEdit) -> InvestigationResponse: ...
```

Task 25 adds `controls: ActionControlService` to `WorkbenchServices`; its concrete implementation composes `ApprovalService`, `RecoveryService`, `CaseRepository`, the ingress firewall, UTC clock, and current scope/identity-version readers.

| Route | Call | Status |
|---|---|---:|
| `GET /api/action-batches/{batch_id}` | `controls.get_batch(batch_id)` | 200 |
| `POST /api/action-batches/{batch_id}/approve` | `controls.grant_batch(batch_id, body.digest)` | 200 |
| `POST /api/action-batches/{batch_id}/edit` | `controls.replace_batch(batch_id, body)` | 201 |
| `POST /api/action-batches/{batch_id}/reject` | `controls.reject_batch(batch_id, body.digest)` | 200 |
| `POST /api/investigations/{id}/advance` | `supervisor.start(id, lambda: controller.advance(id))` | 202 |
| `POST /api/investigations/{id}/stop` | `await supervisor.request_stop(id, recovery, gateway)` | 202 |
| `POST /api/investigations/{id}/resume` | `controls.resume(id)` | 200 |
| `PATCH /api/investigations/{id}/objective` | `controls.edit_objective(id, body)` | 200 |

`ActionControlService.get_batch` calls new `ApprovalService.load_request(batch_id)`, which loads and revalidates the immutable stored batch plus decision/expiry/identity labels without credentials. `grant_batch`/`reject_batch` compare the caller's digest with that record using `compare_digest` before changing state. `replace_batch` compares `expected_digest`, supersedes the old request, ingress-validates purpose, constructs a complete new strict `ActionBatch` against the current scope/identity versions, and calls `ApprovalService.request`; it never patches canonical JSON. Invalid transitions, stale/duplicate approval, digest mismatch, and single-flight conflict return `{error_code, correlation_id}` with `409`.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/workbench/test_actions_api.py tests/workbench/test_controls_api.py -v
python -m pytest tests/workbench tests/runtime tests/policy -q
git diff --check
git add bugintel/policy/approval.py bugintel/workbench/services.py bugintel/workbench/supervisor.py bugintel/workbench/api/actions.py bugintel/workbench/api/investigations.py bugintel/workbench/app.py tests/workbench/test_actions_api.py tests/workbench/test_controls_api.py
git commit -m "feat: expose bounded investigation controls"
```

### Task 26: Add Evidence, Conclusion, Export, and Ephemeral Browser APIs

**Files:**
- Modify: `bugintel/cases/evidence.py`
- Modify: `bugintel/workbench/services.py`
- Create: `bugintel/workbench/browser_view.py`
- Create: `bugintel/workbench/api/evidence.py`
- Create: `bugintel/workbench/api/conclusions.py`
- Create: `bugintel/workbench/api/exports.py`
- Create: `bugintel/workbench/api/browser.py`
- Modify: `bugintel/workbench/app.py`
- Create: `tests/workbench/test_results_api.py`
- Create: `tests/workbench/test_browser_view.py`

**Interfaces:**
- Consumes: evidence/conclusion repositories, case exporter, authenticated session, and `FrameSink` from the browser worker.
- Produces: sanitized result APIs and a bounded in-memory latest-frame store.

- [ ] **Step 1: Write no-raw and memory-only frame tests**

```python
def test_evidence_response_contains_no_raw_or_secret_fields(auth_client, evidence_with_canary) -> None:
    response = auth_client.get(f"/api/evidence/{evidence_with_canary.id}")
    assert response.status_code == 200
    assert "canary-secret" not in response.text
    assert not ({"raw_body", "raw_headers", "cookie", "html"} & set(response.json()))


def test_frame_store_bounds_and_zeroizes_replaced_bytes(frame_store) -> None:
    old = bytearray(b"old-frame")
    frame_store.publish(INVESTIGATION_ID, "Account A", old, "image/png")
    assert old == bytearray(len(old))
    new = bytearray(b"new-frame")
    frame_store.publish(INVESTIGATION_ID, "Account B", new, "image/png")
    assert new == bytearray(len(new))
    assert old == bytearray(len(old))
    assert frame_store.get(INVESTIGATION_ID).body == b"new-frame"


@pytest.mark.parametrize(
    ("body", "media_type"),
    [(bytearray(1_048_577), "image/png"), (bytearray(b"svg"), "image/svg+xml")],
)
def test_frame_store_rejects_oversized_or_active_content(frame_store, body, media_type) -> None:
    with pytest.raises(FrameRejected, match="invalid frame"):
        frame_store.publish(INVESTIGATION_ID, "Account A", body, media_type)
    assert body == bytearray(len(body))


@pytest.mark.parametrize(
    "path",
    [
        f"/api/investigations/{INVESTIGATION_ID}/evidence",
        f"/api/investigations/{INVESTIGATION_ID}/conclusion",
        f"/api/investigations/{INVESTIGATION_ID}/browser/frame",
    ],
)
def test_result_routes_require_bearer_and_do_not_cache(client, auth_client, path) -> None:
    assert client.get(path).status_code == 401
    response = auth_client.get(path)
    assert response.headers["cache-control"] == "no-store"


def test_frame_disappears_on_close_and_restart(auth_client, frame_store, make_frame_store) -> None:
    frame_store.publish(INVESTIGATION_ID, "Account A", bytearray(b"frame"), "image/png")
    frame_store.close_view(INVESTIGATION_ID)
    assert auth_client.get(f"/api/investigations/{INVESTIGATION_ID}/browser/frame").status_code == 404
    assert make_frame_store().get(INVESTIGATION_ID) is None
```

The results fixture serializes a `Conclusion` whose safe summary, limitations, and citations are known values plus raw/model canaries stored only in forbidden fixture fields. Assert the JSON keys are exactly `verdict`, `summary`, `citations`, `limitations`, `recommended_next_step`; assert both canaries are absent. The export test posts once, verifies `Content-Disposition: attachment; filename="investigation-<uuid>.zip"`, then checks every non-export JSON response for the temporary filesystem path and expects no match.

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/workbench/test_results_api.py tests/workbench/test_browser_view.py -v
```

Expected: missing modules/routes.

- [ ] **Step 3: Implement bounded frame storage**

```python
class BrowserFrameStore:
    MAX_FRAME_BYTES = 1_048_576
    MAX_TOTAL_BYTES = 8_388_608

    def publish(self, investigation_id: UUID, identity_label: SanitizedText, body: bytearray, media_type: str) -> int:
        if len(body) > self.MAX_FRAME_BYTES or media_type not in {"image/png", "image/jpeg"}:
            self._zero(body)
            raise FrameRejected("invalid frame")
        with self._lock:
            previous = self._frames.pop(investigation_id, None)
            if previous is not None:
                self._zero(previous.mutable_body)
            sequence = self._next_sequence[investigation_id]
            stored = StoredFrame.from_mutable(body, media_type, identity_label, sequence)
            self._evict_oldest_until_fits(len(stored.mutable_body))
            self._frames[investigation_id] = stored
            self._next_sequence[investigation_id] = sequence + 1
            self._zero(body)
            return sequence
```

`BrowserFrameStore(zeroizer: Callable[[bytearray], None] = zero_bytearray)` uses `threading.RLock`, keeps at most one frame per investigation and 8 MiB across all frames, and evicts/zeroizes the least-recently-published frame before exceeding the global ceiling. `StoredFrame.from_mutable` copies into a new internal `bytearray` before `publish` zeroizes the caller's buffer. It stores branded `identity_label`, monotonically increasing `sequence`, media type, and publication time; its read-only `body` property returns `bytes(self.mutable_body)` and never exposes the internal mutable buffer. The injected-zeroizer test records pre-zero contents and asserts `b"old-frame"` appears twice (caller then replaced internal copy). `publish` returns the sequence to `BrowserToolWorker`; the gateway includes only `tool_kind="browser"`, `frame_sequence`, and the safe identity label in the existing persisted `tool.completed` payload. No new event type is invented. The frame endpoint returns only `X-Frame-Sequence`; the frontend reads the current branded identity label from the authenticated event DTO, not an HTTP header. The reducer updates `frameSequence` only from that persisted `tool.completed` event and then fetches the authenticated image endpoint.

Close/remove clears and zeroizes stored bytes. Never write frames to disk, SQLite, logs, events, model context, or export.

- [ ] **Step 4: Implement sanitized read/export routes**

Provide:

```text
GET  /api/investigations/{id}/evidence
GET  /api/evidence/{id}
GET  /api/investigations/{id}/conclusion
POST /api/investigations/{id}/exports
GET  /api/investigations/{id}/browser/frame
```

Export returns a streamed/download response with `Cache-Control: no-store` and a sanitized UUID filename; it never accepts an output path from the client. Browser frame responses require bearer auth and use `Cache-Control: no-store, max-age=0`.

The public DTOs and frame route are exact:

```python
class EvidenceResponse(FrozenModel):
    id: UUID
    kind: str
    summary: SanitizedText
    normalized_fields: SanitizedPayload
    citations: tuple[EvidenceCitation, ...]
    created_at: AwareDatetime


class ConclusionResponse(FrozenModel):
    verdict: Literal["supported", "rejected", "inconclusive"]
    summary: SanitizedText
    citations: tuple[EvidenceCitation, ...]
    limitations: tuple[SanitizedText, ...]
    recommended_next_step: SanitizedText


@router.get("/api/investigations/{investigation_id}/browser/frame")
def browser_frame(
    investigation_id: UUID,
    _: Authenticated,
    services: WorkbenchServices = Depends(get_services),
) -> Response:
    frame = services.frame_store.get(investigation_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="frame_unavailable")
    return Response(
        content=frame.body,
        media_type=frame.media_type,
        headers={
            "Cache-Control": "no-store, max-age=0",
            "X-Frame-Sequence": str(frame.sequence),
        },
    )
```

Extend `EvidenceRepository` with read-only `get(evidence_id: UUID) -> EvidenceRecord | None` and `list_for_investigation(investigation_id: UUID) -> tuple[EvidenceRecord, ...]`, ordered by `(created_at, id)`. The workbench result service and routes are exact:

```python
class WorkbenchResultService(Protocol):
    def list_evidence(self, investigation_id: UUID) -> tuple[EvidenceResponse, ...]: ...
    def get_evidence(self, evidence_id: UUID) -> EvidenceResponse | None: ...
    def get_conclusion(self, investigation_id: UUID) -> ConclusionResponse | None: ...


def stream_export(exporter: CaseExporter, investigation_id: UUID) -> tuple[Iterator[bytes], str]:
    temporary = TemporaryDirectory(prefix="blackhole-export-")
    manifest = exporter.export(investigation_id, Path(temporary.name))

    def chunks() -> Iterator[bytes]:
        try:
            with manifest.path.open("rb") as archive:
                while chunk := archive.read(65_536):
                    yield chunk
        finally:
            temporary.cleanup()

    return chunks(), f"investigation-{investigation_id}.zip"
```

Task 26 adds `results: WorkbenchResultService` and `frame_store: BrowserFrameStore` to `WorkbenchServices`; the concrete result service converts only sanitized repository/domain records to the public DTOs. In `build_services`, create `frame_store = BrowserFrameStore()` before the browser worker, replace `frame_sink=DiscardingFrameSink()` with `frame_sink=frame_store`, and include that same instance in `WorkbenchServices`. The gateway registry is still installed exactly once with that already-wired worker; no worker or frame store is replaced after sealing.

| Route | Call | Response |
|---|---|---|
| `GET /api/investigations/{id}/evidence` | `results.list_evidence(id)` | `list[EvidenceResponse]`, 200 |
| `GET /api/evidence/{id}` | `results.get_evidence(id)` | `EvidenceResponse`, 200 or 404 |
| `GET /api/investigations/{id}/conclusion` | `results.get_conclusion(id)` | `ConclusionResponse`, 200 or 404 |
| `POST /api/investigations/{id}/exports` | `stream_export(exporter, id)` | `StreamingResponse(application/zip)`, 200 |
| `GET /api/investigations/{id}/browser/frame` | `frame_store.get(id)` | image response, 200 or 404 |

The export route requires both `Authenticated` and `ExactOrigin`, sets `Content-Disposition: attachment; filename="investigation-<uuid>.zip"` and `Cache-Control: no-store`, and never accepts an output path. `TemporaryDirectory.cleanup()` runs after EOF, disconnect, or read error.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/workbench/test_results_api.py tests/workbench/test_browser_view.py -v
python -m pytest tests/workbench tests/cases tests/runtime -q
git diff --check
git add bugintel/cases/evidence.py bugintel/workbench/services.py bugintel/workbench/browser_view.py bugintel/workbench/api/evidence.py bugintel/workbench/api/conclusions.py bugintel/workbench/api/exports.py bugintel/workbench/api/browser.py bugintel/workbench/app.py tests/workbench/test_results_api.py tests/workbench/test_browser_view.py
git commit -m "feat: expose sanitized investigation results"
```

### Task 27: Add Authenticated Fetch-Streamed Events

**Files:**
- Create: `bugintel/workbench/event_stream.py`
- Create: `bugintel/workbench/api/events.py`
- Modify: `bugintel/workbench/services.py`
- Modify: `bugintel/cases/events.py`
- Modify: `bugintel/workbench/app.py`
- Create: `tests/workbench/test_event_stream.py`

**Interfaces:**
- Consumes: `EventStore.list_after`, bearer authentication, client `after` sequence, and an in-memory wake condition.
- Produces: ordered fetch-streamed `text/event-stream` responses with reconnect and heartbeat behavior.

- [ ] **Step 1: Write auth, ordering, and reconnect tests**

```python
def test_stream_requires_authorization_header(client, investigation_id) -> None:
    assert client.get(f"/api/investigations/{investigation_id}/events").status_code == 401


@pytest.mark.asyncio
async def test_reconnect_reads_database_after_sequence_without_duplicates(seeded_events, authenticated_session) -> None:
    stream = iter_events(
        seeded_events.investigation_id,
        after_sequence=2,
        services=seeded_events.services,
        sessions=seeded_events.sessions,
        session=authenticated_session,
    )
    ids = [parse_sse_id(await anext(stream)), parse_sse_id(await anext(stream))]
    await stream.aclose()
    assert ids == [3, 4]


@pytest.mark.asyncio
async def test_idle_stream_heartbeats_at_fifteen_seconds(stream_harness) -> None:
    stream = stream_harness.iter(after_sequence=0)
    stream_harness.clock.advance(seconds=15)
    assert await anext(stream) == b": heartbeat\n\n"
    await stream.aclose()


@pytest.mark.asyncio
async def test_lost_wake_still_reads_committed_event(stream_harness) -> None:
    stream_harness.drop_next_wake()
    stream_harness.append_committed(sequence=1)
    stream_harness.clock.advance(seconds=15)
    item = await anext(stream_harness.iter(after_sequence=0))
    assert parse_sse_id(item) == 1


@pytest.mark.parametrize("query", ["token=x", "session=x", "auth=x", "key=x"])
def test_stream_rejects_query_credentials(client, investigation_id, query) -> None:
    response = client.get(f"/api/investigations/{investigation_id}/events?{query}")
    assert response.status_code == 400
```

`stream_harness` injects `FakeAsyncTimer`, tracks `EventWake.waiter_count`, and can commit or roll back through the real `Database` callbacks. Its exact assertions are: encoded event IDs are `[1, 2, 3]`; rollback yields no event after the next poll; commit makes the record readable before `notify_after_commit` runs; `await stream.aclose()` changes `waiter_count` from one to zero; and advancing the session clock by 30 minutes makes the next cycle raise `SessionRejected("expired")` without another event.

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/workbench/test_event_stream.py -v
```

Expected: missing stream route.

- [ ] **Step 3: Implement database-first iteration**

```python
class EventWake:
    def __init__(self) -> None:
        self._events: dict[UUID, asyncio.Event] = {}
        self._generations: dict[UUID, int] = defaultdict(int)
        self._waiters: Counter[UUID] = Counter()
        self._lock = threading.RLock()
        self._loop: asyncio.AbstractEventLoop | None = None

    def bind_running_loop(self) -> None:
        self._loop = asyncio.get_running_loop()

    def generation(self, investigation_id: UUID) -> int:
        with self._lock:
            return self._generations[investigation_id]

    @property
    def waiter_count(self) -> int:
        return sum(self._waiters.values())

    def notify_after_commit(self, investigation_id: UUID) -> None:
        with self._lock:
            self._generations[investigation_id] += 1
        if self._loop is not None:
            self._loop.call_soon_threadsafe(self._set_event, investigation_id)

    def _set_event(self, investigation_id: UUID) -> None:
        event = self._events.get(investigation_id)
        if event is not None:
            event.set()

    async def wait(self, investigation_id: UUID, generation: int, timeout: float) -> int:
        current = self.generation(investigation_id)
        if current != generation:
            return current
        event = self._events.setdefault(investigation_id, asyncio.Event())
        self._waiters[investigation_id] += 1
        try:
            await asyncio.wait_for(event.wait(), timeout)
            event.clear()
            return self.generation(investigation_id)
        finally:
            self._waiters[investigation_id] -= 1
            if self._waiters[investigation_id] == 0:
                self._waiters.pop(investigation_id)
                self._events.pop(investigation_id, None)


def encode_sse(record: EventRecord) -> bytes:
    data = record.payload.model_dump_json()
    return f"id: {record.sequence}\nevent: {record.type.value}\ndata: {data}\n\n".encode("utf-8")


async def iter_events(
    investigation_id: UUID,
    after_sequence: int,
    services: WorkbenchServices,
    sessions: SessionManager,
    session: AuthenticatedSession,
):
    cursor = after_sequence
    generation = services.event_wake.generation(investigation_id)
    while True:
        sessions.validate(session)
        records = services.events.list_after(investigation_id, cursor)
        for record in records:
            cursor = record.sequence
            yield encode_sse(record)
        try:
            generation = await services.event_wake.wait(investigation_id, generation, timeout=15.0)
        except TimeoutError:
            yield b": heartbeat\n\n"


@router.get("/api/investigations/{investigation_id}/events")
async def events(
    investigation_id: UUID,
    session: Authenticated,
    after: Annotated[int, Query(ge=0)] = 0,
    services: WorkbenchServices = Depends(get_services),
    sessions: SessionManager = Depends(get_sessions),
) -> StreamingResponse:
    return StreamingResponse(
        iter_events(investigation_id, after, services, sessions, session),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-store",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )
```

Task 27 adds `event_wake: EventWake` to `WorkbenchServices`. The app lifespan calls `event_wake.bind_running_loop()` before accepting requests. `EventStore.append` registers `event_wake.notify_after_commit(investigation_id)` through a `Database.after_commit` callback; rollbacks discard callbacks. This wake is only latency optimization because every loop polls SQLite first. Authenticate before starting and recheck session validity on each database/heartbeat cycle. Tests call the iterator directly with an injected fake timer and stop after a fixed item count; they do not use `TestClient.get` on an infinite response. A disconnected request cancels the iterator and removes an empty event; expired sessions end the stream after the next cycle.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/workbench/test_event_stream.py -v
python -m pytest tests/workbench -q
git diff --check
git add bugintel/workbench/event_stream.py bugintel/workbench/api/events.py bugintel/workbench/services.py bugintel/workbench/app.py bugintel/cases/events.py tests/workbench/test_event_stream.py
git commit -m "feat: stream persisted investigation events"
```

### Task 28: Add the React Authentication and Typed Data Plane

**Files:**
- Modify: `.gitignore`
- Create: `web/.nvmrc`
- Create: `web/package.json`
- Create: `web/package-lock.json`
- Create: `web/index.html`
- Create: `web/tsconfig.json`
- Create: `web/vite.config.ts`
- Create: `web/vitest.config.ts`
- Create: `web/openapi.json`
- Create: `tools/export_openapi.py`
- Create: `web/src/api/generated.ts`
- Create: `web/src/api/session.ts`
- Create: `web/src/api/client.ts`
- Create: `web/src/api/eventStream.ts`
- Create: `web/src/state/store.tsx`
- Create: `web/src/api/session.test.ts`
- Create: `web/src/api/eventStream.test.ts`

**Interfaces:**
- Consumes: bootstrap fragment, generated OpenAPI schema, bearer-authenticated REST and event endpoints.
- Produces: memory-only `SessionTokenStore`, `bootstrapSession`, typed `apiFetch`, `streamEvents`, and React application state/context.

- [ ] **Step 1: Create exact frontend manifest and lockfile**

Use Node 24 and these bounded major versions:

```json
{
  "name": "blackhole-controlled-lab-workbench",
  "private": true,
  "engines": {"node": ">=22.12.0"},
  "scripts": {
    "generate-api": "openapi-typescript openapi.json -o src/api/generated.ts",
    "typecheck": "tsc --noEmit",
    "test": "vitest run",
    "build": "vite build",
    "e2e": "playwright test"
  },
  "dependencies": {
    "react": "^19.2.8",
    "react-dom": "^19.2.8"
  },
  "devDependencies": {
    "@playwright/test": "^1.62.1",
    "@testing-library/jest-dom": "^7.0.1",
    "@testing-library/react": "^16.3.2",
    "@testing-library/user-event": "^14.6.4",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.4",
    "@vitejs/plugin-react": "^6.0.5",
    "jsdom": "^30.0.1",
    "openapi-typescript": "^7.13.0",
    "typescript": "^7.0.2",
    "vite": "^8.2.1",
    "vitest": "^4.1.10"
  }
}
```

Write `24` to `.nvmrc`. Add `web/node_modules/`, `web/dist/`, `web/test-results/`, `web/playwright-report/`, and `web/.vite/` to the root `.gitignore`. Run `npm install --prefix web` and commit the generated lockfile; never hand-edit the lockfile.

- [ ] **Step 2: Generate the API contract and write session tests**

`tools/export_openapi.py` imports `create_app` with fake services, sorts JSON keys, and writes `web/openapi.json` as UTF-8. Generate TypeScript types, then test:

```typescript
it("clears the fragment before exchanging the nonce", async () => {
  window.location.hash = "#bootstrap=nonce-value";
  const fetcher = vi.fn().mockResolvedValue(jsonResponse({session_token: "session-value"}));
  const tokenStore = new SessionTokenStore();
  await bootstrapSession(tokenStore, fetcher);
  expect(window.location.hash).toBe("");
  expect(tokenStore.get()).toBe("session-value");
  expect(document.cookie).toBe("");
  expect(localStorage.length).toBe(0);
  expect(sessionStorage.length).toBe(0);
});


it("adds bearer auth, clears on 401, and never attempts a script-set Origin", async () => {
  const store = new SessionTokenStore();
  store.set("session-value");
  const fetcher = vi.fn().mockResolvedValue(new Response(null, {status: 401}));
  await expect(apiFetch(store, "/api/projects", {method: "POST"}, fetcher)).rejects.toThrow("Session expired");
  const [, init] = fetcher.mock.calls[0] as [string, RequestInit];
  const headers = new Headers(init.headers);
  expect(headers.get("Authorization")).toBe("Bearer session-value");
  expect(headers.has("Origin")).toBe(false);
  expect(store.get()).toBeNull();
});


it("streams with bearer auth and reconnects after the last persisted sequence", async () => {
  const store = new SessionTokenStore();
  store.set("session-value");
  const fetcher = vi.fn()
    .mockResolvedValueOnce(sseResponse("id: 7\nevent: plan_updated\ndata: {\"step\":1}\n\n"))
    .mockResolvedValueOnce(sseResponse("id: 8\nevent: observation_recorded\ndata: {\"safe\":true}\n\n"));
  const controller = new AbortController();
  const stream = streamEvents(store, INVESTIGATION_ID, 6, fetcher, controller.signal);
  expect((await stream.next()).value?.id).toBe(7);
  expect((await stream.next()).value?.id).toBe(8);
  expect(fetcher.mock.calls[1][0]).toBe(`/api/investigations/${INVESTIGATION_ID}/events?after=7`);
  expect(new Headers(fetcher.mock.calls[1][1].headers).get("Authorization")).toBe("Bearer session-value");
  controller.abort();
});
```

The browser supplies the exact same-origin `Origin` for mutation fetches; client code must not attempt to set that forbidden header. The Playwright gate in Task 30 verifies the server receives it. `session.test.ts` also spies on `Storage.prototype.setItem`, `indexedDB.open`, `document.cookie`, `console.*`, and `history.pushState` and asserts none receive either nonce or token.

`tools/export_openapi.py` uses the app object directly, not the disabled HTTP route:

```python
def main() -> None:
    app = create_app(fake_services(), fake_sessions(), Path("tests/fixtures/static"), WorkbenchAuthority(port=8765))
    output = Path(__file__).parents[1] / "web" / "openapi.json"
    output.write_text(json.dumps(app.openapi(), sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
```

- [ ] **Step 3: Run and confirm failure**

```powershell
python tools/export_openapi.py
npm run generate-api --prefix web
npm test --prefix web
```

Expected before implementation: frontend module imports fail.

- [ ] **Step 4: Implement memory-only session and fetch stream**

```typescript
export class SessionTokenStore {
  #value: string | null = null;
  set(value: string): void { this.#value = value; }
  get(): string | null { return this.#value; }
  clear(): void { this.#value = null; }
}

export async function bootstrapSession(store: SessionTokenStore, fetcher = fetch): Promise<void> {
  const nonce = new URLSearchParams(location.hash.slice(1)).get("bootstrap");
  history.replaceState(null, "", `${location.pathname}${location.search}`);
  if (!nonce) throw new Error("Missing bootstrap nonce");
  const response = await fetcher("/api/bootstrap/exchange", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({nonce}),
  });
  if (!response.ok) throw new Error("Bootstrap rejected");
  const payload = await response.json() as {session_token: string};
  store.set(payload.session_token);
}


export type ServerEvent = {id: number; type: string; data: unknown};

export async function* parseSse(body: ReadableStream<Uint8Array>): AsyncGenerator<ServerEvent> {
  const reader = body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  try {
    while (true) {
      const {done, value} = await reader.read();
      buffer += decoder.decode(value, {stream: !done}).replaceAll("\r\n", "\n");
      let boundary: number;
      while ((boundary = buffer.indexOf("\n\n")) >= 0) {
        const block = buffer.slice(0, boundary);
        buffer = buffer.slice(boundary + 2);
        if (!block || block.startsWith(":")) continue;
        const lines = block.split("\n");
        const id = Number(lines.find((line) => line.startsWith("id:"))?.slice(3).trim());
        const type = lines.find((line) => line.startsWith("event:"))?.slice(6).trim() ?? "message";
        const text = lines.filter((line) => line.startsWith("data:"))
          .map((line) => line.slice(5).trimStart()).join("\n");
        if (!Number.isSafeInteger(id) || id < 1) throw new Error("Invalid event sequence");
        yield {id, type, data: JSON.parse(text)};
      }
      if (done) break;
    }
    if (buffer.trim() !== "") throw new Error("Truncated event stream");
  } finally {
    reader.releaseLock();
  }
}
```

`apiFetch<T>(store, input, init, fetcher = fetch) -> Promise<T>` merges only `Accept`, `Content-Type` when a body exists, and `Authorization`; on `401` it clears the store and throws `SessionExpired`. `streamEvents(store, investigationId, after, fetcher, signal) -> AsyncGenerator<ServerEvent>` calls fetch with `Accept: text/event-stream`, the bearer header, and `?after=<last id>`, yields `parseSse(response.body)`, reconnects after clean EOF, and clears/throws on `401`. It rejects a missing body, an ID that does not strictly increase, malformed JSON, or a non-2xx response. Never instantiate native `EventSource`.

- [ ] **Step 5: Verify and commit**

```powershell
npm run generate-api --prefix web
npm run typecheck --prefix web
npm test --prefix web
git diff --check
git add .gitignore web/.nvmrc web/package.json web/package-lock.json web/index.html web/tsconfig.json web/vite.config.ts web/vitest.config.ts web/openapi.json web/src/api web/src/state tools/export_openapi.py
git commit -m "feat: add authenticated workbench data plane"
```

### Task 29: Add the Codex-Style Workbench Shell

**Files:**
- Modify: `web/src/api/client.ts`
- Modify: `web/src/state/store.tsx`
- Create: `web/src/main.tsx`
- Create: `web/src/App.tsx`
- Create: `web/src/styles/tokens.css`
- Create: `web/src/styles/app.css`
- Create: `web/src/components/ProjectSidebar.tsx`
- Create: `web/src/components/InvestigationHeader.tsx`
- Create: `web/src/components/Conversation.tsx`
- Create: `web/src/components/ActivityFeed.tsx`
- Create: `web/src/components/Composer.tsx`
- Create: `web/src/components/ToolPanel.tsx`
- Create: `web/src/test/fakes.ts`
- Create: `web/src/components/AppShell.test.tsx`

**Interfaces:**
- Consumes: typed store/client/event stream.
- Produces: accessible three-column Codex-style shell with local project navigation, investigation conversation/activity, persistent composer, real Browser/Evidence tabs, and typed deterministic `fakeServices`/`fakeServicesWithPendingBatch` test fixtures.

- [ ] **Step 1: Write layout and no-fake-feature tests**

```typescript
import {fakeServices} from "../test/fakes";

it("renders the approved workbench regions and only real tool tabs", async () => {
  render(<App services={fakeServices()} />);
  expect(screen.getByRole("navigation", {name: "Projects"})).toBeVisible();
  expect(screen.getByRole("main", {name: "Investigation"})).toBeVisible();
  expect(screen.getByRole("complementary", {name: "Tools"})).toBeVisible();
  expect(screen.getByRole("tab", {name: "Browser"})).toBeVisible();
  expect(screen.getByRole("tab", {name: "Evidence"})).toBeVisible();
  expect(screen.queryByText("Burp")).not.toBeInTheDocument();
  expect(screen.queryByText("Terminal")).not.toBeInTheDocument();
});


it.each([
  ["planning", "Planning", false],
  ["waiting_approval", "Waiting for approval", false],
  ["paused", "Paused", false],
  ["stopped", "Stopped", true],
  ["complete", "Complete", true],
] as const)("renders %s with its exact label and composer state", (state, label, disabled) => {
  const services = fakeServices({status: state});
  render(<App services={services} />);
  expect(screen.getByText(label, {selector: "[role=status]"})).toBeVisible();
  expect(screen.getByRole("textbox", {name: "Message"})).toHaveProperty("disabled", disabled);
});


it("renders the empty state and collapses activity without losing its count", async () => {
  const user = userEvent.setup();
  render(<App services={fakeServices({activeInvestigation: null, events: []})} />);
  expect(screen.getByText("Create an investigation to begin")).toBeVisible();
  await user.click(screen.getByRole("button", {name: "Collapse activity"}));
  expect(screen.getByText("Activity (0)")).toBeVisible();
});


it("supports arrow-key tab navigation and shows only concise safe summaries", async () => {
  const user = userEvent.setup();
  render(<App services={fakeServices({events: [{id: 1, type: "plan.updated", summary: "Proposed two bounded reads"}]})} />);
  const browser = screen.getByRole("tab", {name: "Browser"});
  browser.focus();
  await user.keyboard("{ArrowRight}");
  expect(screen.getByRole("tab", {name: "Evidence"})).toHaveFocus();
  expect(screen.getByText("Proposed two bounded reads")).toBeVisible();
  expect(screen.queryByText(/chain.of.thought|hidden reasoning/i)).not.toBeInTheDocument();
});
```

`fakeServices(overrides?: Partial<WorkbenchState>)` returns a new fixture per call. The `ProjectSidebar` test selects project `P-2` and asserts `services.selectProject` receives only its UUID; the composer test submits `"Compare order 1048"`, asserts one `sendMessage` call, then verifies the input clears only after the promise resolves.

- [ ] **Step 2: Run and confirm failure**

```powershell
npm test --prefix web -- AppShell.test.tsx
```

Expected: missing components.

- [ ] **Step 3: Implement the shell with escaped React text nodes**

```tsx
export function App({services}: AppProps) {
  return (
    <div className="app-shell">
      <ProjectSidebar projects={services.state.projects} />
      <main aria-label="Investigation" className="investigation-column">
        <InvestigationHeader investigation={services.state.activeInvestigation} />
        <Conversation messages={services.state.messages} />
        <ActivityFeed events={services.state.events} />
        <Composer onSubmit={services.sendMessage} state={services.state.status} />
      </main>
      <ToolPanel activeTab={services.state.toolTab} onTabChange={services.selectToolTab} />
    </div>
  );
}
```

The exact shell boundary is:

```typescript
export type InvestigationStatus = "setup" | "planning" | "waiting_approval" | "executing" | "paused" | "stopped" | "complete" | "failed";
export type ToolTab = "browser" | "evidence";
export interface WorkbenchState {
  projects: readonly ProjectResponse[];
  activeProjectId: string | null;
  activeInvestigation: InvestigationResponse | null;
  messages: readonly MessageResponse[];
  events: readonly SafeEventView[];
  status: InvestigationStatus;
  toolTab: ToolTab;
  activityCollapsed: boolean;
}
export interface AppServices {
  state: WorkbenchState;
  selectProject(id: string): void;
  selectToolTab(tab: ToolTab): void;
  toggleActivity(): void;
  sendMessage(content: string): Promise<void>;
}
```

`web/src/test/fakes.ts` returns fresh, fully populated `AppServices` objects whose methods are `vi.fn()` and whose state contains no network handle. `fakeServicesWithPendingBatch()` returns the same typed fixture plus one exact Account A/Account B read-only pending batch. Never use raw HTML APIs. CSS tokens define `--surface-0: #111216`, `--surface-1: #191b21`, `--border: #30333b`, `--accent: #7c6cff`, `--text: #f3f4f7`, `--muted: #a5a8b1`; action/evidence fields use `ui-monospace`, conversation uses `system-ui`; `@media (max-width: 899px)` hides the project sidebar behind an accessible toggle and stacks the tools region below the investigation.

- [ ] **Step 4: Verify visual structure and commit**

```powershell
npm run typecheck --prefix web
npm test --prefix web
npm run build --prefix web
git diff --check
git add web/src/main.tsx web/src/App.tsx web/src/styles web/src/components/ProjectSidebar.tsx web/src/components/InvestigationHeader.tsx web/src/components/Conversation.tsx web/src/components/ActivityFeed.tsx web/src/components/Composer.tsx web/src/components/ToolPanel.tsx web/src/test/fakes.ts web/src/components/AppShell.test.tsx
git commit -m "feat: add Codex-style investigation shell"
```

### Task 30: Add Interactive Plans, Approvals, Evidence, Browser, and Controls

**Files:**
- Modify: `web/src/App.tsx`
- Modify: `web/src/api/client.ts`
- Modify: `web/src/state/store.tsx`
- Modify: `web/src/test/fakes.ts`
- Create: `web/src/components/PlanView.tsx`
- Create: `web/src/components/HypothesisList.tsx`
- Create: `web/src/components/ApprovalCard.tsx`
- Create: `web/src/components/PolicyDecision.tsx`
- Create: `web/src/components/ScopeBudgetBar.tsx`
- Create: `web/src/components/BrowserPanel.tsx`
- Create: `web/src/components/EvidencePanel.tsx`
- Create: `web/src/components/ConclusionCard.tsx`
- Create: `web/src/components/InvestigationControls.tsx`
- Create: `web/src/components/CaseSetup.tsx`
- Create: `web/src/components/InvestigationFlow.test.tsx`
- Create: `web/playwright.config.ts`
- Create: `web/e2e/investigation.spec.ts`
- Create: `tests/workbench/e2e_server.py`

**Interfaces:**
- Consumes: all typed API/event capabilities from Tasks 24-28.
- Produces: the complete researcher interaction loop and browser E2E coverage.

- [ ] **Step 1: Write component interaction tests**

```typescript
import {fakeServicesWithPendingBatch} from "../test/fakes";
import userEvent from "@testing-library/user-event";

it("shows exact approval limits and requires a fresh decision after edit", async () => {
  const user = userEvent.setup();
  const services = fakeServicesWithPendingBatch();
  render(<ApprovalCard batch={services.batch} api={services.api} />);
  expect(screen.getByText("Account A -> GET /api/orders/1048")).toBeVisible();
  expect(screen.getByText("Maximum requests: 2")).toBeVisible();
  expect(screen.getByText("Expires in: 5 minutes")).toBeVisible();
  await user.click(screen.getByRole("button", {name: "Edit proposal"}));
  await user.type(screen.getByLabelText("Purpose"), " compare order 1048 only");
  await user.click(screen.getByRole("button", {name: "Save new proposal"}));
  expect(await screen.findByText("New approval required")).toBeVisible();
});


it("binds approve and reject to the displayed batch id and digest", async () => {
  const user = userEvent.setup();
  const services = fakeServicesWithPendingBatch();
  const first = render(<ApprovalCard batch={services.batch} api={services.api} />);
  await user.click(screen.getByRole("button", {name: "Approve exact actions"}));
  expect(services.api.approveBatch).toHaveBeenCalledWith(services.batch.id, services.batch.digest);
  first.unmount();
  render(<ApprovalCard batch={services.batch} api={services.api} />);
  await user.click(screen.getByRole("button", {name: "Reject proposal"}));
  expect(services.api.rejectBatch).toHaveBeenCalledWith(services.batch.id, services.batch.digest);
});


it("acknowledges durable stop and exposes resume only when paused", async () => {
  const user = userEvent.setup();
  const services = fakeServices({status: "executing"});
  const view = render(<InvestigationControls investigationId={INVESTIGATION_ID} status="executing" api={services.api} />);
  await user.click(screen.getByRole("button", {name: "Stop investigation"}));
  expect(services.api.stop).toHaveBeenCalledWith(INVESTIGATION_ID);
  expect(screen.getByRole("button", {name: "Stopping investigation"})).toBeDisabled();
  view.rerender(<InvestigationControls investigationId={INVESTIGATION_ID} status="paused" api={services.api} />);
  await user.click(screen.getByRole("button", {name: "Resume investigation"}));
  expect(services.api.resume).toHaveBeenCalledWith(INVESTIGATION_ID);
});


it("renders policy, evidence, conclusion, scope, identities, and budgets as safe text", () => {
  const malicious = "<img src=x onerror=window.pwned=true>";
  render(<>
    <PolicyDecision decision={{allowed: false, code: "path_out_of_scope", summary: malicious}} />
    <EvidencePanel records={[evidenceFixture({summary: malicious, citations: ["E-1"]})]} />
    <ConclusionCard conclusion={conclusionFixture({limitations: ["Only the controlled lab was tested"]})} />
    <ScopeBudgetBar scope={scopeFixture()} identities={[identityFixture("Account A"), identityFixture("Account B")]} budget={budgetFixture({requestsRemaining: 36})} />
  </>);
  expect(screen.getAllByText(malicious).length).toBeGreaterThan(0);
  expect(document.querySelector("img[src='x']")).toBeNull();
  expect(screen.getByText("E-1")).toBeVisible();
  expect(screen.getByText("Only the controlled lab was tested")).toBeVisible();
  expect(screen.getByText("36 requests remaining")).toBeVisible();
});


it("revokes each browser blob URL after replacement and unmount", async () => {
  const create = vi.spyOn(URL, "createObjectURL").mockReturnValueOnce("blob:first").mockReturnValueOnce("blob:second");
  const revoke = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => undefined);
  const api = fakeServices().api;
  vi.mocked(api.fetchBrowserFrame).mockResolvedValue(new Blob(["frame"], {type: "image/png"}));
  const view = render(<BrowserPanel api={api} investigationId={INVESTIGATION_ID} frameSequence={1} />);
  expect(await screen.findByRole("img", {name: "Latest controlled browser frame"})).toHaveAttribute("src", "blob:first");
  view.rerender(<BrowserPanel api={api} investigationId={INVESTIGATION_ID} frameSequence={2} />);
  await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
  expect(revoke).toHaveBeenCalledWith("blob:first");
  view.unmount();
  expect(revoke).toHaveBeenCalledWith("blob:second");
});
```

The store reducer test feeds, in order, `plan.created`, `hypothesis.created`, `policy.blocked`, `evidence.created`, `tool.completed` with `{tool_kind:"browser", frame_sequence:4}`, and `investigation.completed`; it asserts the exact plan/hypothesis/evidence payloads are present, the policy block is in activity, `frameSequence == 4`, and status is `complete`.

- [ ] **Step 2: Run component tests and confirm failure**

```powershell
npm test --prefix web -- InvestigationFlow.test.tsx
```

Expected: FAIL because the interactive components and API methods do not exist.

- [ ] **Step 3: Implement bounded browser frame display**

```tsx
useEffect(() => {
  const controller = new AbortController();
  let cancelled = false;
  let objectUrl: string | null = null;
  setFrameUrl(null);
  void api.fetchBrowserFrame(investigationId, controller.signal)
    .then((blob) => {
      const nextUrl = URL.createObjectURL(blob);
      if (cancelled) {
        URL.revokeObjectURL(nextUrl);
        return;
      }
      objectUrl = nextUrl;
      setFrameUrl(nextUrl);
    })
    .catch((error: unknown) => {
      if (!cancelled && !(error instanceof DOMException && error.name === "AbortError")) {
        setFrameError("Browser frame unavailable");
      }
    });
  return () => {
    cancelled = true;
    controller.abort();
    if (objectUrl !== null) URL.revokeObjectURL(objectUrl);
  };
}, [api, investigationId, frameSequence]);
```

Use an `<img>` whose `src` is only that blob URL; never use an iframe, target URL, DOM snapshot, or data URL. Evidence renders normalized fields and citations as text.

- [ ] **Step 4: Implement exact component/API boundaries and event-driven updates**

Extend `AppServices` with this API and view state; no component imports `fetch`:

```typescript
export interface InvestigationApi {
  approveBatch(batchId: string, digest: string): Promise<ActionBatchResponse>;
  editBatch(batchId: string, digest: string, edit: ActionBatchEdit): Promise<ActionBatchResponse>;
  rejectBatch(batchId: string, digest: string): Promise<ActionBatchResponse>;
  advance(investigationId: string): Promise<void>;
  stop(investigationId: string): Promise<void>;
  resume(investigationId: string): Promise<InvestigationResponse>;
  fetchBrowserFrame(investigationId: string, signal: AbortSignal): Promise<Blob>;
}

export interface InteractiveViewState {
  plan: PlanResponse | null;
  hypotheses: readonly HypothesisResponse[];
  pendingBatch: ActionBatchResponse | null;
  latestPolicy: PolicyDecisionView | null;
  scope: ScopeResponse | null;
  identities: readonly IdentityResponse[];
  budget: BudgetView;
  evidence: readonly EvidenceResponse[];
  conclusion: ConclusionResponse | null;
  frameSequence: number;
}
```

| Component | Exact input | Exact effect/output |
|---|---|---|
| `PlanView` | `PlanResponse` | Ordered semantic list; no editable execution fields |
| `HypothesisList` | `readonly HypothesisResponse[]` | Status badge plus safe rationale/citations |
| `ApprovalCard` | `ActionBatchResponse`, `InvestigationApi` | Approve/reject submit `{batch_id,digest}`; edit submits old digest plus a complete replacement purpose/actions document |
| `PolicyDecision` | `PolicyDecisionView` | Safe allowed/blocked label, code, and summary |
| `ScopeBudgetBar` | scope, two identity DTOs, `BudgetView` | Exact origin/path/methods, verified labels only, model/request/byte/deadline remaining |
| `BrowserPanel` | investigation ID, frame sequence, API | Authenticated blob image only; loading/error/identity label text |
| `EvidencePanel` | evidence DTOs | Normalized fields and citation IDs as React text nodes |
| `ConclusionCard` | conclusion DTO | Verdict, summary, citations, every limitation, recommended human next step |
| `InvestigationControls` | investigation ID/status/API | `advance` in waiting-approval or planning, durable `stop`, `resume` only in paused |
| `CaseSetup` | project/setup API | Project, exact loopback scope, exactly two write-only identities, objective, preflight proposal |

Approval buttons call only the exact action endpoints. Stop changes local button state to `Stopping investigation` as soon as the `202` acknowledgment resolves and prevents another call; resume appears only for paused investigations. `ConclusionCard` never maps `supported` to a more certain word than “Supported”.

The reducer handles only the approved persisted event vocabulary:

```typescript
case "plan.created":
case "plan.updated": return {...state, plan: event.data.plan};
case "hypothesis.created":
case "hypothesis.updated": return {...state, hypotheses: upsertById(state.hypotheses, event.data.hypothesis)};
case "policy.blocked": return {...state, latestPolicy: event.data.decision, events: appendActivity(state.events, event)};
case "evidence.created": return {...state, evidence: upsertById(state.evidence, event.data.evidence)};
case "tool.completed": return event.data.tool_kind === "browser"
  ? {...state, frameSequence: Math.max(state.frameSequence, event.data.frame_sequence)}
  : state;
case "investigation.paused":
case "investigation.stopped": return {...state, status: "stopped"};
case "investigation.completed": return {...state, status: "complete", conclusion: event.data.conclusion};
case "investigation.failed": return {...state, status: "failed"};
default: return {...state, events: appendActivity(state.events, event)};
```

- [ ] **Step 5: Write browser E2E for the complete flow**

```typescript
import {expect, type Page, test} from "@playwright/test";

async function configureExactLoopbackScopeAndIdentities(page: Page): Promise<void> {
  await page.getByRole("button", {name: "Configure scope"}).click();
  await page.getByLabel("Allowed origin").fill("http://127.0.0.1:8080");
  await page.getByLabel("Allowed path prefix").fill("/api/");
  await page.getByRole("checkbox", {name: "GET"}).check();
  await page.getByRole("checkbox", {name: "HEAD"}).check();
  await page.getByRole("checkbox", {name: "OPTIONS"}).check();
  await page.getByRole("button", {name: "Save scope"}).click();

  for (const [label, secret] of [
    ["Account A", "lab-account-a-token-v1"],
    ["Account B", "lab-account-b-token-v1"],
  ] as const) {
    await page.getByRole("button", {name: "Add identity"}).click();
    await page.getByLabel("Identity label").fill(label);
    await page.getByLabel("Identity origin").fill("http://127.0.0.1:8080");
    await page.getByLabel("Credential type").selectOption("bearer_token");
    await page.getByLabel("Credential value").fill(secret);
    await page.getByRole("button", {name: "Save identity"}).click();
  }
}

async function approveIdentityPreflight(page: Page): Promise<void> {
  await page.getByRole("button", {name: "Create identity preflight"}).click();
  await page.getByRole("button", {name: "Approve exact actions"}).click();
  await page.getByRole("button", {name: "Run approved preflight"}).click();
  await expect(page.getByText("2 verified identities", {exact: true})).toBeVisible();
}

type CaseMode = "vulnerable" | "secure" | "ambiguous";

async function createCase(page: Page, mode: CaseMode): Promise<{caseId: string; bootstrapUrl: string}> {
  const control = await page.request.post("http://127.0.0.1:8764/cases", {
    data: {mode},
  });
  expect(control.ok()).toBeTruthy();
  const payload = await control.json() as {case_id: string; bootstrap_url: string};
  return {caseId: payload.case_id, bootstrapUrl: payload.bootstrap_url};
}

async function createReadyInvestigation(page: Page, bootstrapUrl: string): Promise<void> {
  await page.goto(bootstrapUrl);
  await page.getByRole("button", {name: "New project"}).click();
  await page.getByLabel("Project name").fill("IDOR lab");
  await page.getByRole("button", {name: "Create project"}).click();
  await configureExactLoopbackScopeAndIdentities(page);
  await page.getByLabel("Objective").fill("Investigate whether Account B can read Account A order 1048");
  await page.getByRole("button", {name: "Create investigation"}).click();
  await approveIdentityPreflight(page);
}

async function runApprovedInvestigation(page: Page): Promise<void> {
  await page.getByRole("button", {name: "Start investigation"}).click();
  await page.getByRole("button", {name: "Approve exact actions"}).click();
  await page.getByRole("button", {name: "Run approved actions"}).click();
}

test.each([
  ["vulnerable", "Supported"],
  ["secure", "Not supported"],
  ["ambiguous", "Inconclusive"],
] as const)("completes the %s controlled-lab investigation", async ({page}, mode, verdict) => {
  const {caseId, bootstrapUrl} = await createCase(page, mode);
  await createReadyInvestigation(page, bootstrapUrl);
  await runApprovedInvestigation(page);
  await expect(page.getByText(verdict, {exact: true})).toBeVisible();
  const storage = await page.evaluate(async () => ({
    cookie: document.cookie,
    local: localStorage.length,
    session: sessionStorage.length,
    indexed: (await indexedDB.databases()).length,
  }));
  expect(storage).toEqual({cookie: "", local: 0, session: 0, indexed: 0});
  const assertions = await page.request.get(`http://127.0.0.1:8764/cases/${caseId}/assertions`);
  expect(await assertions.json()).toMatchObject({
    workbench_token_seen_by_lab: false,
    duplicate_tool_run_count: 0,
    mutation_origin_mismatch_count: 0,
  });
});

test("edit and reject never execute the superseded proposal", async ({page}) => {
  const {caseId, bootstrapUrl} = await createCase(page, "vulnerable");
  await createReadyInvestigation(page, bootstrapUrl);
  await page.getByRole("button", {name: "Start investigation"}).click();
  await page.getByRole("button", {name: "Edit proposal"}).click();
  await page.getByLabel("Purpose").fill("Compare only order 1048");
  await page.getByRole("button", {name: "Save new proposal"}).click();
  await expect(page.getByText("New approval required", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Reject proposal"}).click();
  await expect(page.getByText("Rejected", {exact: true})).toBeVisible();
  const assertions = await page.request.get(`http://127.0.0.1:8764/cases/${caseId}/assertions`);
  expect(await assertions.json()).toMatchObject({tool_started_count: 2, superseded_digest_executed: false});
});

test("invalid or duplicate identities cannot start research", async ({page}) => {
  const {bootstrapUrl} = await createCase(page, "vulnerable");
  await page.goto(bootstrapUrl);
  await page.getByRole("button", {name: "New project"}).click();
  await page.getByLabel("Project name").fill("Invalid identity case");
  await page.getByRole("button", {name: "Create project"}).click();
  await configureExactLoopbackScopeAndIdentities(page);
  await page.getByRole("button", {name: "Add identity"}).click();
  await page.getByLabel("Identity label").fill("Account A");
  await page.getByLabel("Identity origin").fill("http://127.0.0.1:8080");
  await page.getByLabel("Credential type").selectOption("bearer_token");
  await page.getByLabel("Credential value").fill("invalid-token");
  await page.getByRole("button", {name: "Save identity"}).click();
  await expect(page.getByText("Identity label already exists", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Cancel identity"}).click();
  await page.getByRole("row", {name: /Account B/}).getByRole("button", {name: "Replace credential"}).click();
  await page.getByLabel("Credential value").fill("invalid-token");
  await page.getByRole("button", {name: "Save replacement"}).click();
  await page.getByLabel("Objective").fill("Investigate order 1048");
  await page.getByRole("button", {name: "Create investigation"}).click();
  await page.getByRole("button", {name: "Create identity preflight"}).click();
  await page.getByRole("button", {name: "Approve exact actions"}).click();
  await page.getByRole("button", {name: "Run approved preflight"}).click();
  await expect(page.getByText("Identity verification failed", {exact: true})).toBeVisible();
  await expect(page.getByRole("button", {name: "Start investigation"})).toBeDisabled();
});

test("durable stop survives workbench restart and does not replay a tool", async ({page}) => {
  const {caseId, bootstrapUrl} = await createCase(page, "vulnerable");
  await createReadyInvestigation(page, bootstrapUrl);
  await page.request.post(`http://127.0.0.1:8764/cases/${caseId}/pause-next-response`);
  await runApprovedInvestigation(page);
  await expect(page.getByText("Executing", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Stop investigation"}).click();
  await expect(page.getByText("Stopped", {exact: true})).toBeVisible();
  const restarted = await page.request.post(`http://127.0.0.1:8764/cases/${caseId}/restart-workbench`);
  const {bootstrap_url: nextUrl} = await restarted.json() as {bootstrap_url: string};
  await page.goto(nextUrl);
  await expect(page.getByText("Stopped", {exact: true})).toBeVisible();
  await page.getByRole("button", {name: "Resume investigation"}).click();
  await page.getByRole("button", {name: "Start investigation"}).click();
  await page.getByRole("button", {name: "Approve exact actions"}).click();
  await page.getByRole("button", {name: "Run approved actions"}).click();
  await expect(page.getByText("Supported", {exact: true})).toBeVisible();
  const assertions = await page.request.get(`http://127.0.0.1:8764/cases/${caseId}/assertions`);
  expect(await assertions.json()).toMatchObject({duplicate_tool_run_count: 0});
});

test("event reconnect resumes after the last id and malicious target text stays inert", async ({page}) => {
  const {caseId, bootstrapUrl} = await createCase(page, "ambiguous");
  await createReadyInvestigation(page, bootstrapUrl);
  await page.request.post(`http://127.0.0.1:8764/cases/${caseId}/drop-next-event-stream`);
  await runApprovedInvestigation(page);
  const malicious = "<img src=x onerror=window.pwned=true>";
  await expect(page.getByText(malicious, {exact: true})).toBeVisible();
  expect(await page.locator("img[src='x']").count()).toBe(0);
  await expect(page.getByText("Inconclusive", {exact: true})).toBeVisible();
  const assertions = await page.request.get(`http://127.0.0.1:8764/cases/${caseId}/assertions`);
  expect(await assertions.json()).toMatchObject({event_reconnect_after: expect.any(Number), missing_event_count: 0});
});
```

`CaseSetup` implements exactly the labels used above and never reads a saved secret back. `ApprovalCard` grants only the displayed digest; its separate **Run approved actions** button calls the authenticated `advance` endpoint so the UI never implies that approval itself performs the effect. Task 30 wires these components through `App`, the typed client, store reducer, and fresh test services.

`tests/workbench/e2e_server.py` binds a test-only control app to `127.0.0.1:8764`, the workbench to `127.0.0.1:8765`, and the lab to `127.0.0.1:8080`. It serializes mutations with one `asyncio.Lock` and exposes only this test contract:

```text
GET  /health                                      -> 200 {"ready":true}
POST /cases                                       body {"mode":"vulnerable"|"secure"|"ambiguous"}
                                                   -> 201 {"case_id":"<uuid>","bootstrap_url":"http://127.0.0.1:8765/#bootstrap=<nonce>"}
POST /cases/{case_id}/pause-next-response         -> 204
POST /cases/{case_id}/drop-next-event-stream      -> 204
POST /cases/{case_id}/restart-workbench           -> 200 {"bootstrap_url":"http://127.0.0.1:8765/#bootstrap=<new-nonce>"}
GET  /cases/{case_id}/assertions                  -> 200 CaseAssertions
```

`POST /cases` recreates a case-specific temporary database/keyring namespace, resets lab fixtures, selects the hidden lab mode, starts a fresh workbench, and creates a one-use nonce. Restart preserves that database/vault/lab state, stops and joins the workbench, starts it on the same port, runs recovery, and mints a new nonce. `pause-next-response` blocks one lab body after headers until cancellation or 10 seconds; `drop-next-event-stream` closes one authenticated stream immediately after a persisted event. `CaseAssertions` contains only `workbench_token_seen_by_lab: bool`, `duplicate_tool_run_count: int`, `tool_started_count: int`, `superseded_digest_executed: bool`, `event_reconnect_after: int | null`, `missing_event_count: int`, and `mutation_origin_mismatch_count: int`; it never returns identity/provider secrets, raw traffic, or the hidden mode. This module is not imported by or packaged with `bugintel.workbench`; all three servers and temporary paths close on process exit.

Use this exact Playwright configuration:

```typescript
import {defineConfig} from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  use: {baseURL: "http://127.0.0.1:8765", trace: "retain-on-failure"},
  webServer: {
    command: "python ../tests/workbench/e2e_server.py",
    url: "http://127.0.0.1:8764/health",
    reuseExistingServer: false,
    timeout: 30_000,
  },
});
```

Every test calls `POST /cases` and receives a fresh nonce. The mode matrix covers supported/not-supported/inconclusive, storage/cookie absence, exact mutation origin, and workbench-token isolation; the dedicated cases cover edit/reject, durable stop/restart/resume, invalid/duplicate identities, malicious text, and authenticated reconnect after the last persisted event ID.

- [ ] **Step 6: Run the workbench completion gate and commit**

```powershell
npm run typecheck --prefix web
npm test --prefix web
npm run build --prefix web
npm run e2e --prefix web
python -m pytest tests/workbench -q
python -m pytest tests/cases tests/policy tests/runtime tests/tools tests/contracts tests/lab_scenarios tests/workbench -q
git diff --check
git add web/src/App.tsx web/src/api/client.ts web/src/state/store.tsx web/src/test/fakes.ts web/src/components web/playwright.config.ts web/e2e tests/workbench/e2e_server.py
git commit -m "feat: complete the controlled-lab workbench"
```

## Workbench Completion Gate

The gate passes only when the deterministic vulnerable, secure, and ambiguous flows complete through the actual local API and React app; all case/event/action endpoints require the memory-only bearer; no workbench credential reaches the lab; exact approvals are visible and enforced; stop/restart never replay an action; browser images are ephemeral; all untrusted strings render inertly; frontend type/tests/build/E2E pass; backend workbench and prior plan tests pass; and the worktree is clean.
