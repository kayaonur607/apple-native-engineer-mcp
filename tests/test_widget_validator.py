import unittest
import tempfile
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent / "tools" / "widget-validator"))
from validate_widget import audit_widgets

class TestWidgetValidator(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.project_path = Path(self.test_dir.name)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_missing_live_activity_flag_detection(self):
        # Code defines ActivityAttributes but no Info.plist has NSSupportsLiveActivities
        swift_code = """
        import ActivityKit
        import WidgetKit
        struct PizzaDeliveryAttributes: ActivityAttributes {
            struct ContentState: Codable, Hashable { var progress: Double }
        }
        """
        swift_file = self.project_path / "PizzaWidget.swift"
        swift_file.write_text(swift_code, encoding="utf-8")

        result = audit_widgets(self.project_path)
        self.assertTrue(result["hasLiveActivities"])
        self.assertFalse(result["liveActivitiesPlistConfigured"])
        self.assertTrue(any(f["type"] == "MissingLiveActivitiesPlistFlag" for f in result["findings"]))

    def test_incomplete_dynamic_island(self):
        swift_code = """
        import WidgetKit
        import SwiftUI
        struct MyWidget: Widget {
            var body: some WidgetConfiguration {
                ActivityConfiguration(for: PizzaDeliveryAttributes.self) { context in
                    Text("Lock Screen")
                } dynamicIsland: { context in
                    DynamicIsland {
                        // Missing minimal & compact states
                    }
                }
            }
        }
        """
        swift_file = self.project_path / "IncompleteWidget.swift"
        swift_file.write_text(swift_code, encoding="utf-8")

        result = audit_widgets(self.project_path)
        self.assertTrue(result["hasDynamicIsland"])
        self.assertTrue(any(f["type"] == "IncompleteDynamicIslandCompactState" for f in result["findings"]))

if __name__ == "__main__":
    unittest.main()
