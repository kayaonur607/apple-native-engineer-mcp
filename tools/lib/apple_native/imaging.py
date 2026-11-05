"""Minimal, dependency-free image header reader.

App Store rejection reasons are usually structural: wrong pixel dimensions, an
alpha channel on the 1024x1024 marketing icon, or the wrong colour space. None
of that requires decoding pixels, so this module only parses headers — which
keeps the toolkit installable with nothing but ``python3``.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional, Tuple

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

#: PNG colour types -> (name, has alpha channel)
PNG_COLOR_TYPES = {
    0: ("grayscale", False),
    2: ("truecolour", False),
    3: ("indexed", True),
    4: ("grayscale+alpha", True),
    6: ("truecolour+alpha", True),
}

#: App Store Connect screenshot slots (portrait), pixel sizes accepted as of 2026.
SCREENSHOT_SPECS: Dict[str, Dict[str, Tuple[Tuple[int, int], ...]]] = {
    'iPhone 6.9"': {
        "portrait": ((1320, 2868), (1290, 2796)),
        "landscape": ((2868, 1320), (2796, 1290)),
    },
    'iPhone 6.7"': {
        "portrait": ((1290, 2796),),
        "landscape": ((2796, 1290),),
    },
    'iPhone 6.5"': {
        "portrait": ((1242, 2688), (1284, 2778)),
        "landscape": ((2688, 1242), (2778, 1284)),
    },
    'iPhone 5.5"': {
        "portrait": ((1242, 2208),),
        "landscape": ((2208, 1242),),
    },
    'iPad 13"': {
        "portrait": ((2064, 2752), (2048, 2732)),
        "landscape": ((2752, 2064), (2732, 2048)),
    },
    'Apple Watch Ultra': {
        "portrait": ((410, 502),),
        "landscape": ((502, 410),),
    },
    'Apple Watch Series 10/11': {
        "portrait": ((416, 496),),
        "landscape": ((496, 416),),
    },
    "Apple Vision Pro": {
        "portrait": ((3840, 2160),),
        "landscape": ((3840, 2160),),
    },
    "Mac": {
        "portrait": ((2880, 1800), (2560, 1600), (1440, 900), (1280, 800), (3840, 2160)),
        "landscape": ((2880, 1800), (2560, 1600), (1440, 900), (1280, 800), (3840, 2160)),
    },
}


@dataclass
class ImageInfo:
    path: Path
    format: str
    width: int
    height: int
    bit_depth: int = 8
    color_type: Optional[int] = None
    has_alpha: bool = False
    interlaced: bool = False
    color_profile: Optional[str] = None

    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)

    def as_dict(self) -> Dict[str, object]:
        return {
            "file": self.path.name,
            "format": self.format,
            "width": self.width,
            "height": self.height,
            "bit_depth": self.bit_depth,
            "color_type": self.color_type,
            "has_alpha": self.has_alpha,
            "interlaced": self.interlaced,
            "color_profile": self.color_profile,
        }


class UnsupportedImage(Exception):
    pass


def png_info(path: Path) -> ImageInfo:
    with path.open("rb") as handle:
        header = handle.read(33)
    if len(header) < 33 or not header.startswith(PNG_SIGNATURE):
        raise UnsupportedImage(f"{path.name} is not a PNG file")

    width, height = struct.unpack(">II", header[16:24])
    bit_depth = header[24]
    color_type = header[25]
    interlace = header[28]
    _, has_alpha = PNG_COLOR_TYPES.get(color_type, ("unknown", True))

    # tRNS chunk makes an otherwise alpha-less PNG partially transparent.
    if color_type in (0, 2):
        with path.open("rb") as handle:
            handle.read(8)
            while True:
                length_bytes = handle.read(4)
                if len(length_bytes) < 4:
                    break
                length = struct.unpack(">I", length_bytes)[0]
                chunk_type = handle.read(4)
                if chunk_type == b"tRNS":
                    has_alpha = True
                    break
                if chunk_type in (b"IDAT", b"IEND"):
                    break
                handle.seek(length + 4, 1)

    return ImageInfo(
        path=path,
        format="PNG",
        width=width,
        height=height,
        bit_depth=bit_depth,
        color_type=color_type,
        has_alpha=has_alpha,
        interlaced=interlace == 1,
    )


def jpeg_info(path: Path) -> ImageInfo:
    with path.open("rb") as handle:
        if handle.read(2) != b"\xff\xd8":
            raise UnsupportedImage(f"{path.name} is not a JPEG file")
        while True:
            marker = handle.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                raise UnsupportedImage(f"{path.name}: truncated JPEG")
            code = marker[1]
            if code in (0xD8, 0xD9):
                continue
            length_bytes = handle.read(2)
            if len(length_bytes) < 2:
                raise UnsupportedImage(f"{path.name}: truncated JPEG")
            length = struct.unpack(">H", length_bytes)[0]
            if 0xC0 <= code <= 0xCF and code not in (0xC4, 0xC8, 0xCC):
                data = handle.read(5)
                height, width = struct.unpack(">HH", data[1:5])
                return ImageInfo(path=path, format="JPEG", width=width, height=height)
            handle.seek(length - 2, 1)


def image_info(path: Path) -> ImageInfo:
    with path.open("rb") as handle:
        magic = handle.read(8)
    if magic.startswith(PNG_SIGNATURE):
        return png_info(path)
    if magic[:2] == b"\xff\xd8":
        return jpeg_info(path)
    raise UnsupportedImage(f"{path.name}: unsupported image format (expected PNG or JPEG)")


def match_screenshot_spec(width: int, height: int) -> Optional[Tuple[str, str]]:
    """Return ``(device_slot, orientation)`` for a known App Store screenshot size."""

    for device, orientations in SCREENSHOT_SPECS.items():
        for orientation, sizes in orientations.items():
            if (width, height) in sizes:
                return device, orientation
    return None


def closest_screenshot_slots(width: int, height: int, limit: int = 3):
    """Rank known slots by how far they are from the given size (for hints)."""

    target = (width, height)
    scored = []
    for device, orientations in SCREENSHOT_SPECS.items():
        for orientation, sizes in orientations.items():
            for size in sizes:
                distance = abs(size[0] - target[0]) + abs(size[1] - target[1])
                scored.append((distance, device, orientation, size))
    scored.sort(key=lambda item: item[0])
    return scored[:limit]
