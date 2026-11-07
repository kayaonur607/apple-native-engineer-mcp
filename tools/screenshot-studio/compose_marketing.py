#!/usr/bin/env python3
"""Screenshot Studio — compose App Store marketing frames around real captures.

This tool never invents a screen. It takes screenshots you actually captured
(``capture_batch.py``, ``xcrun simctl io … screenshot``, Xcode, fastlane) and
lays each one into a marketing frame: background, headline, subheadline, an
optional device frame, and the capture itself.

Every frame is written twice:

* **SVG** — exact App Store pixel size, text as text, editable in any design
  tool. Its line wrapping is an estimate.
* **PNG** (``--render``) — drawn natively on macOS with CoreGraphics and the
  system San Francisco font (real kerning, optical sizes and line breaking for
  every script, right-to-left included), opaque RGB at the exact slot size, as
  App Store Connect requires. ``rsvg-convert`` is the fallback elsewhere.

Localized copy comes from a captions file. Top-level keys are locales (``*`` is
the fallback), each mapping a screenshot name (or name prefix, ``*`` fallback)
to its copy::

    {
      "en-US": {"01-today": {"headline": "Plan your day in a minute",
                             "subhead": "Focus on what matters"}},
      "tr-TR": {"01-today": {"headline": "Gününü bir dakikada planla"}},
      "*":     {"*": {"headline": "Made for focus"}}
    }

A screenshots folder whose first-level directories are locales
(``en-US/iphone-18-pro-max/01-today.png``, as ``capture_batch.py`` writes it)
is mirrored into ``--out``.

Usage::

    python3 tools/screenshot-studio/compose_marketing.py --screenshots shots --out marketing \\
        --captions captions.json --frame device --render
"""

from __future__ import annotations

import argparse
import base64
import html
import json
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__, native
from apple_native.cli import emit
from apple_native.imaging import UnsupportedImage, image_info, screenshot_slots
from apple_native.report import Report
from apple_native.swiftscan import iter_files

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {"from": "#0A0C11", "to": "#151A24", "headline": "#FFFFFF", "subhead": "#9AA6BA",
             "accent": "#0A84FF", "bezel": "#1C1C1E", "rim": "#3A3A3C"},
    "light": {"from": "#F7F8FA", "to": "#E8ECF2", "headline": "#0B0D12", "subhead": "#5B6472",
              "accent": "#0A84FF", "bezel": "#1C1C1E", "rim": "#48484A"},
    "warm": {"from": "#151013", "to": "#241A1E", "headline": "#FFF6EF", "subhead": "#C9B8AE",
             "accent": "#FF9F0A", "bezel": "#1C1C1E", "rim": "#4A3F3A"},
    "blue": {"from": "#0B1E3F", "to": "#0A3A7A", "headline": "#FFFFFF", "subhead": "#B8CCEB",
             "accent": "#64D2FF", "bezel": "#101418", "rim": "#3A4656"},
    "graphite": {"from": "#2C2C2E", "to": "#1C1C1E", "headline": "#F5F5F7", "subhead": "#AEAEB2",
                 "accent": "#BF5AF2", "bezel": "#0E0E10", "rim": "#48484A"},
}
LAYOUTS = ("caption-top", "caption-bottom")
FRAMES = ("auto", "device", "none")
RENDERERS = ("auto", "native", "rsvg")
RTL_LANGUAGES = {"ar", "he", "fa", "ur", "yi", "ps", "dv"}
LOCALE = re.compile(r"^[a-z]{2,3}(?:[-_][A-Za-z]{2,4})?(?:[-_][A-Z]{2})?$")
DEFAULT_CANVAS = (1320, 2868)  # iPhone 6.9" portrait
SYSTEM_FONT = "-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif"


# --------------------------------------------------------------------------- #
# Slots and copy
# --------------------------------------------------------------------------- #


def slot_for(size: Tuple[int, int]) -> Optional[Dict[str, object]]:
    for slot in screenshot_slots():
        if list(size) in slot["portrait"] or list(size) in slot["landscape"]:
            return slot
    return None


def canvas_for(screenshot: Tuple[int, int], override: Optional[Tuple[int, int]]) -> Tuple[int, int]:
    if override:
        return override
    return screenshot if slot_for(screenshot) else DEFAULT_CANVAS


def locale_of(relative: Path) -> Optional[str]:
    first = relative.parts[0] if len(relative.parts) > 1 else ""
    return first if LOCALE.match(first) else None


def is_rtl(locale: Optional[str]) -> bool:
    return bool(locale) and re.split(r"[-_]", locale)[0].lower() in RTL_LANGUAGES


def caption_for(captions: Dict[str, Dict[str, Dict[str, str]]], locale: Optional[str],
                stem: str) -> Tuple[Optional[Dict[str, str]], Optional[str]]:
    """Return (copy, locale key used). Exact locale, then language, then ``*``."""

    keys = []
    if locale:
        keys += [locale, re.split(r"[-_]", locale)[0]]
    keys.append("*")
    for key in keys:
        table = captions.get(key)
        if not isinstance(table, dict):
            continue
        for name, copy in sorted(table.items(), key=lambda item: -len(item[0])):
            if name != "*" and (stem == name or stem.startswith(name + "-") or stem.startswith(name + "_")):
                return copy, key
        if "*" in table:
            return table["*"], key
    return None, None


# --------------------------------------------------------------------------- #
# Layout model — shared by the SVG writer and the native renderer
# --------------------------------------------------------------------------- #


def build_layout(shot_size: Tuple[int, int], canvas: Tuple[int, int], headline: str, subhead: str,
                 theme_name: str, layout: str, frame: str, rtl: bool, align: str) -> Dict[str, object]:
    theme = THEMES[theme_name]
    width, height = canvas
    portrait = height > width
    slot = slot_for(shot_size)
    platform = slot["platform"] if slot else "iOS"
    if frame == "auto":
        frame = "device" if portrait and platform in ("iOS", "iPadOS") else "none"

    margin = int(width * (0.08 if portrait else 0.05))
    # Size type from the shorter dimension's budget so iPad (3:4) frames keep the
    # same proportion of copy to device as iPhone (≈1:2.17) frames.
    headline_size = int(min(width * (0.074 if portrait else 0.042), height * (0.034 if portrait else 0.075)))
    subhead_size = int(min(width * (0.036 if portrait else 0.022), height * (0.0166 if portrait else 0.039)))
    headline_box = int(headline_size * 1.2 * 2.6)
    subhead_box = int(subhead_size * 1.3 * 2.2) if subhead else 0
    gap = int(width * 0.03)
    text_height = headline_box + (gap // 2 + subhead_box if subhead else 0)

    if layout == "caption-top":
        text_top = margin
        area_top = text_top + text_height + gap * 2
        area_bottom = height - int(margin * 0.7)
    else:
        area_top = int(margin * 0.7)
        area_bottom = height - margin - text_height - gap * 2
        text_top = area_bottom + gap * 2
    area_height = area_bottom - area_top
    area_width = width - 2 * int(margin * (0.7 if portrait else 1))

    shot_w, shot_h = shot_size
    ratio = shot_h / shot_w
    elements: Dict[str, object] = {}
    if frame == "device":
        phone = platform == "iOS"
        bezel_ratio = 0.034 if phone else 0.028
        # Solve the device width that fits the area: screen + bezel on both sides.
        device_width = min(area_width, int(area_height / (ratio * (1 - 2 * bezel_ratio) + 2 * bezel_ratio)))
        bezel = int(device_width * bezel_ratio)
        screen_w = device_width - 2 * bezel
        screen_h = int(screen_w * ratio)
        device_height = screen_h + 2 * bezel
        x = (width - device_width) // 2
        y = area_top + (area_height - device_height) // 2 if layout == "caption-bottom" else area_top
        screen_radius = int(screen_w * (0.137 if phone else 0.034))
        elements["shadow"] = {"x": x, "y": y, "width": device_width, "height": device_height,
                              "radius": screen_radius + bezel, "blur": int(width * 0.05),
                              "offsetY": int(width * 0.025), "opacity": 0.38}
        elements["device"] = {"x": x, "y": y, "width": device_width, "height": device_height,
                              "radius": screen_radius + bezel, "color": theme["bezel"], "rim": theme["rim"],
                              "rimWidth": max(2, int(bezel * 0.18))}
        elements["image"] = {"x": x + bezel, "y": y + bezel, "width": screen_w, "height": screen_h,
                             "radius": screen_radius}
        if phone and slot and slot["display_class"].startswith("Dynamic Island"):
            island_w = int(screen_w * 0.29)
            island_h = int(screen_w * 0.084)
            elements["island"] = {"x": x + bezel + (screen_w - island_w) // 2,
                                  "y": y + bezel + int(screen_w * 0.026), "width": island_w, "height": island_h}
    else:
        image_w = min(area_width, int(area_height / ratio))
        image_h = min(area_height, int(image_w * ratio))
        x = (width - image_w) // 2
        y = area_top
        radius = int(width * (0.055 if portrait else 0.018))
        elements["shadow"] = {"x": x, "y": y, "width": image_w, "height": image_h, "radius": radius,
                              "blur": int(width * 0.04), "offsetY": int(width * 0.02), "opacity": 0.35}
        elements["image"] = {"x": x, "y": y, "width": image_w, "height": image_h, "radius": radius}

    text_x = margin
    text_width = width - 2 * margin
    headline_share = headline_box / max(text_height, 1)
    texts = [{"text": headline, "x": text_x, "y": text_top, "width": text_width, "height": headline_box,
              "size": headline_size, "minSize": int(headline_size * 0.62), "weight": "bold",
              "color": theme["headline"], "tracking": -1.2, "lineHeight": 1.0, "align": align, "rtl": rtl,
              "share": headline_share}]
    if subhead:
        texts.append({"text": subhead, "x": text_x, "y": text_top + headline_box + gap // 2, "width": text_width,
                      "height": subhead_box, "size": subhead_size, "minSize": int(subhead_size * 0.75),
                      "weight": "regular", "color": theme["subhead"], "tracking": 0, "lineHeight": 1.1,
                      "align": align, "rtl": rtl, "share": 1 - headline_share})
    # The native renderer measures real text and centres the stack in this block.
    text_block = {"x": text_x, "y": text_top, "width": text_width, "height": text_height,
                  "gap": int(subhead_size * 0.7)}

    return {
        "width": width, "height": height, "frame": frame, "layout": layout, "platform": platform,
        "background": {"from": theme["from"], "to": theme["to"]},
        "glow": {"color": theme["accent"], "opacity": 0.28, "x": 0.2, "y": 0.05, "radius": 0.8},
        "texts": texts, "textBlock": text_block, **elements,
    }


# --------------------------------------------------------------------------- #
# SVG writer
# --------------------------------------------------------------------------- #


def svg_text(spec: Dict[str, object]) -> str:
    size = int(spec["size"])
    per_line = max(8, int(int(spec["width"]) / (size * 0.52)))
    lines = textwrap.wrap(str(spec["text"]), width=per_line, break_long_words=False) or [""]
    max_lines = max(1, int(int(spec["height"]) / (size * 1.2)))
    lines = lines[:max_lines]
    align = spec["align"] if spec["align"] != "left" or not spec.get("rtl") else "right"
    anchor = {"center": "middle", "right": "end"}.get(str(align), "start")
    x = {"middle": int(spec["x"]) + int(spec["width"]) // 2, "end": int(spec["x"]) + int(spec["width"])}.get(anchor, int(spec["x"]))
    weight = {"bold": 700, "semibold": 600, "regular": 400}.get(str(spec["weight"]), 400)
    tspans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else int(size * 1.2)}">{html.escape(line)}</tspan>'
                     for i, line in enumerate(lines))
    direction = ' direction="rtl"' if spec.get("rtl") else ""
    tracking = round(float(spec.get("tracking", 0)) * size / 100, 2)
    return (f'<text x="{x}" y="{int(spec["y"]) + size}" font-family="{SYSTEM_FONT}" font-size="{size}" '
            f'font-weight="{weight}" letter-spacing="{tracking}" text-anchor="{anchor}"{direction} '
            f'fill="{spec["color"]}">{tspans}</text>')


def compose_svg(screenshot: Path, layout: Dict[str, object], embed: bool = True) -> str:
    width, height = layout["width"], layout["height"]
    image = layout["image"]
    href = (f"data:image/png;base64,{base64.b64encode(screenshot.read_bytes()).decode()}" if embed
            else screenshot.name)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "  <defs>",
        f'    <linearGradient id="bg" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">'
        f'<stop offset="0" stop-color="{layout["background"]["from"]}"/>'
        f'<stop offset="1" stop-color="{layout["background"]["to"]}"/></linearGradient>',
        f'    <radialGradient id="glow" cx="0.2" cy="0.05" r="0.8"><stop offset="0" stop-color="{layout["glow"]["color"]}" '
        f'stop-opacity="0.28"/><stop offset="1" stop-color="{layout["glow"]["color"]}" stop-opacity="0"/></radialGradient>',
        f'    <clipPath id="shotClip"><rect x="{image["x"]}" y="{image["y"]}" width="{image["width"]}" '
        f'height="{image["height"]}" rx="{image["radius"]}"/></clipPath>',
        f'    <filter id="shadow" x="-20%" y="-10%" width="140%" height="130%"><feDropShadow dx="0" '
        f'dy="{layout["shadow"]["offsetY"]}" stdDeviation="{int(layout["shadow"]["blur"]) // 2}" flood-color="#000000" '
        f'flood-opacity="{layout["shadow"]["opacity"]}"/></filter>',
        "  </defs>",
        f'  <rect width="{width}" height="{height}" fill="url(#bg)"/>',
        f'  <rect width="{width}" height="{height}" fill="url(#glow)"/>',
    ]
    parts += [f"  {svg_text(spec)}" for spec in layout["texts"]]
    shadow = layout["shadow"]
    parts.append(f'  <rect x="{shadow["x"]}" y="{shadow["y"]}" width="{shadow["width"]}" height="{shadow["height"]}" '
                 f'rx="{shadow["radius"]}" fill="#000000" filter="url(#shadow)"/>')
    device = layout.get("device")
    if device:
        rim = device["rimWidth"]
        parts.append(f'  <rect x="{device["x"]}" y="{device["y"]}" width="{device["width"]}" height="{device["height"]}" '
                     f'rx="{device["radius"]}" fill="{device["color"]}"/>')
        parts.append(f'  <rect x="{device["x"] + rim / 2}" y="{device["y"] + rim / 2}" width="{device["width"] - rim}" '
                     f'height="{device["height"] - rim}" rx="{device["radius"] - rim / 2}" fill="none" '
                     f'stroke="{device["rim"]}" stroke-width="{rim}"/>')
    parts.append(f'  <image xlink:href="{html.escape(href)}" href="{html.escape(href)}" x="{image["x"]}" '
                 f'y="{image["y"]}" width="{image["width"]}" height="{image["height"]}" '
                 f'preserveAspectRatio="xMidYMin slice" clip-path="url(#shotClip)"/>')
    island = layout.get("island")
    if island:
        parts.append(f'  <rect x="{island["x"]}" y="{island["y"]}" width="{island["width"]}" '
                     f'height="{island["height"]}" rx="{island["height"] // 2}" fill="#000000"/>')
    parts.append("</svg>\n")
    return "\n".join(parts)


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def choose_renderer(requested: str) -> Optional[str]:
    if requested in ("auto", "native") and native.native_helper() is not None:
        return "native"
    if requested in ("auto", "rsvg") and shutil.which("rsvg-convert"):
        return "rsvg"
    return None


def find_renderer() -> Optional[List[str]]:
    """Kept for compatibility: the name of the first available renderer."""

    choice = choose_renderer("auto")
    return [choice] if choice else None


def render_native(jobs: List[Tuple[Dict[str, object], Path, Path]]) -> Dict[str, object]:
    layouts = []
    for layout, shot, png in jobs:
        entry = dict(layout)
        entry["image"] = {**layout["image"], "path": str(shot)}
        entry["output"] = str(png)
        layouts.append(entry)
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as handle:
        json.dump(layouts, handle)
        manifest = handle.name
    try:
        return native.run_helper(["render", manifest])
    finally:
        Path(manifest).unlink(missing_ok=True)


def render_rsvg(svg: Path, png: Path, width: int, height: int) -> bool:
    subprocess.run(["rsvg-convert", "-b", "#000000", "-w", str(width), "-h", str(height), "-o", str(png), str(svg)],
                   check=False, capture_output=True)
    return png.exists()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="compose-marketing",
        description="Compose App Store marketing frames around real screenshots (SVG, plus native PNG with --render).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--screenshots", required=True, help="Directory of real screenshots (locale subfolders allowed)")
    parser.add_argument("--out", required=True, help="Directory to write compositions into")
    parser.add_argument("--headline", default="Made for iPhone", help="Headline when no caption matches")
    parser.add_argument("--subhead", default="", help="Supporting line when no caption matches")
    parser.add_argument("--captions", help="Localized captions JSON (see module docstring)")
    parser.add_argument("--theme", default="dark", choices=sorted(THEMES), help="Colour theme")
    parser.add_argument("--layout", default="caption-top", choices=LAYOUTS)
    parser.add_argument("--frame", default="auto", choices=FRAMES,
                        help="device: drawn bezel for iPhone/iPad portrait; none: rounded capture; auto (default)")
    parser.add_argument("--align", default="center", choices=("center", "left"))
    parser.add_argument("--canvas", help="WxH override, e.g. 1290x2796")
    parser.add_argument("--inset", type=float, default=0.08, help=argparse.SUPPRESS)
    parser.add_argument("--render", action="store_true", help="Also produce opaque PNGs (native on macOS)")
    parser.add_argument("--renderer", default="auto", choices=RENDERERS)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    args = parser.parse_args(argv)

    source = Path(args.screenshots).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    report = Report(tool="compose-marketing", target=str(source), version=__version__)
    title = "Apple Native Engineer — Marketing screenshots"

    if not source.is_dir():
        report.error("SHOT100", f"Screenshots directory not found: {source}")
        return emit(report, args)

    shots = sorted(path for path in iter_files(source, (".png", ".jpg", ".jpeg"))
                   if not str(path).startswith(str(out) + "/"))
    if not shots:
        report.error("SHOT101", "No screenshots found; capture real ones first.",
                     hint="capture_screenshots, or: xcrun simctl io booted screenshot shot.png")
        return emit(report, args)

    override = None
    if args.canvas:
        try:
            width, height = args.canvas.lower().split("x")
            override = (int(width), int(height))
        except ValueError:
            report.error("SHOT102", f"--canvas must look like 1320x2868, got {args.canvas!r}")
            return emit(report, args)

    captions: Dict[str, Dict[str, Dict[str, str]]] = {}
    if args.captions:
        try:
            captions = json.loads(Path(args.captions).expanduser().read_text(encoding="utf-8"))
            if not isinstance(captions, dict):
                raise ValueError("top level must be an object of locales")
        except (OSError, ValueError) as exc:
            report.error("SHOT104", f"Cannot read captions: {exc}")
            return emit(report, args)

    renderer = choose_renderer(args.renderer) if args.render else None
    out.mkdir(parents=True, exist_ok=True)
    written: List[Dict[str, object]] = []
    native_jobs: List[Tuple[Dict[str, object], Path, Path]] = []
    fallbacks = set()

    for shot in shots:
        relative = shot.relative_to(source)
        try:
            info = image_info(shot)
        except (UnsupportedImage, OSError) as exc:
            report.warn("SHOT103", f"Skipping unreadable screenshot {relative}: {exc}")
            continue
        slot = slot_for(info.size)
        if slot and slot["platform"] == "watchOS":
            report.info("SHOT114", f"{relative}: Apple Watch captures are uploaded as captured; not framed.",
                        hint="Upload watch screenshots at one size across all localizations.")
            continue

        locale = locale_of(relative)
        copy, used = caption_for(captions, locale, shot.stem) if captions else (None, None)
        if captions and locale and used not in (locale, re.split(r"[-_]", locale)[0]):
            fallbacks.add(f"{locale}:{shot.stem}")
        headline = (copy or {}).get("headline", args.headline)
        subhead = (copy or {}).get("subhead", args.subhead if not copy else "")

        canvas = canvas_for(info.size, override)
        layout = build_layout(info.size, canvas, headline, subhead, args.theme, args.layout, args.frame,
                              is_rtl(locale), args.align)
        target = out / relative.with_suffix(".svg")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(compose_svg(shot, layout), encoding="utf-8")
        entry: Dict[str, object] = {"screenshot": str(relative), "svg": str(target.relative_to(out)),
                                    "canvas": f"{canvas[0]}x{canvas[1]}", "locale": locale, "frame": layout["frame"],
                                    "headline": headline, "rtl": is_rtl(locale)}
        png = target.with_suffix(".png")
        if renderer == "native":
            native_jobs.append((layout, shot, png))
            entry["png"] = str(png.relative_to(out))
        elif renderer == "rsvg":
            entry["png"] = str(png.relative_to(out)) if render_rsvg(target, png, *canvas) else None
        elif args.render:
            entry["png"] = None
        written.append(entry)

    rendered = 0
    if native_jobs:
        try:
            result = render_native(native_jobs)
            for problem in result.get("errors", []):
                report.error("SHOT118", f"Native render failed: {problem}")
            for item in result.get("results", []):
                for text in item.get("texts", []):
                    if not text.get("fits"):
                        report.warn("SHOT119", f"{Path(item['output']).name}: copy does not fit at the minimum size: "
                                    f"{text['text']!r}", hint="Shorten the caption for this locale.")
        except (native.NativeError, OSError, subprocess.TimeoutExpired) as exc:
            report.error("SHOT118", f"Native render failed: {exc}")

    if args.render:
        if renderer == "rsvg":
            report.info("SHOT120", "Rendered with rsvg-convert; SVG text uses estimated wrapping. "
                        "On macOS the native renderer uses San Francisco and CoreText line breaking.")
        for entry in written:
            if not entry.get("png"):
                continue
            path = out / str(entry["png"])
            if not path.exists():
                entry["png"] = None
                continue
            png_info = image_info(path)
            rendered += 1
            if png_info.has_alpha:
                report.error("SHOT116", f"{entry['png']} has an alpha channel; App Store Connect rejects it.")
            if f"{png_info.width}x{png_info.height}" != entry["canvas"]:
                report.error("SHOT117", f"{entry['png']} is {png_info.width}x{png_info.height}, "
                             f"expected {entry['canvas']}.")
            elif not slot_for(png_info.size):
                report.warn("SHOT117", f"{entry['png']} is {entry['canvas']}, not an App Store slot.",
                            hint="Pass --canvas with a size from data/app-store-specs.json.")

    report.data = {
        "composed": len(written),
        "rendered": rendered,
        "output": str(out),
        "files": written,
        "renderer": renderer or "none",
        "locales": sorted({str(entry["locale"]) for entry in written if entry["locale"]}),
    }
    report.info("SHOT110", f"Composed {len(written)} marketing frame(s) as SVG.",
                hint="SVG is exact and editable; pass --render for App Store-ready PNGs.")
    if fallbacks:
        report.warn("SHOT115", f"{len(fallbacks)} frame(s) used fallback copy instead of their own locale: "
                    + ", ".join(sorted(fallbacks)[:8]),
                    hint="Add those locales to the captions file so every product page reads natively.")
    if args.render and rendered == 0 and written:
        report.warn("SHOT111", "No renderer available, so no PNG was produced.",
                    hint="Run on macOS with Xcode for native rendering, or install librsvg (brew install librsvg).")
    if args.render and rendered:
        report.info("SHOT112", f"Rendered {rendered} opaque PNG frame(s) with the {renderer} renderer.")
    per_set: Dict[str, int] = {}
    for entry in written:
        key = f"{entry['locale'] or 'default'}/{entry['canvas']}"
        per_set[key] = per_set.get(key, 0) + 1
    small = [key for key, count in per_set.items() if count < 3]
    if small:
        report.info("SHOT113", "App Store Connect accepts 1–10 screenshots per device size; most product pages use 3 or more.",
                    hint="Fewer than three in: " + ", ".join(sorted(small)[:6]))
    return emit(report, args, title=title)


if __name__ == "__main__":
    raise SystemExit(main())
