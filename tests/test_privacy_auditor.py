#!/usr/bin/env python3
"""
Unit tests for tools/privacy-auditor
"""

import unittest
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools" / "privacy-auditor"
sys.path.insert(0, str(TOOLS_DIR))
from audit_privacy import run_privacy_audit, inspect_privacy_manifest, scan_source_code_for_apis

class TestPrivacyAuditor(unittest.TestCase):
    
    def test_mock_project_audit(self):
        mock_path = Path(__file__).parent / "fixtures" / "mock_project"
        report = run_privacy_audit(str(mock_path))
        # Since mock_project has UserDefaults and PrivacyInfo declares it, should be compliant
        self.assertTrue(report["compliant"])
        self.assertIn("NSPrivacyAccessedAPICategoryUserDefaults", report["detected_apis"])

    def test_sample_manifest_inspection(self):
        sample_manifest = Path(__file__).parent / "fixtures" / "sample_privacy.xcprivacy"
        info = inspect_privacy_manifest(sample_manifest)
        self.assertTrue(info["found"])
        self.assertIn("NSPrivacyAccessedAPICategoryUserDefaults", info["declared_categories"])
        self.assertFalse(info["tracking_enabled"])

if __name__ == "__main__":
    unittest.main()
