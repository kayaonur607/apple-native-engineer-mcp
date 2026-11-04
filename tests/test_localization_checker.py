import unittest
import tempfile
import json
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "localization-checker"))
from check_localization import scan_swift_files, inspect_string_catalogs

class TestLocalizationChecker(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_directional_padding_detection(self):
        swift_code = """
        import SwiftUI
        struct ContentView: View {
            var body: some View {
                Text("Hello")
                    .padding(.left, 20)
            }
        }
        """
        swift_file = self.project_path / "ContentView.swift"
        swift_file.write_text(swift_code, encoding="utf-8")

        findings, count = scan_swift_files(self.project_path)
        self.assertEqual(count, 1)
        self.assertTrue(any(f["type"] == "DirectionalLayoutIssue" for f in findings))

    def test_string_catalog_parsing(self):
        catalog = {
            "sourceLanguage": "en",
            "strings": {
                "submit_btn": {
                    "extractionState": "manual",
                    "localizations": {
                        "de": {
                            "stringUnit": {
                                "state": "needs_review",
                                "value": "Senden"
                            }
                        }
                    }
                }
            },
            "version": "1.0"
        }
        cat_file = self.project_path / "Localizable.xcstrings"
        cat_file.write_text(json.dumps(catalog), encoding="utf-8")

        findings, stats = inspect_string_catalogs(self.project_path)
        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0]["type"], "PendingTranslation")

if __name__ == "__main__":
    unittest.main()
