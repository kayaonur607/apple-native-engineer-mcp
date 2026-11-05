#!/usr/bin/env python3
"""Benchmark the auditors on a synthetic project.

The tools run before a build exists, on a laptop, so their cost has to be
negligible next to the thing they are checking. This script answers "how much
does the audit cost?" with numbers instead of adjectives.

It generates a project of N Swift files containing a realistic mix of good and
bad SwiftUI, then times every tool with `--json` and reports wall-clock
milliseconds per thousand lines.

Usage::

    python3 scripts/benchmark.py                 # 500 files
    python3 scripts/benchmark.py --files 2000
    python3 scripts/benchmark.py --json
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Dict, List

REPO = Path(__file__).resolve().parents[1]

TOOLS = [
    ("project-inspector", "tools/project-inspector/inspect_project.py"),
    ("privacy-auditor", "tools/privacy-auditor/audit_privacy.py"),
    ("swiftui-linter", "tools/swiftui-linter/lint_swiftui.py"),
    ("accessibility-auditor", "tools/accessibility-auditor/audit_accessibility.py"),
    ("localization-checker", "tools/localization-checker/check_localization.py"),
    ("liquid-glass-auditor", "tools/liquid-glass-auditor/audit_liquid_glass.py"),
    ("sf-symbols-catalog", "tools/sf-symbols-catalog/check_symbols.py"),
    ("release-readiness", "tools/release-readiness/generate_report.py"),
]

GOOD_VIEW = """import SwiftUI

struct Feature{index}View: View {{
    @Environment(AppModel.self) private var model
    @State private var isPresented = false

    var body: some View {{
        NavigationStack {{
            List(model.items) {{ item in
                Label(item.title, systemImage: item.symbol)
                    .accessibilityHint(Text("Opens details"))
            }}
            .navigationTitle(Text("Feature {index}"))
            .toolbar {{
                Button("Add") {{ isPresented = true }}
                    .frame(minWidth: 44, minHeight: 44)
            }}
            .sheet(isPresented: $isPresented) {{
                Text("Sheet")
                    .presentationDetents([.medium])
            }}
        }}
    }}
}}
"""

BAD_VIEW = """import SwiftUI

struct Legacy{index}View: View {{
    @StateObject private var model = LegacyModel{index}()
    @State private var flag = false

    var body: some View {{
        NavigationView {{
            VStack {{
                Text("Welcome {index}")
                    .font(.system(size: {size}))
                    .foregroundColor(Color(hex: "#C7C7CC"))
                    .frame(width: 320)
                Button {{
                    try! model.save()
                }} label: {{
                    Image(systemName: "trash")
                }}
                .frame(width: 30, height: 30)
            }}
            .onChange(of: flag) {{ value in print(value) }}
        }}
    }}
}}
"""

MODEL = """import Combine

final class LegacyModel{index}: ObservableObject {{
    @Published var items: [Item] = []
    func save() throws {{ UserDefaults.standard.set(true, forKey: "k{index}") }}
}}
"""


def generate(root: Path, files: int) -> Dict[str, int]:
    app = root / "App"
    app.mkdir(parents=True, exist_ok=True)
    (root / "Package.swift").write_text(
        "// swift-tools-version: 6.0\n"
        "import PackageDescription\n"
        "let package = Package(\n"
        '    name: "Bench",\n'
        "    platforms: [.iOS(.v16), .macOS(.v14)],\n"
        '    targets: [.target(name: "Bench", path: "App")]\n'
        ")\n"
    )

    written = 0
    for index in range(files):
        if index % 4 == 0:
            (app / f"Legacy{index}View.swift").write_text(
                BAD_VIEW.format(index=index, size=12 + (index % 20))
            )
        elif index % 4 == 1:
            (app / f"Feature{index}View.swift").write_text(GOOD_VIEW.format(index=index))
        elif index % 4 == 2:
            (app / f"LegacyModel{index}.swift").write_text(MODEL.format(index=index))
        else:
            (app / f"Service{index}.swift").write_text(
                "import Foundation\n\n"
                f"struct Service{index} {{\n"
                f"    let id = UUID()\n"
                f"    func load() async throws -> [String] {{ [] }}\n"
                "}\n"
            )
        written += 1

    (app / "Info.plist").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" '
        '"http://www.apple.com/DTDs/PropertyList-1.0.dtd">\n'
        "<plist version=\"1.0\"><dict>"
        "<key>CFBundleIdentifier</key><string>com.example.bench</string>"
        "<key>NSSupportsLiveActivities</key><true/>"
        "</dict></plist>\n"
    )
    return {"swift_files": written}


def run(tool: str, script: str, target: Path) -> Dict[str, object]:
    command = [sys.executable, str(REPO / script), str(target), "--json"]
    start = time.perf_counter()
    proc = subprocess.run(command, capture_output=True, text=True)
    elapsed = (time.perf_counter() - start) * 1000
    findings = 0
    status = "error"
    try:
        payload = json.loads(proc.stdout)
        findings = payload["summary"]["total"]
        status = payload["status"]
    except (json.JSONDecodeError, KeyError):
        pass
    return {
        "tool": tool,
        "status": status,
        "ms": round(elapsed, 1),
        "findings": findings,
        "exit": proc.returncode,
    }


def main(argv: List[str]) -> int:
    files = 500
    if "--files" in argv:
        files = int(argv[argv.index("--files") + 1])

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp) / "BenchProject"
        meta = generate(root, files)
        lines = sum(len(p.read_text().splitlines()) for p in (root / "App").glob("*.swift"))

        results = [run(tool, script, root) for tool, script in TOOLS]

    total_ms = sum(result["ms"] for result in results)  # type: ignore[operator]
    payload = {
        "machine": f"{platform.system()} {platform.machine()} · Python {platform.python_version()}",
        "swift_files": meta["swift_files"],
        "swift_lines": lines,
        "total_ms": round(total_ms, 1),
        "ms_per_1000_lines": round(total_ms / max(lines, 1) * 1000, 1),
        "results": results,
    }

    if "--json" in argv:
        print(json.dumps(payload, indent=2))
        return 0

    print(f"Machine:  {payload['machine']}")
    print(f"Project:  {meta['swift_files']} Swift files, {lines:,} lines")
    print()
    print(f"{'tool':<24} {'status':<6} {'ms':>8} {'findings':>9}")
    print("-" * 52)
    for result in results:
        print(f"{result['tool']:<24} {result['status']:<6} {result['ms']:>8} {result['findings']:>9}")
    print("-" * 52)
    print(f"{f'all {len(TOOLS)} tools':<24} {'':<6} {total_ms:>8}")
    print()
    print(f"{payload['ms_per_1000_lines']} ms per 1,000 lines of Swift across the whole suite")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
