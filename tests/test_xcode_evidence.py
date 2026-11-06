"""Contract tests for the optional xcresult adapter; no simulated device claims."""
import importlib.util
from pathlib import Path
import unittest
from unittest.mock import patch
from support import REPO_ROOT

spec = importlib.util.spec_from_file_location('xcode_evidence', REPO_ROOT / 'scripts/collect_xcode_evidence.py')
evidence = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evidence)


class XcodeEvidenceTests(unittest.TestCase):
    def payload(self, **changes):
        return dict(totalTestCount=2, passedTests=2, failedTests=0, skippedTests=0,
                    expectedFailures=0, result='Passed', **changes)

    def test_passed_execution(self):
        self.assertEqual(evidence.summarize(self.payload(), 'app.xcresult').status, 'pass')

    def test_empty_and_skipped_runs_do_not_pass(self):
        for counts in [dict(totalTestCount=0, passedTests=0),
                       dict(passedTests=0, skippedTests=2)]:
            payload = self.payload()
            payload.update(counts)
            self.assertEqual(evidence.summarize(payload, 'app.xcresult').status, 'fail')

    def test_failures_and_malformed_counts_do_not_pass(self):
        for changes in [dict(passedTests=1, failedTests=1, result='Failed'),
                        dict(totalTestCount=99), dict(passedTests=True), dict(result='unknown')]:
            payload = self.payload()
            payload.update(changes)
            self.assertEqual(evidence.summarize(payload, 'app.xcresult').status, 'fail')

    def test_missing_bundle_fails_without_starting_a_process(self):
        with patch.object(evidence.subprocess, 'run') as run, patch('builtins.print'):
            self.assertEqual(evidence.main([str(REPO_ROOT / 'missing.xcresult')]), 2)
            run.assert_not_called()
