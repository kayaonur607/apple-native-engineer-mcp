#!/usr/bin/env python3
"""Render captured tool output as a terminal card (SVG).

Evidence in a README should be the tool's real output, not a screenshot someone
edited. This script takes the text a command actually printed and draws it into a
terminal window, so the visual can be regenerated whenever the output changes.

Usage::

    python3 tools/app-store-review/review.py tests/fixtures/legacy-app --color never > /tmp/out.txt
    python3 scripts/render_terminal_card.py --input /tmp/out.txt \\
        --title "app-store-review · legacy-app" --out assets/terminal-review.svg
"""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SEVERITY_COLOURS = {
    "✖": "#FF6B60",
    "▲": "#FFDD57",
    "ℹ": "#8FE0FF",
    "✓": "#6FE08A",
}


def strip_ansi(text: str) -> str:
    return ANSI.sub("", text)


def colour_for(line: str) -> str:
    for marker, colour in SEVERITY_COLOURS.items():
        if marker in line:
            return colour
    if line.strip().startswith("Status:"):
        if "FAIL" in line:
            return "#FF6B60"
        if "WARN" in line:
            return "#FFDD57"
        if "PASS" in line:
            return "#6FE08A"
    if line.startswith("=") or line.startswith("-") or line.startswith("─"):
        return "#3A4457"
    if re.match(r"^\s{2}[A-Z][A-Za-z ]+:\s", line):
        return "#9AA6BA"
    return "#C9D1DE"


def render(title: str, lines: list[str], width: int, char_width: float = 7.05) -> str:
    padding = 22
    line_height = 19
    header = 42
    height = header + padding + len(lines) * line_height + padding
    inner_width = width - padding * 2

    body = []
    for index, line in enumerate(lines):
        y = header + padding + index * line_height
        colour = colour_for(line)
        weight = "600" if re.match(r"^\s*[✖▲ℹ✓]", line) else "400"
        body.append(
            f'<text x="{padding}" y="{y}" fill="{colour}" font-weight="{weight}" '
            f'xml:space="preserve">{html.escape(line)}</text>'
        )

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" fill="none"
     xmlns="http://www.w3.org/2000/svg" role="img" aria-label="{html.escape(title)}">
  <defs>
    <linearGradient id="cardBg" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#0D1117"/>
      <stop offset="1" stop-color="#090B10"/>
    </linearGradient>
    <linearGradient id="cardEdge" x1="0" y1="0" x2="{width}" y2="{height}" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="#2C3648"/>
      <stop offset="1" stop-color="#161B24"/>
    </linearGradient>
  </defs>

  <rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="14" fill="url(#cardBg)"/>
  <rect x="0.75" y="0.75" width="{width - 1.5}" height="{height - 1.5}" rx="14" stroke="url(#cardEdge)" stroke-width="1.5"/>

  <circle cx="{padding + 4}" cy="22" r="5" fill="#FF5F57"/>
  <circle cx="{padding + 22}" cy="22" r="5" fill="#FEBC2E"/>
  <circle cx="{padding + 40}" cy="22" r="5" fill="#28C840"/>
  <text x="{padding + 62}" y="26" font-family="'SF Mono', ui-monospace, Menlo, monospace" font-size="11.5"
        fill="#6B7688">{html.escape(title)}</text>
  <line x1="0" y1="{header}" x2="{width}" y2="{header}" stroke="#FFFFFF" stroke-opacity="0.07"/>

  <g font-family="'SF Mono', ui-monospace, Menlo, monospace" font-size="12.5">
    {"".join(body)}
  </g>
</svg>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description="Render tool output as a terminal card (SVG).")
    parser.add_argument("--input", required=True, help="File containing the captured output")
    parser.add_argument("--out", required=True, help="SVG to write")
    parser.add_argument("--title", default="terminal", help="Window title text")
    parser.add_argument("--width", type=int, default=820)
    parser.add_argument("--max-lines", type=int, default=26)
    parser.add_argument("--max-chars", type=int, default=104, help="Truncate lines wider than this")
    parser.add_argument("--strip-prefix", default="", help="Replace this path prefix with <repo> before rendering")
    args = parser.parse_args()

    text = strip_ansi(Path(args.input).read_text(encoding="utf-8", errors="replace"))
    if args.strip_prefix:
        text = text.replace(args.strip_prefix, "<repo>")
    lines = []
    for line in text.splitlines()[: args.max_lines]:
        line = line.rstrip()
        if len(line) > args.max_chars:
            line = line[: args.max_chars - 1].rstrip() + "…"
        lines.append(line)
    longest = max((len(line) for line in lines), default=40)
    width = max(args.width, int(longest * 7.05) + 44)

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(render(args.title, lines, width))
    print(f"wrote {out} ({len(lines)} lines, {width}px wide)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
