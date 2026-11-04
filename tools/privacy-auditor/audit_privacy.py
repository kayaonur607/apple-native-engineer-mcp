#!/usr/bin/env python3
"""Privacy Manifest Auditor — Required-Reason API and PrivacyInfo.xcprivacy audit.

Apple blocks submissions when an app uses a Required-Reason API without declaring
it in a privacy manifest, or declares a reason code that does not exist. This
tool maps every detected API usage to the exact reason codes Apple accepts,
flags undeclared and invalid declarations, and reports tracking domains.

Usage::

    python3 tools/privacy-auditor/audit_privacy.py [PATH] [--json] [--strict]
"""

from __future__ import annotations

import plistlib
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Set

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory
from apple_native.report import Report
from apple_native.swiftscan import load_swift_files
from apple_native.xcode import discover

#: Required-Reason API categories and the reason codes Apple documents for each.
#: Source: developer.apple.com/documentation/bundleresources/privacy_manifest_files
REQUIRED_REASON_APIS: Dict[str, Dict[str, object]] = {
    "NSPrivacyAccessedAPICategoryFileTimestamp": {
        "detect": [
            r"\bFileManager\b[^;\n]*\.(?:attributesOfItem|creationDate|contentModificationDate)",
            r"\b(?:creationDate|contentModificationDate|fileModificationDate)\b",
            r"\.attributesOfItem\s*\(\s*atPath",
            r"\bstat\s*\(",
        ],
        "reasons": {
            "C617.1": "Access file timestamps inside the app container, app group or app's CloudKit container.",
            "3B52.1": "Access file timestamps for files the user explicitly granted access to.",
            "0A2A.1": "Access file timestamps for files outside the container (third-party SDK).",
        },
    },
    "NSPrivacyAccessedAPICategoryUserDefaults": {
        "detect": [r"\bUserDefaults\b", r"\b@AppStorage\b", r"\bNSUbiquitousKeyValueStore\b"],
        "reasons": {
            "CA92.1": "Access user defaults written and read only by the app itself.",
            "1C8F.1": "Access user defaults shared with app extensions in the same app group.",
            "AC6B.1": "Access user defaults for a managed configuration profile.",
            "C56D.1": "Access user defaults to read information provided by a third-party SDK.",
        },
    },
    "NSPrivacyAccessedAPICategorySystemBootTime": {
        "detect": [
            r"\bsystemUptime\b",
            r"\bProcessInfo\b[^;\n]*systemUptime",
            r"\bmach_absolute_time\b",
            r"\bclock_gettime\b",
        ],
        "reasons": {
            "35F9.1": "Measure elapsed time between events inside the app.",
            "8FFB.1": "Calculate absolute timestamps for events that occurred during the same boot.",
            "3D61.1": "Display the device's boot time to the user (diagnostics).",
        },
    },
    "NSPrivacyAccessedAPICategoryDiskSpace": {
        "detect": [
            r"\bvolumeAvailableCapacityKey\b",
            r"\bvolumeTotalCapacityKey\b",
            r"\battributesOfFileSystem\b",
            r"\bNSFileSystemFreeSize\b",
        ],
        "reasons": {
            "E174.1": "Check free disk space before writing files the app manages.",
            "85F4.1": "Display disk space to the user (storage management UI).",
            "7D9E.1": "Write files the user explicitly asked the app to store.",
            "B728.1": "Assess disk space for a feature the user requested.",
        },
    },
    "NSPrivacyAccessedAPICategoryActiveKeyboards": {
        "detect": [r"\bactiveInputModes\b"],
        "reasons": {
            "3EC4.1": "Customise the app's UI for the currently active keyboard language.",
            "54BD.1": "Adapt custom text input for the active keyboard.",
        },
    },
}

TRACKING_SIGNATURES = [
    (r"\bATTrackingManager\b|\bAppTrackingTransparency\b", "App Tracking Transparency usage"),
    (r"\bAdSupport\b|\bASIdentifierManager\b", "IDFA / AdSupport usage"),
    (r"\bFirebaseAnalytics\b|\bGoogleAnalytics\b|\bAmplitude\b|\bMixpanel\b", "Third-party analytics SDK"),
    (r"\bFBSDK|\bFacebookCore\b", "Meta SDK"),
    (r"\badvertisingIdentifier\b", "advertisingIdentifier access"),
]

COLLECTED_DATA_SIGNATURES = [
    (r"\bCLLocationManager\b|\brequestWhenInUseAuthorization\b", "Precise location"),
    (r"\bPHPhotoLibrary\b|\bPHPickerViewController\b", "Photos"),
    (r"\bAVCaptureDevice\b|\bAVAudioRecorder\b", "Camera or microphone"),
    (r"\bCNContactStore\b", "Contacts"),
    (r"\bHKHealthStore\b", "Health data"),
    (r"\bEKEventStore\b", "Calendar"),
    (r"\bUMP\b|\bASIdentifierManager\b", "Advertising identifiers"),
]


def _load_manifest(path: Path) -> Optional[dict]:
    try:
        with path.open("rb") as handle:
            return plistlib.load(handle)
    except Exception:  # noqa: BLE001 - malformed manifest reported by caller
        return None


def _declared_reasons(manifest: dict) -> Dict[str, Set[str]]:
    declared: Dict[str, Set[str]] = {}
    for entry in manifest.get("NSPrivacyAccessedAPITypes", []) or []:
        category = entry.get("NSPrivacyAccessedAPIType")
        reasons = set(entry.get("NSPrivacyAccessedAPITypeReasons", []) or [])
        if category:
            declared[str(category)] = reasons
    return declared


def audit_privacy(raw_root: str) -> Report:
    root = Path(raw_root).expanduser().resolve()
    report = Report(tool="privacy-auditor", target=str(root), version=__version__)

    project = discover(root)
    manifest_path = project.privacy_manifests[0] if project.privacy_manifests else None
    manifest = _load_manifest(manifest_path) if manifest_path else None

    if manifest_path is None:
        report.error(
            "PRIV001",
            "No PrivacyInfo.xcprivacy found in the project.",
            hint="Add PrivacyInfo.xcprivacy to the app target; App Store Connect rejects uploads that "
                 "use Required-Reason APIs without one.",
            docs="https://developer.apple.com/documentation/bundleresources/privacy_manifest_files",
        )
    elif manifest is None:
        report.critical(
            "PRIV002",
            f"Privacy manifest could not be parsed: {manifest_path}",
            hint="Regenerate the manifest in Xcode (File ▸ New ▸ File ▸ Privacy Manifest).",
        )

    declared = _declared_reasons(manifest) if manifest else {}
    sources = load_swift_files(root)

    detected: Dict[str, List[str]] = {}
    for category, spec in REQUIRED_REASON_APIS.items():
        hits: List[str] = []
        for swift in sources:
            for pattern in spec["detect"]:  # type: ignore[index]
                for match in re.finditer(pattern, swift.clean):
                    location = f"{swift.relative}:{swift.line_of(match.start())}"
                    hits.append(location)
        if hits:
            detected[category] = sorted(set(hits))

    data: Dict[str, object] = {
        "manifest": str(manifest_path.relative_to(root)) if manifest_path else None,
        "scanned_swift_files": len(sources),
        "detected_categories": {k: len(v) for k, v in detected.items()},
        "declared_categories": sorted(declared.keys()),
        "tracking_domains": (manifest or {}).get("NSPrivacyTrackingDomains", []),
        "tracking_enabled": (manifest or {}).get("NSPrivacyTracking", False),
    }
    report.data = data

    for category, hits in detected.items():
        valid_reasons = REQUIRED_REASON_APIS[category]["reasons"]  # type: ignore[index]
        declared_reasons = declared.get(category)

        if declared_reasons is None:
            report.error(
                "PRIV010",
                f"{category} is used but not declared in the privacy manifest.",
                file=hits[0].split(":")[0],
                line=int(hits[0].rsplit(":", 1)[1]),
                hint=f"Declare one of: {', '.join(sorted(valid_reasons))} "
                     f"({len(hits)} usage site(s) detected).",
            )
            continue

        unknown = {r for r in declared_reasons if r not in valid_reasons}
        if unknown:
            report.error(
                "PRIV011",
                f"{category} declares invalid reason code(s): {', '.join(sorted(unknown))}.",
                hint=f"Valid codes are: {', '.join(sorted(valid_reasons))}.",
            )

        if not declared_reasons:
            report.warn(
                "PRIV012",
                f"{category} is declared with an empty reason list.",
                hint="App Store Connect requires at least one reason code per declared category.",
            )

    for category in declared:
        if category not in REQUIRED_REASON_APIS:
            report.warn(
                "PRIV013",
                f"Unknown Required-Reason API category in manifest: {category}",
                hint="Check the spelling against Apple's documented category identifiers.",
            )
        elif category not in detected:
            report.info(
                "PRIV014",
                f"{category} is declared but no usage was detected in Swift sources.",
                hint="Keep it only if a dependency needs it; unused declarations are harmless but noisy.",
            )

    joined = "\n".join(f.clean for f in sources)
    tracked = [label for pattern, label in TRACKING_SIGNATURES if re.search(pattern, joined)]
    if tracked:
        if not (manifest or {}).get("NSPrivacyTracking"):
            report.warn(
                "PRIV020",
                f"Tracking-adjacent APIs detected ({', '.join(tracked)}) but NSPrivacyTracking is false.",
                hint="If the SDK only performs first-party analytics, document that; otherwise declare tracking "
                     "and list NSPrivacyTrackingDomains.",
            )
        if not (manifest or {}).get("NSPrivacyTrackingDomains"):
            report.warn(
                "PRIV021",
                "NSPrivacyTrackingDomains is empty while tracking signals are present.",
                hint="List every domain the tracking SDK contacts, e.g. 'app-measurement.com'.",
            )

    collected = [label for pattern, label in COLLECTED_DATA_SIGNATURES if re.search(pattern, joined)]
    if collected:
        data["collected_data_signals"] = collected
        if not (manifest or {}).get("NSPrivacyCollectedDataTypes"):
            report.warn(
                "PRIV022",
                f"Data-collecting APIs detected ({', '.join(collected)}) but NSPrivacyCollectedDataTypes is empty.",
                hint="Declare each collected type plus whether it is linked to the user and used for tracking.",
            )

    if manifest is not None and not detected and not declared:
        report.info(
            "PRIV030",
            "Manifest present but neither Required-Reason usage nor declarations were found.",
            hint="Nothing to do if the app genuinely touches no Required-Reason APIs.",
        )

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "privacy-auditor",
        "Audit PrivacyInfo.xcprivacy against Required-Reason API usage in Swift sources.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    args = parser.parse_args(argv)
    guard = guard_directory("privacy-auditor", args.path)
    if guard is not None:
        return emit(guard, args)
    return emit(audit_privacy(args.path), args, title="Apple Native Engineer — Privacy & Manifest Audit")


if __name__ == "__main__":
    raise SystemExit(main())
