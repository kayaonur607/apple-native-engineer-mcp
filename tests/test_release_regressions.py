"""Release decisions must agree with findings and optional feature coverage."""
import shutil
import tempfile
import unittest
from pathlib import Path
from support import CLEAN, codes, run_tool


class ReleaseRegressionTests(unittest.TestCase):
    def test_app_without_widgets_is_not_an_uninspected_failure(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / 'app'
            shutil.copytree(CLEAN, root)
            shutil.rmtree(root / 'Widgets')
            report = run_tool('release-readiness/generate_report.py', str(root),
                              '--metadata', str(root / 'metadata.json'),
                              '--icon', str(root / 'Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png'),
                              expect=0)
            self.assertEqual(report['status'], 'pass')
            self.assertEqual(report['data']['verdict'], 'CONFIGURED STATIC CHECKS PASSED')
            self.assertNotIn('REL001', codes(report))
            widget = next(g for g in report['data']['gates'] if g['gate'] == 'widgets')
            self.assertEqual(widget['status'], 'not_applicable')
            self.assertEqual(widget['earned'], 0)
            self.assertFalse(widget['applicable'])
            self.assertEqual(report['data']['applicable_weight'], 90)
            self.assertIn('static', report['data']['scope'])

    def test_missing_required_inputs_still_block(self):
        report = run_tool('release-readiness/generate_report.py', str(CLEAN), expect=2)
        self.assertEqual(report['data']['verdict'], 'BLOCKED')
        self.assertIn('REL001', codes(report))
