"""Scoped runtime adapter contracts.

This package currently defines local deterministic contracts only. It does not
send requests, execute tools, launch browsers, call providers, collect evidence,
mutate targets, submit reports, or confirm vulnerabilities.
"""

from bugintel.adapters.scoped_runtime.contracts import (
    ScopedAdapterPreparedCommand,
    ScopedAdapterRequest,
)
from bugintel.adapters.scoped_runtime.result_types import (
    ScopedAdapterResult,
    ScopedAdapterScopeGuardResult,
)
from bugintel.adapters.scoped_runtime.scope_guard import validate_scoped_adapter_request

__all__ = [
    "ScopedAdapterPreparedCommand",
    "ScopedAdapterRequest",
    "ScopedAdapterResult",
    "ScopedAdapterScopeGuardResult",
    "validate_scoped_adapter_request",
]
