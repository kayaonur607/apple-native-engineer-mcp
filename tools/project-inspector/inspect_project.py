#!/usr/bin/env python3
"""
Apple Native Engineer — Project Inspector Tool
Analyzes an Apple platform repository, Xcode project, or Swift Package.
Inspects structure, deployment targets, frameworks, and architecture.
"""

import sys
import os
import json
import argparse
from pathlib import Path

def inspect_project(root_dir: str) -> dict:
    root = Path(root_dir).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Project directory does not exist: {root_dir}")

    results = {
        "root_directory": str(root),
        "project_type": "Unknown",
        "has_xcode_project": False,
        "has_swift_package": False,
        "has_cocoapods": False,
        "swift_files_count": 0,
        "frameworks_detected": set(),
        "architecture_signals": set(),
        "privacy_manifest_found": False,
        "info_plist_found": False,
        "deployment_targets": {},
        "summary": ""
    }

    # Discover Xcode projects & Workspaces
    xcodeproj_files = list(root.glob("*.xcodeproj"))
    xcworkspace_files = list(root.glob("*.xcworkspace"))
    if xcodeproj_files:
        results["has_xcode_project"] = True
        results["xcode_projects"] = [f.name for f in xcodeproj_files]
        results["project_type"] = "Xcode Project"
    
    # Discover Swift Package Manager
    if (root / "Package.swift").exists():
        results["has_swift_package"] = True
        if results["project_type"] == "Unknown":
            results["project_type"] = "Swift Package"

    # Discover CocoaPods
    if (root / "Podfile").exists():
        results["has_cocoapods"] = True

    # Scan Swift source files
    swift_files = list(root.glob("**/*.swift"))
    # Filter out hidden or build files
    swift_files = [f for f in swift_files if ".build" not in str(f) and "DerivedData" not in str(f) and ".git" not in str(f)]
    results["swift_files_count"] = len(swift_files)

    for sf in swift_files:
        try:
            content = sf.read_text(encoding="utf-8", errors="ignore")
            # Framework detection
            if "import SwiftUI" in content:
                results["frameworks_detected"].add("SwiftUI")
            if "import UIKit" in content:
                results["frameworks_detected"].add("UIKit")
            if "import AppKit" in content:
                results["frameworks_detected"].add("AppKit")
            if "import StoreKit" in content:
                results["frameworks_detected"].add("StoreKit 2")
            if "import Observation" in content or "@Observable" in content:
                results["frameworks_detected"].add("Observation")
                results["architecture_signals"].add("Modern @Observable")
            if "import Combine" in content or "ObservableObject" in content:
                results["architecture_signals"].add("Legacy ObservableObject")
            if "import ComposableArchitecture" in content:
                results["architecture_signals"].add("TCA (Composable Architecture)")
            if "@MainActor" in content:
                results["architecture_signals"].add("@MainActor Thread Safety")
            if "import Testing" in content:
                results["frameworks_detected"].add("Swift Testing")
            if "import XCTest" in content:
                results["frameworks_detected"].add("XCTest")
        except Exception:
            continue

    # Discover Privacy Manifests
    privacy_files = list(root.glob("**/PrivacyInfo.xcprivacy"))
    if privacy_files:
        results["privacy_manifest_found"] = True
        results["privacy_manifests"] = [str(p.relative_to(root)) for p in privacy_files]

    # Discover Info.plist
    plist_files = list(root.glob("**/Info.plist"))
    if plist_files:
        results["info_plist_found"] = True
        results["info_plists"] = [str(p.relative_to(root)) for p in plist_files]

    results["frameworks_detected"] = sorted(list(results["frameworks_detected"]))
    results["architecture_signals"] = sorted(list(results["architecture_signals"]))

    results["summary"] = (
        f"{results['project_type']} with {results['swift_files_count']} Swift files. "
        f"Frameworks: {', '.join(results['frameworks_detected']) or 'None detected'}. "
        f"Privacy Manifest: {'Yes' if results['privacy_manifest_found'] else 'No'}."
    )

    return results

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer — Project Inspector")
    parser.add_argument("path", nargs="?", default=".", help="Path to project directory (default: current directory)")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    try:
        report = inspect_project(args.path)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("==========================================================")
            print("  Apple Native Engineer — Project Inspection Report       ")
            print("==========================================================")
            print(f"Directory:       {report['root_directory']}")
            print(f"Project Type:    {report['project_type']}")
            print(f"Swift Files:     {report['swift_files_count']}")
            print(f"Frameworks:      {', '.join(report['frameworks_detected']) or 'None'}")
            print(f"Architecture:    {', '.join(report['architecture_signals']) or 'Standard'}")
            print(f"Privacy Manifest:{' [FOUND]' if report['privacy_manifest_found'] else ' [MISSING]'}")
            print(f"Info.plist:      {' [FOUND]' if report['info_plist_found'] else ' [MISSING]'}")
            print("----------------------------------------------------------")
            print(f"Summary: {report['summary']}")
            print("==========================================================")
    except Exception as e:
        print(f"Error inspecting project: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
