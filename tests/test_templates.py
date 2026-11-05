"""The templates must satisfy the tools they template.

Shipping a metadata template that our own validator rejects, or a screenshot
spec whose dimensions the validator does not recognise, is the kind of
inconsistency a reader only discovers after copying it.
"""

from __future__ import annotations

import json
import sys
import unittest

from support import REPO_ROOT, TOOLS, run_tool

sys.path.insert(0, str(TOOLS / "lib"))

from apple_native.imaging import SCREENSHOT_SPECS, match_screenshot_spec

TEMPLATES = REPO_ROOT / "templates"


class MetadataTemplateTests(unittest.TestCase):
    def test_template_passes_the_metadata_validator(self):
        envelope = run_tool(
            "metadata-validator/validate_metadata.py",
            str(TEMPLATES / "metadata" / "app_metadata_template.json"),
            expect=0,
        )
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["findings"], [])

    def test_template_declares_both_locales(self):
        payload = json.loads((TEMPLATES / "metadata" / "app_metadata_template.json").read_text())
        self.assertEqual(sorted(payload["localizations"]), ["en-US", "tr-TR"])
        for locale, fields in payload["localizations"].items():
            self.assertIn("privacyPolicyUrl", fields, f"{locale} needs a privacy policy URL")
            self.assertGreaterEqual(len(fields["screenshots"]), 3, f"{locale} needs 3+ screenshots")

    def test_camel_case_keys_are_normalised(self):
        """App Store Connect's API is camelCase; the validator must accept it."""

        payload = {
            "name": "Camel App",
            "subtitle": "Short",
            "description": "A description is mandatory, so the fixture includes one.",
            "privacyPolicyUrl": "https://example.com/privacy",
            "supportUrl": "https://example.com/support",
            "promotionalText": "Camel case promotional copy.",
            "screenshots": ["a.png", "b.png", "c.png"],
        }
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "meta.json"
            path.write_text(json.dumps(payload))
            envelope = run_tool("metadata-validator/validate_metadata.py", str(path), expect=0)
            self.assertEqual(envelope["status"], "pass", envelope["findings"])


class IconTemplateTests(unittest.TestCase):
    def test_contents_json_declares_a_marketing_slot(self):
        payload = json.loads((TEMPLATES / "app-icon" / "Contents.json").read_text())
        sizes = {image.get("size") for image in payload["images"]}
        self.assertIn("1024x1024", sizes)
        self.assertIn("info", payload)


class ScreenshotSpecTests(unittest.TestCase):
    def test_spec_dimensions_are_recognised_by_the_validator(self):
        payload = json.loads((TEMPLATES / "screenshot-layouts" / "spec.json").read_text())
        checked = 0
        for device, entry in payload["devices"].items():
            for orientation, size in entry.get("pixel_dimensions", {}).items():
                portrait = tuple(size)
                if orientation == "landscape":
                    portrait = (portrait[1], portrait[0])
                self.assertIsNotNone(
                    match_screenshot_spec(*portrait),
                    f"{device} {orientation} {size} is not an accepted slot in imaging.SCREENSHOT_SPECS",
                )
                checked += 1
        self.assertGreater(checked, 0)

    def test_validator_knows_the_current_iphone_slot(self):
        self.assertIn("iPhone 6.9\"", SCREENSHOT_SPECS)
        self.assertEqual(match_screenshot_spec(1320, 2868)[0], 'iPhone 6.9"')


class ReportTemplateTests(unittest.TestCase):
    def test_placeholders_cover_the_generated_report(self):
        text = (TEMPLATES / "reports" / "release_report_template.md").read_text()
        for placeholder in ("{VERDICT}", "{SCORE}", "{DATE}", "{GATE_PRIVACY}", "{CODE}"):
            self.assertIn(placeholder, text, f"report template is missing {placeholder}")

    def test_template_mentions_the_blocking_rule(self):
        text = (TEMPLATES / "reports" / "release_report_template.md").read_text()
        self.assertIn("not_inspected", text)
        self.assertIn("BLOCKED", text)


if __name__ == "__main__":
    unittest.main()
