#!/usr/bin/env python3
"""
Apple Native Engineer — Asset Validator Tool
Validates App Icons (1024x1024, no transparency, PNG format)
and App Store Screenshots against official device display specifications.
"""

import sys
import os
import struct
import json
import argparse
from pathlib import Path

def parse_png_info(file_path: Path) -> dict:
    """Parses PNG header and chunks without external dependencies."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with file_path.open("rb") as f:
        header = f.read(8)
        if header != b"\x89PNG\r\n\x1a\n":
            return {"valid_png": False, "error": "Not a valid PNG file (invalid signature)"}

        # Read IHDR chunk
        ihdr_len = struct.unpack(">I", f.read(4))[0]
        ihdr_type = f.read(4)
        if ihdr_type != b"IHDR" or ihdr_len < 13:
            return {"valid_png": False, "error": "Corrupt PNG IHDR chunk"}

        width, height = struct.unpack(">II", f.read(8))
        bit_depth = f.read(1)[0]
        color_type = f.read(1)[0]
        compression = f.read(1)[0]
        filter_method = f.read(1)[0]
        interlace = f.read(1)[0]
        f.read(4) # Skip CRC

        has_alpha_channel = color_type in (4, 6) # 4 = Greyscale+Alpha, 6 = RGBA
        has_trns_chunk = False
        color_profile = "Unspecified"

        # Scan subsequent chunks
        while True:
            chunk_len_bytes = f.read(4)
            if not chunk_len_bytes or len(chunk_len_bytes) < 4:
                break
            chunk_len = struct.unpack(">I", chunk_len_bytes)[0]
            chunk_type = f.read(4)
            if chunk_type == b"tRNS":
                has_trns_chunk = True
            elif chunk_type == b"sRGB":
                color_profile = "sRGB"
            elif chunk_type == b"iCCP":
                color_profile = "Embedded ICC Profile (P3/Custom)"
            elif chunk_type == b"IEND":
                break
            
            f.seek(chunk_len + 4, os.SEEK_CUR) # Skip data + CRC

        return {
            "valid_png": True,
            "width": width,
            "height": height,
            "bit_depth": bit_depth,
            "color_type": color_type,
            "has_alpha": has_alpha_channel or has_trns_chunk,
            "color_profile": color_profile
        }

def validate_app_icon(icon_path: str) -> dict:
    path = Path(icon_path).resolve()
    result = {
        "file": str(path),
        "valid": False,
        "width": 0,
        "height": 0,
        "has_alpha": False,
        "errors": [],
        "warnings": []
    }

    if not path.exists():
        result["errors"].append(f"Icon file not found: {path}")
        return result

    try:
        info = parse_png_info(path)
        if not info.get("valid_png"):
            result["errors"].append(info.get("error", "Invalid PNG"))
            return result

        result["width"] = info["width"]
        result["height"] = info["height"]
        result["has_alpha"] = info["has_alpha"]
        result["color_profile"] = info["color_profile"]

        # 1. Dimension Check (Apple requires exact 1024x1024)
        if info["width"] != 1024 or info["height"] != 1024:
            result["errors"].append(
                f"Invalid dimensions: {info['width']}x{info['height']}pt. App Store icon MUST be exactly 1024x1024pt."
            )

        # 2. Alpha Channel Check (Level 1 Requirement: Zero Alpha)
        if info["has_alpha"]:
            result["errors"].append(
                "Icon contains an alpha channel (transparency). App Store Review Guidelines mandate zero alpha transparency."
            )

        if not result["errors"]:
            result["valid"] = True

    except Exception as e:
        result["errors"].append(f"Failed to inspect icon: {e}")

    return result

def validate_screenshot(screenshot_path: str, spec_file: str = None) -> dict:
    path = Path(screenshot_path).resolve()
    result = {
        "file": str(path),
        "valid": False,
        "width": 0,
        "height": 0,
        "matched_device": None,
        "orientation": None,
        "errors": [],
        "warnings": []
    }

    if not path.exists():
        result["errors"].append(f"Screenshot file not found: {path}")
        return result

    info = parse_png_info(path)
    if not info.get("valid_png"):
        result["errors"].append(info.get("error", "Invalid PNG"))
        return result

    w, h = info["width"], info["height"]
    result["width"] = w
    result["height"] = h

    # Load specs
    if spec_file and Path(spec_file).exists():
        spec_path = Path(spec_file)
    else:
        # Default fallback to repo spec.json
        spec_path = Path(__file__).parent.parent.parent / "templates" / "screenshot-layouts" / "spec.json"

    if spec_path.exists():
        spec = json.loads(spec_path.read_text(encoding="utf-8"))
        for dev_key, dev_info in spec.get("devices", {}).items():
            dims = dev_info.get("pixel_dimensions", {})
            if "portrait" in dims and [w, h] == dims["portrait"]:
                result["matched_device"] = dev_info["display_name"]
                result["orientation"] = "portrait"
                result["valid"] = True
                break
            elif "landscape" in dims and [w, h] == dims["landscape"]:
                result["matched_device"] = dev_info["display_name"]
                result["orientation"] = "landscape"
                result["valid"] = True
                break
            elif "standard_16_10" in dims and [w, h] == dims["standard_16_10"]:
                result["matched_device"] = dev_info["display_name"]
                result["orientation"] = "landscape"
                result["valid"] = True
                break

    if not result["valid"]:
        result["errors"].append(
            f"Dimensions {w}x{h} do not match any official Apple App Store display specifications."
        )

    return result

def main():
    parser = argparse.ArgumentParser(description="Apple Native Engineer — Asset Validator")
    parser.add_argument("--icon", type=str, help="Path to app icon file to validate (must be 1024x1024 PNG without alpha)")
    parser.add_argument("--screenshot", type=str, help="Path to screenshot file to validate")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")
    args = parser.parse_args()

    if not args.icon and not args.screenshot:
        parser.print_help()
        sys.exit(1)

    reports = {}
    has_errors = False

    if args.icon:
        report = validate_app_icon(args.icon)
        reports["icon"] = report
        if not report["valid"]:
            has_errors = True

    if args.screenshot:
        report = validate_screenshot(args.screenshot)
        reports["screenshot"] = report
        if not report["valid"]:
            has_errors = True

    if args.json:
        print(json.dumps(reports, indent=2))
    else:
        for asset_type, rep in reports.items():
            print(f"==========================================================")
            print(f"  Asset Validation: {asset_type.upper()}                  ")
            print(f"==========================================================")
            print(f"File:         {rep['file']}")
            print(f"Dimensions:   {rep['width']}x{rep['height']} px")
            print(f"Status:       {'[PASS] VALID' if rep['valid'] else '[FAIL] INVALID'}")
            if rep.get("matched_device"):
                print(f"Target:       {rep['matched_device']} ({rep.get('orientation')})")
            if rep.get("has_alpha") is not None:
                print(f"Alpha/Trans:  {'[WARNING] Present' if rep['has_alpha'] else '[PASS] None'}")
            if rep["errors"]:
                print("Errors:")
                for err in rep["errors"]:
                    print(f"  ✗ {err}")
            print("==========================================================")

    sys.exit(1 if has_errors else 0)

if __name__ == "__main__":
    main()
