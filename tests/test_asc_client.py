#!/usr/bin/env python3
"""
Unit tests for tools/app-store-connect
"""

import unittest
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools" / "app-store-connect"
sys.path.insert(0, str(TOOLS_DIR))
from asc_client import AppStoreConnectClient

class TestAppStoreConnectClient(unittest.TestCase):
    
    def setUp(self):
        self.client = AppStoreConnectClient(
            key_id="TEST_KEY_ID",
            issuer_id="TEST_ISSUER_ID",
            mock_mode=True
        )

    def test_mock_verify_connection(self):
        res = self.client.verify_connection()
        self.assertEqual(res["status"], "connected")
        self.assertEqual(res["mode"], "mock")
        self.assertTrue(res["authenticated"])

    def test_mock_list_apps(self):
        apps = self.client.list_apps()
        self.assertIsInstance(apps, list)
        self.assertGreater(len(apps), 0)
        self.assertIn("bundleId", apps[0])

    def test_mock_inspect_version(self):
        info = self.client.inspect_version("1672348910")
        self.assertEqual(info["app_id"], "1672348910")
        self.assertEqual(info["state"], "READY_FOR_SALE")

    def test_mock_inspect_builds(self):
        builds = self.client.inspect_builds("1672348910")
        self.assertIsInstance(builds, list)
        self.assertEqual(builds[0]["processingState"], "VALID")

if __name__ == "__main__":
    unittest.main()
