#!/usr/bin/env python3
"""Rebuild assets/evidence from a real screenshot-pipeline run.

Reads the outputs of the commands in ``examples/screenshot-pipeline/README.md``
(``.swiftwork/evidence/{shots,frames,*.json}``), and writes:

* ``assets/evidence/screenshot-frames.jpg`` — one raw capture and four composed
  frames, downscaled for the README (the full-size files are not committed),
* ``assets/evidence/pipeline-run.json`` — the tool envelopes' summaries, the
  executed simctl commands and every capture's size, with local paths removed,
* ``assets/evidence/SHA256SUMS``.

Needs macOS (``sips``) and ``rsvg-convert``.
"""

from __future__ import annotations

import base64
import hashlib
import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "assets" / "evidence"
RUNS = {
    "swift": {"dir": ROOT / ".swiftwork" / "evidence", "gallery": "screenshot-frames.jpg", "record": "pipeline-run.json",
              "recorded_with": "examples/screenshot-pipeline (plan.json, captions.json)"},
    "flutter": {"dir": ROOT / ".swiftwork" / "evidence-flutter", "gallery": "flutter-frames.jpg",
                "record": "flutter-run.json", "recorded_with": "examples/flutter-pipeline (main.dart, plan.json, captions.json)"},
}
RUN = RUNS["swift"]["dir"]
FLUTTER_TILES = [
    ("shots/en-US/iphone-18-pro-max/01-today-light.png", "Raw Flutter capture", "en-US · 1320×2868"),
    ("frames/en-US/iphone-18-pro-max/01-today-light.png", "Composed frame", "en-US · light"),
    ("frames/tr-TR/iphone-18-pro-max/02-insights-dark.png", "Composed frame", "tr-TR · dark"),
    ("frames/tr-TR/iphone-18-pro/01-today-light.png", "Composed frame", "tr-TR · 1206×2622"),
]
TILES = [
    ("shots/en-US/iphone-18-pro-max/01-today-light.png", "Raw capture", "en-US · 1320×2868"),
    ("frames/en-US/iphone-18-pro-max/01-today-light.png", "Composed frame", "en-US · same capture"),
    ("frames/tr-TR/iphone-18-pro-max/02-insights-dark.png", "Composed frame", "tr-TR · dark"),
    ("frames/tr-TR/iphone-18-pro/01-today-light.png", "Composed frame", "tr-TR · 1206×2622"),
    ("frames/tr-TR/ipad-pro-13-inch-m5/01-today-light.png", "Composed frame", "tr-TR · iPad 2064×2752"),
]


def gallery(work: Path, tiles=None, name: str = "screenshot-frames.jpg", run_dir: Path = None) -> None:
    tiles = tiles or TILES
    run_dir = run_dir or RUN
    height, gap, pad, top = 820, 36, 48, 40
    parts, x = [], pad
    for index, (relative, label, sub) in enumerate(tiles):
        small = work / f"tile{index}.jpg"
        subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "88", "--resampleHeight",
                        str(height * 2), str(run_dir / relative), "--out", str(small)], check=True, capture_output=True)
        width = int(subprocess.check_output(["sips", "-g", "pixelWidth", str(small)], text=True).split()[-1]) // 2
        data = base64.b64encode(small.read_bytes()).decode()
        parts += [
            f'<clipPath id="c{index}"><rect x="{x}" y="{top}" width="{width}" height="{height}" rx="18"/></clipPath>',
            f'<image x="{x}" y="{top}" width="{width}" height="{height}" href="data:image/jpeg;base64,{data}" clip-path="url(#c{index})"/>',
            f'<rect x="{x}" y="{top}" width="{width}" height="{height}" rx="18" fill="none" stroke="#29374b" stroke-width="2"/>',
            f'<text x="{x}" y="{top + height + 44}" fill="{"#a2b1c6" if index == 0 else "#75e0bd"}" font-size="24" font-weight="600">{label}</text>',
            f'<text x="{x}" y="{top + height + 76}" fill="#a2b1c6" font-size="20">{sub}</text>',
        ]
        if index == 0:
            parts.append(f'<text x="{x + width + 8}" y="{top + height // 2}" fill="#75e0bd" font-size="30">→</text>')
        x += width + gap
    total_w, total_h = x - gap + pad, top + height + 110
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{total_w}" height="{total_h}" viewBox="0 0 {total_w} {total_h}">'
           f'<rect width="{total_w}" height="{total_h}" rx="28" fill="#0b1018"/>'
           '<g font-family="-apple-system,\'SF Pro Display\',Helvetica,Arial,sans-serif">' + "".join(parts) + "</g></svg>")
    (work / "gallery.svg").write_text(svg)
    subprocess.run(["rsvg-convert", "-w", "2400", str(work / "gallery.svg"), "-o", str(work / "gallery.png")], check=True)
    subprocess.run(["sips", "-s", "format", "jpeg", "-s", "formatOptions", "86", str(work / "gallery.png"),
                    "--out", str(OUT / name)], check=True, capture_output=True)


def scrub(text: str) -> str:
    return text.replace(str(RUN), "<run>").replace(str(ROOT), "<repository>").replace(str(Path.home()), "~")


def record(run_name: str = "swift") -> None:
    global RUN
    RUN = RUNS[run_name]["dir"]
    names = ("capture", "audit-captures", "compose", "audit-frames", "audit-before", "audit-after")
    envelopes = {name: json.loads((RUN / f"{name}.json").read_text()) for name in names if (RUN / f"{name}.json").exists()}
    capture = envelopes["capture"]["data"]
    summary = {
        name: {"status": env["status"], "summary": env["summary"],
               "codes": dict(Counter(finding["code"] for finding in env["findings"]))}
        for name, env in envelopes.items()
    }
    run = {
        "recorded_with": RUNS[run_name]["recorded_with"],
        "tool_version": envelopes["capture"].get("tool_version"),
        "devices": [{"name": d["name"], "runtime": d["runtime"]} for d in capture["devices"]],
        "captures": [{k: v for k, v in c.items() if k in ("file", "size", "alpha", "flattened", "locale", "appearance")}
                     for c in capture["captures"]],
        "capture_sizes": dict(Counter(c.get("size") for c in capture["captures"])),
        "flattened_from_alpha": sum(1 for c in capture["captures"] if c.get("flattened")),
        "frames_rendered": envelopes["compose"]["data"]["rendered"],
        "renderer": envelopes["compose"]["data"]["renderer"],
        "envelopes": summary,
        "simctl_commands": capture["commands"],
        "scope": "Real iOS 27.2 Simulator captures of a controlled demo app (not a customer app). Frames are "
                 "marketing compositions of those captures. No upload to App Store Connect was made.",
    }
    if run_name == "flutter":
        run["scope"] = ("A Flutter 3.44.8 app created with `flutter create`, built with `flutter build ios --simulator` "
                        "and captured in the iOS 27.2 Simulator. audit-before is the unmodified template plus "
                        "examples/flutter-pipeline/main.dart; audit-after is after raising the deployment target and "
                        "adding Turkish to knownRegions. No upload was made.")
    (OUT / RUNS[run_name]["record"]).write_text(scrub(json.dumps(run, indent=2, ensure_ascii=False)) + "\n")


def checksums() -> None:
    lines = []
    for path in sorted(OUT.iterdir()):
        if path.name in ("SHA256SUMS", "README.md"):
            continue
        lines.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (OUT / "SHA256SUMS").write_text("\n".join(lines) + "\n")


def main() -> int:
    if not (RUN / "capture.json").exists():
        print("run the commands in examples/screenshot-pipeline/README.md first", file=sys.stderr)
        return 2
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as work:
        gallery(Path(work))
    record("swift")
    flutter = RUNS["flutter"]
    if (flutter["dir"] / "capture.json").exists():
        with tempfile.TemporaryDirectory() as work:
            gallery(Path(work), FLUTTER_TILES, flutter["gallery"], flutter["dir"])
        record("flutter")
    checksums()
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
