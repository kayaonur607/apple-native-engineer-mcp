#!/usr/bin/env python3
"""
Unit tests for tools/asset-validator
"""

import unittest
import sys
import struct
import tempfile
from pathlib import Path

TOOLS_DIR = Path(__file__).parent.parent / "tools" / "asset-validator"
sys.path.insert(0, str(TOOLS_DIR))
from validate_assets import validate_app_icon, validate_screenshot, parse_png_info

def create_mock_png(width: int, height: int, has_alpha: bool = False) -> bytes:
    """Constructs minimal valid PNG byte buffer for testing dimensions & alpha."""
    header = b"\x89PNG\r\n\x1a\n"
    # IHDR: width(4), height(4), depth(1)=8, color_type(1), comp(1)=0, filter(1)=0, interlace(1)=0
    color_type = 6 if has_alpha else 2 # 6=RGBA, 2=RGB
    ihdr_data = struct.pack(">IIBBBBB", width, height, 8, color_type, 0, 0, 0)
    ihdr_chunk = struct.pack(">I", len(ihdr_data)) + b"IHDR" + ihdr_data + b"\x00\x00\x00\x00"
    iend_chunk = struct.pack(">I", 0) + b"IEND" + b"\xae\x42\x60\x82"
    return header + ihdr_chunk + iend_chunk

class TestAssetValidator(unittest.TestCase):
    
    def test_valid_app_icon(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(create_mock_png(1024, 1024, has_alpha=False))
            tmp_path = Path(tmp.name)

        try:
            res = validate_app_icon(str(tmp_path))
            self.assertTrue(res["valid"])
            self.assertEqual(res["width"], 1024)
            self.assertEqual(res["height"], 1024)
            self.assertFalse(res["has_alpha"])
        finally:
            tmp_path.unlink()

    def test_app_icon_with_alpha_fails(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(create_mock_png(1024, 1024, has_alpha=True))
            tmp_path = Path(tmp.name)

        try:
            res = validate_app_icon(str(tmp_path))
            self.assertFalse(res["valid"])
            self.assertTrue(any("alpha channel" in err for err in res["errors"]))
        finally:
            tmp_path.unlink()

    def test_app_icon_wrong_dimensions(self):
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(create_mock_png(512, 512, has_alpha=False))
            tmp_path = Path(tmp.name)

        try:
            res = validate_app_icon(str(tmp_path))
            self.assertFalse(res["valid"])
            self.assertTrue(any("Invalid dimensions" in err for err in res["errors"]))
        finally:
            tmp_path.unlink()

    def test_valid_screenshot_dimensions(self):
        # 1290x2796 is iPhone 6.7" portrait
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            tmp.write(create_mock_png(1290, 2796, has_alpha=False))
            tmp_path = Path(tmp.name)

        try:
            res = validate_screenshot(str(tmp_path))
            self.assertTrue(res["valid"])
            self.assertEqual(res["orientation"], "portrait")
        finally:
            tmp_path.unlink()

if __name__ == "__main__":
    unittest.main()
