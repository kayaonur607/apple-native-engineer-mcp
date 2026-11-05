#!/usr/bin/env python3
"""App Store Review Risk — map what the code does to the guidelines reviewers cite.

This is not a reviewer simulator and it does not promise approval. It looks for
the specific, checkable conditions that appear in rejection letters, and for each
one it names the guideline section, the evidence in the project, and the fix.

Checks are deliberately conservative: every finding points at a file and a line,
or at an absence the tool can prove (a sensor used, a usage description missing).

Usage::

    python3 tools/app-store-review/review.py .
    python3 tools/app-store-review/review.py . --metadata metadata.json --json
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import load_swift_files
from apple_native.xcode import discover, find_info_plist, read_plist

GUIDELINES = "https://developer.apple.com/app-store/review/guidelines/"

#: Frameworks that need a matching NS*UsageDescription in Info.plist (5.1.1).
SENSOR_REQUIREMENTS: List[Tuple[str, str, str]] = [
    (r"\bAVCaptureDevice\b|\bAVCaptureSession\b", "NSCameraUsageDescription", "camera"),
    (r"\bAVAudioRecorder\b|\bAVAudioSession\b.*record", "NSMicrophoneUsageDescription", "microphone"),
    (r"\bCLLocationManager\b|\brequestWhenInUseAuthorization\b", "NSLocationWhenInUseUsageDescription", "location"),
    (r"\bPHPhotoLibrary\b|\bPHPickerViewController\b", "NSPhotoLibraryUsageDescription", "photo library"),
    (r"\bCNContactStore\b", "NSContactsUsageDescription", "contacts"),
    (r"\bEKEventStore\b", "NSCalendarsUsageDescription", "calendar"),
    (r"\bHKHealthStore\b", "NSHealthShareUsageDescription", "health data"),
    (r"\bATTrackingManager\b", "NSUserTrackingUsageDescription", "tracking"),
    (r"\bSFSpeechRecognizer\b", "NSSpeechRecognitionUsageDescription", "speech recognition"),
    (r"\bBluetoothManager\b|\bCBCentralManager\b", "NSBluetoothAlwaysUsageDescription", "Bluetooth"),
]

PLACEHOLDER_PATTERNS = [
    (r"\bTODO\b", "TODO marker"),
    (r"\bFIXME\b", "FIXME marker"),
    (r"lorem ipsum", "placeholder copy"),
    (r"coming soon", "“coming soon” placeholder"),
    (r"sample text", "sample copy"),
]

EXTERNAL_PAYMENT = re.compile(r"stripe\.com|paypal\.com|checkout\.", re.IGNORECASE)
ACCOUNT_CREATION = re.compile(r"sign\s?up|createAccount|register(?:User|Account)|SignInWithApple", re.IGNORECASE)
ACCOUNT_DELETION = re.compile(r"deleteAccount|delete\s?account|removeAccount", re.IGNORECASE)


def info_plist_keys(root: Path, project) -> Tuple[Dict[str, object], Optional[Path]]:
    for candidate in project.info_plists:
        data = read_plist(candidate)
        if data and ("CFBundleIdentifier" in data or "NSCameraUsageDescription" in data):
            return data, candidate
    data = find_info_plist(root, project) or {}
    return data, project.info_plists[0] if project.info_plists else None


def check_usage_descriptions(report: Report, sources, plist: Dict[str, object]) -> None:
    joined = "\n".join(source.clean for source in sources)
    for pattern, key, label in SENSOR_REQUIREMENTS:
        match = re.search(pattern, joined)
        if not match:
            continue
        if plist.get(key):
            continue
        report.error(
            "RVW101",
            f"The app uses the {label} but Info.plist has no {key}.",
            hint=f"Add a specific, user-facing {key} — Guideline 5.1.1 rejects apps that access {label} "
                 "without a purpose string.",
            docs=GUIDELINES,
        )


def check_placeholder_content(report: Report, sources) -> None:
    for source in sources:
        for pattern, label in PLACEHOLDER_PATTERNS:
            for match in re.finditer(pattern, source.code, re.IGNORECASE):
                report.warn(
                    "RVW201",
                    f"{label} in shipped code — reviewers treat visible placeholders as an incomplete app (2.1).",
                    file=source.relative,
                    line=source.line_of(match.start()),
                    hint="Remove it, or gate it behind a debug flag that cannot ship.",
                    docs=GUIDELINES,
                )
                break


def check_account_deletion(report: Report, sources) -> None:
    joined = "\n".join(source.clean for source in sources)
    if not ACCOUNT_CREATION.search(joined):
        return
    if not ACCOUNT_DELETION.search(joined):
        report.error(
            "RVW301",
            "The app offers account creation but no account deletion path was found.",
            hint="Guideline 5.1.1(v): apps that support account creation must let people delete the account in-app.",
            docs=GUIDELINES,
        )


def check_external_payments(report: Report, sources, stores_digital_goods: bool) -> None:
    # Strings matter here: a payment URL lives inside a literal, which `.clean` blanks.
    joined = "\n".join(source.code for source in sources)
    if not EXTERNAL_PAYMENT.search(joined):
        return
    severity = report.error if stores_digital_goods else report.warn
    severity(
        "RVW401",
        "An external payment provider is referenced in code.",
        hint="Guideline 3.1.1: digital goods and subscriptions sold in the app must use In-App Purchase. "
             "Physical goods and services are exempt — say which one this is in the review notes.",
        docs=GUIDELINES,
    )


def check_webview_only(report: Report, sources) -> None:
    joined = "\n".join(source.clean for source in sources)
    if "WKWebView" not in joined:
        return
    native = any(marker in joined for marker in ("NavigationStack", "NavigationSplitView", "List {", "TabView"))
    if not native:
        report.warn(
            "RVW501",
            "The project looks like a web wrapper: WKWebView with no native navigation or list views.",
            hint="Guideline 4.2 (Minimum Functionality) rejects apps that are only a repackaged website.",
            docs=GUIDELINES,
        )


def check_private_api(report: Report, sources) -> None:
    banned = [
        (r"\bUIWebView\b", "UIWebView is a deprecated, rejected API"),
        (r"NSClassFromString\s*\(\s*\"UI[A-Z]", "reflective access to private UIKit classes"),
        (r"\bperformSelector\b", "performSelector on private selectors is a rejection risk (2.5.1)"),
    ]
    for source in sources:
        for pattern, reason in banned:
            for match in re.finditer(pattern, source.code):
                report.error("RVW601", reason + ".",
                             file=source.relative, line=source.line_of(match.start()),
                             hint="Replace with the public API; Guideline 2.5.1 rejects private or deprecated APIs.",
                             docs=GUIDELINES)


def check_review_notes(report: Report, project, plist: Dict[str, object]) -> None:
    if "CFBundleDisplayName" not in plist and "CFBundleName" not in plist:
        report.warn("RVW701", "Info.plist has no CFBundleDisplayName/CFBundleName.",
                    hint="The App Store listing and the bundle name must agree (2.3.1).", docs=GUIDELINES)
    if not project.privacy_manifests:
        report.warn("RVW702", "No privacy manifest in the project.",
                    hint="Guideline 5.1 requires accurate privacy disclosures; run the privacy auditor for detail.",
                    docs=GUIDELINES)


def check_metadata(report: Report, metadata_path: Optional[Path]) -> None:
    if metadata_path is None or not metadata_path.exists():
        report.info("RVW801", "No listing metadata supplied; metadata checks were skipped.",
                    hint="Pass --metadata metadata.json to include 2.3.1 accuracy checks.")
        return
    try:
        payload = json.loads(metadata_path.read_text())
    except (OSError, json.JSONDecodeError):
        report.warn("RVW802", "Listing metadata could not be parsed; skipped.")
        return
    text = json.dumps(payload)
    if "http://" in text:
        report.warn("RVW803", "Listing metadata contains an http:// URL.",
                    hint="Only https:// links are accepted and tappable (2.3.1).", docs=GUIDELINES)
    if "@example.com" in text:
        report.info("RVW804", "Listing metadata still contains example.com placeholders.",
                    hint="Replace them before submitting — reviewers check that URLs resolve.", docs=GUIDELINES)


def review(root: Path, metadata_path: Optional[Path]) -> Report:
    report = Report(tool="app-store-review", target=str(root), version=__version__)
    project = discover(root)
    sources = load_swift_files(root)
    plist, plist_path = info_plist_keys(root, project)
    joined = "\n".join(source.clean for source in sources)

    report.data = {
        "swift_files": len(sources),
        "info_plist": str(plist_path.relative_to(root)) if plist_path and plist_path.is_relative_to(root) else None,
        "privacy_manifests": len(project.privacy_manifests),
        "guidelines": GUIDELINES,
    }

    if not sources:
        report.warn("RVW001", "No Swift sources found; nothing to review.")
        return report

    check_usage_descriptions(report, sources, plist)
    check_placeholder_content(report, sources)
    check_account_deletion(report, sources)
    check_external_payments(report, sources, stores_digital_goods="StoreKit" in joined)
    check_webview_only(report, sources)
    check_private_api(report, sources)
    check_review_notes(report, project, plist)
    check_metadata(report, metadata_path)
    return report


def main(argv=None) -> int:
    parser = build_parser(
        "app-store-review",
        "Find App Store Review risks in the project, each tied to a guideline section.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--metadata", help="Optional listing metadata JSON for 2.3.1 checks")
    args = parser.parse_args(argv)

    guard = guard_directory("app-store-review", args.path)
    if guard is not None:
        return emit(guard, args)

    root = Path(args.path).expanduser().resolve()
    metadata = Path(args.metadata).expanduser() if args.metadata else None
    return emit(review(root, metadata), args, title="Apple Native Engineer — App Store Review Risk")


if __name__ == "__main__":
    raise SystemExit(main())
