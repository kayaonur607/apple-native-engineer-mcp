#!/usr/bin/env python3
"""SF Symbols Catalog — validate symbol names against the real system catalogue.

The catalogue in ``data/sf-symbols.json`` is extracted from the running macOS
``CoreGlyphs.bundle`` (``symbol_order.plist`` + ``name_availability.plist``), so
it knows every symbol name *and* the OS release that introduced it. That lets the
tool answer three questions no linter answers:

1. Does this symbol exist at all? (typos are caught before the build)
2. Is it available on the project's deployment target? (availability is per OS)
3. Is there a better match? (fuzzy suggestions from the same catalogue)

Usage::

    python3 tools/sf-symbols-catalog/check_symbols.py [PATH] [--json]
    python3 tools/sf-symbols-catalog/check_symbols.py --name "square.and.pencil" --ios 17.0
"""

from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import REPO_ROOT, __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import load_swift_files
from apple_native.xcode import discover, parse_version

CATALOG_PATH = REPO_ROOT / "data" / "sf-symbols.json"

SYMBOL_PATTERNS = [
    re.compile(r'Image\s*\(\s*systemName\s*:\s*"([^"]+)"'),
    re.compile(r'Label\s*\(\s*[^,]+,\s*systemImage\s*:\s*"([^"]+)"'),
    re.compile(r'systemImage\s*:\s*"([^"]+)"'),
    re.compile(r'Image\s*\(\s*systemImage\s*:\s*"([^"]+)"'),
    re.compile(r'SymbolEffect|symbolEffect'),
]


class Catalog:
    def __init__(self, payload: dict) -> None:
        self.raw = payload
        self.symbols: Dict[str, str] = payload.get("symbols", {})
        self.releases: Dict[str, Dict[str, str]] = payload.get("releases", {})
        self.names = set(self.symbols)

    def exists(self, name: str) -> bool:
        if name in self.names:
            return True
        # Symbol variants with .fill / .slash suffixes are separate catalogue entries,
        # but Xcode also accepts the base name; treat unknown suffixes as a miss.
        return False

    def available_on(self, name: str, platform: str, version: str) -> Optional[str]:
        release = self.symbols.get(name)
        if release is None:
            return None
        platform_version = self.releases.get(release, {}).get(platform)
        return platform_version

    def suggest(self, name: str, limit: int = 3) -> List[str]:
        return difflib.get_close_matches(name, self.names, n=limit, cutoff=0.6)


def load_catalog() -> Tuple[Optional[Catalog], Optional[str]]:
    if not CATALOG_PATH.exists():
        return None, f"Symbol catalogue missing: {CATALOG_PATH}"
    try:
        payload = json.loads(CATALOG_PATH.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        return None, f"Symbol catalogue is unreadable: {exc}"
    return Catalog(payload), None


def check_symbols(root: Path, ios_target: Optional[str] = None) -> Report:
    report = Report(tool="sf-symbols-catalog", target=str(root), version=__version__)
    catalog, error = load_catalog()
    if catalog is None:
        report.error("SFC001", error or "Symbol catalogue unavailable.")
        return report

    if ios_target is None:
        project = discover(root)
        ios_target = project.deployment_targets.get("iOS")

    report.data["catalog_symbols"] = len(catalog.symbols)
    report.data["deployment_target"] = ios_target or "unspecified"

    files = load_swift_files(root)
    used: Dict[str, List[Tuple[str, int]]] = {}
    for swift in files:
        for pattern in SYMBOL_PATTERNS[:-1]:
            for match in pattern.finditer(swift.code):
                used.setdefault(match.group(1), []).append((swift.relative, swift.line_of(match.start())))

    report.data["symbols_used"] = len(used)

    for name, sites in sorted(used.items()):
        if not catalog.exists(name):
            suggestions = catalog.suggest(name)
            hint = f"Did you mean: {', '.join(suggestions)}?" if suggestions else \
                   "Check the SF Symbols app for the current name."
            report.error(
                "SFC010",
                f"'{name}' is not an SF Symbol in the {catalog.raw.get('catalog_version', 'system')} catalogue.",
                file=sites[0][0],
                line=sites[0][1],
                hint=hint,
                docs="https://developer.apple.com/sf-symbols/",
            )
            continue

        if ios_target:
            introduced = catalog.available_on(name, "iOS", ios_target)
            target_tuple = parse_version(ios_target)
            if introduced and parse_version(introduced) > target_tuple:
                report.warn(
                    "SFC011",
                    f"'{name}' requires iOS {introduced} but the deployment target is {ios_target}.",
                    file=sites[0][0],
                    line=sites[0][1],
                    hint=f"Guard with @available(iOS {introduced}, *) or pick an older symbol.",
                )

    if not used:
        report.info("SFC012", "No SF Symbol references found.")
    return report


def check_single(name: str, platform: str, version: Optional[str]) -> Report:
    report = Report(tool="sf-symbols-catalog", target=name, version=__version__)
    catalog, error = load_catalog()
    if catalog is None:
        report.error("SFC001", error or "Symbol catalogue unavailable.")
        return report

    if not catalog.exists(name):
        suggestions = catalog.suggest(name)
        report.error("SFC010", f"'{name}' is not a known SF Symbol.",
                     hint=f"Closest matches: {', '.join(suggestions) or 'none'}")
        return report

    release = catalog.symbols[name]
    available = catalog.available_on(name, platform, version or "0")
    report.info("SFC020", f"'{name}' exists (release {release}, first shipped in {platform} {available}).")
    if version and available and parse_version(available) > parse_version(version):
        report.warn("SFC011", f"Not available on {platform} {version}; requires {available}.")
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "sf-symbols-catalog",
        "Validate SF Symbol names and their OS availability against the system catalogue.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--name", help="Check a single symbol name instead of scanning a project")
    parser.add_argument("--platform", default="iOS", choices=("iOS", "macOS", "watchOS", "tvOS", "visionOS"))
    parser.add_argument("--ios", dest="ios_target", help="Override the iOS deployment target")
    args = parser.parse_args(argv)

    if args.name:
        return emit(check_single(args.name, args.platform, args.ios_target), args,
                    title="Apple Native Engineer — SF Symbols")

    guard = guard_directory("sf-symbols-catalog", args.path)
    if guard is not None:
        return emit(guard, args)
    return emit(check_symbols(Path(args.path).expanduser().resolve(), args.ios_target), args,
                title="Apple Native Engineer — SF Symbols")


if __name__ == "__main__":
    raise SystemExit(main())
