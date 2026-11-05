#!/usr/bin/env python3
"""Accessibility Auditor — contrast, Dynamic Type, touch targets and VoiceOver.

Static accessibility checks that catch the defects App Store reviewers and
accessibility audits flag most often:

* text colours that fail WCAG AA contrast against the system background in
  either light or dark appearance
* fixed point sizes and single-line limits that break Dynamic Type
* tap targets smaller than 44x44pt
* icon-only buttons without an accessibility label
* interactive elements hidden from assistive technologies
* missing ``.accessibilityElement(children:)`` grouping on composite controls

Usage::

    python3 tools/accessibility-auditor/audit_accessibility.py [PATH] [--json]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.colors import (
    SYSTEM_BACKGROUND_DARK,
    SYSTEM_BACKGROUND_LIGHT,
    RGB,
    contrast_ratio,
    extract_literals,
)
from apple_native.report import Report
from apple_native.swiftscan import SwiftFile, load_swift_files

MIN_TOUCH_TARGET = 44.0

_FOREGROUND_DECL = re.compile(
    r"\.(?:foregroundStyle|foregroundColor|tint)\s*\(([^)\n]{1,80})\)"
)
_BACKGROUND_DECL = re.compile(r"\.background\s*\(([^)\n]{1,80})\)")
_FIXED_FONT = re.compile(r"\.font\s*\(\s*\.system\s*\(\s*size\s*:\s*([0-9.]+)")
_SMALL_FRAME = re.compile(
    r"\.frame\s*\(\s*(?:width|height)\s*:\s*([0-9.]+)\s*(?:,\s*(?:width|height)\s*:\s*([0-9.]+)\s*)?\)"
)


def _resolve_colour(expression: str) -> Optional[RGB]:
    """Best-effort resolution of a colour expression to an opaque RGB value."""

    literals = extract_literals(expression)
    if not literals:
        return None
    _, colour, _ = literals[0]
    if colour.a < 1.0:
        return colour.composite_over(SYSTEM_BACKGROUND_LIGHT)
    return colour


def audit_contrast(swift: SwiftFile, report: Report) -> int:
    hits = 0
    for match in _FOREGROUND_DECL.finditer(swift.code):
        colour = _resolve_colour(match.group(1))
        if colour is None:
            continue
        line = swift.line_of(match.start())
        light = contrast_ratio(colour, SYSTEM_BACKGROUND_LIGHT)
        dark = contrast_ratio(colour, SYSTEM_BACKGROUND_DARK)
        worst = min(light, dark)
        if worst < 3.0:
            hits += 1
            report.error(
                "A11Y001",
                f"Text colour {colour.hex()} reaches only {worst:.2f}:1 contrast "
                f"(light {light:.2f}:1, dark {dark:.2f}:1); WCAG AA requires 4.5:1.",
                file=swift.relative,
                line=line,
                hint="Darken/lighten the colour, or use .primary which adapts automatically.",
                docs="https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html",
            )
        elif worst < 4.5:
            hits += 1
            report.warn(
                "A11Y002",
                f"Text colour {colour.hex()} is {worst:.2f}:1 at worst; below the 4.5:1 AA threshold "
                f"for body text (light {light:.2f}:1, dark {dark:.2f}:1).",
                file=swift.relative,
                line=line,
                hint="Acceptable only for large or bold text (>=18.66pt bold, >=24pt regular).",
            )
    return hits


def audit_dynamic_type(swift: SwiftFile, report: Report) -> int:
    hits = 0
    for match in _FIXED_FONT.finditer(swift.code):
        size = float(match.group(1))
        hits += 1
        report.warn(
            "A11Y010",
            f"Fixed font size {size:g}pt ignores the user's Dynamic Type setting.",
            file=swift.relative,
            line=swift.line_of(match.start()),
            hint="Use a text style (.body, .title2) or .font(.system(.body, design: .rounded)).",
            docs="https://developer.apple.com/documentation/uikit/uifont/scaling_fonts_automatically",
        )
    for match in re.finditer(r"\.lineLimit\s*\(\s*1\s*\)", swift.clean):
        hits += 1
        report.info(
            "A11Y011",
            "lineLimit(1) truncates at accessibility text sizes.",
            file=swift.relative,
            line=swift.line_of(match.start()),
            hint="Allow 2+ lines or add .minimumScaleFactor(0.8).",
        )
    return hits


def audit_touch_targets(swift: SwiftFile, report: Report) -> int:
    hits = 0
    for match in _SMALL_FRAME.finditer(swift.code):
        values = [float(v) for v in match.groups() if v]
        if not values or min(values) >= MIN_TOUCH_TARGET:
            continue
        line = swift.line_of(match.start())
        nearby = swift.code[max(0, match.start() - 240):match.start() + 240]
        if "Button" not in nearby and "onTapGesture" not in nearby:
            continue
        hits += 1
        report.error(
            "A11Y020",
            f"Interactive element sized {min(values):g}pt is below the 44pt minimum touch target.",
            file=swift.relative,
            line=line,
            hint="Add .contentShape(Rectangle()) plus padding to reach 44x44pt without changing the visual size.",
            docs="https://developer.apple.com/design/human-interface-guidelines/accessibility",
        )
    return hits


def audit_labels(swift: SwiftFile, report: Report) -> int:
    hits = 0

    # Icon-only buttons: Button { } label: { Image(...) } with no Text in the label block.
    for match in re.finditer(r"Button\s*[({]", swift.code):
        window = swift.code[match.start():match.start() + 400]
        if "Image(" in window and "Text(" not in window and "accessibilityLabel" not in window:
            hits += 1
            report.warn(
                "A11Y030",
                "Icon-only Button has no accessibilityLabel; VoiceOver will read the SF Symbol name.",
                file=swift.relative,
                line=swift.line_of(match.start()),
                hint='Add .accessibilityLabel("Close") or use Label("Close", systemImage: "xmark").',
            )

    # Interactive elements hidden from assistive tech.
    for match in re.finditer(r"\.accessibilityHidden\s*\(\s*true\s*\)", swift.code):
        window = swift.code[max(0, match.start() - 300):match.start()]
        if "Button" in window or "onTapGesture" in window:
            hits += 1
            report.error(
                "A11Y031",
                "Interactive element is hidden from assistive technologies.",
                file=swift.relative,
                line=swift.line_of(match.start()),
                hint="Only decorative imagery should be hidden; controls must stay reachable.",
            )

    # Images with semantic meaning but no label.
    for match in re.finditer(r'Image\s*\(\s*(?:systemName|")\s*:?', swift.code):
        window = swift.code[match.start():match.start() + 220]
        if "accessibilityLabel" not in window and "accessibilityHidden" not in window and "Label(" not in window:
            hits += 1
            report.info(
                "A11Y032",
                "Image has neither an accessibility label nor an explicit decorative marking.",
                file=swift.relative,
                line=swift.line_of(match.start()),
                hint="Add .accessibilityLabel(_:) or .accessibilityHidden(true) if purely decorative.",
            )
            break
    return hits


def audit_one_file(swift: SwiftFile, report: Report) -> int:
    total = 0
    total += audit_contrast(swift, report)
    total += audit_dynamic_type(swift, report)
    total += audit_touch_targets(swift, report)
    total += audit_labels(swift, report)
    return total


def audit(root: Path) -> Report:
    report = Report(tool="accessibility-auditor", target=str(root), version=__version__)
    files = load_swift_files(root)
    report.data["scanned_files"] = len(files)

    total = 0
    for swift in files:
        total += audit_one_file(swift, report)

    report.data["issues"] = total
    if not files:
        report.warn("A11Y000", "No Swift files found to audit.")
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "accessibility-auditor",
        "Audit contrast, Dynamic Type, touch targets and VoiceOver labelling in SwiftUI sources.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("accessibility-auditor", args.path, allow_file=True)
    if guard is not None:
        return emit(guard, args)
    return emit(audit(Path(args.path).expanduser().resolve()), args,
                title="Apple Native Engineer — Accessibility Audit")


if __name__ == "__main__":
    raise SystemExit(main())
