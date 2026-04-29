"""
Safe Kali Runner for Blackhole AI Workbench.

This module prepares and executes Kali/Linux command-line actions only after
Scope Guard approval.

Version 0.1 supports:
- safe curl planning
- controlled curl execution
"""

from __future__ import annotations

import shlex
import subprocess
from dataclasses import dataclass

from bugintel.core.scope_guard import TargetScope


@dataclass
class CurlPlan:
    allowed: bool
    reason: str
    command: list[str]
    command_text: str
    requires_human_approval: bool


@dataclass
class CurlExecutionResult:
    allowed: bool
    exit_code: int | None
    stdout: str
    stderr: str
    command_text: str
    reason: str


def build_curl_plan(
    scope: TargetScope,
    url: str,
    method: str = "GET",
    timeout: int = 15,
) -> CurlPlan:
    """Build a safe curl command plan if the request is in scope."""
    method = method.upper().strip()
    decision = scope.is_url_allowed(url=url, method=method)

    if not decision.allowed:
        return CurlPlan(
            allowed=False,
            reason=decision.reason,
            command=[],
            command_text="",
            requires_human_approval=True,
        )

    command = [
        "curl",
        "-sk",
        "--http2",
        "--connect-timeout",
        "5",
        "--max-time",
        str(timeout),
        "-i",
        "-X",
        method,
        "-H",
        "Accept: application/json",
        url,
    ]

    return CurlPlan(
        allowed=True,
        reason=decision.reason,
        command=command,
        command_text=" ".join(shlex.quote(part) for part in command),
        requires_human_approval=scope.human_approval_required,
    )


def execute_curl_plan(plan: CurlPlan) -> CurlExecutionResult:
    """Execute an already-approved curl plan."""
    if not plan.allowed:
        return CurlExecutionResult(
            allowed=False,
            exit_code=None,
            stdout="",
            stderr="",
            command_text=plan.command_text,
            reason=plan.reason,
        )

    if not plan.command:
        return CurlExecutionResult(
            allowed=False,
            exit_code=None,
            stdout="",
            stderr="",
            command_text="",
            reason="No command generated",
        )

    completed = subprocess.run(
        plan.command,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )

    return CurlExecutionResult(
        allowed=True,
        exit_code=completed.returncode,
        stdout=completed.stdout,
        stderr=completed.stderr,
        command_text=plan.command_text,
        reason=plan.reason,
    )
