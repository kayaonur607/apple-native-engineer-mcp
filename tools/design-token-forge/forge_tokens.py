#!/usr/bin/env python3
"""Design Token Forge — turn a design token JSON into native Swift and assets.

Design tokens usually live in Figma or a web CSS file and lose their meaning on
the way to SwiftUI: hex strings become hardcoded colours, spacing becomes magic
numbers, and dark mode is forgotten. This tool compiles the token document into
idiomatic Swift (dynamic ``Color`` values, CGFloat scales, Font styles) and can
also emit a colour-set-per-token ``.xcassets`` folder.

Input schema (all sections optional)::

    {
      "name": "Acme",
      "colors": {
        "brand":  {"light": "#0A84FF", "dark": "#409CFF"},
        "canvas": {"light": "#FFFFFF", "dark": "#000000"}
      },
      "spacing": {"xs": 4, "sm": 8, "md": 16},
      "radius":  {"card": 20, "pill": 999},
      "typography": {
        "title": {"style": "title", "weight": "bold", "design": "default"}
      },
      "contrastPairs": [{"foreground": "brand", "background": "canvas"}]
    }

Usage::

    python3 tools/design-token-forge/forge_tokens.py tokens.json --out Sources/Tokens.swift
    python3 tools/design-token-forge/forge_tokens.py tokens.json --xcassets Assets.xcassets
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.colors import SYSTEM_BACKGROUND_DARK, SYSTEM_BACKGROUND_LIGHT, contrast_ratio, parse_hex
from apple_native.report import Report

SWIFT_WEIGHTS = {"ultraLight", "thin", "light", "regular", "medium", "semibold", "bold", "heavy", "black"}
SWIFT_TEXT_STYLES = {
    "largeTitle", "title", "title2", "title3", "headline", "subheadline",
    "body", "callout", "footnote", "caption", "caption2",
}
SWIFT_DESIGNS = {"default", "serif", "rounded", "monospaced"}
IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _camel(name: str) -> str:
    parts = re.split(r"[^A-Za-z0-9]+", name)
    head, *tail = [part for part in parts if part]
    if not head:
        return "token"
    identifier = head[0].lower() + head[1:] + "".join(part[:1].upper() + part[1:] for part in tail)
    if identifier[0].isdigit():
        identifier = "t" + identifier
    return identifier


def _swift_literal_colour(hex_value: str) -> Optional[str]:
    colour = parse_hex(hex_value)
    if colour is None:
        return None
    return (
        f'Color(.sRGB, red: {colour.r / 255:.4f}, green: {colour.g / 255:.4f}, '
        f'blue: {colour.b / 255:.4f}, opacity: {colour.a:.3f})'
    )


def validate_tokens(payload: Dict[str, Any], report: Report) -> None:
    colors = payload.get("colors", {})
    for name, value in colors.items():
        if not isinstance(value, dict):
            report.error("TOK001", f"Colour token '{name}' must be an object with light/dark values.")
            continue
        for appearance in ("light", "dark"):
            hex_value = value.get(appearance)
            if not hex_value:
                report.warn("TOK002", f"Colour token '{name}' has no '{appearance}' value.",
                            hint="Provide both appearances; a single value breaks Dark Mode.")
            elif parse_hex(str(hex_value)) is None:
                report.error("TOK003", f"Colour token '{name}.{appearance}' is not a valid hex colour: {hex_value}")

    for section, expected in (("spacing", (int, float)), ("radius", (int, float))):
        for name, value in payload.get(section, {}).items():
            if not isinstance(value, expected):
                report.error("TOK004", f"{section}.{name} must be a number, got {type(value).__name__}.")
            elif value < 0:
                report.error("TOK005", f"{section}.{name} is negative ({value}).")

    for name, value in payload.get("typography", {}).items():
        if not isinstance(value, dict):
            report.error("TOK006", f"typography.{name} must be an object.")
            continue
        style = value.get("style", "body")
        if style not in SWIFT_TEXT_STYLES:
            report.error("TOK007", f"typography.{name}.style '{style}' is not a Font.TextStyle.",
                         hint=f"Use one of: {', '.join(sorted(SWIFT_TEXT_STYLES))}")
        weight = value.get("weight")
        if weight and weight not in SWIFT_WEIGHTS:
            report.error("TOK008", f"typography.{name}.weight '{weight}' is not a Font.Weight.")
        design = value.get("design")
        if design and design not in SWIFT_DESIGNS:
            report.error("TOK009", f"typography.{name}.design '{design}' is not a Font.Design.")

    for pair in payload.get("contrastPairs", []):
        foreground = colors.get(pair.get("foreground"), {})
        background = colors.get(pair.get("background"), {})
        if not foreground or not background:
            report.warn("TOK010", f"contrastPairs references an unknown token: {pair}")
            continue
        for appearance in ("light", "dark"):
            fg = parse_hex(str(foreground.get(appearance, "")))
            bg = parse_hex(str(background.get(appearance, "")))
            if fg is None or bg is None:
                continue
            ratio = contrast_ratio(fg, bg)
            if ratio < 4.5:
                report.warn(
                    "TOK011",
                    f"contrastPairs {pair['foreground']} on {pair['background']} is {ratio:.2f}:1 in "
                    f"{appearance} appearance; below WCAG AA 4.5:1.",
                    hint="Adjust the token pair, or use it only for large text.",
                )


def render_swift(payload: Dict[str, Any]) -> str:
    name = payload.get("name", "DesignSystem")
    if not IDENTIFIER_RE.match(name):
        name = _camel(name).capitalize()

    lines: List[str] = [
        "// Generated by apple-native-engineer-mcp · design-token-forge",
        "// Do not edit by hand: change the token source and re-run the generator.",
        "",
        "import SwiftUI",
        "",
        f"public enum {name} {{",
    ]

    colors = payload.get("colors", {})
    if colors:
        lines += ["", "    // MARK: - Colour", "", "    public enum Colors {"]
        for token_name, value in colors.items():
            identifier = _camel(token_name)
            light = value.get("light", "#000000")
            dark = value.get("dark", light)
            lines.append(
                f'        /// {token_name} — light {light}, dark {dark}\n'
                f"        public static let {identifier} = Color.token(light: \"{light}\", dark: \"{dark}\")"
            )
        lines += ["    }"]

    spacing = payload.get("spacing", {})
    if spacing:
        lines += ["", "    // MARK: - Spacing (8pt grid)", "", "    public enum Spacing {"]
        for token_name, value in spacing.items():
            lines.append(f"        public static let {_camel(token_name)}: CGFloat = {value:g}")
        lines += ["    }"]

    radius = payload.get("radius", {})
    if radius:
        lines += ["", "    // MARK: - Radius", "", "    public enum Radius {"]
        for token_name, value in radius.items():
            lines.append(f"        public static let {_camel(token_name)}: CGFloat = {value:g}")
        lines += ["    }"]

    typography = payload.get("typography", {})
    if typography:
        lines += ["", "    // MARK: - Typography (Dynamic Type aware)", "", "    public enum Typography {"]
        for token_name, value in typography.items():
            style = value.get("style", "body")
            weight = value.get("weight")
            design = value.get("design")
            modifiers = ""
            if design:
                modifiers += f", design: .{design}"
            base = f".system(.{style}{modifiers})"
            if weight:
                base = f".system(.{style}, weight: .{weight}{modifiers})"
            lines.append(f"        public static let {_camel(token_name)} = Font{base}")
        lines += ["    }"]

    lines += [
        "}",
        "",
        "// MARK: - Dynamic colour helper",
        "",
        "extension Color {",
        "    /// Builds a colour that resolves per appearance without an asset catalogue.",
        "    static func token(light: String, dark: String) -> Color {",
        "        Color(UIColor { traits in",
        "            let isDark = traits.userInterfaceStyle == .dark",
        "            return UIColor(hex: isDark ? dark : light) ?? .label",
        "        })",
        "    }",
        "}",
        "",
        "extension UIColor {",
        "    convenience init?(hex: String) {",
        "        var value = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)",
        "        guard value.count == 6 || value.count == 8, let number = UInt64(value, radix: 16) else {",
        "            return nil",
        "        }",
        "        if value.count == 6 { value += \"FF\" }",
        "        let r = CGFloat((number >> 24) & 0xFF) / 255",
        "        let g = CGFloat((number >> 16) & 0xFF) / 255",
        "        let b = CGFloat((number >> 8) & 0xFF) / 255",
        "        let a = CGFloat(number & 0xFF) / 255",
        "        self.init(red: r, green: g, blue: b, alpha: a)",
        "    }",
        "}",
        "",
    ]
    return "\n".join(lines)


def emit_assets(payload: Dict[str, Any], directory: Path, report: Report) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    contents_root = {"info": {"author": "xcode", "version": 1}}
    (directory / "Contents.json").write_text(json.dumps(contents_root, indent=2) + "\n")

    for token_name, value in payload.get("colors", {}).items():
        light = value.get("light", "#000000")
        dark = value.get("dark", light)
        folder = directory / f"{_camel(token_name)}.colorset"
        folder.mkdir(parents=True, exist_ok=True)
        components = []
        for appearance, hex_value in (("universal", light), (None, dark)):
            colour = parse_hex(hex_value)
            if colour is None:
                continue
            entry = {
                "color": {
                    "color-space": "srgb",
                    "components": {
                        "alpha": f"{colour.a:.3f}",
                        "blue": f"{colour.b / 255:.3f}",
                        "green": f"{colour.g / 255:.3f}",
                        "red": f"{colour.r / 255:.3f}",
                    },
                },
                "idiom": "universal",
            }
            if appearance == "universal":
                entry["appearances"] = [{"appearance": "luminosity", "value": "light"}]
            else:
                entry["appearances"] = [{"appearance": "luminosity", "value": "dark"}]
            components.append(entry)
        (folder / "Contents.json").write_text(
            json.dumps({"colors": components, "info": {"author": "xcode", "version": 1}}, indent=2) + "\n"
        )
    report.data["xcassets"] = str(directory)


def forge(input_path: Path, out: Optional[Path], xcassets: Optional[Path]) -> Report:
    report = Report(tool="design-token-forge", target=str(input_path), version=__version__)
    try:
        payload = json.loads(input_path.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        report.error("TOK000", f"Token file could not be read: {exc}")
        return report

    validate_tokens(payload, report)

    generated = render_swift(payload)
    report.data["tokens"] = {
        "colors": len(payload.get("colors", {})),
        "spacing": len(payload.get("spacing", {})),
        "radius": len(payload.get("radius", {})),
        "typography": len(payload.get("typography", {})),
    }
    report.data["swift_lines"] = len(generated.splitlines())

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(generated)
        report.data["swift_output"] = str(out)
    else:
        report.data["preview"] = generated.splitlines()[:6]

    if xcassets:
        emit_assets(payload, xcassets, report)

    return report


def main(argv=None) -> int:
    parser = build_parser(
        "design-token-forge",
        "Compile a design token JSON into SwiftUI tokens and optional .xcassets colour sets.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
    )
    parser.add_argument("--out", help="Write the generated Swift file here")
    parser.add_argument("--xcassets", help="Also emit a .xcassets colour set directory")
    args = parser.parse_args(argv)

    candidate = Path(args.path).expanduser()
    if not candidate.is_file():
        report = Report(tool="design-token-forge", target=str(candidate), version=__version__)
        report.error("TOK000", f"Token file not found: {candidate}",
                     hint="Pass the token JSON path as the positional argument.")
        return emit(report, args)

    report = forge(
        candidate,
        Path(args.out).expanduser() if args.out else None,
        Path(args.xcassets).expanduser() if args.xcassets else None,
    )
    return emit(report, args, title="Apple Native Engineer — Design Token Forge")


if __name__ == "__main__":
    raise SystemExit(main())
