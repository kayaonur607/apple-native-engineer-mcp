"""Colour maths used by the accessibility and design auditors.

Implements WCAG 2.2 relative luminance and contrast ratio (the ratio Apple and
the App Store review team expect for text legibility) plus a small parser for
the colour literal syntaxes that appear in Swift and SwiftUI sources:

* ``#RRGGBB`` / ``#RRGGBBAA`` inside ``Color(hex:)`` style helpers
* ``Color(red:green:blue:)`` with 0...1 doubles
* ``UIColor(red:green:blue:alpha:)``
* ``Color(.sRGB, red:green:blue:opacity:)``
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple


@dataclass(frozen=True)
class RGB:
    r: int
    g: int
    b: int
    a: float = 1.0

    def hex(self) -> str:
        base = f"#{self.r:02X}{self.g:02X}{self.b:02X}"
        if self.a < 1.0:
            base += f"{int(round(self.a * 255)):02X}"
        return base

    def as_tuple(self) -> Tuple[int, int, int]:
        return (self.r, self.g, self.b)

    def luminance(self) -> float:
        def channel(value: int) -> float:
            srgb = value / 255.0
            return srgb / 12.92 if srgb <= 0.04045 else ((srgb + 0.055) / 1.055) ** 2.4

        r, g, b = (channel(v) for v in self.as_tuple())
        return 0.2126 * r + 0.7152 * g + 0.0722 * b

    def composite_over(self, background: "RGB") -> "RGB":
        """Flatten a translucent colour onto an opaque background."""

        alpha = max(0.0, min(1.0, self.a))
        return RGB(
            r=int(round(self.r * alpha + background.r * (1 - alpha))),
            g=int(round(self.g * alpha + background.g * (1 - alpha))),
            b=int(round(self.b * alpha + background.b * (1 - alpha))),
            a=1.0,
        )


WHITE = RGB(255, 255, 255)
BLACK = RGB(0, 0, 0)

#: System background approximations used when a colour is "semantic" and has no
#: literal definition we can resolve. iOS light / dark system backgrounds.
SYSTEM_BACKGROUND_LIGHT = RGB(255, 255, 255)
SYSTEM_BACKGROUND_DARK = RGB(28, 28, 30)


def parse_hex(value: str) -> Optional[RGB]:
    text = value.strip().lstrip("#")
    if len(text) == 3:
        text = "".join(ch * 2 for ch in text)
    if len(text) not in (6, 8):
        return None
    try:
        r = int(text[0:2], 16)
        g = int(text[2:4], 16)
        b = int(text[4:6], 16)
        a = int(text[6:8], 16) / 255.0 if len(text) == 8 else 1.0
    except ValueError:
        return None
    return RGB(r, g, b, a)


def contrast_ratio(foreground: RGB, background: RGB) -> float:
    """WCAG 2.x contrast ratio, 1.0 (identical) to 21.0 (black on white)."""

    lg1 = foreground.luminance()
    lg2 = background.luminance()
    lighter, darker = max(lg1, lg2), min(lg1, lg2)
    return (lighter + 0.05) / (darker + 0.05)


def required_contrast(font_size_pt: float, bold: bool) -> float:
    """Minimum ratio for AA: 4.5 normal text, 3.0 large text (>=18pt or 14pt bold)."""

    is_large = font_size_pt >= 24 or (font_size_pt >= 18.66 and bold)
    return 3.0 if is_large else 4.5


def required_contrast_aaa(font_size_pt: float, bold: bool) -> float:
    is_large = font_size_pt >= 24 or (font_size_pt >= 18.66 and bold)
    return 4.5 if is_large else 7.0


# -- Swift literal extraction ------------------------------------------------

_HEX_RE = re.compile(r'"\s*(#(?:[0-9A-Fa-f]{3,8}))\s*"')
_RGB_FUNC_RE = re.compile(
    r"(?:Color|UIColor|NSColor)\s*\(\s*(?:\.sRGB\s*,\s*)?red:\s*([0-9.]+)\s*,\s*"
    r"green:\s*([0-9.]+)\s*,\s*blue:\s*([0-9.]+)\s*(?:,\s*(?:alpha|opacity):\s*([0-9.]+)\s*)?\)"
)


def extract_literals(source: str) -> List[Tuple[int, RGB, str]]:
    """Return ``(offset, colour, raw_literal)`` for every resolvable colour."""

    found: List[Tuple[int, RGB, str]] = []

    for match in _HEX_RE.finditer(source):
        colour = parse_hex(match.group(1))
        if colour is not None:
            found.append((match.start(), colour, match.group(0)))

    for match in _RGB_FUNC_RE.finditer(source):
        try:
            r = float(match.group(1))
            g = float(match.group(2))
            b = float(match.group(3))
            a = float(match.group(4)) if match.group(4) else 1.0
        except ValueError:
            continue
        # Swift accepts both 0...1 doubles and 0...255 ints in helper wrappers.
        if max(r, g, b) > 1.0:
            r, g, b = r / 255.0, g / 255.0, b / 255.0
        found.append(
            (
                match.start(),
                RGB(
                    int(round(max(0.0, min(1.0, r)) * 255)),
                    int(round(max(0.0, min(1.0, g)) * 255)),
                    int(round(max(0.0, min(1.0, b)) * 255)),
                    max(0.0, min(1.0, a)),
                ),
                match.group(0),
            )
        )

    found.sort(key=lambda item: item[0])
    return found


#: SwiftUI semantic colours that adapt to light/dark automatically. Using them
#: is correct behaviour, so auditors must not flag them as "hardcoded".
SEMANTIC_COLORS = {
    ".primary", ".secondary", ".tertiary", ".quaternary",
    ".accentColor", ".tint",
    "Color.primary", "Color.secondary", "Color.accentColor",
    ".white", ".black", ".clear", ".gray", ".red", ".blue", ".green",
    ".orange", ".yellow", ".pink", ".purple", ".teal", ".indigo", ".brown",
    ".mint", ".cyan",
}


def is_semantic(color_expression: str) -> bool:
    expr = color_expression.strip()
    if expr in SEMANTIC_COLORS:
        return True
    # .foregroundStyle(.secondary) / Color(uiColor: .label)
    return bool(re.match(r"^(?:Color\.)?\.(?:primary|secondary|tertiary|quaternary|label|"
                         r"secondaryLabel|systemBackground|labelColor)\b", expr))
