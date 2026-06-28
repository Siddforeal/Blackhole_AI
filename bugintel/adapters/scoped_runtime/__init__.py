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
from bugintel.adapters.scoped_runtime.preview_renderer import (
    ScopedRuntimePreviewArtifact,
    render_scoped_runtime_preview,
)
from bugintel.adapters.scoped_runtime.curl_adapter import (
    ScopedCurlAdapter,
    ScopedCurlAdapterPreview,
    render_scoped_curl_adapter_preview,
)

__all__ = [
    "ScopedAdapterPreparedCommand",
    "ScopedAdapterRequest",
    "ScopedAdapterResult",
    "ScopedAdapterScopeGuardResult",
    "validate_scoped_adapter_request",
    "ScopedRuntimePreviewArtifact",
    "render_scoped_runtime_preview",
    "ScopedCurlAdapter",
    "ScopedCurlAdapterPreview",
    "render_scoped_curl_adapter_preview",
]
