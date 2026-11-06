#!/usr/bin/env python3
"""Read an existing xcresult bundle without building, uploading or changing it.

Output is the shared report envelope. This optional CLI does not claim to be an
MCP tool or to change the static release gate. Requires Xcode's xcresulttool.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools/lib'))
from apple_native.report import Report


def summarize(payload: dict, target: str) -> Report:
    report = Report(tool='xcode-test-evidence', target=target, version='1.0.0')
    keys = ('totalTestCount', 'passedTests', 'failedTests', 'skippedTests', 'expectedFailures')
    counts = {key: payload.get(key) for key in keys}
    if any(type(value) is not int or value < 0 for value in counts.values()):
        report.error('XCT001', 'Unsupported xcresult summary: test counts must be non-negative integers.')
        return report
    report.data = {'source': 'xcresulttool get test-results summary', 'counts': counts,
                   'result': payload.get('result'),
                   'scope': 'Recorded test execution only. No signing, App Review approval or UI journey certification.'}
    if counts['failedTests'] or payload.get('result') != 'Passed':
        report.error('XCT002', 'The recorded test run did not pass.')
    if counts['passedTests'] == 0:
        report.error('XCT003', 'No passing tests were recorded; an empty or skipped suite is not evidence of success.')
    if sum(counts[k] for k in keys[1:]) != counts['totalTestCount']:
        report.error('XCT004', 'Test counts are inconsistent; review the xcresult schema before trusting this summary.')
    if counts['skippedTests'] or counts['expectedFailures']:
        report.warn('XCT005', 'Some tests were skipped or recorded as expected failures; review coverage.')
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('path', type=Path, help='Existing .xcresult bundle')
    args = parser.parse_args(argv)
    report = Report(tool='xcode-test-evidence', target=str(args.path), version='1.0.0')
    if not args.path.is_dir() or args.path.suffix != '.xcresult':
        report.error('XCT000', 'Provide an existing .xcresult directory.')
    else:
        try:
            process = subprocess.run(['xcrun', 'xcresulttool', 'get', 'test-results', 'summary',
                                      '--path', str(args.path.resolve()), '--compact'],
                                     capture_output=True, text=True, timeout=60, check=True)
            payload = json.loads(process.stdout)
            if not isinstance(payload, dict):
                raise ValueError('summary is not an object')
            report = summarize(payload, str(args.path.resolve()))
        except (OSError, subprocess.SubprocessError, ValueError):
            report.error('XCT000', 'Could not read the result bundle. Check Xcode selection and xcresulttool compatibility.')
    print(report.to_json())
    return report.exit_code(strict=True)


if __name__ == '__main__':
    raise SystemExit(main())
