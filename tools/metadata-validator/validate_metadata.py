#!/usr/bin/env python3
"""
Apple Native Engineer — App Store Metadata Validator
Validates App Store metadata against Apple requirements:
Character limits, URL validity, keyword duplication, policy-sensitive terms, and missing fields.
"""

import sys
import os
import json
import re
import argparse
from urllib.parse import urlparse
from pathlib import Path

# Sensitive marketing terms often flagged during App Store Review
PROHIBITED_TERMS = [
    "best app", "free app", "#1", "top rated", "apple official",
    "award winning", "guaranteed", "cheapest"
]

def is_valid_url(url: str) -> bool:
    try:
        parsed = urlparse(url)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False

def validate_localization(locale: str, data: dict) -> dict:
    result = {
        "locale": locale,
        "valid": True,
        "errors": [],
        "warnings": [],
        "metrics": {}
    }

    name = data.get("name", "").strip()
    subtitle = data.get("subtitle", "").strip()
    description = data.get("description", "").strip()
    keywords = data.get("keywords", "").strip()
    promo = data.get("promotionalText", "").strip()
    whats_new = data.get("whatsNew", "").strip()
    privacy_url = data.get("privacyPolicyUrl", "").strip()
    support_url = data.get("supportUrl", "").strip()

    result["metrics"] = {
        "name_length": len(name),
        "subtitle_length": len(subtitle),
        "description_length": len(description),
        "keywords_length": len(keywords),
        "promotional_text_length": len(promo),
        "whats_new_length": len(whats_new)
    }

    # 1. Name Check (1-30 chars)
    if not name:
        result["errors"].append("Missing required field: 'name'.")
    elif len(name) > 30:
        result["errors"].append(f"Name exceeds 30 characters (current: {len(name)}).")

    # 2. Subtitle Check (<= 30 chars)
    if len(subtitle) > 30:
        result["errors"].append(f"Subtitle exceeds 30 characters (current: {len(subtitle)}).")

    # 3. Description Check (<= 4000 chars)
    if not description:
        result["errors"].append("Missing required field: 'description'.")
    elif len(description) > 4000:
        result["errors"].append(f"Description exceeds 4000 characters (current: {len(description)}).")

    # 4. Keywords Check (<= 100 chars, comma-separated)
    if len(keywords) > 100:
        result["errors"].append(f"Keywords string exceeds 100 characters (current: {len(keywords)}).")
    
    keyword_list = [k.strip().lower() for k in keywords.split(",") if k.strip()]
    if len(keyword_list) != len(set(keyword_list)):
        result["warnings"].append("Duplicate keywords detected in keyword string.")

    # Check for keyword repetition in title/subtitle (wasted space)
    name_words = set(re.findall(r"\w+", name.lower()))
    for kw in keyword_list:
        if kw in name_words:
            result["warnings"].append(
                f"Keyword '{kw}' is already in app name. Apple's search algorithm indexes the name automatically; repeating it wastes keyword capacity."
            )

    # 5. Promotional Text Check (<= 170 chars)
    if len(promo) > 170:
        result["errors"].append(f"Promotional text exceeds 170 characters (current: {len(promo)}).")

    # 6. What's New Check (<= 4000 chars)
    if len(whats_new) > 4000:
        result["errors"].append(f"What's New text exceeds 4000 characters (current: {len(whats_new)}).")

    # 7. URL Validation
    if not privacy_url:
        result["errors"].append("Missing required 'privacyPolicyUrl' (mandatory under Guideline 5.1.1).")
    elif not is_valid_url(privacy_url):
        result["errors"].append(f"Invalid URL format for privacyPolicyUrl: '{privacy_url}'.")

    if not support_url:
        result["errors"].append("Missing required 'supportUrl' (mandatory for App Store submission).")
    elif not is_valid_url(support_url):
        result["errors"].append(f"Invalid URL format for supportUrl: '{support_url}'.")

    # 8. Prohibited Terms Check
    combined_text = f"{name} {subtitle} {description}".lower()
    for term in PROHIBITED_TERMS:
        if term in combined_text:
            result["warnings"].append(
                f"Potentially sensitive term detected: '{term}'. Apple Review Guidelines discourage unsubstantiated claims."
            )

    if result["errors"]:
        result["valid"] = False

    return result

def validate_metadata_file(file_path: str) -> dict:
    path = Path(file_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")

    content = path.read_text(encoding="utf-8")
    data = json.loads(content)

    results = {
        "file": str(path),
        "app_id": data.get("app_id", "Not specified"),
        "version": data.get("version", "Not specified"),
        "overall_valid": True,
        "localizations": {}
    }

    localizations = data.get("localizations", {})
    if not localizations:
        results["overall_valid"] = False
        results["error"] = "No localizations declared in metadata file."
        return results

    for locale, loc_data in localizations.items():
        loc_result = validate_localization(locale, loc_data)
        results["localizations"][locale] = loc_result
        if not loc_result["valid"]:
            results["overall_valid"] = False

    return results

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer — Metadata Validator")
    parser.add_argument("file", help="Path to metadata JSON file")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    try:
        report = validate_metadata_file(args.file)
        if args.json:
            print(json.dumps(report, indent=2))
        else:
            print("==========================================================")
            print("  Apple Native Engineer — App Store Metadata Report       ")
            print("==========================================================")
            print(f"File:         {report['file']}")
            print(f"App ID:       {report['app_id']} (Version: {report['version']})")
            print(f"Readiness:    {'[PASS] READY' if report['overall_valid'] else '[FAIL] ACTION REQUIRED'}")
            print("----------------------------------------------------------")
            for locale, loc in report["localizations"].items():
                print(f"Locale: [{locale}] - {'VALID' if loc['valid'] else 'INVALID'}")
                print(f"  Name: {loc['metrics']['name_length']}/30 chars | Subtitle: {loc['metrics']['subtitle_length']}/30 chars")
                print(f"  Keywords: {loc['metrics']['keywords_length']}/100 chars | Description: {loc['metrics']['description_length']}/4000 chars")
                if loc["errors"]:
                    print("  Errors:")
                    for err in loc["errors"]:
                        print(f"    ✗ {err}")
                if loc["warnings"]:
                    print("  Warnings / Tips:")
                    for w in loc["warnings"]:
                        print(f"    ⚠ {w}")
            print("==========================================================")

        sys.exit(0 if report["overall_valid"] else 1)
    except Exception as e:
        print(f"Validation error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
