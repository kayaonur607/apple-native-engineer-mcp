"""Uniform report + exit-code contract shared by every CLI tool.

Why a shared contract matters
-----------------------------
An agent (or a CI job) needs to know, without reading prose, whether a tool
found a blocking problem. Every tool therefore emits the same JSON envelope and
uses the same exit codes:

======  ==========================================================
exit 0  pass    - nothing above informational severity
exit 1  warn    - warnings only (treated as failure with --strict)
exit 2  fail    - at least one error or critical finding
======  ==========================================================

The JSON envelope is stable and versioned so that the MCP server, CI and third
party integrations can parse it without depending on human-readable output:

.. code-block:: json

    {
      "schema_version": "2.0",
      "tool": "privacy-auditor",
      "tool_version": "2.0.0",
      "target": "/abs/path",
      "status": "fail",
      "summary": {"critical": 1, "error": 0, "warning": 2, "info": 0, "total": 3},
      "findings": [
        {"code": "PRIV001", "severity": "critical", "message": "...",
         "file": "App/Store.swift", "line": 42, "hint": "...", "docs": "https://..."}
      ],
      "data": {"...": "tool specific payload"}
    }
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from enum import IntEnum
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

SCHEMA_VERSION = "2.0"


class Severity(IntEnum):
    """Ordered severity so that ``max()`` and comparisons behave sensibly."""

    INFO = 0
    WARNING = 1
    ERROR = 2
    CRITICAL = 3

    @property
    def label(self) -> str:
        return self.name.lower()


@dataclass
class Finding:
    """A single actionable observation produced by a tool."""

    code: str
    severity: Severity
    message: str
    file: Optional[str] = None
    line: Optional[int] = None
    hint: Optional[str] = None
    docs: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "code": self.code,
            "severity": self.severity.label,
            "message": self.message,
        }
        if self.file is not None:
            payload["file"] = self.file
        if self.line is not None:
            payload["line"] = self.line
        if self.hint is not None:
            payload["hint"] = self.hint
        if self.docs is not None:
            payload["docs"] = self.docs
        return payload

    def render(self) -> str:
        location = ""
        if self.file:
            location = f" {self.file}"
            if self.line:
                location += f":{self.line}"
        return f"[{self.severity.label.upper():8}] {self.code}{location} — {self.message}"


# Colour handling -----------------------------------------------------------


class _Palette:
    """ANSI colours, disabled automatically when stdout is not a TTY."""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def _wrap(self, code: str, text: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def bold(self, text: str) -> str:
        return self._wrap("1", text)

    def dim(self, text: str) -> str:
        return self._wrap("2", text)

    def red(self, text: str) -> str:
        return self._wrap("31", text)

    def yellow(self, text: str) -> str:
        return self._wrap("33", text)

    def green(self, text: str) -> str:
        return self._wrap("32", text)

    def cyan(self, text: str) -> str:
        return self._wrap("36", text)

    def blue(self, text: str) -> str:
        return self._wrap("34", text)


def _use_color(mode: str) -> bool:
    if mode == "always":
        return True
    if mode == "never":
        return False
    if os.environ.get("NO_COLOR"):
        return False
    return sys.stdout.isatty()


@dataclass
class Report:
    """Accumulates findings and renders the human / JSON representations."""

    tool: str
    target: str
    version: str = "2.0.0"
    data: Dict[str, Any] = field(default_factory=dict)
    findings: List[Finding] = field(default_factory=list)

    # -- accumulation -------------------------------------------------
    def add(
        self,
        code: str,
        severity: Severity,
        message: str,
        file: Any = None,
        line: Optional[int] = None,
        hint: Optional[str] = None,
        docs: Optional[str] = None,
    ) -> Finding:
        finding = Finding(
            code=code,
            severity=severity,
            message=message,
            file=str(file) if file is not None else None,
            line=line,
            hint=hint,
            docs=docs,
        )
        self.findings.append(finding)
        return finding

    def info(self, code: str, message: str, **kwargs: Any) -> Finding:
        return self.add(code, Severity.INFO, message, **kwargs)

    def warn(self, code: str, message: str, **kwargs: Any) -> Finding:
        return self.add(code, Severity.WARNING, message, **kwargs)

    def error(self, code: str, message: str, **kwargs: Any) -> Finding:
        return self.add(code, Severity.ERROR, message, **kwargs)

    def critical(self, code: str, message: str, **kwargs: Any) -> Finding:
        return self.add(code, Severity.CRITICAL, message, **kwargs)

    def extend(self, findings: Iterable[Finding]) -> None:
        self.findings.extend(findings)

    # -- derived state -------------------------------------------------
    def counts(self) -> Dict[str, int]:
        counts = {"critical": 0, "error": 0, "warning": 0, "info": 0}
        for finding in self.findings:
            counts[finding.severity.label] += 1
        counts["total"] = len(self.findings)
        return counts

    @property
    def status(self) -> str:
        counts = self.counts()
        if counts["critical"] or counts["error"]:
            return "fail"
        if counts["warning"]:
            return "warn"
        return "pass"

    def exit_code(self, strict: bool = False) -> int:
        status = self.status
        if status == "fail":
            return 2
        if status == "warn" and strict:
            return 1
        return 0

    # -- serialisation -------------------------------------------------
    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": SCHEMA_VERSION,
            "tool": self.tool,
            "tool_version": self.version,
            "target": self.target,
            "status": self.status,
            "summary": self.counts(),
            "findings": [finding.as_dict() for finding in self.findings],
            "data": self.data,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), indent=2, sort_keys=False, default=str)

    # -- human output --------------------------------------------------
    def render_human(self, color_mode: str = "auto", title: Optional[str] = None) -> str:
        c = _Palette(_use_color(color_mode))
        counts = self.counts()
        heading = title or f"{self.tool} — report"
        width = 74

        lines: List[str] = []
        lines.append(c.bold("=" * width))
        lines.append(c.bold(f"  {heading}"))
        lines.append(c.bold("=" * width))
        lines.append(f"  {'Target:':<14}{self.target}")
        lines.append(f"  {'Status:':<14}{self._status_text(c)}")
        lines.append(f"  {'Findings:':<14}{counts['total']} "
                     f"({counts['critical']} critical, {counts['error']} error, "
                     f"{counts['warning']} warning, {counts['info']} info)")
        lines.append(c.bold("-" * width))

        if not self.findings:
            lines.append(c.green("  No issues detected."))
        else:
            order = [Severity.CRITICAL, Severity.ERROR, Severity.WARNING, Severity.INFO]
            for severity in order:
                group = [f for f in self.findings if f.severity == severity]
                if not group:
                    continue
                for finding in group:
                    prefix = {
                        Severity.CRITICAL: c.red("✖"),
                        Severity.ERROR: c.red("✖"),
                        Severity.WARNING: c.yellow("▲"),
                        Severity.INFO: c.cyan("ℹ"),
                    }[severity]
                    lines.append(f"  {prefix} {c.bold(finding.code)} {finding.message}")
                    if finding.file:
                        loc = finding.file + (f":{finding.line}" if finding.line else "")
                        lines.append(c.dim(f"      at {loc}"))
                    if finding.hint:
                        lines.append(c.dim(f"      → {finding.hint}"))

        if self.data:
            lines.append(c.bold("-" * width))
            for key, value in self.data.items():
                if isinstance(value, (list, dict)):
                    rendered = json.dumps(value, default=str)
                    if len(rendered) > 60:
                        rendered = rendered[:57] + "..."
                    lines.append(f"  {key + ':':<22}{rendered}")
                else:
                    lines.append(f"  {key + ':':<22}{value}")

        lines.append(c.bold("=" * width))
        return "\n".join(lines)

    def _status_text(self, c: _Palette) -> str:
        status = self.status
        if status == "pass":
            return c.green("PASS")
        if status == "warn":
            return c.yellow("WARN")
        return c.red("FAIL")

    # -- emission ------------------------------------------------------
    def emit(self, json_output: bool = False, strict: bool = False,
             color_mode: str = "auto", title: Optional[str] = None) -> int:
        """Write the report to stdout and return the process exit code."""

        if json_output:
            sys.stdout.write(self.to_json() + "\n")
        else:
            sys.stdout.write(self.render_human(color_mode=color_mode, title=title) + "\n")
        return self.exit_code(strict=strict)


def fail_fast(tool: str, target: str, message: str, code: str = "GEN001",
              hint: Optional[str] = None) -> Report:
    """Build a one-finding report for unrecoverable setup errors."""

    report = Report(tool=tool, target=target)
    report.error(code, message, hint=hint)
    return report


def relative_path(path: Path, root: Path) -> str:
    """Best-effort path relative to *root*, for stable report output."""

    try:
        return str(path.resolve().relative_to(root.resolve()))
    except (ValueError, OSError):
        return str(path)
