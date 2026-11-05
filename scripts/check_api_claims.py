#!/usr/bin/env python3
"""Check that the modifiers this repository teaches actually exist in the SDK.

Documentation drifts by invention: someone writes `.scrollEdgeEffect(...)` from
memory, the snippet looks right, and a reader ships code that does not compile.
Parsing snippets catches syntax errors but not invented API.

This script builds an index of every public declaration in the installed SDK's
Swift module interfaces, extracts every view modifier written at the start of a
line inside a ```swift block, and reports the ones that do not exist.

Usage::

    python3 scripts/check_api_claims.py
    python3 scripts/check_api_claims.py --json
    python3 scripts/check_api_claims.py --list   # show every modifier found

The check only means something on an SDK at least as new as the API the docs
teach, so it skips (exit 0) when the installed SDK is older than the documented
baseline. Pass `--strict-sdk` to turn that skip into a failure.

Exit codes: 0 all verified (or skipped), 2 at least one unverified modifier.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Set

REPO = Path(__file__).resolve().parents[1]
ALLOWLIST = REPO / "data" / "api-allowlist.json"
DOC_DIRS = ("references", "examples")

#: The oldest SDK this repository's documentation is written against.
MIN_SDK_RELEASE = 26

MODIFIER_RE = re.compile(r"^\s*\.([a-z][A-Za-z0-9_]*)\s*[({]", re.MULTILINE)
FENCE_RE = re.compile(r"```swift\n(.*?)```", re.DOTALL)

DECLARATION_PATTERNS = (
    r"\bfunc\s+([a-zA-Z_][\w]*)",
    r"\b(?:var|let|case)\s+([a-zA-Z_][\w]*)",
    r"\b(?:struct|class|enum|protocol|actor|typealias)\s+([A-Z][\w]*)",
)


def sdk_path() -> Path:
    output = subprocess.check_output(
        ["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"], text=True
    ).strip()
    return Path(output)


def build_index(sdk: Path) -> Set[str]:
    """Every public name declared in any iOS Swift interface in the SDK."""

    index: Set[str] = set()
    for interface in sdk.glob("System/Library/Frameworks/*/Modules/*.swiftmodule/*.swiftinterface"):
        if "arm64-apple-ios-simulator" not in interface.name:
            continue
        text = interface.read_text(errors="ignore")
        for pattern in DECLARATION_PATTERNS:
            index.update(re.findall(pattern, text))
    return index


def extract_modifiers(markdown: str) -> Counter:
    """Count modifiers that appear at the start of a line inside swift fences.

    Line-leading position is what separates a view modifier from a method call on
    a model object (`model.fetchProfile()`), which cannot be checked this way.
    """

    counts: Counter = Counter()
    for block in FENCE_RE.findall(markdown):
        counts.update(MODIFIER_RE.findall(block))
    return counts


def load_allowlist() -> Dict[str, str]:
    if not ALLOWLIST.exists():
        return {}
    payload = json.loads(ALLOWLIST.read_text())
    return {entry["symbol"]: entry.get("reason", "") for entry in payload.get("allowed", [])}


def _relative(path: Path) -> str:
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return path.name


def collect(docs: Iterable[Path]) -> Dict[str, List[str]]:
    """Map modifier name -> files that use it."""

    usage: Dict[str, List[str]] = {}
    for document in docs:
        for name in extract_modifiers(document.read_text(errors="ignore")):
            usage.setdefault(name, []).append(_relative(document))
    return usage


def check(docs: Iterable[Path], index: Set[str], allowlist: Dict[str, str]) -> List[dict]:
    findings: List[dict] = []
    for name, files in sorted(collect(docs).items()):
        if name in index or name in allowlist:
            continue
        findings.append(
            {
                "symbol": name,
                "kind": "modifier",
                "files": sorted(files),
                "message": f"`.{name}(` does not exist in the iOS SDK",
                "hint": "Fix the call, or add it to data/api-allowlist.json with the platform it comes from.",
            }
        )
    return findings


def documents() -> List[Path]:
    docs: List[Path] = []
    for directory in DOC_DIRS:
        docs.extend(sorted((REPO / directory).glob("*.md")))
    return docs


def main(argv: List[str]) -> int:
    try:
        sdk = sdk_path()
    except (OSError, subprocess.CalledProcessError):
        print("error: xcrun is required (macOS with Xcode); nothing to verify against", file=sys.stderr)
        return 2

    release_match = re.search(r"iPhoneSimulator(\d+)\.", sdk.name)
    release = int(release_match.group(1)) if release_match else 0
    if release < MIN_SDK_RELEASE:
        message = (
            f"skipped: installed SDK is iOS {release}, documentation targets "
            f"iOS {MIN_SDK_RELEASE}+ — select a newer Xcode to run this check"
        )
        if "--strict-sdk" in argv:
            print(message, file=sys.stderr)
            return 2
        print(message)
        return 0

    index = build_index(sdk)
    if not index:
        print(f"error: no Swift interfaces found in {sdk}", file=sys.stderr)
        return 2

    docs = documents()
    usage = collect(docs)
    allowlist = load_allowlist()
    findings = check(docs, index, allowlist)

    if "--list" in argv:
        for name, files in sorted(usage.items()):
            status = "ok" if name in index else ("allowlisted" if name in allowlist else "UNKNOWN")
            print(f"{name:38} {len(files):3} file(s)  {status}")

    payload = {
        "sdk": sdk.name,
        "indexed_symbols": len(index),
        "documents": len(docs),
        "modifiers": len(usage),
        "verified": len([name for name in usage if name in index]),
        "allowlisted": len([name for name in usage if name in allowlist]),
        "unverified": findings,
    }

    if "--json" in argv:
        print(json.dumps(payload, indent=2))
    else:
        print(f"SDK index:        {len(index):,} symbols from {sdk.name}")
        print(f"Documents:        {len(docs)}")
        print(f"Modifiers taught: {payload['modifiers']}")
        print(f"Verified:         {payload['verified']}")
        print(f"Allowlisted:      {payload['allowlisted']}")
        print(f"Unverified:       {len(findings)}")
        for finding in findings:
            print(f"  ✖ .{finding['symbol']}( — {finding['files'][0]}")
            print(f"    {finding['hint']}")

    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
