#!/usr/bin/env python3
"""Liquid Glass Auditor — iOS 26 material adoption without the fake-glass trap.

Liquid Glass (iOS 26 / macOS 26) is a system material with real optics: it
refracts the backdrop, reacts to motion and merges with neighbouring glass. The
common failure mode is imitating it with stacked ``.ultraThinMaterial``,
``.blur`` and drop shadows — which looks wrong, costs GPU time per frame and
breaks under Reduce Transparency.

API surface verified against the iOS 27.2 SDK (SwiftUICore.swiftinterface):

======================================  ===================================
``.glassEffect(_:in:)``                 iOS 26+, visionOS unavailable
``GlassEffectContainer``                iOS 26+
``.glassEffectID / .glassEffectUnion``  iOS 26+
``.glassEffectTransition(_:)``          iOS 26+
``Glass.regular / .clear / .identity``  tints via ``.tint()``, ``.interactive()``
``.buttonStyle(.glass / .glassProminent)``
``.scrollEdgeEffectStyle(_:for:)``      iOS 26+
======================================  ===================================
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import SwiftFile, load_swift_files
from apple_native.xcode import discover, parse_version

#: Verified iOS 26 Liquid Glass API entry points.
GLASS_APIS = {
    ".glassEffect": "26.0",
    "GlassEffectContainer": "26.0",
    ".glassEffectID": "26.0",
    ".glassEffectUnion": "26.0",
    ".glassEffectTransition": "26.0",
    ".scrollEdgeEffectStyle": "26.0",
    ".scrollEdgeEffectHidden": "26.0",
    ".buttonStyle(.glass": "26.0",
    ".glassProminent": "26.0",
}

#: Combinations that imitate glass rather than using it.
FAKE_GLASS_PATTERNS = [
    (re.compile(r"\.ultraThinMaterial"), "Material used directly on a background"),
    (re.compile(r"\.blur\s*\(\s*radius\s*:"), "Manual blur stack"),
    (re.compile(r"\.background\s*\(\s*(?:Color|\.)?\s*\.?white\s*\.\s*opacity\s*\("),
     "Translucent white overlay pretending to be glass"),
    (re.compile(r"\.overlay\s*\{[^}]*LinearGradient"), "Hand-rolled specular gradient overlay"),
]

AVAILABILITY_GUARD = re.compile(r"[@#]available\s*\(\s*(?:iOS|macOS)\s*2[6-9]")


def _has_guard(swift: SwiftFile, offset: int) -> bool:
    """True when an availability guard exists in the 400 characters before *offset*."""

    window = swift.clean[max(0, offset - 400):offset]
    return bool(AVAILABILITY_GUARD.search(window))


def audit_file(swift: SwiftFile, report: Report, deployment: Tuple[int, ...], guarded: bool) -> Dict[str, int]:
    stats = {"glass_usages": 0, "guarded": 0, "fake": 0}

    for api, minimum in GLASS_APIS.items():
        for match in re.finditer(re.escape(api), swift.clean):
            stats["glass_usages"] += 1
            line = swift.line_of(match.start())
            if deployment and deployment < parse_version(minimum):
                if _has_guard(swift, match.start()) or guarded:
                    stats["guarded"] += 1
                else:
                    target_text = f"{deployment[0]}.{deployment[1]}"
                    report.error(
                        "LG001",
                        f"{api} requires iOS {minimum} but the deployment target is "
                        f"{target_text} without an availability guard.",
                        file=swift.relative,
                        line=line,
                        hint=f"Wrap the call site in `if #available(iOS {minimum.split('.')[0]}, *)` "
                             "or raise the deployment target.",
                    )
            else:
                stats["guarded"] += 1

    for pattern, label in FAKE_GLASS_PATTERNS:
        for match in pattern.finditer(swift.clean):
            line = swift.line_of(match.start())
            window = swift.clean[max(0, match.start() - 200):match.start() + 220]
            guarded_fallback = ".glassEffect" in window and (
                "#available" in window or "@available" in window
            )
            if guarded_fallback:
                continue  # legitimate material fallback next to real glass
            stats["fake"] += 1
            report.warn(
                "LG010",
                f"{label} — this is the classic imitation of Liquid Glass, not the material.",
                file=swift.relative,
                line=line,
                hint="Use .glassEffect(_:in:) on iOS 26+, with a material fallback guarded by "
                     "@available for older OS versions.",
                docs="https://developer.apple.com/documentation/technologyoverviews/liquid-glass",
            )
    return stats


def audit(root: Path) -> Report:
    report = Report(tool="liquid-glass-auditor", target=str(root), version=__version__)
    project = discover(root)
    ios_target = project.deployment_targets.get("iOS")
    deployment = parse_version(ios_target) if ios_target else tuple()

    files = load_swift_files(root)
    report.data["deployment_target"] = ios_target or "unspecified"
    report.data["swift_files"] = len(files)

    totals = {"glass_usages": 0, "guarded": 0, "fake": 0}
    for swift in files:
        guarded = bool("@available(iOS 26" in swift.clean or "@available(iOS 27" in swift.clean)
        stats = audit_file(swift, report, deployment, guarded)
        for key in totals:
            totals[key] += stats[key]

    report.data["glass_usages"] = totals["glass_usages"]
    report.data["guarded_usages"] = totals["guarded"]
    report.data["fake_glass_sites"] = totals["fake"]

    if totals["glass_usages"] == 0 and files:
        report.info(
            "LG020",
            "No Liquid Glass APIs detected.",
            hint="On iOS 26+, prefer .glassEffect / .buttonStyle(.glass) over hand-built translucent cards.",
        )
    elif totals["glass_usages"]:
        report.info(
            "LG021",
            f"{totals['glass_usages']} Liquid Glass API usage(s) detected "
            f"({totals['guarded']} guarded).",
        )

    if totals["glass_usages"] > 1:
        container_usage = any("GlassEffectContainer" in f.clean for f in files)
        if not container_usage:
            report.info(
                "LG022",
                "Multiple glass effects without GlassEffectContainer; adjacent glass cannot merge or morph.",
                hint="Wrap sibling glass elements in GlassEffectContainer and give them .glassEffectID "
                     "so they animate between states.",
            )

    heaviest = max(files, key=lambda f: f.clean.count(".ultraThinMaterial"), default=None)
    if heaviest and heaviest.clean.count(".ultraThinMaterial") >= 3:
        report.info(
            "LG023",
            f"{heaviest.relative} stacks {heaviest.clean.count('.ultraThinMaterial')} ultra-thin materials; "
            "each one samples the backdrop separately.",
            hint="One material surface plus content is cheaper and reads better than nested layers.",
        )

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "liquid-glass-auditor",
        "Audit iOS 26 Liquid Glass adoption and detect imitation glassmorphism.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("liquid-glass-auditor", args.path, allow_file=True)
    if guard is not None:
        return emit(guard, args)
    return emit(audit(Path(args.path).expanduser().resolve()), args,
                title="Apple Native Engineer — Liquid Glass Audit")


if __name__ == "__main__":
    raise SystemExit(main())
