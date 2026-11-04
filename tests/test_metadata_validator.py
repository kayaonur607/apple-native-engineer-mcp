#!/usr/bin/env python3
"""
Unit tests for tools/metadata-validator
"""

import unittest
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools" / "metadata-validator"
sys.path.insert(0, str(TOOLS_DIR))
from validate_metadata import validate_localization, validate_metadata_file

class TestMetadataValidator(unittest.TestCase):
    
    def test_valid_localization(self):
        valid_data = {
            "name": "SuperApp",
            "subtitle": "Native Swift Productivity",
            "privacyPolicyUrl": "https://example.com/privacy",
            "supportUrl": "https://example.com/support",
            "description": "A very useful app description.",
            "keywords": "native,swift,tools"
        }
        res = validate_localization("en-US", valid_data)
        self.assertTrue(res["valid"])
        self.assertEqual(len(res["errors"]), 0)

    def test_name_exceeds_30_chars(self):
        invalid_data = {
            "name": "This is a super long app name that exceeds thirty chars",
            "privacyPolicyUrl": "https://example.com/privacy",
            "supportUrl": "https://example.com/support",
            "description": "Desc"
        }
        res = validate_localization("en-US", invalid_data)
        self.assertFalse(res["valid"])
        self.assertTrue(any("exceeds 30 characters" in e for e in res["errors"]))

    def test_missing_privacy_url(self):
        invalid_data = {
            "name": "Valid Name",
            "supportUrl": "https://example.com/support",
            "description": "Desc"
        }
        res = validate_localization("en-US", invalid_data)
        self.assertFalse(res["valid"])
        self.assertTrue(any("privacyPolicyUrl" in e for e in res["errors"]))

    def test_sample_metadata_fixture(self):
        fixture_path = Path(__file__).parent / "fixtures" / "sample_metadata.json"
        rep = validate_metadata_file(str(fixture_path))
        self.assertTrue(rep["overall_valid"])

if __name__ == "__main__":
    unittest.main()
