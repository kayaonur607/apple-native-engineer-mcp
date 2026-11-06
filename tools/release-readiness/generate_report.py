#!/usr/bin/env python3
"""Release Readiness — weighted, evidence-based pre-submission gate.

This is the only tool that aggregates the others, and it is deliberately strict:

* a gate that could not be evaluated (no metadata file, no icon) is **NOT
  INSPECTED**, scores zero and forces the overall verdict to BLOCKED. A missing
  input is not the same thing as a passing input.
* the score is the weighted share of the gates that actually passed, not a
  starting 100 with deductions.
* every gate links back to the tool that produced it, so a failed release has a
  concrete next command.

Gate weights::

    privacy 25 · assets 15 · metadata 15 · project 15
    localization 10 · widgets 10 · accessibility 10

Usage::

    python3 tools/release-readiness/generate_report.py . --metadata metadata.json --icon AppIcon.png
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

_TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_TOOLS / "lib"))
for _tool in (
    "project-inspector", "privacy-auditor", "asset-validator", "metadata-validator",
    "localization-checker", "widget-validator", "accessibility-auditor",
):
    sys.path.insert(0, str(_TOOLS / _tool))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report, Severity

from audit_accessibility import audit as audit_accessibility
from audit_privacy import audit_privacy
from check_localization import check_localization
from inspect_project import inspect_project
from validate_assets import validate_assets
from validate_metadata import validate_metadata
from validate_widget import validate_widgets


@dataclass
class Gate:
    key: str
    label: str
    weight: int
    report: Optional[Report]
    command: str
    inspected: bool = True
    applicable: bool = True

    @property
    def status(self) -> str:
        if not self.applicable:
            return "not_applicable"
        if not self.inspected or self.report is None:
            return "not_inspected"
        return self.report.status

    def earned(self) -> float:
        """A gate is binary on errors: any critical or error finding zeroes it.

        Warnings cost 5% each, capped at 25%, so a gate with nothing but small
        advisories still contributes most of its weight.
        """

        if not self.applicable or not self.inspected or self.report is None:
            return 0.0
        counts = self.report.counts()
        if counts["critical"] or counts["error"]:
            return 0.0
        penalty = min(counts["warning"] * 0.05, 0.25)
        return (1.0 - penalty) * self.weight

    def as_row(self) -> Dict[str, object]:
        counts = self.report.counts() if self.report else {"critical": 0, "error": 0, "warning": 0, "info": 0}
        return {
            "gate": self.key,
            "label": self.label,
            "weight": self.weight,
            "status": self.status,
            "applicable": self.applicable,
            "inspected": self.inspected,
            "earned": round(self.earned(), 2),
            "findings": {k: counts[k] for k in ("critical", "error", "warning", "info")},
            "next_command": self.command,
        }


def _gate_from_report(key: str, label: str, weight: int, report: Report, command: str) -> Gate:
    return Gate(key=key, label=label, weight=weight, report=report, command=command)


def evaluate(root: Path, metadata_file: Optional[Path], icon_file: Optional[Path],
             screenshots: Optional[Path]) -> Tuple[Report, List[Gate]]:
    report = Report(tool="release-readiness", target=str(root), version=__version__)
    gates: List[Gate] = []

    gates.append(_gate_from_report(
        "project", "Project hygiene", 15, inspect_project(str(root)),
        "python3 tools/project-inspector/inspect_project.py .",
    ))
    gates.append(_gate_from_report(
        "privacy", "Privacy manifest", 25, audit_privacy(str(root)),
        "python3 tools/privacy-auditor/audit_privacy.py .",
    ))
    gates.append(_gate_from_report(
        "accessibility", "Accessibility", 10, audit_accessibility(root),
        "python3 tools/accessibility-auditor/audit_accessibility.py .",
    ))
    gates.append(_gate_from_report(
        "localization", "Localisation & RTL", 10, check_localization(str(root)),
        "python3 tools/localization-checker/check_localization.py .",
    ))

    widget_report = validate_widgets(str(root))
    has_widgets = bool(widget_report.data.get("widget_sources"))
    gates.append(Gate(
        key="widgets", label="Widgets & Live Activities", weight=10,
        report=widget_report, command="python3 tools/widget-validator/validate_widget.py .",
        inspected=has_widgets, applicable=has_widgets,
    ))

    if metadata_file and metadata_file.exists():
        asset_report = validate_assets(str(root), icon=str(icon_file) if icon_file else None,
                                       screenshots=str(screenshots) if screenshots else None)
        gates.append(_gate_from_report(
            "assets", "Assets & icon", 15, asset_report,
            "python3 tools/asset-validator/validate_assets.py . --icon AppIcon.png",
        ))

        import json
        try:
            payload = json.loads(metadata_file.read_text())
            meta_report = validate_metadata(payload, str(metadata_file))
            inspected = True
        except Exception as exc:  # noqa: BLE001 - surfaces as a blocked gate
            meta_report = Report(tool="metadata-validator", target=str(metadata_file), version=__version__)
            meta_report.error("META000", f"Metadata could not be parsed: {exc}")
            inspected = True
        gates.append(Gate(
            key="metadata", label="App Store metadata", weight=15,
            report=meta_report, command="python3 tools/metadata-validator/validate_metadata.py metadata.json",
            inspected=inspected,
        ))
    else:
        blocked = Report(tool="asset-validator", target=str(root), version=__version__)
        gates.append(Gate(
            key="assets", label="Assets & icon", weight=15, report=blocked,
            command="python3 tools/asset-validator/validate_assets.py . --icon AppIcon.png",
            inspected=False,
        ))
        gates.append(Gate(
            key="metadata", label="App Store metadata", weight=15, report=blocked,
            command="python3 tools/metadata-validator/validate_metadata.py metadata.json",
            inspected=False,
        ))

    applicable = [g for g in gates if g.applicable]
    total_weight = sum(g.weight for g in applicable) or 1
    earned = sum(g.earned() for g in applicable)
    score = round(earned / total_weight * 100)

    blockers = [g for g in gates if g.applicable and not g.inspected]
    failing = [g for g in gates if g.inspected and g.status == "fail"]
    warning_gates = [g for g in gates if g.inspected and g.status == "warn"]

    if blockers or failing:
        status = "BLOCKED"
    elif score >= 90 and not warning_gates:
        status = "CONFIGURED STATIC CHECKS PASSED"
    elif score >= 60:
        status = "ACTION REQUIRED"
    else:
        status = "BLOCKED"

    report.data = {
        "generated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "verdict": status,
        "score": score,
        "applicable_weight": total_weight,
        "gates": [g.as_row() for g in gates],
        "scope": "Configured static checks only; build, runtime accessibility, signing and App Review approval are not verified.",
        "blockers": [g.key for g in blockers],
        "failing_gates": [g.key for g in failing],
        "warning_gates": [g.key for g in warning_gates],
    }

    for gate in gates:
        if not gate.applicable:
            continue
        if not gate.inspected:
            report.error(
                "REL001",
                f"Gate '{gate.label}' was not inspected — no input provided.",
                hint=f"Provide the input, then re-run: {gate.command}",
            )
        elif gate.status == "fail" and gate.report is not None:
            counts = gate.report.counts()
            report.error(
                "REL002",
                f"Gate '{gate.label}' failed with {counts['critical']} critical and {counts['error']} error finding(s).",
                hint=f"Details: {gate.command}",
            )
        elif gate.status == "warn" and gate.report is not None:
            counts = gate.report.counts()
            report.warn(
                "REL003",
                f"Gate '{gate.label}' has {counts['warning']} warning(s).",
                hint=f"Details: {gate.command}",
            )

    if status == "CONFIGURED STATIC CHECKS PASSED":
        report.info("REL010", f"All {len(applicable)} applicable gates passed with a score of {score}/100.")
    elif blockers:
        report.info("REL011",
                    f"{len(blockers)} gate(s) could not be inspected, so the verdict is BLOCKED by design.",
                    hint="A gate with no input is not a passing gate.")

    return report, gates


def render_markdown(report: Report, gates: List[Gate]) -> str:
    data = report.data
    lines = [
        "# App Store Release Readiness Report",
        "",
        f"**Generated**: {data['generated_at']}  ",
        f"**Project**: `{report.target}`  ",
        f"**Verdict**: **{data['verdict']}**  ",
        f"**Score**: **{data['score']}/100** (weighted over {data['applicable_weight']} applicable points)",
        "",
        f"**Scope**: {data['scope']}",
        "",
        "## Quality gates",
        "",
        "| Gate | Weight | Status | Earned | Critical | Errors | Warnings |",
        "| :--- | ---: | :--- | ---: | ---: | ---: | ---: |",
    ]
    for gate in gates:
        row = gate.as_row()
        findings = row["findings"]  # type: ignore[index]
        status = str(row["status"]).upper().replace("_", " ")
        lines.append(
            f"| {row['label']} | {row['weight']} | {status} | {row['earned']} | "
            f"{findings['critical']} | {findings['error']} | {findings['warning']} |"
        )

    if data["blockers"]:
        lines += ["", "## Blocking inputs", ""]
        for gate in gates:
            if gate.applicable and not gate.inspected:
                lines.append(f"- **{gate.label}** — run `{gate.command}`")

    lines += ["", "## Finding register", ""]
    if not report.findings:
        lines.append("No findings.")
    else:
        for finding in sorted(report.findings, key=lambda f: -int(f.severity)):
            lines.append(f"- `{finding.code}` **{finding.severity.label}** — {finding.message}")
            if finding.hint:
                lines.append(f"  - {finding.hint}")

    lines += ["", "---", "", "_Generated by apple-native-engineer-mcp · release-readiness_", ""]
    return "\n".join(lines)


def main(argv=None) -> int:
    parser = build_parser(
        "release-readiness",
        "Aggregate every audit into a weighted App Store readiness verdict.",
        epilog="Exit codes: 0 ready, 1 warnings with --strict, 2 blocked.",
    )
    parser.add_argument("--metadata", help="Path to the App Store metadata JSON")
    parser.add_argument("--icon", help="Path to the 1024x1024 marketing icon")
    parser.add_argument("--screenshots", help="Path to a screenshots directory")
    parser.add_argument("--output", help="Write the Markdown report to this file")
    args = parser.parse_args(argv)

    guard = guard_directory("release-readiness", args.path)
    if guard is not None:
        return emit(guard, args)

    root = Path(args.path).expanduser().resolve()
    report, gates = evaluate(
        root,
        Path(args.metadata).expanduser() if args.metadata else None,
        Path(args.icon).expanduser() if args.icon else None,
        Path(args.screenshots).expanduser() if args.screenshots else None,
    )

    if args.output:
        out = Path(args.output).expanduser()
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_markdown(report, gates))
        report.data["markdown_output"] = str(out)

    return emit(report, args, title="Apple Native Engineer — Release Readiness")


if __name__ == "__main__":
    raise SystemExit(main())
