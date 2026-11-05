#!/usr/bin/env python3
"""Icon Studio — turn one master PNG into a complete, valid AppIcon set.

The workflow Apple expects is: design at 1024×1024, let the toolchain produce the
sizes, ship an asset catalogue. This tool performs that step locally, with the
standard library only — a real box-filter downscale, a correct PNG encoder, and a
`Contents.json` Xcode accepts — so an agent can produce shippable assets without
an image SDK.

It refuses to guess: the master must be 1024×1024, PNG, and free of alpha, which
is exactly what App Store Connect enforces.

Usage::

    python3 tools/icon-studio/icon_studio.py prepare AppIcon-1024.png --out Assets.xcassets/AppIcon.appiconset
    python3 tools/icon-studio/icon_studio.py verify Assets.xcassets/AppIcon.appiconset
    python3 tools/icon-studio/icon_studio.py preview AppIcon-1024.png --at 120 --out /tmp/preview.png
"""

from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Dict, List, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import emit
from apple_native.imaging import UnsupportedImage, image_info
from apple_native.report import Report

MASTER_SIZE = (1024, 1024)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

#: Slots Xcode expects for a universal iOS app icon. (idiom, size in points, scale)
SLOTS: List[Tuple[str, int, int]] = [
    ("iphone", 20, 2), ("iphone", 20, 3),
    ("iphone", 29, 2), ("iphone", 29, 3),
    ("iphone", 40, 2), ("iphone", 40, 3),
    ("iphone", 60, 2), ("iphone", 60, 3),
    ("ipad", 20, 1), ("ipad", 20, 2),
    ("ipad", 29, 1), ("ipad", 29, 2),
    ("ipad", 40, 1), ("ipad", 40, 2),
    ("ipad", 76, 1), ("ipad", 76, 2),
    ("ipad", 83.5, 2),
    ("ios-marketing", 1024, 1),
]


class IconError(RuntimeError):
    pass


# --------------------------------------------------------------------------- #
# PNG codec (8-bit RGB / RGBA, non-interlaced)
# --------------------------------------------------------------------------- #


class Bitmap:
    def __init__(self, width: int, height: int, pixels: bytearray) -> None:
        self.width = width
        self.height = height
        self.pixels = pixels  # RGB triplets, row-major

    def row(self, y: int) -> memoryview:
        start = y * self.width * 3
        return memoryview(self.pixels)[start:start + self.width * 3]


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    return b if pb <= pc else c


def decode_png(path: Path) -> Bitmap:
    data = path.read_bytes()
    if not data.startswith(PNG_SIGNATURE):
        raise IconError(f"{path.name} is not a PNG file")

    offset = 8
    width = height = bit_depth = color_type = interlace = 0
    idat = bytearray()
    while offset < len(data):
        length = struct.unpack(">I", data[offset:offset + 4])[0]
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:offset + 8 + length]
        offset += 12 + length
        if kind == b"IHDR":
            width, height, bit_depth, color_type, _, _, interlace = struct.unpack(">IIBBBBB", payload)
        elif kind == b"IDAT":
            idat.extend(payload)
        elif kind == b"IEND":
            break

    if bit_depth != 8:
        raise IconError(f"{path.name}: only 8-bit PNGs are supported (found {bit_depth})")
    if interlace:
        raise IconError(f"{path.name}: interlaced PNGs are not supported — re-export without interlacing")
    channels = {2: 3, 6: 4, 0: 1}.get(color_type)
    if channels is None:
        raise IconError(f"{path.name}: unsupported PNG colour type {color_type} (use RGB or RGBA)")

    raw = zlib.decompress(bytes(idat))
    stride = width * channels
    out = bytearray(width * height * 3)
    previous = bytearray(stride)
    position = 0
    for y in range(height):
        filter_type = raw[position]
        position += 1
        line = bytearray(raw[position:position + stride])
        position += stride
        if filter_type == 1:
            for i in range(channels, stride):
                line[i] = (line[i] + line[i - channels]) & 0xFF
        elif filter_type == 2:
            for i in range(stride):
                line[i] = (line[i] + previous[i]) & 0xFF
        elif filter_type == 3:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                line[i] = (line[i] + ((left + previous[i]) >> 1)) & 0xFF
        elif filter_type == 4:
            for i in range(stride):
                left = line[i - channels] if i >= channels else 0
                up_left = previous[i - channels] if i >= channels else 0
                line[i] = (line[i] + _paeth(left, previous[i], up_left)) & 0xFF
        elif filter_type != 0:
            raise IconError(f"{path.name}: unknown PNG filter {filter_type}")
        previous = line
        base = y * width * 3
        if channels == 3:
            out[base:base + width * 3] = line
        else:
            for x in range(width):
                source = x * channels
                target = base + x * 3
                out[target:target + 3] = line[source:source + 3]
    return Bitmap(width, height, out)


def encode_png(bitmap: Bitmap) -> bytes:
    raw = bytearray()
    for y in range(bitmap.height):
        raw.append(0)
        raw.extend(bitmap.row(y))

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return (struct.pack(">I", len(payload)) + kind + payload
                + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF))

    header = struct.pack(">IIBBBBB", bitmap.width, bitmap.height, 8, 2, 0, 0, 0)
    return (PNG_SIGNATURE + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(bytes(raw), 9))
            + chunk(b"IEND", b""))


def resize(bitmap: Bitmap, width: int) -> Bitmap:
    """Box-filter downscale. Integer-friendly and free of ringing artefacts."""

    if width > bitmap.width:
        raise IconError(f"cannot upscale {bitmap.width}px to {width}px; start from a 1024px master")
    if width == bitmap.width:
        return Bitmap(bitmap.width, bitmap.height, bytearray(bitmap.pixels))
    height = width
    scale = bitmap.width / width
    out = bytearray(width * height * 3)
    for y in range(height):
        y0 = int(y * scale)
        y1 = max(y0 + 1, int((y + 1) * scale))
        for x in range(width):
            x0 = int(x * scale)
            x1 = max(x0 + 1, int((x + 1) * scale))
            r = g = b = 0
            count = 0
            for sy in range(y0, min(y1, bitmap.height)):
                row = bitmap.row(sy)
                for sx in range(x0, min(x1, bitmap.width)):
                    offset = sx * 3
                    r += row[offset]
                    g += row[offset + 1]
                    b += row[offset + 2]
                    count += 1
            count = max(count, 1)
            target = (y * width + x) * 3
            out[target] = r // count
            out[target + 1] = g // count
            out[target + 2] = b // count
    return Bitmap(width, height, out)


# --------------------------------------------------------------------------- #
# Operations
# --------------------------------------------------------------------------- #


def slot_filename(idiom: str, points: float, scale: int) -> str:
    size = f"{points:g}"
    return f"AppIcon-{idiom}-{size}@{scale}x.png"


def contents_json(slots: List[Tuple[str, float, int]]) -> Dict[str, object]:
    images = []
    for idiom, points, scale in slots:
        images.append({
            "filename": slot_filename(idiom, points, scale),
            "idiom": idiom,
            "scale": f"{scale}x",
            "size": f"{points:g}x{points:g}",
        })
    return {"images": images, "info": {"author": "icon-studio", "version": 1}}


def prepare(source: Path, out: Path) -> Report:
    report = Report(tool="icon-studio", target=str(source), version=__version__)
    try:
        info = image_info(source)
    except (UnsupportedImage, OSError) as exc:
        report.error("ICON001", f"Master icon cannot be read: {exc}")
        return report

    if info.format != "PNG":
        report.error("ICON002", f"Master must be PNG; found {info.format}.")
    if info.size != MASTER_SIZE:
        report.error("ICON003", f"Master is {info.width}×{info.height}; Apple's master size is 1024×1024.",
                     hint="Export at 1024×1024 — the tool produces every smaller slot from it.")
    if info.has_alpha:
        report.error("ICON004", "Master has an alpha channel; App Store rejects icons with transparency.",
                     hint="Flatten onto an opaque background before running this tool.")
    if report.status == "fail":
        return report

    try:
        master = decode_png(source)
    except (IconError, zlib.error) as exc:
        report.error("ICON005", f"PNG could not be decoded: {exc}")
        return report

    out.mkdir(parents=True, exist_ok=True)
    generated = []
    for idiom, points, scale in SLOTS:
        pixels = int(round(points * scale))
        bitmap = resize(master, pixels)
        target = out / slot_filename(idiom, points, scale)
        target.write_bytes(encode_png(bitmap))
        generated.append({"file": target.name, "px": pixels, "idiom": idiom, "scale": f"{scale}x"})

    (out / "Contents.json").write_text(json.dumps(contents_json(SLOTS), indent=2) + "\n")
    report.data = {
        "output": str(out),
        "slots": len(generated),
        "files": [entry["file"] for entry in generated],
        "master": {"width": info.width, "height": info.height, "has_alpha": info.has_alpha},
    }
    report.info("ICON010", f"Wrote {len(generated)} PNG slots and Contents.json to {out}.",
                hint="Open the asset catalogue in Xcode to confirm the slots resolve.")
    return report


def verify(directory: Path) -> Report:
    report = Report(tool="icon-studio", target=str(directory), version=__version__)
    contents = directory / "Contents.json"
    if not contents.exists():
        report.error("ICON020", "No Contents.json: this is not an AppIcon set.")
        return report
    payload = json.loads(contents.read_text())
    images = payload.get("images", [])
    missing = [image.get("filename") for image in images if image.get("filename") and not (directory / image["filename"]).exists()]
    if missing:
        report.error("ICON021", f"{len(missing)} referenced file(s) are missing.",
                     hint="Missing: " + ", ".join(missing[:5]))
    wrong = []
    for image in images:
        filename = image.get("filename")
        if not filename or not (directory / filename).exists():
            continue
        expected = image.get("size", "0x0").split("x")[0]
        scale = int(image.get("scale", "1x").rstrip("x"))
        want = int(round(float(expected) * scale))
        actual = image_info(directory / filename).size
        if actual != (want, want):
            wrong.append(f"{filename}: {actual[0]}px, expected {want}px")
    if wrong:
        report.error("ICON022", f"{len(wrong)} slot(s) have the wrong pixel size.", hint="; ".join(wrong[:4]))
    report.data = {"slots": len(images), "missing": len(missing), "wrong_size": len(wrong)}
    if not missing and not wrong:
        report.info("ICON023", f"{len(images)} slots verified.")
    return report


def preview(source: Path, at: int, out: Path) -> Report:
    report = Report(tool="icon-studio", target=str(source), version=__version__)
    try:
        master = decode_png(source)
    except (IconError, zlib.error) as exc:
        report.error("ICON030", f"PNG could not be decoded: {exc}")
        return report
    smaller = resize(master, at)
    out.write_bytes(encode_png(smaller))
    report.data = {"output": str(out), "width": at}
    report.info("ICON031", f"Wrote a {at}×{at} preview to {out}.",
                hint="Check legibility at small sizes before shipping the icon.")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="icon-studio",
        description="Generate a complete AppIcon set from one 1024×1024 master, verify it, or preview it small.",
        epilog="Exit codes: 0 pass, 1 warnings with --strict, 2 failure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    prepare_cmd = sub.add_parser("prepare", help="Master PNG → AppIcon.appiconset")
    prepare_cmd.add_argument("source")
    prepare_cmd.add_argument("--out", required=True, help="Destination .appiconset directory")

    verify_cmd = sub.add_parser("verify", help="Check an existing .appiconset")
    verify_cmd.add_argument("directory")

    preview_cmd = sub.add_parser("preview", help="Render the icon at a small size for legibility review")
    preview_cmd.add_argument("source")
    preview_cmd.add_argument("--at", type=int, default=120)
    preview_cmd.add_argument("--out", required=True)

    for command in (prepare_cmd, verify_cmd, preview_cmd):
        command.add_argument("--json", action="store_true")
        command.add_argument("--strict", action="store_true")
        command.add_argument("--color", choices=("auto", "always", "never"), default="auto")

    args = parser.parse_args(argv)

    if args.command == "prepare":
        report = prepare(Path(args.source).expanduser().resolve(), Path(args.out).expanduser().resolve())
    elif args.command == "verify":
        report = verify(Path(args.directory).expanduser().resolve())
    else:
        report = preview(Path(args.source).expanduser().resolve(), args.at, Path(args.out).expanduser().resolve())

    return emit(report, args, title="Apple Native Engineer — Icon Studio")


if __name__ == "__main__":
    raise SystemExit(main())
