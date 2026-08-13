# Blackhole Web/API Investigator Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the fail-closed domain, persistence, secret, scope, budget, and approval foundation required before any new live adapter is allowed to exist.

**Architecture:** New code lives beside the legacy system under `bugintel/cases`, `bugintel/policy`, and `bugintel/runtime`; it does not call the legacy live integrations. Immutable Pydantic contracts, a SQLite/WAL event store, capability-separated secrets, canonical numeric-loopback scope, persistent hard budgets, and digest-bound approvals form the trusted base for the later agent loop.

**Tech Stack:** Python 3.11/3.12, Pydantic 2.13, SQLite, keyring 25.7, pytest, coverage, and Ruff.

## Global Constraints

- Implement only on `codex/web-api-investigator-alpha`; keep every commit local unless the researcher separately authorizes a push.
- Do not change version `1.84.1`, create a tag or release, open a pull request, merge to `main`, or announce a release.
- Support Python 3.11 and 3.12 only; set package metadata to `>=3.11,<3.13` and test both versions later in CI.
- The only alpha target form is `http://127.0.0.1:` followed by an explicit decimal port; reject every hostname, IPv6 address, alternate IPv4 spelling, implicit port, HTTPS origin, LAN address, and external origin.
- The only target methods are `GET`, `HEAD`, and `OPTIONS`; no user approval can enable a request body, mutation, arbitrary header, shell, curl argv, browser script, click, form fill, upload, or filesystem-write tool.
- No new network adapter may be introduced in this plan. The first live worker is added only after all foundation gates pass.
- Keep configured provider keys and identity secrets out of model context, SQLite, logs, events, evidence, exports, filenames, URLs, and exception text.
- Store raw target content nowhere. Persist only explicitly branded sanitized payloads.
- Do not import or route the new runtime through `bugintel/core/scope_guard.py`, `bugintel/integrations/web_fetcher.py`, `bugintel/integrations/playwright_runner.py`, `bugintel/core/evidence_store.py`, or `bugintel/analyzers/secret_redactor.py`.
- Use UUIDs for durable identifiers, UTC timestamps, canonical JSON with sorted keys and compact separators for hashes, and `ConfigDict(extra="forbid", frozen=True)` for immutable contracts.
- Alpha hard ceilings are: 4 top-level actions per batch, 40 target requests per investigation, 8 requests per minute, 5-minute approval expiry, 15-second resource timeout, 60-second batch timeout, 30 active minutes, 1 MiB per resource, 5 MiB per browser navigation, a schema ceiling of 40 browser subresources, one top-level browser navigation, 24 model decisions, and 24 provider calls. All limits apply together, so the 40-request total makes the effective fresh-investigation browser maximum 39 subresources after its initial document and lowers it further after prior requests.
- Every task follows red-green-refactor: observe the named failing test, implement the smallest complete behavior, run the focused test, run the plan-level regression set, and commit only the task files.

---

## Plan Sequence

1. This plan: trusted foundation.
2. `2026-08-13-web-api-investigator-agent-loop.md`: lab, gateway, adapters, model boundary, controller, recovery, and export.
3. `2026-08-13-web-api-investigator-workbench.md`: authenticated local API and Codex-style React workbench.
4. `2026-08-13-web-api-investigator-hardening.md`: security matrix, live-model evaluation gate, packaging, documentation, and CI.

## File Structure

Create these focused units during this plan:

```text
bugintel/
  cases/
    __init__.py
    models.py              # immutable durable domain contracts
    redaction.py           # shared sanitizer and ingress firewall
    database.py            # connection setup, WAL, migrations, transactions
    events.py              # append-only sequenced events
    repository.py          # project/investigation projections
    secrets.py             # vault namespaces and capabilities
    migrations/
      0001_core.sql
      0002_events.sql
      0003_projections.sql
      0004_identities.sql
      0005_budgets.sql
      0006_approvals.sql
  policy/
    __init__.py
    scope.py               # canonical numeric-loopback policy
    budgets.py             # persistent reservation and charge ledger
    approval.py            # canonical batches and exact grants
  runtime/
    __init__.py
    state_machine.py       # service-owned lifecycle transitions
    tool_protocol.py       # strict model-visible action schemas
tests/
  cases/
  policy/
  runtime/
```

Existing files modified in this plan are limited to `pyproject.toml`, `.gitignore`, `bugintel/integrations/playwright_runner.py`, `bugintel/cli.py`, `tests/test_cli.py`, and the existing Playwright/demo tests needed to restore the Windows baseline.

---

### Task 1: Restore the Cross-Platform Legacy Baseline

**Files:**
- Modify: `bugintel/integrations/playwright_runner.py:347-366`
- Modify: `bugintel/cli.py:19566-19571`
- Modify: `tests/test_cli.py:248-383`
- Modify: `tests/test_blackhole_demo_case_pack_cli.py`
- Test: `tests/test_playwright_runner.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: existing `PlaywrightArtifactPlan`, Typer CLI output, and demo case-pack command.
- Produces: portable POSIX-form artifact strings in serialized plans and explicit UTF-8 demo exports; it does not alter any live behavior.

- [ ] **Step 1: Capture the six known Windows failures and the UTF-8 regression**

Run exactly:

```powershell
python -m pytest -q `
  tests/test_cli.py::test_execute_playwright_plan_command_blocks_out_of_scope_url `
  tests/test_cli.py::test_build_playwright_request_command_writes_json_request `
  tests/test_playwright_runner.py::test_build_playwright_artifact_plan_returns_safe_paths `
  tests/test_playwright_runner.py::test_build_playwright_execution_request_is_pre_execution_only `
  tests/test_playwright_runner.py::test_run_playwright_adapter_stub_returns_not_implemented_capture_result `
  tests/test_playwright_runner.py::test_execute_playwright_plan_routes_through_adapter_stub_after_safety_gates
```

Expected before the fix: six failures caused by Rich line wrapping and native Windows path separators.

Add this byte-level assertion to `tests/test_blackhole_demo_case_pack_cli.py`:

```python
raw_markdown = markdown_path.read_bytes()
assert raw_markdown.decode("utf-8") == markdown_path.read_text(encoding="utf-8")
```

Run its node and expect the current Windows implementation to fail with a UTF-8 decoding error.

- [ ] **Step 2: Make serialized artifact paths platform-independent**

Add a private serializer and use it for all five `PlaywrightArtifactPlan` fields:

```python
def _portable_artifact_path(path: Path) -> str:
    return path.as_posix()


return PlaywrightArtifactPlan(
    artifact_dir=_portable_artifact_path(artifact_dir),
    screenshot_path=_portable_artifact_path(artifact_dir / "screenshot.png"),
    html_snapshot_path=_portable_artifact_path(artifact_dir / "page.html"),
    network_log_path=_portable_artifact_path(artifact_dir / "network.json"),
    trace_path=_portable_artifact_path(artifact_dir / "trace.zip"),
)
```

Keep `Path(request.artifacts.artifact_dir)` at the filesystem boundary so portable serialized strings still create native paths correctly.

- [ ] **Step 3: Remove duplicate tests, normalize only the brittle Rich assertion, and encode exports explicitly**

Delete the duplicate function blocks at the second definitions of `test_execute_playwright_plan_command_blocks_by_default` and `test_execute_playwright_plan_command_blocks_out_of_scope_url`. In the retained out-of-scope test, assert normalized display text:

```python
normalized_output = " ".join(result.output.split())
assert "Domain not in scope: evil.example.net" in normalized_output
```

Change both demo writes to explicit UTF-8:

```python
json_output.write_text(
    json.dumps(data, indent=2, sort_keys=True) + "\n",
    encoding="utf-8",
)
output_file.write_text(pack.to_markdown(), encoding="utf-8")
```

- [ ] **Step 4: Verify the focused regressions**

Run:

```powershell
python -m pytest -q tests/test_playwright_runner.py tests/test_cli.py tests/test_blackhole_demo_case_pack_cli.py
```

Expected: all selected tests pass; pytest collects each retained test name exactly once.

- [ ] **Step 5: Verify the legacy suite and commit**

Run:

```powershell
python -m pytest -q
git diff --check
git add bugintel/integrations/playwright_runner.py bugintel/cli.py tests/test_cli.py tests/test_playwright_runner.py tests/test_blackhole_demo_case_pack_cli.py
git commit -m "fix: restore Windows test portability"
```

Expected: 0 failures, no whitespace errors, and one focused local commit.

### Task 2: Freeze Python Support, Dependencies, and Domain Contracts

**Files:**
- Modify: `pyproject.toml:10-44`
- Modify: `.gitignore`
- Create: `bugintel/cases/__init__.py`
- Create: `bugintel/cases/models.py`
- Create: `bugintel/policy/__init__.py`
- Create: `bugintel/runtime/__init__.py`
- Create: `tests/cases/test_models.py`

**Interfaces:**
- Consumes: no new runtime interfaces.
- Produces: `InvestigationState`, `HypothesisStatus`, `ToolRunState`, `Verdict`, `Project`, `IdentityRef`, `Investigation`, `Plan`, `Hypothesis`, `ToolRun`, `Observation`, `EvidenceRecord`, and `Conclusion`.

- [ ] **Step 1: Write strict model tests**

Create tests that prove immutability, forbidden extra fields, UUID validation, and terminal-state vocabulary:

```python
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bugintel.cases.models import InvestigationState, Project


def test_project_is_frozen_and_rejects_unknown_fields() -> None:
    project = Project(
        id=uuid4(),
        name="Local IDOR lab",
        created_at=datetime.now(UTC),
    )
    with pytest.raises(ValidationError):
        Project.model_validate({**project.model_dump(), "secret": "forbidden"})
    with pytest.raises(ValidationError):
        project.name = "changed"


def test_terminal_investigation_states_are_exact() -> None:
    assert {state.value for state in InvestigationState if state.is_terminal} == {
        "completed",
        "stopped",
        "failed",
    }
```

- [ ] **Step 2: Run the tests and observe the missing contracts**

Run:

```powershell
python -m pytest tests/cases/test_models.py -v
```

Expected: collection fails because `bugintel.cases.models` does not exist.

- [ ] **Step 3: Add dependency bounds without changing the product version**

Set `requires-python = ">=3.11,<3.13"`. Add these direct dependencies:

```toml
"pydantic>=2.13.4,<3.0",
"keyring>=25.7.0,<26.0",
```

Add these development dependencies while retaining pytest:

```toml
"coverage>=7.10,<8.0",
"ruff>=0.16,<1.0",
"build>=1.3,<2.0",
"pip-audit>=2.9,<3.0",
```

Do not edit `version = "1.84.1"`. Add `.coverage*`, `htmlcov/`, `.pytest_cache/`, and `web/node_modules/` to `.gitignore`.

- [ ] **Step 4: Implement immutable domain models**

Use one shared strict base and exact enums:

```python
from __future__ import annotations

from enum import StrEnum
from typing import Any, Literal
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class FrozenModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class InvestigationState(StrEnum):
    CREATED = "created"
    PLANNING = "planning"
    PASSIVE_ANALYSIS = "passive_analysis"
    WAITING_APPROVAL = "waiting_approval"
    EXECUTING = "executing"
    OBSERVING = "observing"
    PAUSED = "paused"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"

    @property
    def is_terminal(self) -> bool:
        return self in {self.COMPLETED, self.STOPPED, self.FAILED}


class HypothesisStatus(StrEnum):
    PROPOSED = "proposed"
    TESTING = "testing"
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class ToolRunState(StrEnum):
    PROPOSED = "proposed"
    STARTED = "started"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


class Verdict(StrEnum):
    SUPPORTED = "supported"
    REJECTED = "rejected"
    INCONCLUSIVE = "inconclusive"


class Project(FrozenModel):
    id: UUID
    name: str = Field(min_length=1, max_length=120)
    created_at: AwareDatetime


class SecretNamespace(StrEnum):
    PROVIDER = "provider"
    IDENTITY = "identity"


class SecretRef(FrozenModel):
    id: UUID
    namespace: SecretNamespace
    version: int = Field(ge=1)


class IdentityRef(FrozenModel):
    id: UUID
    label: str = Field(min_length=1, max_length=80)
    secret_ref: SecretRef
    secret_version: int = Field(ge=1)
    target_origin: str
    header_profile: Literal["session_cookie", "bearer_token"]
    verified_subject_id: str | None = None
    verification_evidence_id: UUID | None = None
    verified_target_origin: str | None = None
    verified_at: AwareDatetime | None = None
    created_at: AwareDatetime
    last_used_at: AwareDatetime | None = None


class Investigation(FrozenModel):
    id: UUID
    project_id: UUID
    objective: str = Field(min_length=1, max_length=8192)
    pending_objective: str | None = None
    state: InvestigationState
    active_scope_snapshot_id: UUID
    selected_identity_ids: tuple[UUID, UUID]
    current_plan_id: UUID | None = None
    stop_requested: bool = False
    created_at: AwareDatetime
    updated_at: AwareDatetime
    terminal_at: AwareDatetime | None = None


class Plan(FrozenModel):
    id: UUID
    investigation_id: UUID
    version: int = Field(ge=1)
    summary: str = Field(min_length=1, max_length=500)
    steps: tuple[str, ...] = Field(min_length=1, max_length=8)
    created_at: AwareDatetime


class Hypothesis(FrozenModel):
    id: UUID
    investigation_id: UUID
    statement: str = Field(min_length=1, max_length=500)
    status: HypothesisStatus
    evidence_ids: tuple[UUID, ...] = ()
    updated_at: AwareDatetime


class ToolRun(FrozenModel):
    id: UUID
    investigation_id: UUID
    action_batch_id: UUID
    action_id: UUID
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity_ref: UUID
    approval_grant_id: UUID | None
    state: ToolRunState
    started_at: AwareDatetime | None = None
    ended_at: AwareDatetime | None = None
    evidence_ids: tuple[UUID, ...] = ()
    safe_error_code: str | None = None


class Observation(FrozenModel):
    id: UUID
    investigation_id: UUID
    tool_run_id: UUID
    summary: str = Field(min_length=1, max_length=1000)
    semantic_fields: dict[str, Any]
    evidence_ids: tuple[UUID, ...] = Field(min_length=1)
    created_at: AwareDatetime


class EvidenceRecord(FrozenModel):
    id: UUID
    investigation_id: UUID
    action_id: UUID
    tool_run_id: UUID
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    identity_label: str
    canonical_url: str
    method: Literal["GET", "HEAD", "OPTIONS"]
    status_code: int | None
    safe_headers: dict[str, Any]
    content_type: str | None
    sanitized_payload: dict[str, Any]
    semantic_fields: dict[str, Any]
    sanitized_body_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    body_size: int = Field(ge=0)
    policy_decision_id: UUID
    approval_grant_id: UUID
    content_hash: str = Field(pattern=r"^[0-9a-f]{64}$")
    sanitizer_version: Literal["alpha-1"] = "alpha-1"
    created_at: AwareDatetime


class Conclusion(FrozenModel):
    id: UUID
    investigation_id: UUID
    verdict: Verdict
    cited_evidence_ids: tuple[UUID, ...]
    supported_claims: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    limitations: tuple[str, ...]
    confidence_rationale: str = Field(min_length=1, max_length=1000)
    recommended_human_next_step: str = Field(min_length=1, max_length=1000)
    created_at: AwareDatetime
```

These pre-persistence contracts intentionally use plain strings/dictionaries only until Task 3 creates the branded sanitizer types. Task 3 replaces `Investigation.objective`, `pending_objective`, plan/hypothesis/observation/conclusion text, and every event/evidence dictionary with `SanitizedText` or `SanitizedPayload` before any repository exists. Model-provider response schemas in the Agent Loop remain untrusted plain `str`; the controller must pass them through `RedactionPolicy` to obtain branded values before domain construction.

- [ ] **Step 5: Verify models, metadata, and legacy regression**

Run:

```powershell
python -m pip install -e ".[dev]"
python -m pytest tests/cases/test_models.py -v
python -m pytest -q
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases tests/cases
git diff --check
```

Expected: all commands succeed and `python -c "import sys; assert (3, 11) <= sys.version_info[:2] < (3, 13)"` succeeds.

- [ ] **Step 6: Commit**

```powershell
git add pyproject.toml .gitignore bugintel/cases bugintel/policy/__init__.py bugintel/runtime/__init__.py tests/cases/test_models.py
git commit -m "feat: define alpha domain contracts"
```

### Task 3: Add Shared Redaction and the Message-Ingress Firewall

**Files:**
- Create: `bugintel/cases/redaction.py`
- Modify: `bugintel/cases/models.py`
- Create: `tests/cases/test_redaction.py`

**Interfaces:**
- Consumes: a `SecretMatcher` capability that returns match metadata without returning a secret value.
- Produces: nominal `SanitizedPayload`, `RedactionPolicy.redact_text`, `redact_mapping`, `redact_url`, canonical `serialize_payload`/`restore_payload` and `restore_text` persistence boundaries, `IngressFirewall.inspect`, and `IngressDecision`.

- [ ] **Step 1: Write canary and key-aware failing tests**

```python
import pytest
from pydantic import ValidationError

from bugintel.cases.redaction import (
    IngressFirewall,
    RedactionPolicy,
    SanitizedPayload,
    SanitizedPersistenceError,
    StaticSecretMatcher,
)


def test_redacts_sensitive_keys_recursively() -> None:
    policy = RedactionPolicy()
    cleaned = policy.redact_mapping(
        {"Cookie": "session=abc", "nested": {"refresh_token": "short"}}
    )
    assert cleaned == {
        "Cookie": "[REDACTED]",
        "nested": {"refresh_token": "[REDACTED]"},
    }


def test_rejects_configured_secret_before_persistence() -> None:
    firewall = IngressFirewall(StaticSecretMatcher(("configured-canary",)))
    decision = firewall.inspect("please use configured-canary")
    assert decision.allowed is False
    assert decision.category == "configured_credential"
    assert "configured-canary" not in decision.safe_event_payload.model_dump_json()


def test_rejects_message_larger_than_8192_utf8_bytes() -> None:
    firewall = IngressFirewall(StaticSecretMatcher(()))
    assert firewall.inspect("é" * 4097).category == "message_too_large"


def test_only_policy_can_restore_canonical_persisted_payload(policy) -> None:
    payload = policy.sanitize_payload({"safe": ["value"]})
    stored = policy.serialize_payload(payload)
    assert policy.restore_payload(stored) == payload
    with pytest.raises(ValidationError):
        SanitizedPayload.model_validate_json(stored)
    with pytest.raises(SanitizedPersistenceError):
        policy.restore_payload('{"Cookie":"raw-session"}')


@pytest.mark.parametrize("non_finite", [float("nan"), float("inf"), float("-inf")])
def test_sanitized_payload_rejects_non_finite_floats(policy, non_finite) -> None:
    with pytest.raises(TypeError):
        policy.sanitize_payload({"number": non_finite})
```

Use this exact detector table in the same test module:

```python
@pytest.mark.parametrize(
    ("raw", "category"),
    [
        ({"Authorization": "Basic YTpi"}, "authorization"),
        ({"Proxy-Authorization": "Bearer opaque"}, "proxy_authorization"),
        ({"Cookie": "session=opaque"}, "cookie"),
        ({"Set-Cookie": "session=opaque"}, "set_cookie"),
        ({"api_key": "short"}, "api_key"),
        ({"access_token": "short"}, "access_token"),
        ({"refresh-token": "short"}, "refresh_token"),
        ({"session_id": "short"}, "session_id"),
        ({"password": "short"}, "password"),
        ({"client_secret": "short"}, "client_secret"),
    ],
)
def test_sensitive_keys_replace_complete_values(policy, raw, category) -> None:
    serialized = policy.sanitize_payload(raw).model_dump_json()
    assert "short" not in serialized and "opaque" not in serialized and "YTpi" not in serialized
    assert "[REDACTED]" in serialized


@pytest.mark.parametrize("value", ["sk-test", "ghp_test", "github_pat_test", "xoxb-test", "xoxp-test"])
def test_provider_token_forms_return_category_only(policy, value) -> None:
    assert policy.detect_category(value) == "provider_token"


@pytest.mark.parametrize("key", [
    "access_token", "refresh_token", "api_key", "apikey", "key", "token",
    "session", "sessionid", "password", "client_secret",
])
def test_sensitive_query_values_are_redacted(policy, key) -> None:
    sanitized = policy.redact_url(f"http://127.0.0.1:8080/x?{key}=canary&safe=ok#fragment")
    assert "canary" not in sanitized and "fragment" not in sanitized and "safe=ok" in sanitized
```

- [ ] **Step 2: Run the focused tests and confirm failure**

```powershell
python -m pytest tests/cases/test_redaction.py -v
```

Expected: import failure for `bugintel.cases.redaction`.

- [ ] **Step 3: Implement branded sanitized data and fail-closed ingress**

```python
import json
import math
from types import MappingProxyType
from typing import Any, ClassVar, Mapping, Protocol

from pydantic import BaseModel, ConfigDict, field_serializer, model_validator
from pydantic_core import core_schema


class PersistenceError(RuntimeError):
    """Safe base class for repository serialization and storage failures."""


class SanitizedPersistenceError(PersistenceError):
    pass


class SanitizedText(str):
    _seal: ClassVar[object] = object()

    def __new__(cls, value: str, *, _seal: object):
        if _seal is not cls._seal:
            raise TypeError("SanitizedText must be created by RedactionPolicy")
        return str.__new__(cls, value)

    @classmethod
    def _from_policy(cls, value: str) -> "SanitizedText":
        return cls(value, _seal=cls._seal)

    @classmethod
    def __get_pydantic_core_schema__(cls, source_type, handler):
        return core_schema.is_instance_schema(
            cls,
            serialization=core_schema.to_string_ser_schema(),
        )


class _TrustedPayloadInput:
    def __init__(self, *, value: Mapping[str, Any], sanitizer_version: str, seal: object):
        self.value = value
        self.sanitizer_version = sanitizer_version
        self.seal = seal


class SanitizedPayload(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True, extra="forbid", frozen=True)
    _seal: ClassVar[object] = object()
    value: Mapping[str, Any]
    sanitizer_version: str = "alpha-1"

    @model_validator(mode="before")
    @classmethod
    def _require_policy_input(cls, data):
        if isinstance(data, cls):
            return data
        if not isinstance(data, _TrustedPayloadInput) or data.seal is not cls._seal:
            raise ValueError("SanitizedPayload must be created by RedactionPolicy")
        return {"value": data.value, "sanitizer_version": data.sanitizer_version}

    @field_serializer("value")
    def _serialize_value(self, value: Mapping[str, Any]) -> dict[str, Any]:
        return _thaw_sanitized(value)


def _freeze_sanitized(value: Any) -> Any:
    if isinstance(value, dict):
        return MappingProxyType({key: _freeze_sanitized(item) for key, item in value.items()})
    if isinstance(value, (list, tuple)):
        return tuple(_freeze_sanitized(item) for item in value)
    if isinstance(value, float) and not math.isfinite(value):
        raise TypeError("non-finite floats are not valid sanitized values")
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    raise TypeError("unsupported sanitized value")


def _thaw_sanitized(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {key: _thaw_sanitized(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw_sanitized(item) for item in value]
    return value


class RedactionPolicy:
    def sanitize_payload(self, value: dict[str, Any]) -> SanitizedPayload:
        redacted = self.redact_mapping(value)
        return SanitizedPayload.model_validate(_TrustedPayloadInput(
            value=_freeze_sanitized(redacted),
            sanitizer_version="alpha-1",
            seal=SanitizedPayload._seal,
        ))

    def serialize_payload(self, payload: SanitizedPayload) -> str:
        return json.dumps(
            payload.model_dump(mode="json"),
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        )

    def restore_payload(self, serialized: str) -> SanitizedPayload:
        try:
            parsed = json.loads(serialized)
        except (TypeError, ValueError) as error:
            raise SanitizedPersistenceError("invalid_sanitized_payload") from error
        if not isinstance(parsed, dict):
            raise SanitizedPersistenceError("invalid_sanitized_payload")
        if set(parsed) != {"value", "sanitizer_version"}:
            raise SanitizedPersistenceError("invalid_sanitized_payload")
        try:
            restored = self.sanitize_payload(parsed["value"])
        except (TypeError, ValueError) as error:
            raise SanitizedPersistenceError("invalid_sanitized_payload") from error
        if self.serialize_payload(restored) != serialized:
            raise SanitizedPersistenceError("stored_payload_failed_redaction_check")
        return restored

    def restore_text(self, stored: str) -> SanitizedText:
        restored = self.redact_text(stored)
        if str(restored) != stored:
            raise SanitizedPersistenceError("stored_text_failed_redaction_check")
        return restored


class SecretMatcher(Protocol):
    def match_category(self, text: str) -> str | None:
        raise NotImplementedError


class StaticSecretMatcher:
    def __init__(self, values: tuple[str, ...]):
        self._values = values

    def match_category(self, text: str) -> str | None:
        return "configured_credential" if any(value and value in text for value in self._values) else None


class IngressDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    allowed: bool
    sanitized_text: SanitizedText | None
    category: str | None
    safe_event_payload: SanitizedPayload


class IngressFirewall:
    MAX_UTF8_BYTES = 8192

    def __init__(self, matcher: SecretMatcher, policy: RedactionPolicy | None = None):
        self._matcher = matcher
        self._policy = policy or RedactionPolicy()

    def inspect(self, text: str) -> IngressDecision:
        if len(text.encode("utf-8")) > self.MAX_UTF8_BYTES:
            return self._reject("message_too_large")
        category = self._matcher.match_category(text) or self._policy.detect_category(text)
        if category is not None:
            return self._reject(category)
        sanitized = self._policy.redact_text(text)
        return IngressDecision(
            allowed=True,
            sanitized_text=sanitized,
            category=None,
            safe_event_payload=self._policy.sanitize_payload({"accepted": True}),
        )
```

`RedactionPolicy` compares lowercased keys after removing `-` and `_` against `authorization`, `proxyauthorization`, `cookie`, `setcookie`, `apikey`, `accesstoken`, `refreshtoken`, `sessionid`, `password`, and `clientsecret`; matches replace the complete value. Its query-key set is `access_token`, `refresh_token`, `api_key`, `apikey`, `key`, `token`, `session`, `sessionid`, `password`, and `client_secret`. Text detectors classify RFC Basic/Bearer authorization syntax, Cookie/Set-Cookie syntax, URL query pairs with those keys, and provider-token prefixes `sk-`, `ghp_`, `github_pat_`, `xoxb-`, and `xoxp-`. A detector returns only its category. `redact_mapping` recursively handles mappings, lists, and tuples; `redact_url` removes user info, replaces sensitive query values, and removes fragments. Policy methods return sealed `SanitizedText._from_policy(...)` or `RedactionPolicy.sanitize_payload(...)`; the latter redacts then recursively freezes all mappings/sequences. Both trusted brands use instance-only Pydantic schemas, so their constructors/parsing reject ordinary strings/dictionaries and parsed JSON cannot manufacture them. Every repository serializes payloads with `serialize_payload` and rehydrates persisted payload/text only with `restore_payload`/`restore_text`; a value whose canonical form would change under the current redaction policy fails closed as `SanitizedPersistenceError`. All concrete matcher methods return a category or `None` and never expose a secret value. `StaticSecretMatcher` exists only for deterministic tests; production assembly uses `VaultSecretMatcher` from Task 7.

- [ ] **Step 4: Replace unbranded persistent payload types**

Before any repository task begins, replace every persistable free-text field in `bugintel/cases/models.py` with `SanitizedText`: project name, identity label, objective/pending objective, plan summary/steps, hypothesis statement, tool identity label, observation summary, conclusion claims/limitations/rationale/next step, and any future action purpose/expected observation. Exact closed enums and service-generated safe reason codes remain ordinary strings. Change `Observation.semantic_fields`, `EvidenceRecord.sanitized_payload`, and every event-facing payload field to `SanitizedPayload`, then add this exact rejection test:

```python
def test_persistence_models_reject_unbranded_dicts(evidence_kwargs) -> None:
    with pytest.raises(ValidationError):
        EvidenceRecord(**{**evidence_kwargs, "sanitized_payload": {"raw": "value"}})
```

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/cases/test_models.py tests/cases/test_redaction.py -v
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases tests/cases
python -m ruff format --check bugintel/cases tests/cases
git diff --check
git add bugintel/cases/models.py bugintel/cases/redaction.py tests/cases/test_redaction.py
git commit -m "feat: add fail-closed secret redaction"
```

### Task 4: Add the SQLite/WAL Migration Engine

**Files:**
- Create: `bugintel/cases/database.py`
- Create: `bugintel/cases/migrations/0001_core.sql`
- Create: `tests/cases/test_database.py`

**Interfaces:**
- Consumes: a filesystem path supplied by the launcher later.
- Produces: `Database.open`, `connect`, `read_one`, `read_all`, `transaction`, and ordered checksum-verified migrations.

- [ ] **Step 1: Write migration, WAL, and rollback tests**

```python
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from queue import Queue

import sqlite3

import pytest

from bugintel.cases.database import Database


def test_open_enables_wal_foreign_keys_and_applies_migrations(tmp_path) -> None:
    database = Database.open(tmp_path / "case.db")
    with closing(database.connect()) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"
        assert connection.execute("PRAGMA foreign_keys").fetchone()[0] == 1
    assert database.schema_version == 1


def test_transaction_rolls_back_all_changes(tmp_path) -> None:
    database = Database.open(tmp_path / "case.db")
    with pytest.raises(RuntimeError):
        with database.transaction() as connection:
            connection.execute("INSERT INTO projects(id, name, created_at) VALUES(?, ?, ?)", ("p1", "name", "now"))
            raise RuntimeError("stop")
    assert database.read_one("SELECT count(*) FROM projects")[0] == 0


def test_two_threads_receive_distinct_connections_and_serialize_writes(tmp_path) -> None:
    database = Database.open(tmp_path / "case.db")
    connection_ids: Queue[int] = Queue()
    def insert(project_id: str) -> None:
        with database.transaction() as connection:
            connection_ids.put(id(connection))
            connection.execute(
                "INSERT INTO projects(id, name, created_at) VALUES(?, ?, ?)",
                (project_id, project_id, "2026-08-13T00:00:00+00:00"),
            )
    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(insert, ("p1", "p2")))
    assert len({connection_ids.get(), connection_ids.get()}) == 2
    assert database.read_one("SELECT count(*) FROM projects")[0] == 2
```

Add the exact checksum test:

```python
def test_reopen_rejects_changed_applied_migration(tmp_path, migration_source) -> None:
    copied = migration_source.copy_to(tmp_path / "migrations")
    database_path = tmp_path / "case.db"
    Database.open(database_path, migrations_path=copied)
    copied.joinpath("0001_core.sql").write_text("-- changed\n", encoding="utf-8")
    with pytest.raises(MigrationChecksumError):
        Database.open(database_path, migrations_path=copied)
```

- [ ] **Step 2: Run and observe the missing database module**

```powershell
python -m pytest tests/cases/test_database.py -v
```

Expected: import failure.

- [ ] **Step 3: Implement connection hardening and migrations**

```python
class Database:
    @classmethod
    def open(cls, path: Path, *, migrations_path: Path | None = None) -> "Database":
        path.parent.mkdir(parents=True, exist_ok=True)
        database = cls(path=path, migrations_path=migrations_path)
        with closing(database.connect()) as connection:
            connection.execute("PRAGMA journal_mode=WAL")
        database.apply_migrations()
        return database

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path, isolation_level=None, timeout=5.0)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA busy_timeout=5000")
        return connection

    @contextmanager
    def transaction(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        connection.execute("BEGIN IMMEDIATE")
        try:
            yield connection
        except BaseException:
            connection.rollback()
            raise
        else:
            connection.commit()
        finally:
            connection.close()
```

`Database.read_one/read_all` each open and close a read connection; `database.connection` is removed so no connection crosses a thread. Update the earlier test assertions to use these read helpers and a short-lived `connect()` context. `migrations_path` exists only as an explicit test seam; production assembly always leaves it `None`, which loads packaged migrations through `importlib.resources`. `0001_core.sql` creates `schema_migrations(version INTEGER PRIMARY KEY, name TEXT UNIQUE, sha256 TEXT, applied_at TEXT)` and `projects`. Sort migrations by numeric prefix, hash exact UTF-8 bytes, and reject an applied version whose name or hash differs.

- [ ] **Step 4: Verify reopen and atomic behavior**

```powershell
python -m pytest tests/cases/test_database.py -v
python -m pytest tests/cases -q
git diff --check
```

Expected: all case tests pass and no partially inserted project remains after rollback.

- [ ] **Step 5: Commit**

```powershell
git add bugintel/cases/database.py bugintel/cases/migrations/0001_core.sql tests/cases/test_database.py
git commit -m "feat: add transactional case database"
```

### Task 5: Add the Immutable Ordered Event Store

**Files:**
- Create: `bugintel/cases/events.py`
- Create: `bugintel/cases/migrations/0002_events.sql`
- Create: `tests/cases/test_events.py`

**Interfaces:**
- Consumes: `Database`, `SanitizedPayload`, an investigation UUID, and a caller-owned transaction.
- Produces: exact `EventType`, `EventDraft`, `EventRecord`, `EventStore.append`, and `EventStore.list_after`.

- [ ] **Step 1: Write ordering and append-only tests**

```python
from uuid import uuid4

from bugintel.cases.events import EventDraft, EventStore
from bugintel.cases.redaction import RedactionPolicy, SanitizedPayload


def test_append_assigns_strict_sequence_inside_caller_transaction(database, investigation_id) -> None:
    store = EventStore(database)
    policy = RedactionPolicy()
    with database.transaction() as connection:
        first = store.append(connection, investigation_id, EventDraft(
            type="investigation.created",
            correlation_id=uuid4(),
            payload=policy.sanitize_payload({"state": "created"}),
        ))
        second = store.append(connection, investigation_id, EventDraft(
            type="plan.created",
            correlation_id=uuid4(),
            payload=policy.sanitize_payload({"steps": ["compare identities"]}),
        ))
    assert (first.sequence, second.sequence) == (1, 2)


def test_event_store_has_no_update_or_delete_surface(database) -> None:
    store = EventStore(database)
    assert not hasattr(store, "update")
    assert not hasattr(store, "delete")
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/cases/test_events.py -v
```

Expected: missing module or missing migration failure.

- [ ] **Step 3: Create the append-only schema and store**

Define the exact event vocabulary before accepting any draft:

```python
class EventType(StrEnum):
    INVESTIGATION_CREATED = "investigation.created"
    SCOPE_VERIFIED = "scope.verified"
    IDENTITY_CONFIGURED = "identity.configured"
    IDENTITY_VERIFIED = "identity.verified"
    IDENTITY_REJECTED = "identity.rejected"
    MESSAGE_RECEIVED = "message.received"
    MESSAGE_REJECTED = "message.rejected"
    PLAN_CREATED = "plan.created"
    PLAN_UPDATED = "plan.updated"
    HYPOTHESIS_CREATED = "hypothesis.created"
    HYPOTHESIS_UPDATED = "hypothesis.updated"
    TOOL_PROPOSED = "tool.proposed"
    POLICY_ALLOWED = "policy.allowed"
    POLICY_BLOCKED = "policy.blocked"
    APPROVAL_REQUESTED = "approval.requested"
    APPROVAL_GRANTED = "approval.granted"
    APPROVAL_REJECTED = "approval.rejected"
    APPROVAL_EXPIRED = "approval.expired"
    TOOL_STARTED = "tool.started"
    TOOL_COMPLETED = "tool.completed"
    TOOL_FAILED = "tool.failed"
    TOOL_INTERRUPTED = "tool.interrupted"
    OBSERVATION_CREATED = "observation.created"
    EVIDENCE_CREATED = "evidence.created"
    MEMORY_UPDATED = "memory.updated"
    INVESTIGATION_PAUSED = "investigation.paused"
    INVESTIGATION_RESUMED = "investigation.resumed"
    INVESTIGATION_STOPPED = "investigation.stopped"
    INVESTIGATION_COMPLETED = "investigation.completed"
    INVESTIGATION_FAILED = "investigation.failed"


class EventDraft(FrozenModel):
    type: EventType
    correlation_id: UUID
    payload: SanitizedPayload
```

`0002_events.sql` creates an `investigations` parent row and this event constraint:

```sql
CREATE TABLE events (
    id TEXT PRIMARY KEY,
    investigation_id TEXT NOT NULL REFERENCES investigations(id),
    sequence INTEGER NOT NULL CHECK(sequence > 0),
    type TEXT NOT NULL,
    schema_version INTEGER NOT NULL CHECK(schema_version = 1),
    correlation_id TEXT NOT NULL,
    occurred_at TEXT NOT NULL,
    sanitized_payload_json TEXT NOT NULL,
    UNIQUE(investigation_id, sequence)
);
```

In `append`, calculate the next sequence under the caller's `BEGIN IMMEDIATE` transaction and serialize only `SanitizedPayload`:

```python
next_sequence = connection.execute(
    "SELECT COALESCE(MAX(sequence), 0) + 1 FROM events WHERE investigation_id = ?",
    (str(investigation_id),),
).fetchone()[0]
payload_json = self._redaction.serialize_payload(draft.payload)
```

`EventStore.list_after` and every later repository call `RedactionPolicy.restore_payload`/`restore_text` for stored branded fields; they never pass parsed JSON or ordinary strings directly into persistence models.

- [ ] **Step 4: Verify transaction ordering and commit**

```powershell
python -m pytest tests/cases/test_database.py tests/cases/test_events.py -v
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases tests/cases
git diff --check
git add bugintel/cases/events.py bugintel/cases/migrations/0002_events.sql tests/cases/test_events.py
git commit -m "feat: persist ordered investigation events"
```

### Task 6: Add Projections and the Service-Owned State Machine

**Files:**
- Create: `bugintel/cases/repository.py`
- Create: `bugintel/cases/memory.py`
- Create: `bugintel/runtime/state_machine.py`
- Create: `bugintel/cases/migrations/0003_projections.sql`
- Create: `tests/cases/test_repository.py`
- Create: `tests/cases/test_memory.py`
- Create: `tests/runtime/test_state_machine.py`

**Interfaces:**
- Consumes: domain models, `Database`, and `EventStore`.
- Produces: `validate_transition`, `CaseRepository.create_project`, `create_investigation`, `get_investigation`, `transition`, `edit_objective`, `CaseMemoryRepository.record_observation`, `list_endpoints`, `retrieve`, `compare`, `list_saved_comparisons`, `model_payload`, `model_summaries`, and projection/event atomicity.

- [ ] **Step 1: Write transition-table and atomic projection tests**

```python
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from bugintel.cases.models import InvestigationState
from bugintel.runtime.state_machine import InvalidTransition, validate_transition


def test_resume_always_returns_to_planning() -> None:
    validate_transition(InvestigationState.PAUSED, InvestigationState.PLANNING)


@pytest.mark.parametrize("terminal", [
    InvestigationState.COMPLETED,
    InvestigationState.STOPPED,
    InvestigationState.FAILED,
])
def test_terminal_states_have_no_outgoing_transition(terminal) -> None:
    with pytest.raises(InvalidTransition):
        validate_transition(terminal, InvestigationState.PLANNING)
```

In `tests/cases/test_repository.py`, add the exact atomicity proof:

```python
def test_event_failure_rolls_back_projection(repository, event_store, investigation) -> None:
    before = repository.get_investigation(investigation.id)
    event_store.fail_next_append = True
    with pytest.raises(SimulatedEventFailure):
        repository.transition(investigation.id, InvestigationState.PLANNING)
    assert repository.get_investigation(investigation.id) == before
    assert event_store.list_after(investigation.id, sequence=0) == ()
```

- [ ] **Step 2: Run focused tests and confirm failure**

```powershell
python -m pytest tests/runtime/test_state_machine.py tests/cases/test_repository.py -v
```

Expected: missing modules.

- [ ] **Step 3: Implement an explicit transition table**

```python
ALLOWED_TRANSITIONS: dict[InvestigationState, frozenset[InvestigationState]] = {
    InvestigationState.CREATED: frozenset({InvestigationState.PLANNING}),
    InvestigationState.PLANNING: frozenset({InvestigationState.PASSIVE_ANALYSIS, InvestigationState.WAITING_APPROVAL, InvestigationState.COMPLETED}),
    InvestigationState.PASSIVE_ANALYSIS: frozenset({InvestigationState.PLANNING, InvestigationState.WAITING_APPROVAL}),
    InvestigationState.WAITING_APPROVAL: frozenset({InvestigationState.EXECUTING, InvestigationState.PLANNING}),
    InvestigationState.EXECUTING: frozenset({InvestigationState.OBSERVING}),
    InvestigationState.OBSERVING: frozenset({InvestigationState.PLANNING, InvestigationState.COMPLETED}),
    InvestigationState.PAUSED: frozenset({InvestigationState.PLANNING}),
    InvestigationState.COMPLETED: frozenset(),
    InvestigationState.STOPPED: frozenset(),
    InvestigationState.FAILED: frozenset(),
}


def validate_transition(current: InvestigationState, requested: InvestigationState) -> None:
    if requested in {InvestigationState.PAUSED, InvestigationState.STOPPED, InvestigationState.FAILED} and not current.is_terminal:
        return
    if requested not in ALLOWED_TRANSITIONS[current]:
        raise InvalidTransition(current=current, requested=requested)
```

- [ ] **Step 4: Implement repository transactions**

`0003_projections.sql` creates project/investigation projections plus the dependency-neutral immutable storage table `scope_snapshots(id, digest UNIQUE, canonical_json, created_at)` with `UPDATE`/`DELETE` rejection triggers. Task 6 does not import or construct the not-yet-defined `ScopeSnapshot`; Task 9 adds the typed repository methods after defining that contract. `CaseRepository.transition` calls `validate_transition`, updates the projection, and appends the matching event using one `Database.transaction()` block. `edit_objective` stores a sanitized objective, invalidates unconsumed proposals through the approval service in Task 11, and transitions only at a safe controller boundary; until Task 11 exists, expose an `invalidate_callback: Callable[[Connection, UUID], None]` dependency and test it is invoked inside the transaction.

- [ ] **Step 5: Implement durable sanitized case memory**

```python
class EndpointMemory(FrozenModel):
    id: UUID
    investigation_id: UUID
    canonical_url: str
    method: Literal["GET", "HEAD", "OPTIONS"]
    identity_id: UUID
    latest_status_code: int | None
    content_type: str | None
    semantic_fields: SanitizedPayload
    cache_ambiguity: bool
    evidence_ids: tuple[UUID, ...]
    version: int = Field(ge=1)


class SavedComparison(FrozenModel):
    id: UUID
    investigation_id: UUID
    left_endpoint_memory_id: UUID
    right_endpoint_memory_id: UUID
    sanitized_difference: SanitizedPayload
    evidence_ids: tuple[UUID, ...]
    created_at: AwareDatetime


class MemoryBoundaryError(RuntimeError):
    """A requested memory object does not belong to the active investigation."""
```

`0003_projections.sql` also creates append-only `endpoint_memory_versions` and `saved_comparisons` tables plus a current-version index; triggers reject update/delete. `CaseMemoryRepository.record_observation(connection, observation)` accepts only a branded, already-sanitized observation contract, appends the next endpoint-memory version, and appends `memory.updated` inside the caller's transaction. `list_endpoints(investigation_id)` returns only UUID, canonical URL, safe method, identity label, status, version, and evidence IDs. `retrieve(investigation_id, memory_id)` requires ownership and returns the sealed sanitized record. `compare(investigation_id, left_id, right_id)` requires the same investigation and canonical URL, computes structural key/value differences only from the two sealed semantic payloads, stores a `SavedComparison`, and appends `memory.updated`. `list_saved_comparisons(investigation_id, limit)` returns the newest sealed comparison summaries in deterministic `(created_at, id)` order. `model_payload(investigation_id, memory_id)` and `model_summaries(investigation_id, endpoint_limit, comparison_limit)` convert only allowlisted fields through `RedactionPolicy.sanitize_payload` and return sealed payloads; no full record or arbitrary query reaches model context. There is no general JSON-patch, path, index, old-value, arbitrary dictionary, delete, or model-owned memory mutation API.

```python
def test_memory_observation_and_event_are_atomic(memory, event_store, observation, database) -> None:
    memory.fail_after_version_insert = True
    with pytest.raises(SimulatedMemoryFailure):
        with database.transaction() as connection:
            memory.record_observation(connection, observation)
    assert memory.list_endpoints(observation.investigation_id) == ()
    assert event_store.types(observation.investigation_id).count("memory.updated") == 0


def test_memory_compare_is_sanitized_and_same_case_only(memory_harness) -> None:
    left, right = memory_harness.same_url_pair()
    comparison = memory_harness.memory.compare(
        memory_harness.investigation_id,
        left.id,
        right.id,
    )
    assert comparison.evidence_ids == (left.evidence_ids[-1], right.evidence_ids[-1])
    assert memory_harness.secret_canary not in comparison.model_dump_json()
    with pytest.raises(MemoryBoundaryError):
        memory_harness.memory.compare(
            memory_harness.investigation_id,
            left.id,
            memory_harness.other_investigation_endpoint().id,
        )


def test_memory_has_no_arbitrary_patch_surface(memory) -> None:
    for name in ("apply_patch", "update_path", "delete", "set_raw"):
        assert not hasattr(memory, name)
```

- [ ] **Step 6: Verify and commit**

```powershell
python -m pytest tests/cases tests/runtime/test_state_machine.py -q
python -m ruff format --check bugintel/cases bugintel/runtime tests/cases tests/runtime/test_state_machine.py
git diff --check
git add bugintel/cases/repository.py bugintel/cases/memory.py bugintel/runtime/state_machine.py bugintel/cases/migrations/0003_projections.sql tests/cases/test_repository.py tests/cases/test_memory.py tests/runtime/test_state_machine.py
git commit -m "feat: add case projections and lifecycle"
```

### Task 7: Add the Capability-Separated Credential Vault

**Files:**
- Create: `bugintel/cases/secrets.py`
- Modify: `bugintel/cases/models.py`
- Create: `bugintel/cases/migrations/0004_identities.sql`
- Create: `tests/cases/test_secrets.py`

**Interfaces:**
- Consumes: keyring backend, opaque UUID references, and the exact one-use provider/target capability contracts defined in this task.
- Produces: `CredentialVault`, `KeyringCredentialVault`, `InMemoryCredentialVault`, `ProviderCallCapability`, `ExecutionSecretCapability`, `ProviderCredentialSource`, `TargetCredentialSource`, and `VaultSecretMatcher`.

- [ ] **Step 1: Write namespace and non-enumeration tests**

```python
import pytest

from bugintel.cases.secrets import InMemoryCredentialVault, SecretAccessDenied


def test_provider_source_cannot_read_target_identity() -> None:
    vault = InMemoryCredentialVault()
    identity = vault.store_identity_secret("cookie-value")
    provider = vault.provider_source()
    target_capability = ExecutionSecretCapability(
        id=uuid4(),
        investigation_id=uuid4(),
        identity_ref=identity,
        action_digest="a" * 64,
        expires_at=vault.clock.now() + timedelta(seconds=30),
    )
    with pytest.raises(SecretAccessDenied):
        provider.read(target_capability)  # type: ignore[arg-type]


def test_target_source_requires_bound_execution_capability() -> None:
    vault = InMemoryCredentialVault()
    identity = vault.store_identity_secret("cookie-value")
    target = vault.target_source()
    with pytest.raises(SecretAccessDenied):
        target.read(capability=None)


def test_public_vault_surface_cannot_enumerate_values() -> None:
    assert not hasattr(InMemoryCredentialVault(), "list_secrets")
```

Add these exact namespace/version/backend tests:

```python
def test_provider_key_requires_provider_call_capability(vault, provider_ref) -> None:
    source = vault.provider_source()
    with pytest.raises(SecretAccessDenied):
        source.read(capability=None)
    capability = vault.issue_provider_call_capability(
        provider_ref,
        provider_call_number=1,
        expires_at=vault.clock.now() + timedelta(seconds=30),
    )
    with source.read(capability) as lease:
        assert lease.reveal_for_provider_call() == "provider-canary"


def test_replacing_identity_secret_increments_version(vault, identity_ref) -> None:
    replaced = vault.replace_identity_secret(identity_ref, "replacement")
    assert replaced.id == identity_ref.id
    assert replaced.version == identity_ref.version + 1


def test_unavailable_keyring_has_no_plaintext_fallback(tmp_path) -> None:
    with pytest.raises(SecureBackendUnavailable):
        CredentialVault.open(keyring_backend=UnavailableKeyring(), data_directory=tmp_path)
    assert list(tmp_path.rglob("*")) == []
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/cases/test_secrets.py -v
```

Expected: missing secret module.

- [ ] **Step 3: Implement opaque namespaces and sources**

Use the dependency-neutral `SecretNamespace` and `SecretRef` already defined in `bugintel/cases/models.py`; `bugintel/cases/secrets.py` imports them and does not redefine them. Add the capability contract:

```python
class ExecutionSecretCapability(FrozenModel):
    id: UUID
    investigation_id: UUID
    identity_ref: SecretRef
    action_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    expires_at: AwareDatetime


class ProviderCallCapability(FrozenModel):
    id: UUID
    provider_ref: SecretRef
    provider_call_number: int = Field(ge=1, le=24)
    expires_at: AwareDatetime


class ProviderCredentialSource(Protocol):
    def read(self, capability: ProviderCallCapability) -> "ProviderSecretLease":
        raise NotImplementedError


class TargetCredentialSource(Protocol):
    def read(self, capability: ExecutionSecretCapability) -> "TargetSecretLease":
        raise NotImplementedError


class _SecretLease:
    def __init__(self, value: str):
        self._buffer = bytearray(value.encode("utf-8"))
        self._closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        self.close()

    def _reveal(self) -> str:
        if self._closed:
            raise SecretAccessDenied("lease_closed")
        return self._buffer.decode("utf-8")

    def close(self) -> None:
        for index in range(len(self._buffer)):
            self._buffer[index] = 0
        self._closed = True


class ProviderSecretLease(_SecretLease):
    def reveal_for_provider_call(self) -> str:
        return self._reveal()


class TargetSecretLease(_SecretLease):
    def reveal_for_target_request(self) -> str:
        return self._reveal()
```

`CredentialVault.issue_provider_call_capability(provider_ref, provider_call_number, expires_at)` accepts only a provider-namespace reference, creates a one-use UUID capability, and never accepts an investigation/action/identity reference. `ProviderCredentialSource.read(capability)` checks provider namespace, exact reference, expiry, and one-use consumption; it returns a context-managed `ProviderSecretLease` whose only reveal method is `reveal_for_provider_call()` and whose mutable buffer is erased on close. `ExecutionSecretCapability` is minted only by the execution gateway after approval/policy/budget validation. `TargetCredentialSource.read(capability)` checks target namespace, exact identity reference, action digest, expiry, and one-use consumption; it returns a context-managed `TargetSecretLease` whose only reveal method is `reveal_for_target_request()` and whose buffer is erased on close. Neither source exposes a reference/value enumeration method, and neither capability type is accepted by the other source. `KeyringCredentialVault` uses service names `blackhole-alpha/provider` and `blackhole-alpha/identity`; SQLite stores only `SecretRef`, label, target origin, version, verification metadata, and timestamps. `IdentityRef` rejects provider-namespace secret references at validation.

- [ ] **Step 4: Implement match-only secret detection**

`VaultSecretMatcher.match_category(text)` compares the text against configured vault values inside the vault component and returns only `"configured_credential"` or `None`. It must not return a matching substring, reference, or value. Update Task 3 tests to use this concrete matcher.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/cases/test_redaction.py tests/cases/test_secrets.py -v
python -m pytest tests/cases -q
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases tests/cases
git diff --check
git add bugintel/cases/models.py bugintel/cases/secrets.py bugintel/cases/migrations/0004_identities.sql tests/cases/test_secrets.py tests/cases/test_redaction.py
git commit -m "feat: isolate provider and target credentials"
```

### Task 8: Add the Strict Typed-Tool Protocol

**Files:**
- Create: `bugintel/runtime/tool_protocol.py`
- Create: `tests/runtime/test_tool_protocol.py`

**Interfaces:**
- Consumes: identity UUIDs and scope-independent action descriptions.
- Produces: `HttpRequestAction`, `BrowserNavigationAction`, `LiveAction`, `ActionBatch.create`, `canonical_bytes`, and `digest`.

- [ ] **Step 1: Write rejection and digest tests**

```python
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from pydantic import ValidationError

from bugintel.runtime.tool_protocol import ActionBatch, HttpRequestAction


@pytest.mark.parametrize("forbidden", [
    {"body": "forbidden"},
    {"headers": {"X-Arbitrary": "forbidden"}},
])
def test_http_action_rejects_body_and_arbitrary_headers(redaction, forbidden) -> None:
    payload = {
        "id": uuid4(),
        "kind": "http_request",
        "identity_ref": uuid4(),
        "method": "GET",
        "url": "http://127.0.0.1:8080/api/orders/1048",
        "header_profile": "session_cookie",
        "purpose": redaction.redact_text("paired comparison"),
        "expected_observation": redaction.redact_text("authorization result"),
        "timeout_seconds": 15,
        "max_response_bytes": 1_048_576,
        "max_redirect_hops": 0,
        **forbidden,
    }
    with pytest.raises(ValidationError):
        HttpRequestAction.model_validate(payload)


def test_batch_digest_changes_for_every_authorized_field(action, redaction) -> None:
    inputs = {
        "investigation_id": uuid4(),
        "scope_digest": "a" * 64,
        "purpose": redaction.redact_text("compare account access"),
        "actions": (action,),
        "max_request_count": 1 + action.max_redirect_hops,
        "batch_timeout_seconds": 60,
        "max_total_bytes": action.max_response_bytes,
        "approval_expires_at": datetime.now(UTC) + timedelta(minutes=5),
    }
    original = ActionBatch.create(**inputs)
    changed = ActionBatch.create(**{
        **inputs,
        "purpose": redaction.redact_text("different"),
    })
    assert original.digest != changed.digest
```

Use the following exact mutation names and require every one to change the canonical authorization digest or fail validation before approval:

```python
@pytest.mark.parametrize("mutation", [
    "identity_ref", "method", "url", "header_profile", "purpose",
    "expected_observation", "timeout_seconds", "max_response_bytes",
    "scope_digest", "max_redirect_hops", "subresource_rule",
    "max_subresources", "approval_expires_at",
])
def test_authorized_field_mutation_never_preserves_digest(batch_harness, mutation) -> None:
    original, mutated_or_error = batch_harness.mutate(mutation)
    if isinstance(mutated_or_error, ValidationError):
        return
    assert mutated_or_error.digest != original.digest
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/runtime/test_tool_protocol.py -v
```

Expected: missing module.

- [ ] **Step 3: Implement strict discriminated action models**

```python
import json
from datetime import UTC, datetime
from hashlib import sha256
from typing import Annotated, Any, Literal
from uuid import UUID, uuid4

from pydantic import AwareDatetime, Field, model_validator

from bugintel.cases.models import FrozenModel
from bugintel.cases.redaction import SanitizedText


def canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def action_digest(action: "LiveAction") -> str:
    return sha256(canonical_bytes(action.model_dump(mode="json"))).hexdigest()


class HttpRequestAction(FrozenModel):
    id: UUID
    kind: Literal["http_request"] = "http_request"
    identity_ref: UUID
    method: Literal["GET", "HEAD", "OPTIONS"]
    url: str
    header_profile: Literal["session_cookie", "bearer_token"]
    purpose: Annotated[SanitizedText, Field(min_length=1, max_length=240)]
    expected_observation: Annotated[SanitizedText, Field(min_length=1, max_length=240)]
    timeout_seconds: int = Field(ge=1, le=15)
    max_response_bytes: int = Field(ge=1, le=1_048_576)
    max_redirect_hops: int = Field(default=0, ge=0, le=3)


class BrowserNavigationAction(FrozenModel):
    id: UUID
    kind: Literal["browser_navigation"] = "browser_navigation"
    identity_ref: UUID
    start_url: str
    purpose: Annotated[SanitizedText, Field(min_length=1, max_length=240)]
    max_top_level_navigations: Literal[1] = 1
    subresource_rule: Literal["same_origin_safe_methods"] = "same_origin_safe_methods"
    max_subresources: int = Field(ge=0, le=40)
    max_resource_bytes: int = Field(ge=1, le=1_048_576)
    max_total_bytes: int = Field(ge=1, le=5_242_880)
    timeout_seconds: int = Field(ge=1, le=15)


LiveAction = Annotated[HttpRequestAction | BrowserNavigationAction, Field(discriminator="kind")]


class ActionBatch(FrozenModel):
    id: UUID
    investigation_id: UUID
    scope_digest: str = Field(pattern=r"^[0-9a-f]{64}$")
    purpose: Annotated[SanitizedText, Field(min_length=1, max_length=240)]
    actions: tuple[LiveAction, ...] = Field(min_length=1, max_length=4)
    max_request_count: int = Field(ge=1, le=40)
    batch_timeout_seconds: int = Field(ge=1, le=60)
    max_total_bytes: int = Field(ge=1, le=5_242_880)
    created_at: AwareDatetime
    approval_expires_at: AwareDatetime
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")

    @classmethod
    def create(
        cls,
        *,
        investigation_id: UUID,
        scope_digest: str,
        purpose: SanitizedText,
        actions: tuple[LiveAction, ...],
        max_request_count: int,
        batch_timeout_seconds: int,
        max_total_bytes: int,
        approval_expires_at: datetime,
        created_at: datetime | None = None,
    ) -> "ActionBatch":
        created = created_at or datetime.now(UTC)
        authorization = {
            "investigation_id": str(investigation_id),
            "scope_digest": scope_digest,
            "purpose": purpose,
            "actions": [action.model_dump(mode="json") for action in actions],
            "max_request_count": max_request_count,
            "batch_timeout_seconds": batch_timeout_seconds,
            "max_total_bytes": max_total_bytes,
            "approval_expires_at": approval_expires_at.isoformat(),
        }
        digest = sha256(canonical_bytes(authorization)).hexdigest()
        return cls(
            id=uuid4(),
            investigation_id=investigation_id,
            scope_digest=scope_digest,
            purpose=purpose,
            actions=actions,
            max_request_count=max_request_count,
            batch_timeout_seconds=batch_timeout_seconds,
            max_total_bytes=max_total_bytes,
            created_at=created,
            approval_expires_at=approval_expires_at,
            digest=digest,
        )
```

`action_digest` is the only per-action digest rule; scope canonicalization recomputes it over the canonical action and all `ToolRun`, policy, secret, and execution capabilities use that value, while approval always uses `ActionBatch.digest`. `ActionBatch` validates `approval_expires_at > created_at` and at most five minutes later, rejects duplicate action IDs, requires `max_request_count` to equal the top-level action count plus declared redirect/subresource ceilings without exceeding 40, and recomputes/compares its digest when loaded from model or database data. A browser batch must contain exactly one browser action; an HTTP batch may contain up to four HTTP actions. For a browser action, `max_request_count = 1 + max_subresources` and therefore `max_subresources <= 39` under the 40-request hard ceiling; `max_total_bytes` equals its navigation limit. For an HTTP batch, `max_total_bytes` equals the sum of response limits and may be up to 4 MiB. The authorization digest intentionally excludes the storage UUID and creation timestamp, but includes every field capable of changing the approved effect. The workbench preview reads these stored envelope fields rather than recalculating them.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/runtime/test_tool_protocol.py -v
python -m pytest tests/runtime tests/cases -q
git diff --check
git add bugintel/runtime/tool_protocol.py tests/runtime/test_tool_protocol.py
git commit -m "feat: define strict live action protocol"
```

### Task 9: Add Canonical Numeric-Loopback Scope Policy

**Files:**
- Create: `bugintel/policy/scope.py`
- Create: `bugintel/policy/budgets.py`
- Modify: `bugintel/cases/repository.py`
- Create: `tests/policy/test_scope.py`

**Interfaces:**
- Consumes: `LiveAction` values.
- Produces: `BudgetLimits`, `CanonicalUrl`, immutable `ScopeSnapshot`, `ScopePolicy.create_snapshot`, `ScopePolicy.evaluate`, `PolicyDecision`, and typed `CaseRepository.create_scope_snapshot`/`load_scope_snapshot` methods over Task 6's storage table.

- [ ] **Step 1: Write a canonicalization attack matrix**

```python
import pytest

from bugintel.policy.scope import ScopeViolation, canonicalize_url


def test_accepts_exact_numeric_loopback_origin() -> None:
    result = canonicalize_url("http://127.0.0.1:8080/api/orders/1048")
    assert result.origin == "http://127.0.0.1:8080"
    assert result.path == "/api/orders/1048"


@pytest.mark.parametrize("url", [
    "http://localhost:8080/",
    "http://127.1:8080/",
    "http://2130706433:8080/",
    "http://[::1]:8080/",
    "https://127.0.0.1:8080/",
    "http://127.0.0.1/",
    "http://user@127.0.0.1:8080/",
    "http://127.0.0.1:8080/a/%252e%252e/b",
    "http://127.0.0.1:8080/a%2fb",
    "http://127.0.0.1:8080/?access_token=secret",
])
def test_rejects_ambiguous_or_secret_bearing_urls(url) -> None:
    with pytest.raises(ScopeViolation):
        canonicalize_url(url)
```

Add these exact boundary tests:

```python
def test_path_prefix_matches_segment_boundary_only(scope_policy, scope_snapshot, action_factory) -> None:
    allowed = scope_policy.evaluate(action_factory(url="http://127.0.0.1:8080/api/orders/1048"), scope_snapshot)
    blocked = scope_policy.evaluate(action_factory(url="http://127.0.0.1:8080/api/orders-admin"), scope_snapshot)
    assert allowed.allowed is True
    assert blocked.allowed is False and blocked.reason_code == "path_out_of_scope"


def test_redirect_target_is_reparsed_as_new_action(scope_policy, scope_snapshot, action_factory) -> None:
    original = action_factory(url="http://127.0.0.1:8080/api/orders/1048")
    redirected = original.model_copy(update={"url": "http://127.0.0.1:9090/escape"})
    assert scope_policy.evaluate(original, scope_snapshot).allowed is True
    assert scope_policy.evaluate(redirected, scope_snapshot).allowed is False


def test_loaded_scope_snapshot_recomputes_digest(repository, connection, scope_policy) -> None:
    snapshot = scope_policy.create_snapshot(alpha_scope_input())
    connection.execute(
        "INSERT INTO scope_snapshots(id, digest, canonical_json, created_at) VALUES(?, ?, ?, ?)",
        (str(snapshot.id), snapshot.digest, "{}", snapshot.created_at.isoformat()),
    )
    with pytest.raises(ScopeIntegrityError):
        repository.load_scope_snapshot(connection, snapshot.digest)
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/policy/test_scope.py -v
```

Expected: missing module.

- [ ] **Step 3: Implement one parser and one authorized representation**

```python
class BudgetLimits(FrozenModel):
    max_actions_per_batch: int = Field(default=4, ge=1, le=4)
    max_requests_total: int = Field(default=40, ge=1, le=40)
    max_requests_per_minute: int = Field(default=8, ge=1, le=8)
    approval_ttl_seconds: int = Field(default=300, ge=1, le=300)
    resource_timeout_seconds: int = Field(default=15, ge=1, le=15)
    batch_timeout_seconds: int = Field(default=60, ge=1, le=60)
    active_wall_seconds: int = Field(default=1800, ge=1, le=1800)
    max_response_bytes: int = Field(default=1_048_576, ge=1, le=1_048_576)
    max_browser_bytes: int = Field(default=5_242_880, ge=1, le=5_242_880)
    max_browser_subresources: int = Field(default=40, ge=0, le=40)
    max_top_level_navigations: int = Field(default=1, ge=1, le=1)
    max_model_decisions: int = Field(default=24, ge=1, le=24)
    max_provider_calls: int = Field(default=24, ge=1, le=24)

    @classmethod
    def alpha_defaults(cls) -> "BudgetLimits":
        return cls()


class CanonicalUrl(FrozenModel):
    value: str
    origin: str
    path: str
    query: tuple[tuple[str, str], ...]


class ScopeSnapshot(FrozenModel):
    id: UUID
    origins: tuple[str, ...]
    allowed_methods: tuple[Literal["GET", "HEAD", "OPTIONS"], ...]
    allowed_path_prefixes: tuple[str, ...]
    forbidden_path_prefixes: tuple[str, ...]
    loopback_rule: Literal["canonical_127_0_0_1"] = "canonical_127_0_0_1"
    redirect_policy: Literal["manual_same_scope"] = "manual_same_scope"
    limits: BudgetLimits
    created_at: AwareDatetime
    digest: str = Field(pattern=r"^[0-9a-f]{64}$")


class PolicyDecision(FrozenModel):
    id: UUID
    allowed: bool
    reason_code: str
    scope_digest: str
    action_digest: str
    canonical_action: LiveAction | None
    decided_at: AwareDatetime
```

Parse with `urllib.parse.urlsplit`, require scheme `http`, literal hostname `127.0.0.1`, no username/password/fragment, a present decimal port from 1 through 65535, canonical netloc equality, and exactly one decode/normalize pass. Reject encoded slash, backslash, NUL, dot-segment, double-encoding, and sensitive query keys before creating `CanonicalUrl`. The adapter later receives `CanonicalUrl.value` verbatim; it must never recompose from the raw string.

- [ ] **Step 4: Bind snapshots and decisions deterministically**

`ScopePolicy.create_snapshot` canonicalizes every origin and path rule and hashes the full immutable policy plus limits. `evaluate` returns a reason code and canonical action; it never trusts caller-supplied `reviewed_hosts`, `reviewed_paths`, or blocker lists.

`CaseRepository.create_scope_snapshot(connection, snapshot)` stores canonical JSON plus digest and appends `scope.verified` in the same transaction. `load_scope_snapshot(connection, digest)` parses the stored JSON through `ScopeSnapshot`, recomputes the digest, compares the requested/stored/recomputed values with `hmac.compare_digest`, and raises `ScopeIntegrityError` on any mismatch. No caller may supply a replacement limits object at load time.

- [ ] **Step 5: Verify and commit**

```powershell
python -m pytest tests/policy/test_scope.py -v
python -m pytest tests/policy tests/runtime/test_tool_protocol.py -q
python -m ruff format --check bugintel/policy tests/policy
git diff --check
git add bugintel/policy/scope.py bugintel/policy/budgets.py bugintel/cases/repository.py tests/policy/test_scope.py
git commit -m "feat: enforce exact loopback scope"
```

### Task 10: Add the Persistent Hard-Budget Ledger

**Files:**
- Modify: `bugintel/policy/budgets.py`
- Create: `bugintel/cases/migrations/0005_budgets.sql`
- Create: `tests/policy/test_budgets.py`

**Interfaces:**
- Consumes: `Database`, investigation UUIDs, and the `BudgetLimits` defined in Task 9 and stored on scope snapshots.
- Produces: `BudgetLedger.begin_active_segment`, `end_active_segment`, `active_deadline`, `reserve_request(investigation_id, count, *, connection=None, now=None)`, `charge_bytes`, `charge_model_decision`, `charge_provider_call`, `check_batch_deadline`, `check_active_deadline`, and `BudgetExceeded`.

- [ ] **Step 1: Write exact-ceiling and atomic-reservation tests**

```python
from bugintel.policy.budgets import BudgetExceeded, BudgetLimits


def test_alpha_defaults_are_exact() -> None:
    limits = BudgetLimits.alpha_defaults()
    assert limits.max_actions_per_batch == 4
    assert limits.max_requests_total == 40
    assert limits.max_requests_per_minute == 8
    assert limits.max_response_bytes == 1_048_576
    assert limits.max_browser_bytes == 5_242_880
    assert limits.max_browser_subresources == 40
    assert limits.max_model_decisions == 24
    assert limits.max_provider_calls == 24


def test_request_reservation_never_oversubscribes(database, ledger, investigation_id, clock) -> None:
    for _ in range(40):
        ledger.reserve_request(investigation_id, count=1, now=clock.now())
        clock.advance(seconds=61)
    with pytest.raises(BudgetExceeded, match="requests_total"):
        ledger.reserve_request(investigation_id, count=1, now=clock.now())


def test_ninth_request_in_rolling_minute_is_blocked(ledger, investigation_id, clock) -> None:
    for _ in range(8):
        ledger.reserve_request(investigation_id, count=1, now=clock.now())
    with pytest.raises(BudgetExceeded, match="requests_per_minute"):
        ledger.reserve_request(investigation_id, count=1, now=clock.now())


def test_batch_and_active_deadlines_fail_closed(ledger, investigation_id, clock) -> None:
    batch_started_at = clock.now()
    clock.advance(seconds=61)
    with pytest.raises(BudgetExceeded, match="batch_timeout"):
        ledger.check_batch_deadline(investigation_id, batch_started_at, now=clock.now())
    segment = ledger.begin_active_segment(investigation_id, now=clock.now())
    clock.advance(seconds=1800)
    with pytest.raises(BudgetExceeded, match="active_wall"):
        ledger.check_active_deadline(investigation_id, now=clock.now())
    ledger.end_active_segment(investigation_id, segment, now=clock.now())
    with pytest.raises(BudgetExceeded):
        ledger.reserve_request(investigation_id, count=1)


def test_only_active_segments_consume_wall_budget(ledger, investigation_id, clock) -> None:
    first = ledger.begin_active_segment(investigation_id, now=clock.now())
    clock.advance(seconds=600)
    ledger.end_active_segment(investigation_id, first, now=clock.now())
    clock.advance(seconds=3600)  # waiting for researcher approval does not count
    second = ledger.begin_active_segment(investigation_id, now=clock.now())
    clock.advance(seconds=1200)
    with pytest.raises(BudgetExceeded, match="active_wall"):
        ledger.check_active_deadline(investigation_id, now=clock.now())
    ledger.end_active_segment(investigation_id, second, now=clock.now())


def test_active_deadline_is_remaining_persisted_allowance(ledger, investigation_id, clock) -> None:
    segment = ledger.begin_active_segment(investigation_id, now=clock.now())
    clock.advance(seconds=300)
    assert ledger.active_deadline(investigation_id, now=clock.now()) == clock.now() + timedelta(seconds=1500)
    ledger.end_active_segment(investigation_id, segment, now=clock.now())
```

Use this two-connection proof:

```python
def test_concurrent_reservations_never_reach_41(ledger_factory, investigation_id) -> None:
    ledger_a, ledger_b = ledger_factory.two_independent_connections(requests_already_used=39)
    barrier = Barrier(2)
    def reserve(ledger):
        barrier.wait()
        try:
            ledger.reserve_request(investigation_id, count=1)
            return "reserved"
        except BudgetExceeded:
            return "blocked"
    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(reserve, (ledger_a, ledger_b)))
    assert sorted(outcomes) == ["blocked", "reserved"]
    assert ledger_a.snapshot(investigation_id).requests_total == 40
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/policy/test_budgets.py -v
```

Expected: missing module or table.

- [ ] **Step 3: Implement limits and reservation-before-effect semantics**

```python
def reserve_request(
    self,
    investigation_id: UUID,
    count: int,
    *,
    connection: sqlite3.Connection | None = None,
    now: datetime | None = None,
) -> None:
    current = now or self._clock.now()
    with self._database.use_or_open_transaction(connection) as active:
        self._assert_active_deadline(active, investigation_id, current)
        self._reserve_total_and_rolling_window(active, investigation_id, count, current)


def charge_model_decision(self, investigation_id: UUID) -> None:
    self._increment_bounded(investigation_id, "model_decisions", "max_model_decisions")


def charge_provider_call(self, investigation_id: UUID) -> None:
    self._increment_bounded(investigation_id, "provider_calls", "max_provider_calls")
```

Preserve Task 9's exact `BudgetLimits`. Persist total requests, an exact timestamp for each of the last eight request reservations, active elapsed seconds, at most one open active-segment timestamp, bytes, valid model decisions, and provider call attempts. `begin_active_segment` atomically refuses a second open segment and returns its UUID; `end_active_segment` conditionally closes that exact UUID and adds `max(0, now-started_at)` to persisted elapsed time. `active_deadline` returns `now + max(0, 1800 - elapsed - current_open_duration)`. The controller brackets every `run_until_boundary` call in `begin_active_segment`/`end_active_segment`; approval wait and paused time therefore do not count. Recovery closes an orphaned open segment at startup time, conservatively counting downtime, before allowing resume. `_assert_active_deadline` is called inside every request/byte/model/provider budget mutation transaction, so exhaustion cannot be bypassed by forgetting a separate precheck. `_reserve_total_and_rolling_window` drops timestamps at or before `now - 60 seconds`, rejects when `len(recent)+count > 8`, and conditionally updates total/recent rows before issuing a capability. `check_batch_deadline` rejects elapsed time greater than 60 seconds; `check_active_deadline(investigation_id, *, now)` rejects when persisted elapsed plus the current open duration is greater than or equal to 1,800 seconds. Charge response bytes from streaming chunks and fail once the next chunk would exceed the ceiling. No method accepts an override above the stored scope limits.

- [ ] **Step 4: Verify and commit**

```powershell
python -m pytest tests/policy/test_budgets.py tests/policy/test_scope.py -v
python -m pytest tests/policy tests/cases -q
git diff --check
git add bugintel/policy/budgets.py bugintel/cases/migrations/0005_budgets.sql tests/policy/test_budgets.py
git commit -m "feat: enforce persistent execution budgets"
```

### Task 11: Add Digest-Bound Bounded Approvals

**Files:**
- Create: `bugintel/policy/approval.py`
- Create: `bugintel/cases/migrations/0006_approvals.sql`
- Modify: `bugintel/cases/database.py`
- Modify: `bugintel/cases/repository.py`
- Create: `tests/policy/test_approval.py`

**Interfaces:**
- Consumes: `ActionBatch`, `ScopeSnapshot`, `BudgetLedger`, secret versions, UTC clock, and the case transaction.
- Produces: `ApprovalRequest`, `ApprovalGrant`, `PendingApprovalLookup`, `ApprovalService.request`, `grant`, `reject`, `consume`, `load_batch_for_grant`, `lookup_pending_approval`, `assert_current_identity_version`, `invalidate_for_scope`, `invalidate_for_objective`, and `invalidate_for_secret_version`.

- [ ] **Step 1: Write expiry, tamper, consumption, and invalidation tests**

```python
def test_grant_binds_exact_batch_scope_and_secret_versions(approval_service, batch, scope) -> None:
    request = approval_service.request(
        investigation_id=batch.investigation_id,
        batch=batch,
        scope=scope,
        identity_versions={str(batch.actions[0].identity_ref): 3},
    )
    grant = approval_service.grant(request.id)
    assert grant.batch_digest == batch.digest
    assert grant.scope_digest == scope.digest
    assert grant.identity_versions == {str(batch.actions[0].identity_ref): 3}


def test_edit_never_reuses_a_grant(approval_service, granted_batch) -> None:
    edited = granted_batch.batch.model_copy(update={"purpose": "changed"})
    with pytest.raises(ApprovalMismatch):
        approval_service.consume(
            granted_batch.grant.id,
            edited,
            edited.actions[0].id,
            now=approval_service.clock.now(),
        )


def test_expired_grant_is_not_consumed(approval_service, expired_grant, batch) -> None:
    with pytest.raises(ApprovalExpired):
        approval_service.consume(
            expired_grant.id,
            batch,
            batch.actions[0].id,
            now=approval_service.clock.now(),
        )
```

Use this exact invalidation matrix plus strict-union test:

```python
@pytest.mark.parametrize(
    "mutation",
    ["reject", "all_actions_consumed", "scope_changed", "objective_edited", "secret_replaced"],
)
def test_grant_becomes_unusable_after_boundary_change(approval_harness, mutation) -> None:
    case = approval_harness.granted_case()
    approval_harness.apply(mutation, case)
    with pytest.raises((ApprovalRejected, ApprovalConsumed, ApprovalMismatch, ApprovalExpired)):
        approval_harness.consume_next(case)


def test_request_rejects_non_union_action(approval_service, batch_payload, scope) -> None:
    batch_payload["actions"] = [{"kind": "shell_command", "command": "whoami"}]
    with pytest.raises(ValidationError):
        approval_service.request_untrusted(batch_payload, scope=scope)
```

- [ ] **Step 2: Run and confirm failure**

```powershell
python -m pytest tests/policy/test_approval.py -v
```

Expected: missing approval service or table.

- [ ] **Step 3: Implement immutable requests and one-time consumption**

```python
class ApprovalGrant(FrozenModel):
    id: UUID
    investigation_id: UUID
    request_id: UUID
    batch_digest: str
    scope_digest: str
    identity_versions: dict[str, int]
    action_ids: tuple[UUID, ...]
    consumed_action_ids: tuple[UUID, ...]
    granted_at: datetime
    expires_at: datetime
    remaining_consumptions: int


class PendingApprovalLookup(FrozenModel):
    state: Literal["pending", "granted", "rejected", "expired", "exhausted", "missing"]
    request_id: UUID | None = None
    grant_id: UUID | None = None
    safe_reason_code: str


def consume(
    self,
    grant_id: UUID,
    batch: ActionBatch,
    action_id: UUID,
    *,
    now: datetime,
    connection: sqlite3.Connection | None = None,
) -> ApprovalGrant:
    with self._database.use_or_open_transaction(connection) as active:
        grant = self._load_for_update(active, grant_id)
        self._assert_exact_match(grant, batch, now)
        if action_id not in grant.action_ids or action_id in grant.consumed_action_ids:
            raise ApprovalConsumed(action_id)
        updated = grant.model_copy(update={
            "consumed_action_ids": (*grant.consumed_action_ids, action_id),
            "remaining_consumptions": grant.remaining_consumptions - 1,
        })
        self._persist_consumption(active, prior=grant, updated=updated)
        return updated
```

`Database.use_or_open_transaction(connection)` yields the caller's existing connection without committing it, or opens a transaction when `None`; Task 4 adds this helper and a nested-transaction test when Task 11 needs it. Store canonical batch JSON and digest, scope digest, identity versions, ordered action IDs, consumed action IDs, expiry, decision, and consumption. Use a conditional SQL update requiring the prior remaining count and exact prior consumed-action JSON so concurrent consumers cannot double-spend or replay an action.

`load_batch_for_grant(grant_id)` loads the immutable stored batch, recomputes its digest, and returns it only when grant/request/batch/investigation IDs agree. `lookup_pending_approval(investigation_id, now)` returns exactly one closed state rather than conflating absence, pending, rejection, expiry, or exhaustion; multiple active rows are a fail-closed integrity error. `assert_current_identity_version(connection, grant_id, identity_id, version)` compares the exact stored grant map and raises `ApprovalMismatch` on absence or difference. All three methods return metadata only and cannot read a credential value.

- [ ] **Step 4: Wire invalidation into objective edits**

Replace Task 6's callback seam with `ApprovalService.invalidate_for_objective(connection, investigation_id)`. Scope snapshot replacement and identity secret replacement call their corresponding invalidators in the same transaction as the version change.

- [ ] **Step 5: Run the foundation gate**

```powershell
python -m pytest tests/cases tests/policy tests/runtime/test_state_machine.py tests/runtime/test_tool_protocol.py -q
python -m coverage run --branch --source=bugintel.cases,bugintel.policy,bugintel.runtime -m pytest tests/cases tests/policy tests/runtime/test_state_machine.py tests/runtime/test_tool_protocol.py
python -m coverage report --fail-under=90
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases bugintel/policy bugintel/runtime tests/cases tests/policy tests/runtime
python -m ruff format --check bugintel/cases bugintel/policy bugintel/runtime tests/cases tests/policy tests/runtime
git diff --check
```

Expected: all tests pass, new foundation branch coverage is at least 90%, and the policy/approval/secret/redaction targets reach 100% branch coverage when measured with focused source invocations.

- [ ] **Step 6: Commit**

```powershell
git add bugintel/policy/approval.py bugintel/cases/migrations/0006_approvals.sql bugintel/cases/database.py bugintel/cases/repository.py tests/policy/test_approval.py
git commit -m "feat: bind approvals to exact actions"
```

## Foundation Completion Gate

Before moving to the Agent Loop plan, run and record:

```powershell
python -m pytest -q
python -m coverage run --branch --source=bugintel.cases,bugintel.policy,bugintel.runtime -m pytest tests/cases tests/policy tests/runtime
python -m coverage report --fail-under=90
python -m coverage run --branch --source=bugintel.policy.scope,bugintel.policy.approval,bugintel.cases.secrets,bugintel.cases.redaction -m pytest tests/policy/test_scope.py tests/policy/test_approval.py tests/cases/test_secrets.py tests/cases/test_redaction.py
python -m coverage report --fail-under=100
python -m ruff check --select E9,F63,F7,F82,F601,F811,F401,F841 bugintel/cases bugintel/policy bugintel/runtime tests/cases tests/policy tests/runtime
python -m ruff format --check bugintel/cases bugintel/policy bugintel/runtime tests/cases tests/policy tests/runtime
git status --short
```

The gate passes only with zero test failures, no Ruff or format failures, required coverage, and a clean worktree. There is still no new network path at this checkpoint.
