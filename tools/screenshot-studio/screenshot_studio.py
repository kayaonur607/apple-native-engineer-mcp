#!/usr/bin/env python3
"""
Apple Native Engineer — Screenshot Studio Tool
Manages App Store screenshot workflows:
- Validates screenshot sets against official display specs.
- Captures screenshots from active iOS/iPadOS simulators using xcrun simctl.
- Organizes export folders by device and locale.
"""

import sys
import os
import json
import shutil
import subprocess
import argparse
from pathlib import Path

# Add asset validator to path
sys.path.insert(0, str(Path(__file__).parent.parent / "asset-validator"))
from validate_assets import validate_screenshot

def capture_simulator_screenshot(output_path: str) -> dict:
    dest = Path(output_path).resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Check if xcrun is available (macOS only)
    if shutil.which("xcrun") is None:
        return {
            "success": False,
            "error": "'xcrun' is not available. Simulator screenshot capture requires macOS with Xcode Command Line Tools installed."
        }

    try:
        cmd = ["xcrun", "simctl", "io", "booted", "screenshot", str(dest)]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            return {
                "success": False,
                "error": f"xcrun simctl failed: {proc.stderr.strip()}"
            }
        
        # Validate captured screenshot
        val_result = validate_screenshot(str(dest))
        return {
            "success": True,
            "file": str(dest),
            "validation": val_result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

def audit_screenshot_directory(dir_path: str) -> dict:
    root = Path(dir_path).resolve()
    if not root.exists():
        raise FileNotFoundError(f"Screenshot directory not found: {dir_path}")

    images = list(root.glob("**/*.png")) + list(root.glob("**/*.jpg")) + list(root.glob("**/*.jpeg"))
    results = {
        "directory": str(root),
        "total_images": len(images),
        "valid_count": 0,
        "invalid_count": 0,
        "device_breakdown": {},
        "files": []
    }

    for img in images:
        val = validate_screenshot(str(img))
        results["files"].append(val)
        if val["valid"]:
            results["valid_count"] += 1
            dev = val.get("matched_device", "Unknown")
            results["device_breakdown"][dev] = results["device_breakdown"].get(dev, 0) + 1
        else:
            results["invalid_count"] += 1

    return results

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer — Screenshot Studio")
    parser.add_argument("--capture", type=str, help="Capture screenshot from booted iOS Simulator and save to specified file path")
    parser.add_argument("--audit", type=str, help="Audit a folder of screenshots against App Store specifications")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if not args.capture and not args.audit:
        parser.print_help()
        sys.exit(0)

    if args.capture:
        res = capture_simulator_screenshot(args.capture)
        if args.json:
            print(json.dumps(res, indent=2))
        else:
            if res["success"]:
                print(f"✓ Screenshot captured successfully: {res['file']}")
                val = res.get("validation", {})
                if val.get("valid"):
                    print(f"  Matched Device: {val.get('matched_device')} ({val.get('width')}x{val.get('height')} px)")
                else:
                    print(f"  ⚠ Warning: {', '.join(val.get('errors', []))}")
            else:
                print(f"✗ Failed to capture screenshot: {res['error']}", file=sys.stderr)
                sys.exit(1)

    elif args.audit:
        rep = audit_screenshot_directory(args.audit)
        if args.json:
            print(json.dumps(rep, indent=2))
        else:
            print("==========================================================")
            print("  Apple Native Engineer — Screenshot Set Audit            ")
            print("==========================================================")
            print(f"Directory:    {rep['directory']}")
            print(f"Total Images: {rep['total_images']}")
            print(f"Valid:        {rep['valid_count']} | Invalid: {rep['invalid_count']}")
            print("Device Breakdown:")
            for dev, count in rep["device_breakdown"].items():
                print(f"  • {dev}: {count} image(s)")
            print("==========================================================")
            if rep["invalid_count"] > 0:
                sys.exit(1)

if __name__ == "__main__":
    main()
