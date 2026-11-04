#!/usr/bin/env python3
"""Project Inspector — structural analysis of an Apple platform codebase.

Answers the questions a senior engineer asks in the first five minutes on an
unfamiliar repository: what is this, what does it target, which frameworks and
architectural patterns are in play, and where is the debt?

Usage::

    python3 tools/project-inspector/inspect_project.py [PATH] [--json] [--strict]
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import iter_files, load_swift_files
from apple_native.xcode import discover, parse_version

FRAMEWORK_SIGNATURES = {
    "SwiftUI": ["import SwiftUI"],
    "UIKit": ["import UIKit"],
    "AppKit": ["import AppKit"],
    "WatchKit": ["import WatchKit"],
    "WidgetKit": ["import WidgetKit"],
    "ActivityKit": ["import ActivityKit"],
    "AppIntents": ["import AppIntents"],
    "StoreKit": ["import StoreKit"],
    "SwiftData": ["import SwiftData"],
    "CoreData": ["import CoreData"],
    "CloudKit": ["import CloudKit"],
    "Combine": ["import Combine"],
    "Observation": ["import Observation"],
    "Swift Testing": ["import Testing"],
    "XCTest": ["import XCTest"],
    "MapKit": ["import MapKit"],
    "AVFoundation": ["import AVFoundation"],
    "CoreLocation": ["import CoreLocation"],
    "PhotosUI": ["import PhotosUI"],
    "Charts": ["import Charts"],
    "Metal": ["import Metal"],
    "SpriteKit": ["import SpriteKit"],
    "RealityKit": ["import RealityKit"],
    "Spatial": ["import Spatial"],
    "HealthKit": ["import HealthKit"],
    "UserNotifications": ["import UserNotifications"],
    "BackgroundTasks": ["import BackgroundTasks"],
    "Network": ["import Network"],
    "Security": ["import Security"],
    "LocalAuthentication": ["import LocalAuthentication"],
    "CryptoKit": ["import CryptoKit"],
    "Vision": ["import Vision"],
    "CoreML": ["import CoreML"],
}

#: Deployment targets below this are considered legacy for a 2026 codebase.
MINIMUM_MODERN_IOS = (17, 0)


def _analyse_architecture(joined: str) -> List[str]:
    signals: List[str] = []
    if "@Observable" in joined:
        signals.append("Observation (@Observable)")
    if "ObservableObject" in joined:
        signals.append("Combine ObservableObject")
    if "@MainActor" in joined:
        signals.append("MainActor isolation")
    if "async let" in joined or "TaskGroup" in joined:
        signals.append("Structured concurrency")
    if "ComposableArchitecture" in joined or "@Reducer" in joined:
        signals.append("The Composable Architecture")
    if "ViewModel" in joined:
        signals.append("MVVM")
    if "Repository" in joined and "UseCase" in joined:
        signals.append("Clean Architecture (UseCase/Repository)")
    if "@Model" in joined and "ModelContainer" in joined:
        signals.append("SwiftData persistence")
    if "@Query" in joined:
        signals.append("SwiftData @Query")
    return signals


def inspect_project(raw_root: str) -> Report:
    root = Path(raw_root).expanduser().resolve()
    report = Report(tool="project-inspector", target=str(root), version=__version__)

    project = discover(root)
    swift_files = load_swift_files(root)
    joined = "\n".join(f.clean for f in swift_files)

    frameworks: List[str] = []
    for name, signatures in FRAMEWORK_SIGNATURES.items():
        if any(sig in joined for sig in signatures):
            frameworks.append(name)

    architecture = _analyse_architecture(joined)
    test_files = [f for f in swift_files if "Tests" in f.relative or "Test" in f.path.name]
    string_catalogs = list(iter_files(root, (".xcstrings",)))

    report.data = {
        "project_kind": project.kind,
        "targets": project.targets,
        "deployment_targets": project.deployment_targets,
        "swift_versions": project.swift_versions,
        "swift_files": len(swift_files),
        "swift_lines": sum(len(f.raw.splitlines()) for f in swift_files),
        "test_files": len(test_files),
        "frameworks": frameworks,
        "architecture": architecture,
        "string_catalogs": len(string_catalogs),
        "privacy_manifests": len(project.privacy_manifests),
        "spm_dependencies": project.has_spm_dependencies,
        "cocoapods": project.has_cocoapods,
        "bundle_ids": project.bundle_ids[:5],
    }

    # -- findings ---------------------------------------------------
    if project.kind == "unknown":
        report.warn(
            "PROJ001",
            "No .xcodeproj, .xcworkspace or Package.swift found at the project root.",
            hint="Run the tool from the directory that contains the project, or pass its path.",
        )
    if not swift_files:
        report.warn(
            "PROJ002",
            "No Swift sources found; nothing to analyse.",
            hint="Check that you passed the repository root rather than a build folder.",
        )

    ios_target = project.deployment_targets.get("iOS")
    if ios_target:
        if parse_version(ios_target) < MINIMUM_MODERN_IOS:
            report.warn(
                "PROJ003",
                f"iOS deployment target is {ios_target}; anything below 17.0 blocks modern SwiftUI "
                "APIs (@Observable, .spring(duration:bounce:), SwiftData).",
                hint="Raise IPHONEOS_DEPLOYMENT_TARGET to 17.0 or later, or use @available guards.",
                docs="https://developer.apple.com/documentation/xcode/configuring-a-multiplatform-app-target",
            )
    elif project.kind != "unknown":
        report.info(
            "PROJ004",
            "Deployment target could not be determined from the project files.",
            hint="Set an explicit deployment target so audits can reason about API availability.",
        )

    swift_versions = [v for v in project.swift_versions if v]
    if swift_versions and all(parse_version(v)[0] < 6 for v in swift_versions):
        report.warn(
            "PROJ005",
            f"Project builds with Swift {', '.join(swift_versions)}; Swift 6 language mode enables "
            "compile-time data-race safety.",
            hint="Adopt SWIFT_VERSION = 6.0 and fix strict-concurrency diagnostics module by module.",
            docs="https://www.swift.org/migration/documentation/swift-6-concurrency-migration-guide/",
        )

    if not test_files:
        report.warn(
            "PROJ006",
            "No test target sources found.",
            hint="Add a Swift Testing target (import Testing) — it is the default for new Xcode projects.",
        )

    if "ObservableObject" in joined and "@Observable" not in joined:
        report.warn(
            "PROJ007",
            "Combine-based ObservableObject state without any @Observable usage.",
            hint="Migrate view models to @Observable to avoid whole-view invalidation on every @Published write.",
            docs="https://developer.apple.com/documentation/observation/migrating-from-the-observable-object-protocol-to-the-observable-macro",
        )

    if "NavigationView" in joined:
        report.warn(
            "PROJ008",
            "NavigationView is deprecated since iOS 16.",
            hint="Replace with NavigationStack (or NavigationSplitView for multi-column layouts).",
        )

    if project.privacy_manifests == [] and project.kind != "unknown":
        report.info(
            "PROJ009",
            "No PrivacyInfo.xcprivacy present. Required if the app (or a bundled SDK) uses "
            "Required-Reason APIs or tracks users.",
            hint="Run tools/privacy-auditor/audit_privacy.py for a per-API breakdown.",
        )

    if len(string_catalogs) == 0 and project.kind != "unknown" and len(swift_files) > 5:
        report.info(
            "PROJ010",
            "No String Catalog (.xcstrings) found.",
            hint="String Catalogs are the supported localization format since Xcode 15.",
        )

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "project-inspector",
        "Inspect an Xcode project or Swift package: targets, deployment targets, "
        "frameworks, architecture signals and structural debt.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("project-inspector", args.path)
    if guard is not None:
        return emit(guard, args)
    report = inspect_project(args.path)
    return emit(report, args, title="Apple Native Engineer — Project Inspection")


if __name__ == "__main__":
    raise SystemExit(main())
