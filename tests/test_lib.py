"""Unit tests for the shared library (report contract, scanning, colour maths)."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from support import REPO_ROOT, TOOLS

sys.path.insert(0, str(TOOLS / "lib"))

from apple_native.colors import (
    RGB,
    contrast_ratio,
    extract_literals,
    parse_hex,
    required_contrast,
)
from apple_native.imaging import image_info, match_screenshot_spec
from apple_native.report import Report, Severity
from apple_native.swiftscan import (
    SwiftFile,
    declared_types,
    strip_comments,
    strip_comments_and_strings,
)
from apple_native.xcode import parse_package_swift, parse_version, ProjectInfo


class ReportContractTests(unittest.TestCase):
    def test_empty_report_passes(self):
        report = Report(tool="t", target="/tmp")
        self.assertEqual(report.status, "pass")
        self.assertEqual(report.exit_code(), 0)
        self.assertEqual(report.exit_code(strict=True), 0)

    def test_warning_only_warns(self):
        report = Report(tool="t", target="/tmp")
        report.warn("X001", "a warning")
        self.assertEqual(report.status, "warn")
        self.assertEqual(report.exit_code(), 0, "warnings must not fail a default run")
        self.assertEqual(report.exit_code(strict=True), 1, "--strict promotes warnings")

    def test_error_fails(self):
        report = Report(tool="t", target="/tmp")
        report.error("X002", "an error")
        self.assertEqual(report.status, "fail")
        self.assertEqual(report.exit_code(), 2)

    def test_envelope_is_stable_and_serialisable(self):
        report = Report(tool="t", target="/tmp")
        report.critical("X003", "boom", file="A.swift", line=7, hint="fix it")
        payload = json.loads(report.to_json())
        self.assertEqual(payload["schema_version"], "2.0")
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["summary"]["critical"], 1)
        self.assertEqual(payload["summary"]["total"], 1)
        self.assertEqual(payload["findings"][0]["file"], "A.swift")
        self.assertEqual(payload["findings"][0]["line"], 7)
        self.assertEqual(payload["findings"][0]["severity"], "critical")

    def test_counts_cover_every_severity(self):
        report = Report(tool="t", target="/tmp")
        for severity in Severity:
            report.add("X", severity, "m")
        counts = report.counts()
        self.assertEqual(counts["info"], 1)
        self.assertEqual(counts["warning"], 1)
        self.assertEqual(counts["error"], 1)
        self.assertEqual(counts["critical"], 1)
        self.assertEqual(counts["total"], 4)


class SwiftScanTests(unittest.TestCase):
    SOURCE = """import SwiftUI
// .glassEffect() in a comment must not count
let a = "a string with .foregroundColor( in it"
/* block comment
   spanning lines */
let b = realCall()
"""

    def test_comments_are_blanked(self):
        stripped = strip_comments(self.SOURCE)
        self.assertNotIn("block comment", stripped)
        self.assertIn('.foregroundColor(', stripped, "string literals survive comment stripping")

    def test_strings_are_blanked_on_request(self):
        stripped = strip_comments_and_strings(self.SOURCE)
        self.assertNotIn(".foregroundColor(", stripped)
        self.assertIn("realCall", stripped)

    def test_offsets_and_line_numbers_are_preserved(self):
        stripped = strip_comments_and_strings(self.SOURCE)
        self.assertEqual(len(stripped), len(self.SOURCE))
        self.assertEqual(stripped.count("\n"), self.SOURCE.count("\n"))
        swift = SwiftFile(path=Path("x.swift"), relative="x.swift", raw=self.SOURCE,
                          clean=stripped, code=strip_comments(self.SOURCE))
        offset = swift.clean.index("realCall")
        self.assertEqual(swift.line_of(offset), 6)

    def test_nested_block_comments(self):
        source = "a\n/* outer /* inner */ still comment */\nb"
        self.assertEqual(strip_comments(source).count("comment"), 0)
        self.assertIn("b", strip_comments(source))

    def test_url_literals_are_not_treated_as_comments(self):
        source = 'let a = "https://example.com/x" // real comment\n'
        stripped = strip_comments(source)
        self.assertIn("https://example.com/x", stripped, "// inside a literal is not a comment")
        self.assertNotIn("real comment", stripped)

    def test_declared_types(self):
        types = declared_types("struct A {}\nclass B {}\nactor C {}\nprotocol D {}")
        self.assertEqual(types, {"A": "struct", "B": "class", "C": "actor", "D": "protocol"})


class ColourMathTests(unittest.TestCase):
    def test_black_on_white_is_21(self):
        self.assertAlmostEqual(contrast_ratio(RGB(0, 0, 0), RGB(255, 255, 255)), 21.0, places=2)

    def test_identical_colours_are_1(self):
        self.assertAlmostEqual(contrast_ratio(RGB(18, 52, 86), RGB(18, 52, 86)), 1.0, places=4)

    def test_known_gray_contrast(self):
        # #767676 on white is the canonical WCAG AA boundary (4.54:1).
        ratio = contrast_ratio(parse_hex("#767676"), RGB(255, 255, 255))
        self.assertAlmostEqual(ratio, 4.54, places=1)

    def test_hex_parsing_variants(self):
        self.assertEqual(parse_hex("#fff"), RGB(255, 255, 255, 1.0))
        self.assertEqual(parse_hex("0A84FF"), RGB(10, 132, 255, 1.0))
        self.assertAlmostEqual(parse_hex("#0A84FF80").a, 128 / 255, places=3)
        self.assertIsNone(parse_hex("nope"))

    def test_large_text_threshold(self):
        self.assertEqual(required_contrast(17, bold=False), 4.5)
        self.assertEqual(required_contrast(24, bold=False), 3.0)
        self.assertEqual(required_contrast(19, bold=True), 3.0)

    def test_extract_literals_from_swift(self):
        source = 'Text("x").foregroundStyle(Color(hex: "#C7C7CC"))'
        literals = extract_literals(source)
        self.assertEqual(len(literals), 1)
        offset, colour, raw = literals[0]
        self.assertEqual(colour.hex(), "#C7C7CC")
        self.assertIn("#C7C7CC", raw)

    def test_rgb_function_literal(self):
        literals = extract_literals("Color(red: 1.0, green: 0.5, blue: 0.0)")
        self.assertEqual(literals[0][1].hex(), "#FF8000")


class VersionTests(unittest.TestCase):
    def test_zero_padded_comparison(self):
        self.assertFalse(parse_version("17") < parse_version("17.0"))
        self.assertTrue(parse_version("16") < parse_version("26.0"))
        self.assertTrue(parse_version("17.0") < parse_version("17.1"))
        self.assertEqual(parse_version("bogus"), (0, 0, 0))

    def test_package_swift_platform_shorthand(self):
        info = ProjectInfo(root=REPO_ROOT)
        parse_package_swift(REPO_ROOT / "tests/fixtures/clean-app/Package.swift", info)
        self.assertEqual(info.deployment_targets["iOS"], "17")
        self.assertEqual(info.deployment_targets["macOS"], "14")
        self.assertIn("6.0", info.swift_versions)


class ImagingTests(unittest.TestCase):
    def test_valid_icon_has_no_alpha(self):
        info = image_info(REPO_ROOT / "tests/fixtures/clean-app/Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png")
        self.assertEqual(info.size, (1024, 1024))
        self.assertFalse(info.has_alpha)

    def test_invalid_icon_has_alpha(self):
        info = image_info(REPO_ROOT / "tests/fixtures/legacy-app/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png")
        self.assertEqual(info.size, (512, 512))
        self.assertTrue(info.has_alpha)

    def test_screenshot_slot_matching(self):
        self.assertEqual(match_screenshot_spec(1320, 2868)[0], 'iPhone 6.9"')
        self.assertIsNone(match_screenshot_spec(123, 456))


if __name__ == "__main__":
    unittest.main()
