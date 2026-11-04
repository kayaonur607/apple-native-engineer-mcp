#!/usr/bin/env python3
"""
Apple Native Engineer — Widget & Dynamic Island Validator
Validates WidgetKit bundles, ActivityKit Live Activities, and Dynamic Island configurations.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

def audit_widgets(project_dir: Path):
    findings = []
    swift_files = list(project_dir.glob("**/*.swift"))
    plist_files = list(project_dir.glob("**/Info.plist"))

    has_live_activity_model = False
    has_dynamic_island = False
    has_widget_protocol = False
    has_compact_leading = False
    has_compact_trailing = False
    has_minimal = False

    for sfile in swift_files:
        if any(part in sfile.parts for part in [".build", "DerivedData"]):
            continue
        try:
            content = sfile.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        rel_path = str(sfile.relative_to(project_dir))

        if ": Widget" in content or "struct " in content and "Widget" in content:
            has_widget_protocol = True

        if "ActivityAttributes" in content:
            has_live_activity_model = True

        if "DynamicIsland" in content:
            has_dynamic_island = True
            if "compactLeading:" in content or "compactLeading" in content:
                has_compact_leading = True
            if "compactTrailing:" in content or "compactTrailing" in content:
                has_compact_trailing = True
            if "minimal:" in content or "minimal" in content:
                has_minimal = True

    # Validate Info.plist for NSSupportsLiveActivities
    has_live_activity_plist_flag = False
    for pfile in plist_files:
        try:
            pcontent = pfile.read_text(encoding="utf-8", errors="ignore")
            if "NSSupportsLiveActivities" in pcontent:
                has_live_activity_plist_flag = True
                break
        except Exception:
            pass

    if has_live_activity_model and not has_live_activity_plist_flag:
        findings.append({
            "severity": "Critical",
            "type": "MissingLiveActivitiesPlistFlag",
            "message": "Project defines ActivityAttributes but 'NSSupportsLiveActivities' boolean is missing from Info.plist."
        })

    if has_dynamic_island:
        if not (has_compact_leading and has_compact_trailing):
            findings.append({
                "severity": "High",
                "type": "IncompleteDynamicIslandCompactState",
                "message": "DynamicIsland implementation is missing either compactLeading or compactTrailing presentation."
            })
        if not has_minimal:
            findings.append({
                "severity": "High",
                "type": "MissingDynamicIslandMinimalState",
                "message": "DynamicIsland implementation is missing 'minimal' presentation for multi-activity situations."
            })

    return {
        "hasWidget": has_widget_protocol,
        "hasLiveActivities": has_live_activity_model,
        "hasDynamicIsland": has_dynamic_island,
        "liveActivitiesPlistConfigured": has_live_activity_plist_flag,
        "findings": findings
    }

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer Widget Validator")
    parser.add_argument("--project-dir", default=".", help="Path to project directory")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: Directory '{project_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    result = audit_widgets(project_dir)
    findings = result["findings"]
    criticals = [f for f in findings if f["severity"] == "Critical"]
    highs = [f for f in findings if f["severity"] == "High"]

    status = "PASS" if not criticals and not highs else "FAIL" if criticals else "WARNING"

    output = {
        "status": status,
        "projectDir": str(project_dir),
        "widgetSummary": {
            "hasWidget": result["hasWidget"],
            "hasLiveActivities": result["hasLiveActivities"],
            "hasDynamicIsland": result["hasDynamicIsland"],
            "plistConfigured": result["liveActivitiesPlistConfigured"]
        },
        "summary": {
            "critical": len(criticals),
            "high": len(highs),
            "totalIssues": len(findings)
        },
        "findings": findings
    }

    if args.json:
        print(json.dumps(output, indent=2))
        sys.exit(0 if not criticals else 1)

    print("=" * 60)
    print("🏝️  Apple Native Engineer — Widget & Live Activity Validator")
    print("=" * 60)
    print(f"WidgetKit Detected:    {'Yes' if result['hasWidget'] else 'No'}")
    print(f"Live Activities:       {'Yes' if result['hasLiveActivities'] else 'No'}")
    print(f"Dynamic Island:        {'Yes' if result['hasDynamicIsland'] else 'No'}")
    print(f"Plist Flag Configured: {'Yes' if result['liveActivitiesPlistConfigured'] else 'No'}")
    print(f"Status:                {status}")
    print("=" * 60)

    if findings:
        print("\nFindings:")
        for idx, item in enumerate(findings, start=1):
            print(f"[{idx}] [{item['severity'].upper()}] {item['type']}")
            print(f"    {item['message']}")
    else:
        print("\n✅ All WidgetKit and Dynamic Island configurations conform to Apple guidelines.")

    sys.exit(0 if not criticals else 1)

if __name__ == "__main__":
    main()
