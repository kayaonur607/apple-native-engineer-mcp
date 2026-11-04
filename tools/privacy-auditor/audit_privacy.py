#!/usr/bin/env python3
"""
Apple Native Engineer — Privacy & Required-Reason API Auditor
Scans source code for Apple Required-Reason API usage, verifies
PrivacyInfo.xcprivacy declarations, and audits Info.plist permission strings.
"""

import sys
import os
import re
import plistlib
import json
import argparse
from pathlib import Path

REQUIRED_REASON_SIGNATURES = {
    "NSPrivacyAccessedAPICategoryUserDefaults": [
        r"UserDefaults\.standard",
        r"NSUserDefaults",
        r"@AppStorage"
    ],
    "NSPrivacyAccessedAPICategoryFileTimestamp": [
        r"contentModificationDate",
        r"creationDate",
        r"\bstat\b",
        r"\bfstat\b",
        r"\bgetattrlist\b"
    ],
    "NSPrivacyAccessedAPICategorySystemBootTime": [
        r"systemUptime",
        r"mach_absolute_time"
    ],
    "NSPrivacyAccessedAPICategoryDiskSpace": [
        r"volumeAvailableCapacityKey",
        r"volumeTotalCapacityKey",
        r"\bstatfs\b",
        r"\bfstatfs\b"
    ]
}

SENSITIVE_PERMISSIONS = [
    "NSCameraUsageDescription",
    "NSMicrophoneUsageDescription",
    "NSLocationWhenInUseUsageDescription",
    "NSLocationAlwaysAndWhenInUseUsageDescription",
    "NSPhotoLibraryUsageDescription",
    "NSContactsUsageDescription",
    "NSBluetoothAlwaysUsageDescription",
    "NSFaceIDUsageDescription",
    "NSUserTrackingUsageDescription"
]

def scan_source_code_for_apis(root: Path) -> dict:
    detected = {cat: [] for cat in REQUIRED_REASON_SIGNATURES}
    swift_files = list(root.glob("**/*.swift")) + list(root.glob("**/*.m")) + list(root.glob("**/*.mm"))
    swift_files = [f for f in swift_files if ".build" not in str(f) and "DerivedData" not in str(f) and ".git" not in str(f)]

    for file_path in swift_files:
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            for cat, patterns in REQUIRED_REASON_SIGNATURES.items():
                for pat in patterns:
                    matches = list(re.finditer(pat, content))
                    if matches:
                        rel_path = str(file_path.relative_to(root))
                        detected[cat].append({
                            "file": rel_path,
                            "pattern": pat,
                            "occurrences": len(matches)
                        })
                        break
        except Exception:
            continue

    return {k: v for k, v in detected.items() if v}

def inspect_privacy_manifest(manifest_path: Path) -> dict:
    if not manifest_path.exists():
        return {"found": False, "declared_categories": []}

    try:
        with manifest_path.open("rb") as f:
            plist = plistlib.load(f)
            api_types = plist.get("NSPrivacyAccessedAPITypes", [])
            categories = [item.get("NSPrivacyAccessedAPIType") for item in api_types if isinstance(item, dict)]
            return {
                "found": True,
                "file": str(manifest_path),
                "declared_categories": categories,
                "tracking_enabled": plist.get("NSPrivacyTracking", False)
            }
    except Exception as e:
        return {"found": True, "error": str(e), "declared_categories": []}

def audit_info_plist(plist_path: Path) -> dict:
    if not plist_path.exists():
        return {"found": False, "permissions": {}}

    try:
        with plist_path.open("rb") as f:
            plist = plistlib.load(f)
            found_permissions = {}
            for perm in SENSITIVE_PERMISSIONS:
                if perm in plist:
                    val = str(plist[perm]).strip()
                    is_generic = len(val) < 20 or any(bad in val.lower() for bad in ["needed", "required", "access", "app needs"])
                    found_permissions[perm] = {
                        "value": val,
                        "length": len(val),
                        "suspicious_generic": is_generic
                    }
            return {"found": True, "file": str(plist_path), "permissions": found_permissions}
    except Exception as e:
        return {"found": True, "error": str(e), "permissions": {}}

def run_privacy_audit(project_dir: str) -> dict:
    root = Path(project_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Directory not found: {project_dir}")

    report = {
        "project_directory": str(root),
        "compliant": True,
        "critical_issues": [],
        "warnings": [],
        "detected_apis": scan_source_code_for_apis(root),
        "privacy_manifest": None,
        "permission_descriptions": None
    }

    # Find Privacy Manifest
    manifests = list(root.glob("**/PrivacyInfo.xcprivacy"))
    if manifests:
        manifest_info = inspect_privacy_manifest(manifests[0])
        report["privacy_manifest"] = manifest_info
        declared = manifest_info.get("declared_categories", [])

        # Cross-reference detected APIs against declared categories
        for api_cat, callers in report["detected_apis"].items():
            if api_cat not in declared:
                report["compliant"] = False
                report["critical_issues"].append(
                    f"Required-Reason API '{api_cat}' is called in {len(callers)} file(s) but is NOT declared in PrivacyInfo.xcprivacy!"
                )
    else:
        # If APIs were detected but NO manifest exists
        if report["detected_apis"]:
            report["compliant"] = False
            report["critical_issues"].append(
                f"Source code calls {len(report['detected_apis'])} Required-Reason API category/categories, but NO PrivacyInfo.xcprivacy was found in the project!"
            )
        else:
            report["warnings"].append("No PrivacyInfo.xcprivacy found in project.")

    # Find Info.plist
    plists = list(root.glob("**/Info.plist"))
    if plists:
        plist_info = audit_info_plist(plists[0])
        report["permission_descriptions"] = plist_info
        for perm_key, perm_data in plist_info.get("permissions", {}).items():
            if perm_data.get("suspicious_generic"):
                report["warnings"].append(
                    f"Permission '{perm_key}' description may be too vague ('{perm_data['value']}'). Apple Review Guidelines recommend explaining the specific user benefit."
                )

    return report

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer — Privacy & Manifest Auditor")
    parser.add_argument("path", nargs="?", default=".", help="Path to project directory")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    try:
        report = run_privacy_audit(args.path)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("==========================================================")
            print("  Apple Native Engineer — Privacy & Manifest Audit Report ")
            print("==========================================================")
            print(f"Directory:    {report['project_directory']}")
            print(f"Compliance:   {'[PASS] COMPLIANT' if report['compliant'] else '[FAIL] ACTION REQUIRED'}")
            print("----------------------------------------------------------")
            
            print(f"Detected Required-Reason APIs:")
            if report["detected_apis"]:
                for cat, files in report["detected_apis"].items():
                    print(f"  • {cat} (in {len(files)} file(s))")
            else:
                print("  • None detected.")

            print("\nPrivacy Manifest Status:")
            if report["privacy_manifest"] and report["privacy_manifest"].get("found"):
                print(f"  ✓ Found: {report['privacy_manifest']['file']}")
                print(f"  Declared Categories: {', '.join(report['privacy_manifest']['declared_categories']) or 'None'}")
            else:
                print("  ✗ Missing PrivacyInfo.xcprivacy!")

            if report["critical_issues"]:
                print("\n[CRITICAL ISSUES - APP STORE REJECTION RISK]:")
                for issue in report["critical_issues"]:
                    print(f"  ✗ {issue}")

            if report["warnings"]:
                print("\n[WARNINGS / SUGGESTIONS]:")
                for w in report["warnings"]:
                    print(f"  ⚠ {w}")

            print("==========================================================")

        sys.exit(0 if report["compliant"] else 1)
    except Exception as e:
        print(f"Error executing privacy audit: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
