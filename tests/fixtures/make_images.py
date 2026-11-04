#!/usr/bin/env python3
"""Generate the binary image fixtures used by the test suite.

Committing tiny generated PNGs keeps the tests hermetic: no network, no Pillow,
no checked-in megabytes. Run this only when a fixture needs to change::

    python3 tests/fixtures/make_images.py
"""

from __future__ import annotations

import struct
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent


def write_png(path: Path, width: int, height: int, rgb: tuple[int, int, int],
              alpha: int | None = None) -> None:
    """Write a solid-colour PNG. ``alpha`` adds an RGBA colour type."""

    colour_type = 6 if alpha is not None else 2
    channels = 4 if alpha is not None else 3
    pixel = bytes(rgb) + (bytes([alpha]) if alpha is not None else b"")
    row = b"\x00" + pixel * width
    raw = row * height

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (
            struct.pack(">I", len(payload))
            + kind
            + payload
            + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", width, height, 8, colour_type, 0, 0, 0)
    idat = zlib.compress(raw, 9)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", idat) + chunk(b"IEND", b"")
    )
    print(f"wrote {path.relative_to(HERE)} ({width}x{height}, {channels} channels)")


def main() -> None:
    # Deliberately invalid: 512x512 with an alpha channel where 1024x1024 opaque
    # is required.
    write_png(
        HERE / "legacy-app" / "Assets.xcassets" / "AppIcon.appiconset" / "AppIcon-512.png",
        512, 512, (14, 122, 254), alpha=255,
    )

    # Valid marketing icon: exactly 1024x1024, RGB, no alpha channel.
    write_png(
        HERE / "clean-app" / "Assets.xcassets" / "AppIcon.appiconset" / "AppIcon-1024.png",
        1024, 1024, (10, 132, 255),
    )

    # Valid App Store screenshot slot (iPhone 6.9").
    write_png(
        HERE / "clean-app" / "screenshots" / "home.png",
        1320, 2868, (248, 248, 250),
    )
    write_png(
        HERE / "clean-app" / "screenshots" / "detail.png",
        1320, 2868, (32, 32, 34),
    )
    write_png(
        HERE / "clean-app" / "screenshots" / "settings.png",
        1320, 2868, (242, 242, 247),
    )


if __name__ == "__main__":
    main()
