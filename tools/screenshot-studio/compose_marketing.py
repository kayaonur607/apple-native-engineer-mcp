#!/usr/bin/env python3
"""Screenshot Studio — compose App Store marketing frames around real captures.

This tool never invents a screen. It takes screenshots you actually captured
(`xcrun simctl io … screenshot`, fastlane snapshot, Xcode) and lays them into a
marketing frame: background, headline, subheadline, and the screenshot itself.

Output is **SVG**, deliberately:

* it is exact — App Store pixel dimensions, text as text, no resampling artefacts
* it is editable — a designer can open it in any tool and adjust copy
* it is honest — the file is a composition, not a claim that the app looks like
  something it does not

Rasterising to PNG is a separate, explicit step. On macOS the machine already has
a renderer (`qlmanage`, or `rsvg-convert` if installed); the tool tells you which
one it found and refuses to pretend a PNG exists when it does not.

Usage::

    python3 tools/screenshot-studio/compose_marketing.py \\
        --screenshots fastlane/screenshots/en-US \\
        --out build/marketing \\
        --headline "Plan your week in a minute" \\
        --subhead "Native on iPhone and iPad"

    python3 tools/screenshot-studio/compose_marketing.py --screenshots shots --out out --render
"""

from __future__ import annotations

import argparse
import html
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path
from typing import Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import emit
from apple_native.imaging import SCREENSHOT_SPECS, UnsupportedImage, image_info
from apple_native.report import Report
from apple_native.swiftscan import iter_files

THEMES: Dict[str, Dict[str, str]] = {
    "dark": {"from": "#0A0C11", "to": "#151A24", "headline": "#FFFFFF",
             "subhead": "#9AA6BA", "accent": "#0A84FF"},
    "light": {"from": "#F7F8FA", "to": "#E8ECF2", "headline": "#0B0D12",
              "subhead": "#5B6472", "accent": "#0A84FF"},
    "warm": {"from": "#151013", "to": "#241A1E", "headline": "#FFF6EF",
             "subhead": "#C9B8AE", "accent": "#FF9F0A"},
}

DEFAULT_CANVAS = (1320, 2868)  # iPhone 6.9" portrait


def canvas_for(screenshot: Tuple[int, int], override: Optional[Tuple[int, int]]) -> Tuple[int, int]:
    if override:
        return override
    for device, orientations in SCREENSHOT_SPECS.items():
        for sizes in orientations.values():
            if screenshot in sizes:
                return screenshot
    return DEFAULT_CANVAS


def wrap(text: str, per_line: int) -> List[str]:
    return textwrap.wrap(text, width=per_line, break_long_words=False) or [""]


def compose_svg(screenshot: Path, canvas: Tuple[int, int], headline: str, subhead: str,
                theme_name: str, inset: float, embed: bool = True) -> str:
    theme = THEMES[theme_name]
    width, height = canvas
    margin = int(width * 0.09)
    headline_size = int(width * 0.075)
    subhead_size = int(width * 0.034)
    headline_lines = wrap(headline, max(18, int(width / (headline_size * 0.52))))[:3]
    subhead_lines = wrap(subhead, max(24, int(width / (subhead_size * 0.5))))[:2] if subhead else []

    shot_width = int(width * (1 - inset * 2))
    shot_top = margin + len(headline_lines) * int(headline_size * 1.18) + int(width * 0.04)
    if subhead_lines:
        shot_top += len(subhead_lines) * int(subhead_size * 1.35) + int(width * 0.02)
    shot_height = height - shot_top - margin
    shot_href = f"data:image/png;base64,{__import__('base64').b64encode(screenshot.read_bytes()).decode()}" if embed else screenshot.name

    headline_tspans = "".join(
        f'<tspan x="{margin}" dy="{0 if index == 0 else int(headline_size * 1.18)}">{html.escape(line)}</tspan>'
        for index, line in enumerate(headline_lines)
    )
    subhead_tspans = "".join(
        f'<tspan x="{margin}" dy="{0 if index == 0 else int(subhead_size * 1.35)}">{html.escape(line)}</tspan>'
        for index, line in enumerate(subhead_lines)
    )
    subhead_y = margin + len(headline_lines) * int(headline_size * 1.18) + int(subhead_size * 1.1)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="{theme['from']}"/>
      <stop offset="1" stop-color="{theme['to']}"/>
    </linearGradient>
    <radialGradient id="glow" cx="0.2" cy="0.05" r="0.8">
      <stop offset="0" stop-color="{theme['accent']}" stop-opacity="0.28"/>
      <stop offset="1" stop-color="{theme['accent']}" stop-opacity="0"/>
    </radialGradient>
    <clipPath id="shotClip">
      <rect x="{int((width - shot_width) / 2)}" y="{shot_top}" width="{shot_width}" height="{shot_height}"
            rx="{int(width * 0.055)}"/>
    </clipPath>
    <filter id="shadow" x="-20%" y="-10%" width="140%" height="130%">
      <feDropShadow dx="0" dy="{int(width * 0.02)}" stdDeviation="{int(width * 0.03)}"
                    flood-color="#000000" flood-opacity="0.35"/>
    </filter>
  </defs>

  <rect width="{width}" height="{height}" fill="url(#bg)"/>
  <rect width="{width}" height="{height}" fill="url(#glow)"/>

  <text x="{margin}" y="{margin + headline_size}" font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Display', 'Helvetica Neue', sans-serif"
        font-size="{headline_size}" font-weight="700" letter-spacing="-1" fill="{theme['headline']}">{headline_tspans}</text>

  <text x="{margin}" y="{subhead_y}" font-family="-apple-system, BlinkMacSystemFont, 'SF Pro Text', 'Helvetica Neue', sans-serif"
        font-size="{subhead_size}" font-weight="400" fill="{theme['subhead']}">{subhead_tspans}</text>

  <rect x="{int((width - shot_width) / 2)}" y="{shot_top + int(width * 0.012)}" width="{shot_width}"
        height="{shot_height}" rx="{int(width * 0.055)}" fill="#000000" opacity="0.35" filter="url(#shadow)"/>
  <image xlink:href="{html.escape(shot_href)}" href="{html.escape(shot_href)}"
         x="{int((width - shot_width) / 2)}" y="{shot_top}"
         width="{shot_width}" height="{shot_height}" preserveAspectRatio="xMidYMin slice" clip-path="url(#shotClip)"/>
</svg>
'''


def find_renderer() -> Optional[List[str]]:
    if shutil.which("rsvg-convert"):
        return ["rsvg-convert"]
    if shutil.which("qlmanage"):
        return ["qlmanage"]
    return None


def render(svg: Path, width: int, height: int) -> Optional[Path]:
    renderer = find_renderer()
    if renderer is None:
        return None
    target = svg.with_suffix(".png")
    if renderer[0] == "rsvg-convert":
        subprocess.run(["rsvg-convert", "-w", str(width), "-h", str(height), "-o", str(target), str(svg)],
                       check=False, capture_output=True)
    else:
        subprocess.run(["qlmanage", "-t", "-s", str(max(width, height)), "-o", str(svg.parent), str(svg)],
                       check=False, capture_output=True)
        produced = svg.parent / f"{svg.name}.png"
        if produced.exists():
            produced.rename(target)
    return target if target.exists() else None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="compose-marketing",
        description="Compose App Store marketing frames (SVG) around real screenshots.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--screenshots", required=True, help="Directory of real screenshots (PNG/JPEG)")
    parser.add_argument("--out", required=True, help="Directory to write compositions into")
    parser.add_argument("--headline", default="Made for iPhone", help="Headline copy")
    parser.add_argument("--subhead", default="", help="Supporting line")
    parser.add_argument("--theme", default="dark", choices=sorted(THEMES), help="Colour theme")
    parser.add_argument("--canvas", help="WxH override, e.g. 1290x2796")
    parser.add_argument("--inset", type=float, default=0.08, help="Side inset as a fraction (default 0.08)")
    parser.add_argument("--render", action="store_true", help="Also rasterise to PNG when a renderer is available")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--color", choices=("auto", "always", "never"), default="auto")
    args = parser.parse_args(argv)

    source = Path(args.screenshots).expanduser().resolve()
    out = Path(args.out).expanduser().resolve()
    report = Report(tool="compose-marketing", target=str(source), version=__version__)

    if not source.is_dir():
        report.error("SHOT100", f"Screenshots directory not found: {source}")
        return emit(report, args)

    shots = list(iter_files(source, (".png", ".jpg", ".jpeg")))
    if not shots:
        report.error("SHOT101", "No screenshots found; capture real ones first.",
                     hint="xcrun simctl io booted screenshot shot.png")
        return emit(report, args)

    override = None
    if args.canvas:
        try:
            width, height = args.canvas.lower().split("x")
            override = (int(width), int(height))
        except ValueError:
            report.error("SHOT102", f"--canvas must look like 1320x2868, got {args.canvas!r}")
            return emit(report, args)

    out.mkdir(parents=True, exist_ok=True)
    written: List[Dict[str, object]] = []
    rendered = 0

    for shot in shots:
        try:
            info = image_info(shot)
        except (UnsupportedImage, OSError) as exc:
            report.warn("SHOT103", f"Skipping unreadable screenshot {shot.name}: {exc}")
            continue
        canvas = canvas_for(info.size, override)
        svg_path = out / f"{shot.stem}.svg"
        svg_path.write_text(compose_svg(shot, canvas, args.headline, args.subhead, args.theme, args.inset))
        entry: Dict[str, object] = {"screenshot": shot.name, "svg": svg_path.name, "canvas": f"{canvas[0]}x{canvas[1]}"}
        if args.render:
            png = render(svg_path, canvas[0], canvas[1])
            if png:
                rendered += 1
                entry["png"] = png.name
            else:
                entry["png"] = None
        written.append(entry)

    report.data = {
        "composed": len(written),
        "rendered": rendered,
        "output": str(out),
        "files": written,
        "renderer": (find_renderer() or ["none"])[0],
    }
    report.info("SHOT110", f"Composed {len(written)} marketing frame(s) as SVG.",
                hint="SVG is exact and editable; pass --render to rasterise when a renderer is installed.")
    if args.render and rendered == 0:
        report.warn("SHOT111", "No renderer found, so no PNG was produced.",
                    hint="Install librsvg (brew install librsvg) or export the SVG in any design tool.")
    if args.render and rendered:
        report.info("SHOT112", f"Rasterised {rendered} frame(s) with {report.data['renderer']}.")
    if len(written) < 3:
        report.info("SHOT113", "App Store Connect wants 3–10 screenshots per device size.",
                    hint=f"You composed {len(written)}; capture more before submitting.")
    return emit(report, args, title="Apple Native Engineer — Marketing screenshots")


if __name__ == "__main__":
    raise SystemExit(main())
