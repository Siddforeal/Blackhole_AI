"""
Recon Agent for BugIntel AI Workbench.

Website-mode passive recon utilities.

Current capabilities:
- Parse HTML
- Extract links
- Extract JavaScript source URLs
- Extract forms
- Mine endpoints from page content

This module does not perform active network testing by itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin

from bugintel.analyzers.endpoint_miner import mine_endpoints


@dataclass
class FormInfo:
    method: str
    action: str
    inputs: list[str] = field(default_factory=list)


@dataclass
class WebReconResult:
    base_url: str
    links: list[str]
    scripts: list[str]
    forms: list[FormInfo]
    endpoints: list[str]


class _HTMLReconParser(HTMLParser):
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url
        self.links: set[str] = set()
        self.scripts: set[str] = set()
        self.forms: list[FormInfo] = []
        self._current_form: FormInfo | None = None

    def handle_starttag(self, tag: str, attrs):
        attrs_dict = dict(attrs)

        if tag == "a" and attrs_dict.get("href"):
            self.links.add(urljoin(self.base_url, attrs_dict["href"]))

        if tag == "script" and attrs_dict.get("src"):
            self.scripts.add(urljoin(self.base_url, attrs_dict["src"]))

        if tag == "form":
            method = attrs_dict.get("method", "GET").upper()
            action = urljoin(self.base_url, attrs_dict.get("action", ""))
            self._current_form = FormInfo(method=method, action=action)

        if tag == "input" and self._current_form is not None:
            name = attrs_dict.get("name") or attrs_dict.get("id") or attrs_dict.get("type") or "unnamed"
            self._current_form.inputs.append(name)

    def handle_endtag(self, tag: str):
        if tag == "form" and self._current_form is not None:
            self.forms.append(self._current_form)
            self._current_form = None


def analyze_html(base_url: str, html: str) -> WebReconResult:
    """Analyze HTML and return passive website recon results."""
    parser = _HTMLReconParser(base_url=base_url)
    parser.feed(html or "")

    mined = mine_endpoints(html or "")
    endpoints = sorted({endpoint.value for endpoint in mined})

    return WebReconResult(
        base_url=base_url,
        links=sorted(parser.links),
        scripts=sorted(parser.scripts),
        forms=parser.forms,
        endpoints=endpoints,
    )
