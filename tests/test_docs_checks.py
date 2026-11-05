"""Tests for the documentation checks: modifier extraction and claim checking."""

from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

from support import REPO_ROOT


def load(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / relative)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


CLAIMS = load("check_api_claims", "scripts/check_api_claims.py")

MARKDOWN = """
Text("hello")
    .font(.body)
    .glassEffect(.regular)
    .padding()

```swift
content
    .containerBackground(.fill.tertiary, for: .widget)
    .madeUpModifier(42)
```

```kotlin
    .notSwiftAtAll()
```
"""


class ModifierExtractionTests(unittest.TestCase):
    def test_only_line_leading_modifiers_are_counted(self):
        counts = CLAIMS.extract_modifiers(MARKDOWN)
        self.assertIn("containerBackground", counts)
        self.assertIn("madeUpModifier", counts)
        # Inline chains outside a fence, and non-swift fences, are ignored.
        self.assertNotIn("glassEffect", counts)
        self.assertNotIn("notSwiftAtAll", counts)

    def test_method_calls_on_models_are_not_modifiers(self):
        markdown = "```swift\nmodel.fetchProfile()\nlet x = 1\n```"
        self.assertEqual(dict(CLAIMS.extract_modifiers(markdown)), {})

    def test_duplicates_are_counted(self):
        markdown = "```swift\n.padding()\n.padding()\n```"
        self.assertEqual(CLAIMS.extract_modifiers(markdown)["padding"], 2)


class ClaimCheckTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.doc = Path(self.tempdir.name) / "doc.md"
        self.doc.write_text(MARKDOWN)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_known_modifier_passes(self):
        findings = CLAIMS.check([self.doc], {"containerBackground"}, {})
        self.assertEqual([finding["symbol"] for finding in findings], ["madeUpModifier"])

    def test_allowlist_suppresses_a_finding(self):
        findings = CLAIMS.check([self.doc], {"containerBackground"}, {"madeUpModifier": "test"})
        self.assertEqual(findings, [])

    def test_finding_carries_files_and_hint(self):
        findings = CLAIMS.check([self.doc], set(), {})
        self.assertTrue(findings)
        finding = findings[0]
        self.assertIn("files", finding)
        self.assertIn("api-allowlist.json", finding["hint"])


class RepositoryAllowlistTests(unittest.TestCase):
    def test_every_allowlist_entry_has_a_reason(self):
        payload = json.loads((REPO_ROOT / "data" / "api-allowlist.json").read_text())
        entries = payload.get("allowed", [])
        self.assertGreater(len(entries), 0)
        for entry in entries:
            self.assertIn("symbol", entry)
            self.assertTrue(entry.get("reason"), f"{entry.get('symbol')} needs a documented reason")
            self.assertGreater(len(entry["reason"]), 20, "reasons must explain, not gesture")

    def test_no_empty_uid_modifiers_in_docs(self):
        """Every swift fence that contains a modifier must contain real code."""

        for directory in ("references", "examples"):
            for document in (REPO_ROOT / directory).glob("*.md"):
                text = document.read_text(errors="ignore")
                self.assertNotIn("```swift\n…\n```", text, f"{document.name}: placeholder snippet")


if __name__ == "__main__":
    unittest.main()
