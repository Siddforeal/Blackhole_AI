"""
Android Agent for BugIntel AI Workbench.

Android Mode foundation.

Current capabilities:
- Parse AndroidManifest.xml text
- Extract package name
- Extract permissions
- Extract components
- Identify exported components
- Extract deep links from intent filters
- Mine endpoints from manifest/config text

This module performs static analysis only. It does not install, run, or modify apps.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field

from bugintel.analyzers.endpoint_miner import mine_endpoints


ANDROID_NS = "{http://schemas.android.com/apk/res/android}"


@dataclass(frozen=True)
class AndroidComponent:
    kind: str
    name: str
    exported: bool | None


@dataclass(frozen=True)
class AndroidDeepLink:
    component: str
    scheme: str
    host: str
    path: str


@dataclass
class AndroidAnalysisResult:
    package_name: str | None
    permissions: list[str] = field(default_factory=list)
    components: list[AndroidComponent] = field(default_factory=list)
    deep_links: list[AndroidDeepLink] = field(default_factory=list)
    endpoints: list[str] = field(default_factory=list)

    @property
    def exported_components(self) -> list[AndroidComponent]:
        return [component for component in self.components if component.exported is True]


def analyze_android_manifest(manifest_text: str, extra_text: str = "") -> AndroidAnalysisResult:
    """
    Analyze AndroidManifest.xml text and optional extra config/source text.
    """
    root = ET.fromstring(manifest_text)

    package_name = root.attrib.get("package")

    permissions = sorted(
        {
            _android_attr(child, "name")
            for child in root.findall("uses-permission")
            if _android_attr(child, "name")
        }
    )

    components: list[AndroidComponent] = []
    deep_links: list[AndroidDeepLink] = []

    application = root.find("application")

    if application is not None:
        for kind in ["activity", "activity-alias", "service", "receiver", "provider"]:
            for node in application.findall(kind):
                name = _android_attr(node, "name") or ""
                exported = _parse_bool(_android_attr(node, "exported"))

                components.append(
                    AndroidComponent(
                        kind=kind,
                        name=name,
                        exported=exported,
                    )
                )

                for intent_filter in node.findall("intent-filter"):
                    for data in intent_filter.findall("data"):
                        scheme = _android_attr(data, "scheme") or ""
                        host = _android_attr(data, "host") or ""
                        path = (
                            _android_attr(data, "path")
                            or _android_attr(data, "pathPrefix")
                            or _android_attr(data, "pathPattern")
                            or ""
                        )

                        if scheme or host or path:
                            deep_links.append(
                                AndroidDeepLink(
                                    component=name,
                                    scheme=scheme,
                                    host=host,
                                    path=path,
                                )
                            )

    combined_text = manifest_text + "\n" + extra_text
    ignored_endpoints = {
        "/apk/res/android",
    }

    endpoints = sorted(
        {
            endpoint.value
            for endpoint in mine_endpoints(combined_text)
            if endpoint.value not in ignored_endpoints
        }
    )

    return AndroidAnalysisResult(
        package_name=package_name,
        permissions=permissions,
        components=components,
        deep_links=deep_links,
        endpoints=endpoints,
    )


def _android_attr(node: ET.Element, name: str) -> str | None:
    return node.attrib.get(ANDROID_NS + name) or node.attrib.get(name)


def _parse_bool(value: str | None) -> bool | None:
    if value is None:
        return None

    lowered = value.strip().lower()

    if lowered == "true":
        return True

    if lowered == "false":
        return False

    return None
