#!/usr/bin/env python3
"""Widget & Live Activity Validator.

WidgetKit bundles fail in ways that are invisible until a user adds the widget:
a missing ``DynamicIsland`` region, a Live Activity without the Info.plist flag,
or a timeline provider that never reloads. This tool audits all of them.

Usage::

    python3 tools/widget-validator/validate_widget.py [PATH] [--json]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import iter_files, load_swift_files
from apple_native.xcode import discover, read_plist

DYNAMIC_ISLAND_REGIONS = {
    "compactLeading": r"\bcompactLeading\s*:|CompactLeading",
    "compactTrailing": r"\bcompactTrailing\s*:|CompactTrailing",
    "minimal": r"DynamicIslandExpandedRegion|\bminimal\b|\bMinimal\b",
    "expanded": r"\.expanded\s*\(|ExpandedRegion",
}

WIDGET_FAMILIES = [
    "systemSmall", "systemMedium", "systemLarge", "systemExtraLarge",
    "accessoryCircular", "accessoryRectangular", "accessoryInline",
    "accessoryCorner",
]


def _widget_sources(root: Path):
    files = load_swift_files(root)
    return [f for f in files if "import WidgetKit" in f.clean or "import ActivityKit" in f.clean]


def validate_widgets(raw_root: str) -> Report:
    root = Path(raw_root).expanduser().resolve()
    report = Report(tool="widget-validator", target=str(root), version=__version__)

    project = discover(root)
    widget_files = _widget_sources(root)
    joined = "\n".join(f.code for f in widget_files)

    report.data["widget_sources"] = [f.relative for f in widget_files]
    report.data["has_widgetkit"] = "import WidgetKit" in joined
    report.data["has_activitykit"] = "import ActivityKit" in joined

    if not widget_files:
        report.info(
            "WID001",
            "No WidgetKit/ActivityKit sources found — nothing to validate.",
            hint="Run this tool inside a project that ships a widget extension.",
        )
        return report

    # -- Live Activities -------------------------------------------------
    if "import ActivityKit" in joined:
        families: List[str] = []
        if "ActivityAttributes" in joined:
            families.append("ActivityAttributes")
        live_activities = bool(re.search(r"\bActivity(?:<[^>]+>)?\.request\b", joined))
        supports_flag = False

        for plist_path in project.info_plists:
            data = read_plist(plist_path)
            if data and data.get("NSSupportsLiveActivities"):
                supports_flag = True
                break

        report.data["live_activities"] = live_activities
        report.data["live_activity_flag"] = supports_flag

        if live_activities and not supports_flag:
            report.error(
                "WID010",
                "Live Activities are requested but NSSupportsLiveActivities is not set in Info.plist.",
                hint="Add <key>NSSupportsLiveActivities</key><true/> to the app target's Info.plist.",
                docs="https://developer.apple.com/documentation/activitykit/starting-and-updating-live-activities-with-activitykit-push-notifications",
            )
        if live_activities and "ActivityAttributes" not in joined:
            report.error(
                "WID011",
                "Activity.request used without an ActivityAttributes conforming type.",
                hint="Live Activities require a struct conforming to ActivityAttributes.",
            )
        if live_activities and not re.search(r"pushType|\.token", joined):
            report.info(
                "WID013",
                "No push token handling found; the Live Activity will only update from the app process.",
                hint="Capture activity.pushToken updates if you need server-driven updates.",
            )

    # -- Dynamic Island ---------------------------------------------------
    has_dynamic_island = "DynamicIsland" in joined
    report.data["dynamic_island"] = has_dynamic_island

    if has_dynamic_island:
        for region, pattern in DYNAMIC_ISLAND_REGIONS.items():
            if not re.search(pattern, joined):
                report.warn(
                    "WID020",
                    f"DynamicIsland is missing the '{region}' presentation region.",
                    hint="Live Activities look broken on iPhone when compact/minimal states are empty.",
                )
        if not re.search(r"\.contentMarginsDisabled\s*\(", joined):
            report.info(
                "WID021",
                "Dynamic Island content may inherit default margins.",
                hint="Consider .contentMarginsDisabled() for edge-to-edge compact content.",
            )
    elif "ActivityAttributes" in joined:
        report.warn(
            "WID022",
            "A Live Activity is declared but no DynamicIsland presentation is implemented.",
            hint="Without it the activity falls back to the Lock Screen presentation only.",
        )

    # -- Widget configuration ---------------------------------------------
    families_found = [family for family in WIDGET_FAMILIES if family in joined]
    report.data["supported_families"] = families_found
    if families_found and "accessoryRectangular" not in families_found:
        report.info(
            "WID030",
            "No accessoryRectangular family declared; the widget will not appear on the Lock Screen.",
            hint="Add .accessoryRectangular to supportedFamilies for Lock Screen presence.",
        )
    if "supportedFamilies" not in joined:
        report.warn(
            "WID031",
            "No .supportedFamilies(_:) declaration found.",
            hint="Without it WidgetKit shows only the default family.",
        )

    providers = []
    if "TimelineProvider" in joined:
        providers.append("TimelineProvider")
    if "AppIntentTimelineProvider" in joined or "AppIntentConfiguration" in joined:
        providers.append("AppIntentTimelineProvider")
    if "@main" in joined and "WidgetBundle" in joined:
        providers.append("WidgetBundle")
    report.data["providers"] = providers
    if not providers:
        report.error(
            "WID032",
            "No TimelineProvider / AppIntentTimelineProvider / WidgetBundle found.",
            hint="A widget extension needs an @main entry point and a timeline provider.",
        )
    if "AppIntentTimelineProvider" not in providers and "AppIntentConfiguration" not in joined:
        report.info(
            "WID033",
            "Widget is not configurable via App Intents.",
            hint="AppIntentConfiguration is the modern replacement for IntentConfiguration (iOS 17+).",
        )

    # -- Shared container --------------------------------------------------
    if "App Group" not in joined and not re.search(r"group\.[a-zA-Z0-9_.-]+", joined):
        report.info(
            "WID034",
            "No App Group identifier found; the widget cannot share data with the app.",
            hint="Use containerURL(forSecurityApplicationGroupIdentifier:) with a group.* identifier.",
        )

    # -- Platform availability ---------------------------------------------
    if "WidgetKit" in joined and not re.search(r"@available\(iOS 1[4-9]|@available\(iOS 2[0-9]", joined):
        report.info(
            "WID035",
            "Widget sources do not declare availability.",
            hint="Guard iOS 17+ APIs (containerBackground, interactive widgets) with @available.",
        )

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "widget-validator",
        "Validate WidgetKit widgets, Dynamic Island regions and Live Activity configuration.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("widget-validator", args.path)
    if guard is not None:
        return emit(guard, args)
    return emit(validate_widgets(args.path), args,
                title="Apple Native Engineer — Widget & Live Activity Audit")


if __name__ == "__main__":
    raise SystemExit(main())
