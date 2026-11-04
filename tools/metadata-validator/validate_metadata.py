#!/usr/bin/env python3
"""Metadata Validator — App Store listing copy and URL limits.

Every limit here comes from App Store Connect's own validation rules. Getting
them wrong costs a submission round-trip, so the tool checks them locally and
explains exactly how to fix each violation.

Usage::

    python3 tools/metadata-validator/validate_metadata.py metadata.json [--json]
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.report import Report

#: App Store Connect field limits (characters, not bytes).
LIMITS = {
    "name": 30,
    "subtitle": 30,
    "keywords": 100,
    "promotional_text": 170,
    "description": 4000,
    "whats_new": 4000,
}

REQUIRED_URLS = ("support_url", "privacy_url")
OPTIONAL_URLS = ("marketing_url",)

URL_RE = re.compile(r"^https://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?:/[^\s]*)?$")

LOCALES_REQUIRED = {"en-US"}


def _as_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _normalise(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Accept both flat and localisation-nested metadata shapes."""

    if "localizations" in payload and isinstance(payload["localizations"], dict):
        result: Dict[str, Any] = {}
        for locale, fields in payload["localizations"].items():
            merged = dict(payload)
            merged.pop("localizations", None)
            merged.update(fields)
            result[locale] = merged
        return {"__locales__": result}
    return {"__locales__": {"default": payload}}


def validate_metadata(payload: Dict[str, Any], source: str = "metadata.json") -> Report:
    report = Report(tool="metadata-validator", target=source, version=__version__)
    normalised = _normalise(payload)
    locales: Dict[str, Dict[str, Any]] = normalised["__locales__"]

    report.data = {"locales": sorted(locales.keys()), "fields_checked": 0}
    checked = 0

    for locale, fields in locales.items():
        prefix = f"[{locale}] " if locale != "default" else ""

        for field, limit in LIMITS.items():
            if field not in fields:
                continue
            text = _as_text(fields[field])
            checked += 1
            length = len(text)
            if length > limit:
                report.error(
                    "META001",
                    f"{prefix}{field} is {length} characters; the limit is {limit}.",
                    hint=f"Trim {length - limit} character(s). Apple counts characters, not bytes.",
                )
            if field in ("name", "subtitle") and text != text.strip():
                report.warn("META002", f"{prefix}{field} has leading or trailing whitespace.", hint="Trim it.")

        for field in ("name", "description"):
            if field not in fields or not _as_text(fields[field]).strip():
                report.error(
                    "META003",
                    f"{prefix}{field} is required but empty.",
                    hint="App Store Connect blocks submission without it.",
                )

        for field in REQUIRED_URLS:
            value = _as_text(fields.get(field))
            if not value:
                report.error(
                    "META004",
                    f"{prefix}{field} is required.",
                    hint="Provide an https URL that loads without authentication.",
                )
            elif not URL_RE.match(value):
                report.error(
                    "META005",
                    f"{prefix}{field} is not a valid https URL: {value}",
                    hint="Use https:// and a real TLD; App Store Connect rejects http:// and bare domains.",
                )
        for field in OPTIONAL_URLS:
            value = _as_text(fields.get(field))
            if value and not URL_RE.match(value):
                report.warn("META006", f"{prefix}{field} is not a valid https URL: {value}")

        keywords = _as_text(fields.get("keywords"))
        if keywords:
            checked += 1
            tokens = [token.strip() for token in keywords.split(",")]
            duplicates = {token.lower() for token in tokens if tokens.count(token) > 1}
            if duplicates:
                report.warn(
                    "META007",
                    f"{prefix}keywords contain duplicates: {', '.join(sorted(duplicates))}",
                    hint="Duplicate keywords waste the 100-character budget.",
                )
            if any(len(token) < 2 for token in tokens if token):
                report.info("META008", f"{prefix}keywords contain single-character tokens.",
                            hint="One-character keywords rarely rank and consume the budget.")
            if re.search(r"[A-Z]", keywords) and keywords == keywords.upper():
                report.info("META009", f"{prefix}keywords are all caps.", hint="Keyword casing does not matter for ranking.")

        description = _as_text(fields.get("description"))
        if description:
            if "http://" in description:
                report.warn("META010", f"{prefix}description contains an http:// link.",
                            hint="Only https:// links are tappable in the App Store description.")
            if description.count("\n") == 0 and len(description) > 400:
                report.info("META011", f"{prefix}description is a single paragraph.",
                            hint="Break long copy into short paragraphs or bullets for readability.")

        screenshots = fields.get("screenshots")
        if isinstance(screenshots, list) and screenshots:
            checked += 1
            if len(screenshots) < 3:
                report.warn(
                    "META012",
                    f"{prefix}only {len(screenshots)} screenshot(s) supplied.",
                    hint="App Store Connect requires 3–10 screenshots per device size.",
                )
            if len(screenshots) > 10:
                report.error("META013", f"{prefix}{len(screenshots)} screenshots supplied; the maximum is 10.")

    has_named_locales = set(locales) != {"default"}
    if has_named_locales and not (set(locales) & LOCALES_REQUIRED):
        report.warn("META014", "No en-US localisation present.",
                    hint="en-US is the fallback locale for the App Store listing.")

    report.data["fields_checked"] = checked
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "metadata-validator",
        "Validate an App Store listing metadata JSON against App Store Connect limits.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--file", help="Metadata JSON file (alternative to the positional path)")
    args = parser.parse_args(argv)

    candidate = Path(args.file or args.path).expanduser()
    if not candidate.is_file():
        report = Report(tool="metadata-validator", target=str(candidate), version=__version__)
        report.error(
            "META000",
            f"Metadata file not found: {candidate}",
            hint="Pass the JSON file as the positional argument, e.g. "
                 "tools/metadata-validator/validate_metadata.py metadata.json",
        )
        return emit(report, args)

    try:
        payload = json.loads(candidate.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report = Report(tool="metadata-validator", target=str(candidate), version=__version__)
        report.error("META016", f"Metadata file is not valid JSON: {exc}")
        return emit(report, args)

    return emit(validate_metadata(payload, str(candidate)), args,
                title="Apple Native Engineer — App Store Metadata Validation")


if __name__ == "__main__":
    raise SystemExit(main())
