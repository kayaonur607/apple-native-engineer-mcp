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

import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.imaging import (
    UnsupportedImage,
    closest_screenshot_slots,
    image_info,
    match_screenshot_spec,
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


def audit_image(path: Path, report: Report) -> None:
    try:
        info = image_info(path)
    except (UnsupportedImage, OSError) as exc:
        report.error("SHOT010", f"Unreadable screenshot: {exc}", file=path.name)
        return

    match = match_screenshot_spec(info.width, info.height)
    if match is None:
        hints = closest_screenshot_slots(info.width, info.height, 1)
        suggestion = ""
        if hints:
            _, device, orientation, size = hints[0]
            suggestion = f" Closest App Store slot: {device} {orientation} {size[0]}x{size[1]}."
        report.warn(
            "SHOT011",
            f"{path.name} is {info.width}x{info.height}, which is not an App Store screenshot slot.",
            file=path.name,
            hint="App Store Connect rejects unsupported dimensions." + suggestion,
        )
    else:
        device_slot, orientation = match
        report.info("SHOT012", f"{path.name} matches {device_slot} ({orientation}).", file=path.name)
        report.data["slot"] = f"{device_slot} {orientation}"


def audit_directory(directory: Path, report: Report) -> None:
    images = list(iter_files(directory, (".png", ".jpg", ".jpeg")))
    report.data["screenshot_count"] = len(images)
    if not images:
        report.warn("SHOT020", "No screenshots found in directory.", file=str(directory))
        return
    for image in images:
        audit_image(image, report)


def main(argv=None) -> int:
    parser = build_parser(
        "screenshot-studio",
        "Capture simulator screenshots and validate them against App Store slots.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--out", help="Capture a screenshot to this path (requires a booted simulator)")
    parser.add_argument("--device", help="Simulator UDID to capture from (default: first booted)")
    parser.add_argument("--screenshots", help="Audit an existing screenshots directory")
    args = parser.parse_args(argv)

    if args.out:
        report = capture(Path(args.out).expanduser().resolve(), device=args.device)
        return emit(report, args, title="Apple Native Engineer — Screenshot Capture")

    if args.screenshots:
        target = Path(args.screenshots).expanduser().resolve()
        report = Report(tool="screenshot-studio", target=str(target), version=__version__)
        if not target.is_dir():
            report.error("SHOT000", f"Directory not found: {target}")
        else:
            audit_directory(target, report)
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
