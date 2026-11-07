#!/usr/bin/env python3
"""Screenshot Studio — capture and audit App Store screenshots.

Two modes:

``capture``  grabs a screenshot from the booted simulator via ``xcrun simctl``
             (macOS + Xcode only) and immediately validates the resulting pixel
             size against the App Store slots.
``audit``    validates an existing directory of screenshots.

Usage::

    python3 tools/screenshot-studio/screenshot_studio.py --out shot.png
    python3 tools/screenshot-studio/screenshot_studio.py --screenshots ./shots
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.imaging import (
    UnsupportedImage,
    closest_screenshot_slots,
    image_info,
    load_app_store_specs,
    screenshot_slots,
)
from apple_native.report import Report
from apple_native.swiftscan import iter_files


def list_booted_simulators() -> List[Dict[str, str]]:
    if shutil.which("xcrun") is None:
        return []
    try:
        proc = subprocess.run(
            ["xcrun", "simctl", "list", "devices", "booted", "--json"],
            capture_output=True, text=True, timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if proc.returncode != 0:
        return []
    import json
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return []
    devices: List[Dict[str, str]] = []
    for runtime, entries in payload.get("devices", {}).items():
        for entry in entries:
            if entry.get("state") == "Booted":
                devices.append({"name": entry.get("name", "?"), "udid": entry.get("udid", "?"), "runtime": runtime})
    return devices


def capture(output: Path, device: Optional[str] = None, report: Optional[Report] = None) -> Report:
    report = report or Report(tool="screenshot-studio", target=str(output), version=__version__)

    if shutil.which("xcrun") is None:
        report.error(
            "SHOT001",
            "xcrun is not available; simulator capture requires macOS with Xcode installed.",
            hint="Run this on a Mac with Xcode, or use --screenshots to audit existing files.",
        )
        return report

    devices = list_booted_simulators()
    report.data["booted_simulators"] = devices
    if not devices:
        report.error(
            "SHOT002",
            "No booted simulator found.",
            hint="Boot one with: xcrun simctl boot 'iPhone 17 Pro' (then re-run).",
        )
        return report

    target = device or devices[0]["udid"]
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        proc = subprocess.run(
            ["xcrun", "simctl", "io", target, "screenshot", str(output)],
            capture_output=True, text=True, timeout=120,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        report.error("SHOT003", f"Simulator capture failed: {exc}")
        return report

    if proc.returncode != 0:
        report.error(
            "SHOT004",
            f"simctl screenshot failed: {proc.stderr.strip() or 'unknown error'}",
            hint="Check the device is booted and not showing a permission dialog.",
        )
        return report

    report.data["captured"] = str(output)
    audit_image(output, report)
    return report


PLATFORMS = ("iOS", "iPadOS", "macOS", "tvOS", "visionOS", "watchOS")
LOCALE_PATTERN = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z]{2,4})?(?:[-_][A-Z]{2})?$")


def audit_image(path: Path, report: Report, label: Optional[str] = None) -> Optional[Dict[str, object]]:
    """Validate one capture. Returns its slot record, or None when it is unusable."""

    name = label or path.name
    try:
        info = image_info(path)
    except (UnsupportedImage, OSError) as exc:
        report.error("SHOT010", f"Unreadable screenshot: {exc}", file=name)
        return None

    if info.has_alpha:
        report.error(
            "SHOT013",
            f"{name} has an alpha channel or transparency.",
            file=name,
            hint="App Store Connect rejects screenshots with alpha. Flatten to RGB, e.g. "
                 "sips -s format jpeg in.png --out out.jpg, or re-render with compose_marketing_screenshots.",
        )

    matches = matching_slots(info.width, info.height)
    if not matches:
        hints = closest_screenshot_slots(info.width, info.height, 1)
        suggestion = ""
        if hints:
            _, device, orientation, size = hints[0]
            suggestion = f" Closest App Store slot: {device} {orientation} {size[0]}x{size[1]}."
        report.warn(
            "SHOT011",
            f"{name} is {info.width}x{info.height}, which is not an App Store screenshot slot.",
            file=name,
            hint="App Store Connect rejects unsupported dimensions." + suggestion,
        )
        return None

    slot, orientation = matches[0]
    report.info("SHOT012", f"{name} matches {slot['label']} ({orientation}).", file=name)
    if len(matches) > 1:
        others = ", ".join(sorted({other['label'] for other, _ in matches[1:]}))
        report.info("SHOT014", f"{name}: {info.width}x{info.height} is also accepted for {others}.", file=name,
                    hint="Upload it to the set that matches the device you captured.")
    report.data["slot"] = f"{slot['label']} {orientation}"
    return {"slot": slot, "orientation": orientation, "size": f"{info.width}x{info.height}", "file": name}


def matching_slots(width: int, height: int) -> List[Tuple[Dict[str, object], str]]:
    found = []
    for slot in screenshot_slots():
        for orientation in ("portrait", "landscape"):
            if [width, height] in slot[orientation]:
                found.append((slot, orientation))
    return found


def collect_sets(directory: Path) -> Dict[str, List[Path]]:
    """Group images by locale. A first-level folder named like a locale is a locale."""

    groups: Dict[str, List[Path]] = {}
    for image in iter_files(directory, (".png", ".jpg", ".jpeg")):
        relative = image.relative_to(directory)
        first = relative.parts[0] if len(relative.parts) > 1 else ""
        locale = first if LOCALE_PATTERN.match(first) else "default"
        groups.setdefault(locale, []).append(image)
    return groups


def required_coverage(platforms: List[str], present: set, report: Report, locale: str) -> List[str]:
    """Check Apple's required sets for each declared platform; returns missing slot ids."""

    missing: List[str] = []
    slots = screenshot_slots()
    by_id = {slot["id"]: slot for slot in slots}
    for platform in platforms:
        candidates = [slot for slot in slots if slot["platform"] == platform]
        required = [slot for slot in candidates if slot["requirement"] == "required"]
        for slot in required:
            if slot["id"] not in present:
                missing.append(slot["id"])
                report.warn("SHOT022", f"[{locale}] {platform}: no {slot['label']} screenshots "
                            f"({slot['display_class']}). Apple: {slot['required']}.",
                            hint=f"Capture on {slot['simulator'] or slot['devices'][0]} at "
                                 f"{slot['portrait'][0][0] if slot['portrait'] else slot['landscape'][0][0]}x"
                                 f"{slot['portrait'][0][1] if slot['portrait'] else slot['landscape'][0][1]}. "
                                 "If the UI is identical across sizes, App Store Connect can scale the highest "
                                 "required resolution down; confirm which sets it marks as required.",
                            docs=load_app_store_specs()["sources"]["screenshots"])
        alternatives = [slot for slot in candidates if slot["requirement"] == "alternative"]
        if alternatives and not any(slot["id"] in present for slot in alternatives):
            labels = " or ".join(slot["label"] for slot in alternatives)
            missing.append("|".join(slot["id"] for slot in alternatives))
            report.warn("SHOT022", f"[{locale}] {platform}: provide {labels} screenshots. "
                        f"Apple: {alternatives[-1]['required']}.",
                        hint=f"Capture on {by_id[alternatives[0]['id']]['simulator']}.",
                        docs=load_app_store_specs()["sources"]["screenshots"])
        if platform == "watchOS" and not any(slot["platform"] == "watchOS" and slot["id"] in present for slot in slots):
            missing.append("watch")
            report.warn("SHOT022", f"[{locale}] watchOS: no Apple Watch screenshots.",
                        hint="Use one watch size consistently across every localization.")
        future = [slot for slot in candidates if slot["requirement"] == "future" and slot["id"] not in present]
        for slot in future:
            report.info("SHOT024", f"[{locale}] {slot['label']}: {slot['required']}.",
                        hint=f"Plan captures on the {slot['simulator']} simulator.")
    return missing


def audit_directory(directory: Path, report: Report, platforms: Optional[List[str]] = None) -> None:
    groups = collect_sets(directory)
    total = sum(len(images) for images in groups.values())
    report.data["screenshot_count"] = total
    if not total:
        report.warn("SHOT020", "No screenshots found in directory.", file=str(directory))
        return

    summary: Dict[str, Dict[str, object]] = {}
    watch_sizes: Dict[str, set] = {}
    for locale, images in sorted(groups.items()):
        sets: Dict[str, Dict[str, object]] = {}
        for image in sorted(images):
            record = audit_image(image, report, label=str(image.relative_to(directory)))
            if record is None:
                continue
            slot = record["slot"]
            entry = sets.setdefault(slot["id"], {"label": slot["label"], "platform": slot["platform"],
                                                 "count": 0, "orientations": set(), "sizes": set()})
            entry["count"] += 1
            entry["orientations"].add(record["orientation"])
            entry["sizes"].add(record["size"])
            if slot["platform"] == "watchOS":
                watch_sizes.setdefault(locale, set()).add(record["size"])

        for slot_id, entry in sets.items():
            if entry["count"] > 10:
                report.error("SHOT021", f"[{locale}] {entry['label']}: {entry['count']} screenshots; "
                             "App Store Connect accepts at most 10 per device size.",
                             hint="Keep the ten that tell the story best; order matters, the first three are seen most.")
            if len(entry["orientations"]) > 1:
                report.warn("SHOT025", f"[{locale}] {entry['label']}: mixes portrait and landscape.",
                            hint="Use one orientation per set so the product page reads consistently.")
        if platforms:
            required_coverage(platforms, set(sets), report, locale)
        summary[locale] = {slot_id: {"label": entry["label"], "platform": entry["platform"], "count": entry["count"],
                                     "orientations": sorted(entry["orientations"]), "sizes": sorted(entry["sizes"])}
                           for slot_id, entry in sets.items()}

    distinct_watch = {size for sizes in watch_sizes.values() for size in sizes}
    if len(distinct_watch) > 1:
        report.warn("SHOT023", f"Apple Watch screenshots use {len(distinct_watch)} sizes: {', '.join(sorted(distinct_watch))}.",
                    hint="Apple requires the same watch size across all localizations.")

    report.data["locales"] = sorted(groups)
    report.data["sets"] = summary
    report.data["platforms_checked"] = platforms or []
    report.data["specs_retrieved"] = load_app_store_specs()["retrieved"]
    report.data["specs_source"] = load_app_store_specs()["sources"]["screenshots"]
    report.data.pop("slot", None)


def main(argv=None) -> int:
    parser = build_parser(
        "screenshot-studio",
        "Capture simulator screenshots and validate them against App Store slots.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--out", help="Capture a screenshot to this path (requires a booted simulator)")
    parser.add_argument("--device", help="Simulator UDID to capture from (default: first booted)")
    parser.add_argument("--screenshots", help="Audit an existing screenshots directory (locale subfolders allowed)")
    parser.add_argument("--specs", action="store_true",
                        help="Print Apple's screenshot, preview and icon specifications (filter with --platforms)")
    parser.add_argument("--platforms", help="Comma-separated platforms to check required sets for: "
                        + ", ".join(PLATFORMS))
    args = parser.parse_args(argv)

    if args.specs:
        report = Report(tool="screenshot-studio", target="app-store-specs", version=__version__)
        specs = load_app_store_specs()
        wanted = {name.strip().lower() for name in (args.platforms or "").split(",") if name.strip()}
        slots = [slot for slot in specs["screenshots"]["slots"]
                 if not wanted or slot["platform"].lower() in wanted]
        report.data = {
            "retrieved": specs["retrieved"],
            "sources": specs["sources"],
            "note": specs["note"],
            "screenshots": {**{k: v for k, v in specs["screenshots"].items() if k != "slots"}, "slots": slots},
            "previews": specs["previews"],
            "icons": specs["icons"],
        }
        report.info("SHOT040", f"{len(slots)} screenshot slot(s) from Apple's specification retrieved {specs['retrieved']}.",
                    hint="Re-check the source URLs before submission; Apple updates these pages.")
        return emit(report, args, title="Apple Native Engineer — App Store specifications")

    if args.out:
        report = capture(Path(args.out).expanduser().resolve(), device=args.device)
        return emit(report, args, title="Apple Native Engineer — Screenshot Capture")

    if args.screenshots:
        target = Path(args.screenshots).expanduser().resolve()
        report = Report(tool="screenshot-studio", target=str(target), version=__version__)
        if not target.is_dir():
            report.error("SHOT000", f"Directory not found: {target}")
        else:
            platforms = None
            if args.platforms:
                lookup = {name.lower(): name for name in PLATFORMS}
                platforms = []
                for raw in args.platforms.split(","):
                    key = raw.strip().lower()
                    if key not in lookup:
                        report.error("SHOT031", f"Unknown platform {raw.strip()!r}.", hint="Use: " + ", ".join(PLATFORMS))
                        return emit(report, args, title="Apple Native Engineer — Screenshot Audit")
                    platforms.append(lookup[key])
            audit_directory(target, report, platforms)
        return emit(report, args, title="Apple Native Engineer — Screenshot Audit")

    report = Report(tool="screenshot-studio", target=".", version=__version__)
    report.info(
        "SHOT030",
        "Nothing to do: pass --out <file> to capture or --screenshots <dir> to audit.",
        hint="Example: --out ./shots/home.png --device <UDID>",
    )
    return emit(report, args, title="Apple Native Engineer — Screenshot Studio")


if __name__ == "__main__":
    raise SystemExit(main())
