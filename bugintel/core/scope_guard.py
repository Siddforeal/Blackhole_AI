"""
Scope Guard for Blackhole AI Workbench.

This module prevents agents from running tests outside the user-defined
authorized scope. It is intentionally conservative.

It checks:
- URL scheme
- hostname/domain
- HTTP method
- forbidden path patterns
"""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from urllib.parse import urlparse


SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}
WRITE_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


@dataclass
class ScopeDecision:
    allowed: bool
    reason: str


@dataclass
class TargetScope:
    target_name: str
    allowed_domains: list[str]
    allowed_schemes: list[str] = field(default_factory=lambda: ["https"])
    allowed_methods: list[str] = field(default_factory=lambda: ["GET", "HEAD", "OPTIONS"])
    forbidden_paths: list[str] = field(default_factory=list)
    requests_per_minute: int = 30
    human_approval_required: bool = True

    def is_url_allowed(self, url: str, method: str = "GET") -> ScopeDecision:
        method = method.upper().strip()
        parsed = urlparse(url)

        if not parsed.scheme or not parsed.netloc:
            return ScopeDecision(False, "URL must include scheme and hostname")

        if parsed.scheme not in self.allowed_schemes:
            return ScopeDecision(False, f"Scheme not allowed: {parsed.scheme}")

        hostname = parsed.hostname or ""

        if not self._domain_allowed(hostname):
            return ScopeDecision(False, f"Domain not in scope: {hostname}")

        if method not in [m.upper() for m in self.allowed_methods]:
            return ScopeDecision(False, f"HTTP method not allowed: {method}")

        path = parsed.path or "/"

        for pattern in self.forbidden_paths:
            if fnmatch(path, pattern):
                return ScopeDecision(False, f"Path is forbidden by pattern: {pattern}")

        return ScopeDecision(True, "Allowed by scope")

    def _domain_allowed(self, hostname: str) -> bool:
        hostname = hostname.lower().strip(".")

        for domain in self.allowed_domains:
            domain = domain.lower().strip(".")

            if hostname == domain:
                return True

            if domain.startswith("*."):
                base = domain[2:]
                if hostname.endswith("." + base):
                    return True

        return False


def load_scope_from_dict(data: dict) -> TargetScope:
    return TargetScope(
        target_name=data["target_name"],
        allowed_domains=data["allowed_domains"],
        allowed_schemes=data.get("allowed_schemes", ["https"]),
        allowed_methods=data.get("allowed_methods", ["GET", "HEAD", "OPTIONS"]),
        forbidden_paths=data.get("forbidden_paths", []),
        requests_per_minute=int(data.get("requests_per_minute", 30)),
        human_approval_required=bool(data.get("human_approval_required", True)),
    )
