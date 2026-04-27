"""
iOS Agent for BugIntel AI Workbench.

iOS Mode foundation.

Current capabilities:
- Parse Info.plist XML text
- Extract bundle identifier
- Extract URL schemes
- Extract associated domains
- Extract App Transport Security settings
- Mine API endpoints from plist/config text

This module performs static analysis only. It does not install, run, or modify apps.
"""

from __future__ import annotations

import plistlib
import re
from dataclasses import dataclass, field
from typing import Any

from bugintel.analyzers.endpoint_miner import mine_endpoints


@dataclass(frozen=True)
class IOSURLScheme:
    name: str
    schemes: list[str]


@dataclass
class IOSAnalysisResult:
    bundle_id: str | None
    display_name: str | None
    url_schemes: list[IOSURLScheme] = field(default_factory=list)
    associated_domains: list[str] = field(default_factory=list)
    ats_allows_arbitrary_loads: bool | None = None
    endpoints: list[str] = field(default_factory=list)
    hosts: list[str] = field(default_factory=list)


def analyze_ios_plist(plist_text: str, extra_text: str = "") -> IOSAnalysisResult:
    data = plistlib.loads(plist_text.encode("utf-8"))

    bundle_id = _as_str(data.get("CFBundleIdentifier"))
    display_name = _as_str(data.get("CFBundleDisplayName") or data.get("CFBundleName"))

    url_schemes = _extract_url_schemes(data)
    associated_domains = _extract_associated_domains(data)
    ats_allows_arbitrary_loads = _extract_ats_allows_arbitrary_loads(data)

    combined_text = plist_text + "\n" + extra_text

    endpoints = sorted(
        {
            endpoint.value
            for endpoint in mine_endpoints(combined_text)
            if endpoint.value not in {"/plist", "/DTDs/PropertyList-1.0.dtd", "/dtds/propertylist-1.0.dtd"}
        }
    )

    ignored_hosts = {"www.apple.com"}
    hosts = sorted({host for host in _extract_hosts(combined_text) if host not in ignored_hosts})

    return IOSAnalysisResult(
        bundle_id=bundle_id,
        display_name=display_name,
        url_schemes=url_schemes,
        associated_domains=associated_domains,
        ats_allows_arbitrary_loads=ats_allows_arbitrary_loads,
        endpoints=endpoints,
        hosts=hosts,
    )


def _extract_url_schemes(data: dict[str, Any]) -> list[IOSURLScheme]:
    results: list[IOSURLScheme] = []

    for item in data.get("CFBundleURLTypes", []) or []:
        if not isinstance(item, dict):
            continue

        name = _as_str(item.get("CFBundleURLName")) or ""
        schemes_raw = item.get("CFBundleURLSchemes", []) or []

        schemes = [
            str(scheme)
            for scheme in schemes_raw
            if isinstance(scheme, str) and scheme.strip()
        ]

        if name or schemes:
            results.append(IOSURLScheme(name=name, schemes=schemes))

    return results


def _extract_associated_domains(data: dict[str, Any]) -> list[str]:
    entitlements = data.get("com.apple.developer.associated-domains", []) or []

    if isinstance(entitlements, list):
        return sorted(str(item) for item in entitlements if str(item).strip())

    return []


def _extract_ats_allows_arbitrary_loads(data: dict[str, Any]) -> bool | None:
    ats = data.get("NSAppTransportSecurity")

    if not isinstance(ats, dict):
        return None

    value = ats.get("NSAllowsArbitraryLoads")

    if isinstance(value, bool):
        return value

    return None


def _extract_hosts(text: str) -> list[str]:
    pattern = re.compile(r"https?://([A-Za-z0-9.-]+)(?::\d+)?", re.IGNORECASE)
    return [match.group(1).lower() for match in pattern.finditer(text or "")]


def _as_str(value: Any) -> str | None:
    if isinstance(value, str):
        return value

    return None
