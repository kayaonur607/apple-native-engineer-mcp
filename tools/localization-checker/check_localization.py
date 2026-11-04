#!/usr/bin/env python3
"""
Apple Native Engineer — Localization Checker
Scans Apple platform projects for hardcoded UI strings, directional layout anti-patterns,
and String Catalog (.xcstrings) completeness.
"""

import os
import sys
import json
import re
import argparse
from pathlib import Path

# Patterns indicating hardcoded strings in SwiftUI views
HARDCODED_TEXT_PATTERN = re.compile(r'\b(Text|Button|Label|NavigationTitle)\s*\(\s*"([^"]+)"\s*\)')
DIRECTIONAL_PADDING_PATTERN = re.compile(r'\.padding\s*\(\s*\.(left|right)\b')
ALIGNMENT_PATTERN = re.compile(r'\b(TextAlignment|\.alignment)\s*:\s*\.(leading|trailing|center|left|right)\b')

def scan_swift_files(project_dir: Path):
    findings = []
    swift_files = list(project_dir.glob("**/*.swift"))

    for file_path in swift_files:
        # Ignore build or test fixture directories
        if any(part in file_path.parts for part in [".build", "DerivedData", "Pods", "Carthage"]):
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
        except Exception:
            continue

        rel_path = str(file_path.relative_to(project_dir))

        for idx, line in enumerate(lines, start=1):
            # Check for non-RTL padding (.left / .right)
            pad_match = DIRECTIONAL_PADDING_PATTERN.search(line)
            if pad_match:
                direction = pad_match.group(1)
                findings.append({
                    "file": rel_path,
                    "line": idx,
                    "severity": "High",
                    "type": "DirectionalLayoutIssue",
                    "message": f"Found non-adaptive '.padding(.{direction})'. Use '.leading' or '.trailing' for RTL mirroring."
                })

            # Check for hardcoded UI strings that should be localized
            # Filter out SF Symbol names or technical keys
            for match in HARDCODED_TEXT_PATTERN.finditer(line):
                element = match.group(1)
                text = match.group(2)
                # Ignore system symbol identifiers or empty strings
                if len(text.strip()) > 1 and not text.startswith("systemImage:"):
                    findings.append({
                        "file": rel_path,
                        "line": idx,
                        "severity": "Medium",
                        "type": "UnlocalizedStringLiteral",
                        "message": f"Hardcoded string \"{text}\" in {element}(). Consider String Catalog localization."
                    })

    return findings, len(swift_files)

def inspect_string_catalogs(project_dir: Path):
    catalog_findings = []
    xcstrings_files = list(project_dir.glob("**/*.xcstrings"))
    catalog_stats = {}

    for cat_path in xcstrings_files:
        rel_path = str(cat_path.relative_to(project_dir))
        try:
            with open(cat_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            catalog_findings.append({
                "file": rel_path,
                "line": 1,
                "severity": "Critical",
                "type": "InvalidStringCatalog",
                "message": f"Failed to parse JSON in String Catalog: {e}"
            })
            continue

        source_lang = data.get("sourceLanguage", "en")
        strings = data.get("strings", {})
        total_keys = len(strings)
        untranslated_count = 0

        for key, details in strings.items():
            localizations = details.get("localizations", {})
            for lang, loc_data in localizations.items():
                unit = loc_data.get("stringUnit", {})
                state = unit.get("state", "")
                if state in ["new", "needs_review"]:
                    untranslated_count += 1
                    catalog_findings.append({
                        "file": rel_path,
                        "line": 1,
                        "severity": "Medium",
                        "type": "PendingTranslation",
                        "message": f"String key '{key}' has pending translation state '{state}' for language '{lang}'."
                    })

        catalog_stats[rel_path] = {
            "sourceLanguage": source_lang,
            "totalKeys": total_keys,
            "untranslatedKeys": untranslated_count
        }

    return catalog_findings, catalog_stats

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer Localization Checker")
    parser.add_argument("--project-dir", default=".", help="Path to project directory")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Error: Project directory '{project_dir}' not found.", file=sys.stderr)
        sys.exit(1)

    code_findings, swift_count = scan_swift_files(project_dir)
    catalog_findings, catalog_stats = inspect_string_catalogs(project_dir)

    all_findings = code_findings + catalog_findings
    criticals = [f for f in all_findings if f["severity"] == "Critical"]
    highs = [f for f in all_findings if f["severity"] == "High"]
    mediums = [f for f in all_findings if f["severity"] == "Medium"]

    result_data = {
        "status": "PASS" if not criticals and not highs else "WARNING" if not criticals else "FAIL",
        "totalSwiftFilesScanned": swift_count,
        "stringCatalogs": catalog_stats,
        "summary": {
            "critical": len(criticals),
            "high": len(highs),
            "medium": len(mediums),
            "totalIssues": len(all_findings)
        },
        "findings": all_findings
    }

    if args.json:
        print(json.dumps(result_data, indent=2))
        sys.exit(0 if not criticals else 1)

    print("=" * 60)
    print("🌍 Apple Native Engineer — Localization Audit")
    print("=" * 60)
    print(f"Directory:          {project_dir}")
    print(f"Swift Files:        {swift_count}")
    print(f"String Catalogs:    {len(catalog_stats)}")
    print(f"Status:             {result_data['status']}")
    print("-" * 60)
    print(f"Critical: {len(criticals)} | High: {len(highs)} | Medium: {len(mediums)}")
    print("=" * 60)

    if all_findings:
        print("\nFindings:")
        for idx, item in enumerate(all_findings, start=1):
            print(f"[{idx}] [{item['severity'].upper()}] {item['file']}:{item['line']} - {item['type']}")
            print(f"    {item['message']}")
    else:
        print("\n✅ Zero localization issues detected. RTL layout and string management are optimal.")

    sys.exit(0 if not criticals else 1)

if __name__ == "__main__":
    main()
