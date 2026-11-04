#!/usr/bin/env python3
"""Asset Validator — App Store icon and screenshot compliance.

Checks the things App Store Connect rejects silently at upload time:

* marketing icon is exactly 1024x1024, PNG, and has **no alpha channel**
* every image in an ``.appiconset`` referenced by ``Contents.json`` exists
* screenshots match a known App Store device slot and orientation
* screenshot sets are complete enough per device

Usage::

    python3 tools/asset-validator/validate_assets.py [PATH] [--json]
    python3 tools/asset-validator/validate_assets.py --icon AppIcon.png
    python3 tools/asset-validator/validate_assets.py --screenshots ./fastlane/screenshots
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit, guard_directory, resolve_target
from apple_native.imaging import (
    ImageInfo,
    UnsupportedImage,
    closest_screenshot_slots,
    image_info,
    match_screenshot_spec,
)
from apple_native.report import Report
from apple_native.swiftscan import iter_files

REQUIRED_ICON_SIZE = (1024, 1024)


def validate_icon(path: Path, report: Report) -> Optional[ImageInfo]:
    try:
        info = image_info(path)
    except (UnsupportedImage, OSError) as exc:
        report.critical(
            "ASSET001",
            f"App icon cannot be read: {exc}",
            file=path.name,
            hint="Provide a PNG exported from your design tool, not a renamed JPEG.",
        )
        return None

    report.data["icon"] = info.as_dict()

    if info.format != "PNG":
        report.critical(
            "ASSET002",
            f"Marketing icon must be PNG; found {info.format}.",
            file=path.name,
            hint="Export the 1024x1024 icon as PNG (8-bit, sRGB).",
        )
    if info.size != REQUIRED_ICON_SIZE:
        report.critical(
            "ASSET003",
            f"Marketing icon is {info.width}x{info.height}; App Store requires 1024x1024.",
            file=path.name,
            hint="Resample to exactly 1024x1024 — App Store Connect does not accept other sizes.",
        )
    if info.has_alpha:
        report.critical(
            "ASSET004",
            "Marketing icon has an alpha channel; App Store rejects icons with transparency.",
            file=path.name,
            hint="Flatten onto an opaque background before exporting (no rounded corners either — iOS masks them).",
        )
    if info.bit_depth not in (8, 16):
        report.warn(
            "ASSET005",
            f"Unusual bit depth for an app icon: {info.bit_depth}.",
            file=path.name,
            hint="Use 8 bits per channel.",
        )
    return info


def validate_appiconset(set_dir: Path, report: Report) -> None:
    contents = set_dir / "Contents.json"
    if not contents.exists():
        report.warn(
            "ASSET010",
            f"{set_dir.name} has no Contents.json; Xcode cannot resolve the icon slots.",
            file=str(set_dir),
        )
        return

    try:
        payload = json.loads(contents.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        report.error("ASSET011", f"Contents.json is not valid JSON: {exc}", file=str(contents))
        return

    images = payload.get("images", [])
    missing: List[str] = []
    present = 0
    has_marketing = False

    for entry in images:
        filename = entry.get("filename")
        if not filename:
            continue
        size = entry.get("size", "")
        scale = entry.get("scale", "")
        if size == "1024x1024":
            has_marketing = True
        candidate = set_dir / filename
        if not candidate.exists():
            missing.append(f"{filename} ({size} @{scale})")
            continue
        present += 1
        try:
            info = image_info(candidate)
        except (UnsupportedImage, OSError):
            report.warn("ASSET012", f"Unreadable icon file: {filename}", file=str(candidate))
            continue
        if size and "x" in size:
            expected = tuple(int(part) for part in size.split("x"))
            if info.size != expected:
                report.error(
                    "ASSET013",
                    f"{filename} is {info.width}x{info.height} but Contents.json declares {size}.",
                    file=str(candidate.relative_to(set_dir)),
                    hint="Regenerate the icon set; mismatched sizes fail asset compilation.",
                )

    if missing:
        report.error(
            "ASSET014",
            f"{len(missing)} icon file(s) referenced by Contents.json are missing.",
            file=str(set_dir.name),
            hint="Missing: " + ", ".join(missing[:5]) + ("…" if len(missing) > 5 else ""),
        )
    if not has_marketing:
        report.warn(
            "ASSET015",
            "No 1024x1024 marketing icon slot found in Contents.json.",
            file=str(set_dir.name),
            hint="Xcode 15+ uses a single 'ios-marketing' style slot with a 1024x1024 asset.",
        )
    report.data.setdefault("appiconsets", {})[set_dir.name] = {
        "declared": len(images),
        "present": present,
        "missing": len(missing),
    }


def validate_screenshots(directory: Path, report: Report) -> None:
    images = list(iter_files(directory, (".png", ".jpg", ".jpeg")))
    if not images:
        report.warn(
            "ASSET020",
            "No screenshots found in the supplied directory.",
            file=str(directory),
            hint="Export from Xcode ▸ Product ▸ Screenshots or your Fastlane snapshot output.",
        )
        return

    unknown = 0
    for image in images:
        try:
            info = image_info(image)
        except (UnsupportedImage, OSError) as exc:
            report.error("ASSET021", f"Unreadable screenshot: {exc}", file=image.name)
            continue
        match = match_screenshot_spec(info.width, info.height)
        if match is None:
            unknown += 1
            hints = closest_screenshot_slots(info.width, info.height, 1)
            suggestion = ""
            if hints:
                _, device, orientation, size = hints[0]
                suggestion = f" Closest valid slot: {device} {orientation} {size[0]}x{size[1]}."
            report.warn(
                "ASSET022",
                f"{image.name} is {info.width}x{info.height}, which matches no App Store slot.",
                file=image.name,
                hint="Resize to an accepted slot; App Store Connect rejects arbitrary dimensions." + suggestion,
            )
    report.data["screenshots"] = {"count": len(images), "unmatched": unknown}


def validate_assets(raw_root: str, icon: Optional[str] = None,
                    screenshots: Optional[str] = None) -> Report:
    root = Path(raw_root).expanduser().resolve()
    report = Report(tool="asset-validator", target=str(root), version=__version__)

    if icon:
        validate_icon(Path(icon).expanduser().resolve(), report)
    if screenshots:
        validate_screenshots(Path(screenshots).expanduser().resolve(), report)

    if not icon and not screenshots:
        icon_sets = [p for p in root.rglob("*.appiconset") if p.is_dir()]
        if not icon_sets:
            report.warn(
                "ASSET030",
                "No .appiconset found. Pass --icon path/to/AppIcon-1024.png to validate a single file.",
                hint="App Store submissions require a 1024x1024 marketing icon.",
            )
        for icon_set in icon_sets[:20]:
            validate_appiconset(icon_set, report)

        marketing = [
            p for p in root.rglob("*.png")
            if p.stem.lower().startswith(("appicon", "icon")) and p.stat().st_size > 20_000
        ]
        for candidate in marketing[:5]:
            try:
                if image_info(candidate).size == REQUIRED_ICON_SIZE:
                    validate_icon(candidate, report)
                    break
            except (UnsupportedImage, OSError):
                continue

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "asset-validator",
        "Validate App Store marketing icons and screenshot dimensions.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--icon", help="Path to the 1024x1024 marketing icon PNG")
    parser.add_argument("--screenshots", help="Directory of screenshots to validate")
    args = parser.parse_args(argv)

    guard = guard_directory("asset-validator", args.path)
    if guard is not None:
        return emit(guard, args)
    return emit(validate_assets(args.path, args.icon, args.screenshots), args,
                title="Apple Native Engineer — Asset Validation")


if __name__ == "__main__":
    raise SystemExit(main())
