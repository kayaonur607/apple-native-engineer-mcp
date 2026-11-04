#!/usr/bin/env python3
"""Localization Checker — hardcoded strings, RTL mirroring and String Catalogs.

Detects the three localisation bugs that are cheap to fix early and expensive to
fix after launch:

1. user-visible string literals in SwiftUI views instead of ``LocalizedStringKey``
   or ``String(localized:)``
2. layout code that assumes left-to-right (``.padding(.leading)`` is fine,
   ``.left``/``.right`` and hardcoded ``alignment: .leading`` in RTL-hostile ways)
3. ``.xcstrings`` catalogs with missing languages or unlocalised plural forms

Usage::

    python3 tools/localization-checker/check_localization.py [PATH] [--json]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import iter_files, load_swift_files

#: Constructs that explicitly bypass localisation.
VERBATIM_PATTERNS = [
    re.compile(r'Text\s*\(\s*verbatim\s*:\s*"((?:[^"\\]|\\.){2,})"'),
    re.compile(r'String\s*\(\s*verbatim\s*:\s*"((?:[^"\\]|\\.){2,})"'),
]

#: UIKit / AppKit properties whose String overload is not localisable at all.
UIKIT_STRING_ASSIGNMENTS = [
    (re.compile(r'\.text\s*=\s*"((?:[^"\\]|\\.){2,})"'), ".text = \"...\""),
    (re.compile(r'\.placeholder\s*=\s*"((?:[^"\\]|\\.){2,})"'), ".placeholder = \"...\""),
    (re.compile(r'\.title\s*=\s*"((?:[^"\\]|\\.){2,})"'), ".title = \"...\""),
    (re.compile(r'setTitle\s*\(\s*"((?:[^"\\]|\\.){2,})"'), "setTitle(\"...\")"),
    (re.compile(r'setMessage\s*\(\s*"((?:[^"\\]|\\.){2,})"'), "setMessage(\"...\")"),
]

#: SwiftUI's `Text(String)` overload takes an already-resolved string, so an
#: interpolated variable is *not* looked up in the String Catalog.
TEXT_DYNAMIC = re.compile(r'Text\s*\(\s*([a-zA-Z_][\w.]*(?:\([^)]*\))?)\s*\)')

#: Direction-agnostic padding/margins are correct; these are not.
RTL_HOSTILE = [
    (re.compile(r"\.padding\s*\(\s*\.left\b"), ".padding(.left) does not mirror in RTL",
     "Use .padding(.leading) / .padding(.horizontal)."),
    (re.compile(r"\.padding\s*\(\s*\.right\b"), ".padding(.right) does not mirror in RTL",
     "Use .padding(.trailing) / .padding(.horizontal)."),
    (re.compile(r"\btextAlignment\s*:\s*\.left\b"), "textAlignment: .left ignores RTL",
     "Use .leading for natural alignment."),
    (re.compile(r"\bUIEdgeInsets\s*\([^)]*left\s*:"), "UIEdgeInsets(left:) is not mirrored",
     "Use leading/trailing insets or semantic margins."),
]


def scan_hardcoded_strings(report: Report, root: Path) -> None:
    """Report strings that genuinely cannot be localised.

    `Text("Hello")` is *not* a defect: SwiftUI treats the literal as a
    `LocalizedStringKey` and looks it up in the String Catalog automatically.
    The real defects are `Text(verbatim:)`, UIKit String assignments and
    `Text(someString)` where the value is already resolved.
    """

    files = load_swift_files(root)
    hits = 0

    for swift in files:
        if "#Preview" in swift.raw and swift.relative.endswith("Preview.swift"):
            continue

        for pattern in VERBATIM_PATTERNS:
            for match in pattern.finditer(swift.code):
                hits += 1
                report.warn(
                    "L10N001",
                    f'verbatim string bypasses localisation: "{match.group(1)[:60]}"',
                    file=swift.relative,
                    line=swift.line_of(match.start()),
                    hint="Use Text(\"...\") or String(localized: \"...\") so the String Catalog is consulted.",
                )

        for pattern, label in UIKIT_STRING_ASSIGNMENTS:
            for match in pattern.finditer(swift.code):
                hits += 1
                report.warn(
                    "L10N002",
                    f'UIKit string assignment is never localised: {label}',
                    file=swift.relative,
                    line=swift.line_of(match.start()),
                    hint="Use String(localized:) or NSLocalizedString(_:comment:).",
                )

        for match in TEXT_DYNAMIC.finditer(swift.clean):
            argument = match.group(1)
            if argument.startswith(("verbatim", ".init", "Image")):
                continue
            if argument[0].islower() and "(" not in argument:
                hits += 1
                report.info(
                    "L10N003",
                    f"Text({argument}) receives a resolved String, so it is not localised.",
                    file=swift.relative,
                    line=swift.line_of(match.start()),
                    hint="Pass a literal (LocalizedStringKey) or wrap the value in String(localized:).",
                )

    report.data["hardcoded_strings"] = hits


def scan_directional_layout(report: Report, root: Path) -> None:
    files = load_swift_files(root)
    hits = 0
    for swift in files:
        for pattern, message, hint in RTL_HOSTILE:
            for match in pattern.finditer(swift.code):
                hits += 1
                report.warn(
                    "L10N010",
                    message,
                    file=swift.relative,
                    line=swift.line_of(match.start()),
                    hint=hint,
                )
    report.data["rtl_issues"] = hits


def scan_string_catalogs(report: Report, root: Path) -> None:
    catalogs = list(iter_files(root, (".xcstrings",)))
    report.data["string_catalogs"] = len(catalogs)

    for catalog in catalogs:
        try:
            payload = json.loads(catalog.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            report.error("L10N020", f"String Catalog is not valid JSON: {exc}", file=str(catalog))
            continue

        source_language = payload.get("sourceLanguage", "en")
        strings = payload.get("strings", {})
        untranslated: List[str] = []
        total_locales: Dict[str, int] = {}

        for key, entry in strings.items():
            localizations = entry.get("localizations", {})
            for locale, value in localizations.items():
                total_locales[locale] = total_locales.get(locale, 0) + 1
            if entry.get("shouldTranslate") is False:
                continue
            if not localizations:
                untranslated.append(key)
                continue
            missing = [loc for loc in localizations if loc != source_language and not _has_translation(localizations[loc])]
            if missing:
                untranslated.append(f"{key} ({', '.join(missing)})")

        if untranslated:
            report.warn(
                "L10N021",
                f"{catalog.name}: {len(untranslated)} key(s) missing translations.",
                file=str(catalog.relative_to(root)) if catalog.is_relative_to(root) else str(catalog),
                hint="First few: " + ", ".join(untranslated[:5]),
            )

        for key, entry in strings.items():
            for locale, value in entry.get("localizations", {}).items():
                unit = value.get("stringUnit")
                if unit and unit.get("state") == "needs_review":
                    report.info(
                        "L10N022",
                        f"{catalog.name}: '{key}' [{locale}] is marked needs_review.",
                        file=str(catalog.name),
                    )
                    break

        report.data.setdefault("catalog_locales", {})[catalog.name] = sorted(total_locales.keys())

        variations = sum(1 for entry in strings.values() if _has_plural(entry))
        report.data.setdefault("plural_keys", {})[catalog.name] = variations

    if not catalogs:
        report.info(
            "L10N023",
            "No .xcstrings catalog found; strings are presumably localised elsewhere.",
            hint="Xcode 15+ defaults to String Catalogs for new localisations.",
        )


def _has_translation(value: Dict) -> bool:
    unit = value.get("stringUnit")
    if unit and unit.get("value"):
        return True
    variations = value.get("variations") or {}
    plural = variations.get("plural") or {}
    if plural:
        return all(
            (entry.get("stringUnit") or {}).get("value")
            for entry in plural.values()
        )
    return False


def _has_plural(entry: Dict) -> bool:
    for value in entry.get("localizations", {}).values():
        if (value.get("variations") or {}).get("plural"):
            return True
    return False


def check_localization(raw_root: str) -> Report:
    root = Path(raw_root).expanduser().resolve()
    report = Report(tool="localization-checker", target=str(root), version=__version__)

    scan_hardcoded_strings(report, root)
    scan_directional_layout(report, root)
    scan_string_catalogs(report, root)

    if report.data.get("hardcoded_strings", 0) == 0 and report.data.get("rtl_issues", 0) == 0:
        report.info("L10N030", "No localisation issues detected.")
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "localization-checker",
        "Detect hardcoded user-visible strings, RTL-hostile layout and incomplete String Catalogs.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("localization-checker", args.path)
    if guard is not None:
        return emit(guard, args)
    return emit(check_localization(args.path), args,
                title="Apple Native Engineer — Localization & RTL Audit")


if __name__ == "__main__":
    raise SystemExit(main())
