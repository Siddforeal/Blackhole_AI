"""
Response Diff Analyzer for Blackhole AI Workbench.

Compares HTTP responses to identify interesting authorization/security signals.

This module does not send requests. It only analyzes response metadata and bodies.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResponseSummary:
    status_code: int | None
    content_type: str
    body_size: int
    body_sha256: str
    is_json: bool
    json_keys: list[str] = field(default_factory=list)
    interesting_keywords: list[str] = field(default_factory=list)


@dataclass
class ResponseComparison:
    baseline_status: int | None
    candidate_status: int | None
    same_status: bool
    size_delta: int
    size_ratio: float
    json_key_overlap: float
    signals: list[str]
    verdict: str


INTERESTING_KEYWORDS = [
    "admin",
    "role",
    "permission",
    "permissions",
    "token",
    "secret",
    "api_key",
    "apikey",
    "email",
    "user_id",
    "account_id",
    "project_id",
    "organization",
    "tenant",
    "invoice",
    "billing",
]


def summarize_response(
    status_code: int | None,
    headers: dict[str, Any] | None,
    body: str,
) -> ResponseSummary:
    headers = headers or {}
    body = body or ""

    content_type = ""
    for key, value in headers.items():
        if key.lower() == "content-type":
            content_type = str(value)
            break

    body_sha256 = hashlib.sha256(body.encode("utf-8", errors="replace")).hexdigest()
    body_size = len(body.encode("utf-8", errors="replace"))

    is_json = False
    json_keys: list[str] = []

    try:
        parsed = json.loads(body)
        is_json = True
        json_keys = sorted(_extract_json_keys(parsed))
    except Exception:
        is_json = False
        json_keys = []

    lowered = body.lower()
    interesting_keywords = sorted({kw for kw in INTERESTING_KEYWORDS if kw in lowered})

    return ResponseSummary(
        status_code=status_code,
        content_type=content_type,
        body_size=body_size,
        body_sha256=body_sha256,
        is_json=is_json,
        json_keys=json_keys,
        interesting_keywords=interesting_keywords,
    )


def compare_responses(
    baseline: ResponseSummary,
    candidate: ResponseSummary,
) -> ResponseComparison:
    same_status = baseline.status_code == candidate.status_code
    size_delta = candidate.body_size - baseline.body_size

    if baseline.body_size == 0:
        size_ratio = 0.0 if candidate.body_size == 0 else 999.0
    else:
        size_ratio = round(candidate.body_size / baseline.body_size, 3)

    json_key_overlap = _overlap_score(baseline.json_keys, candidate.json_keys)
    signals: list[str] = []

    if baseline.status_code == 200 and candidate.status_code == 200:
        signals.append("candidate_also_returned_200")

    if baseline.status_code in {401, 403} and candidate.status_code == 200:
        signals.append("candidate_more_permissive_than_baseline")

    if baseline.status_code == 200 and candidate.status_code in {401, 403, 404}:
        signals.append("candidate_blocked_or_not_found")

    if same_status and baseline.status_code == 200 and json_key_overlap >= 0.6:
        signals.append("similar_successful_json_structure")

    if candidate.interesting_keywords:
        signals.append("candidate_contains_interesting_keywords")

    if candidate.body_sha256 == baseline.body_sha256 and candidate.body_size > 0:
        signals.append("identical_body")

    verdict = _make_verdict(
        baseline=baseline,
        candidate=candidate,
        json_key_overlap=json_key_overlap,
        signals=signals,
    )

    return ResponseComparison(
        baseline_status=baseline.status_code,
        candidate_status=candidate.status_code,
        same_status=same_status,
        size_delta=size_delta,
        size_ratio=size_ratio,
        json_key_overlap=json_key_overlap,
        signals=signals,
        verdict=verdict,
    )


def _extract_json_keys(value: Any, prefix: str = "") -> set[str]:
    keys: set[str] = set()

    if isinstance(value, dict):
        for key, child in value.items():
            full_key = f"{prefix}.{key}" if prefix else str(key)
            keys.add(full_key)
            keys.update(_extract_json_keys(child, full_key))

    elif isinstance(value, list):
        for item in value[:5]:
            keys.update(_extract_json_keys(item, prefix))

    return keys


def _overlap_score(left: list[str], right: list[str]) -> float:
    if not left or not right:
        return 0.0

    left_set = set(left)
    right_set = set(right)

    return round(len(left_set & right_set) / len(left_set | right_set), 3)


def _make_verdict(
    baseline: ResponseSummary,
    candidate: ResponseSummary,
    json_key_overlap: float,
    signals: list[str],
) -> str:
    if baseline.status_code == 200 and candidate.status_code == 200 and json_key_overlap >= 0.6:
        return "interesting: candidate response resembles successful baseline"

    if baseline.status_code == 200 and candidate.status_code in {401, 403}:
        return "expected: candidate appears blocked"

    if baseline.status_code == 200 and candidate.status_code == 404:
        return "likely safe/blocked: candidate returned not found"

    if candidate.status_code == 200 and candidate.interesting_keywords:
        return "review: candidate returned 200 with sensitive-looking keywords"

    if "identical_body" in signals:
        return "note: responses are identical"

    return "informational"
