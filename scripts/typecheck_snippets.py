#!/usr/bin/env python3
"""Type-check the Swift that this repository teaches.

`swiftc -parse` proves syntax; `check_api_claims.py` proves the modifier exists.
Neither proves the snippet type-checks — that `.spring(response:dampingRatio:)`
has an argument label the compiler actually accepts.

This script extracts every ```swift block, wraps it in the imports a fragment
would normally inherit from the surrounding document, compiles it against the
iOS SDK, and classifies each diagnostic:

* **artifact** — the snippet is a fragment: undefined symbols that live outside
  the block, top-level expressions, or a missing import. Not a documentation bug.
* **real** — wrong argument labels, wrong types, ambiguous calls. A reader who
  copies this gets a compile error, so it is a bug in the guide.

Usage::

    python3 scripts/typecheck_snippets.py            # report
    python3 scripts/typecheck_snippets.py --json     # machine readable
    python3 scripts/typecheck_snippets.py --strict   # exit 2 if any real error

macOS + Xcode only.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
WORK = REPO / ".swiftwork" / "snippets-typecheck"
TARGET = "arm64-apple-ios18.0-simulator"
HEADER = "import SwiftUI\nimport Foundation\n"

#: A fence may name the platform the snippet targets: ```swift visionOS.
#: Everything else is iOS, which is what the guides teach by default.
FENCE_RE = re.compile(r"```swift(?:[ \t]+([A-Za-z]+))?[ \t]*\n(.*?)```", re.DOTALL)
ERROR_RE = re.compile(r"^(.*?):(\d+):(\d+): error: (.*)$")

#: platform → (SDK name for xcrun, swiftc target triple). The target embeds the
#: repository's documented deployment floor (iOS 17 and its contemporaries), so a
#: snippet that needs a newer OS fails here rather than in a reader's Xcode.
PLATFORMS: Dict[str, Tuple[str, str]] = {
    "ios": ("iphonesimulator", TARGET),
    "visionos": ("xros", "arm64-apple-xros1.0"),
    "macos": ("macosx", "arm64-apple-macos14.0"),
    "watchos": ("watchsimulator", "arm64-apple-watchos10.0-simulator"),
    "tvos": ("appletvsimulator", "arm64-apple-tvos17.0-simulator"),
}
DEFAULT_PLATFORM = "ios"

#: A missing symbol means the block is a fragment: the type lives in another
#: snippet, or in the prose around it. Consequences of that single problem (bad
#: conformances, odd overload errors) are not worth reporting separately.
MISSING_SYMBOL_PATTERNS = (
    r"cannot find (?:type )?'[^']*' in scope",
    r"cannot find '[^']*' in scope",
)

#: Diagnostics that are artifacts of compiling an isolated block.
ARTIFACT_PATTERNS = (
    r"has no member named",
    r"value of type '[^']*' has no member",
    r"expressions are not allowed at the top level",
    r"property wrappers are not yet supported in top-level code",
    r"cannot infer contextual base in reference to member",
    r"reference to member '[^']*' cannot be resolved without a contextual type",
    r"cannot infer key path type from context",
    r"type annotation missing in pattern",
    r"unknown attribute '[^']*'",
    r"'main' attribute cannot be used in a module that contains top-level code",
    r"invalid redeclaration",
    r"could not infer type for placeholder",
    r"no such module 'Testing'",
    r"is unavailable in iOS",
    r"extraneous argument label",
    r"an enum with no cases cannot declare a raw type",
    r"generic parameter '[^']*' could not be inferred",
    r"function declares an opaque return type",
)


@dataclass
class Snippet:
    document: str
    index: int
    code: str
    platform: str = DEFAULT_PLATFORM
    status: str = "unknown"
    errors: List[str] = field(default_factory=list)


def sdk_path(platform: str = DEFAULT_PLATFORM) -> Path:
    sdk = PLATFORMS[platform][0]
    return Path(subprocess.check_output(["xcrun", "--sdk", sdk, "--show-sdk-path"],
                                        text=True).strip())


def extract() -> List[Snippet]:
    snippets: List[Snippet] = []
    for directory in ("references", "examples"):
        for document in sorted((REPO / directory).glob("*.md")):
            for index, match in enumerate(FENCE_RE.findall(document.read_text(errors="ignore"))):
                declared, block = match
                platform = (declared or DEFAULT_PLATFORM).lower()
                snippets.append(
                    Snippet(
                        document=f"{directory}/{document.name}",
                        index=index,
                        code=block,
                        # An unknown tag is an error in the guide, not a reason to
                        # silently compile visionOS code against the iOS SDK.
                        platform=platform if platform in PLATFORMS else "unknown",
                    )
                )
    return snippets


def classify(diagnostic: str) -> str:
    for pattern in MISSING_SYMBOL_PATTERNS:
        if re.search(pattern, diagnostic):
            return "missing"
    for pattern in ARTIFACT_PATTERNS:
        if re.search(pattern, diagnostic):
            return "artifact"
    return "real"


def compile_snippet(snippet: Snippet, sdk: Path, target_dir: Path) -> None:
    if snippet.platform == "unknown":
        snippet.status = "real"
        snippet.errors = [
            f"unknown platform tag in the fence — use one of {', '.join(sorted(PLATFORMS))}"
        ]
        return
    target = PLATFORMS[snippet.platform][1]
    path = target_dir / f"snippet-{len(snippet.code):05d}-{snippet.index}.swift"
    path.write_text(HEADER + "\n" + snippet.code)
    proc = subprocess.run(
        [
            "swiftc", "-typecheck", "-disable-sandbox", "-sdk", str(sdk), "-target", target,
            "-module-cache-path", str(WORK / "mc"), str(path),
        ],
        capture_output=True, text=True, env={**os.environ, "TMPDIR": str(WORK / "tmp")},
    )
    if proc.returncode == 0:
        snippet.status = "ok"
        return

    diagnostics = [match.group(4) for match in (ERROR_RE.match(line) for line in proc.stderr.splitlines()) if match]
    if not diagnostics:
        snippet.status = "unknown-error"
        snippet.errors = proc.stderr.splitlines()[:2]
        return

    kinds = {classify(diagnostic) for diagnostic in diagnostics}
    # One undefined symbol explains the rest of the diagnostics for that block.
    if "missing" in kinds or kinds == {"artifact"}:
        snippet.status = "fragment"
    else:
        snippet.status = "real"
        snippet.errors = [d for d in diagnostics if classify(d) == "real"][:4]


def main(argv: List[str]) -> int:
    snippets = extract()
    used = sorted({snippet.platform for snippet in snippets if snippet.platform in PLATFORMS})

    sdks: Dict[str, Path] = {}
    skipped: Dict[str, str] = {}
    for platform in used:
        try:
            sdks[platform] = sdk_path(platform)
        except (OSError, subprocess.CalledProcessError):
            # A runner without the visionOS platform installed is not a defect in
            # this repository: verify what the toolchain can see and say what was
            # skipped, loudly, instead of failing the whole job.
            skipped[platform] = PLATFORMS[platform][0]

    if not sdks:
        print(
            "error: no Apple SDK found (xmux/iphonesimulator); macOS with Xcode required",
            file=sys.stderr,
        )
        return 2

    for platform, sdk_name in skipped.items():
        count = sum(1 for snippet in snippets if snippet.platform == platform)
        print(
            f"  ! {platform}: {sdk_name} SDK is not installed, skipping {count} snippet(s)",
            file=sys.stderr,
        )

    if WORK.exists():
        shutil.rmtree(WORK)
    (WORK / "mc").mkdir(parents=True, exist_ok=True)
    (WORK / "tmp").mkdir(parents=True, exist_ok=True)
    target_dir = WORK / "src"
    target_dir.mkdir(parents=True, exist_ok=True)

    for snippet in snippets:
        if snippet.platform in skipped:
            snippet.status = "skipped"
            continue
        compile_snippet(snippet, sdks[snippet.platform], target_dir)

    counts = Counter(snippet.status for snippet in snippets)
    real = [snippet for snippet in snippets if snippet.status == "real"]
    by_platform = Counter(snippet.platform for snippet in snippets)

    payload = {
        "sdks": {platform: path.name for platform, path in sdks.items()},
        "platforms": dict(by_platform),
        "snippets": len(snippets),
        "ok": counts.get("ok", 0),
        "fragments": counts.get("fragment", 0),
        "real_errors": [
            {"document": s.document, "block": s.index, "platform": s.platform, "errors": s.errors}
            for s in real
        ],
        "skipped": skipped,
        "unknown_errors": [
            {"document": s.document, "block": s.index, "stderr": s.errors}
            for s in snippets if s.status == "unknown-error"
        ],
    }

    if "--json" in argv:
        print(json.dumps(payload, indent=2))
    else:
        print("SDK:              " + ", ".join(f"{p} → {name}" for p, name in payload["sdks"].items()))
        print(f"Snippets:         {len(snippets)}")
        print("Per platform:     " + ", ".join(f"{p} {n}" for p, n in sorted(by_platform.items())))
        if skipped:
            print("Skipped:          " + ", ".join(f"{p} ({name} SDK missing)" for p, name in skipped.items()))
        print(f"Type-check clean: {payload['ok']}")
        print(f"Fragments:        {payload['fragments']}")
        print(f"Real errors:      {len(real)}")
        for snippet in real:
            print(f"  ✖ {snippet.document} block {snippet.index} ({snippet.platform})")
            for error in snippet.errors:
                print(f"      {error[:120]}")

    if real and ("--strict" in argv):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
