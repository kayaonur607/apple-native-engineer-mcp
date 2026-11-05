#!/usr/bin/env python3
"""Generate a "what's new" reference from the installed Apple SDK.

Turns the SDK's Swift module interfaces into a human-readable list of the API a
given OS release introduced — grouped by framework and declaration kind. Nothing
in the output is recalled from training data: every row is a declaration that is
annotated `@available(iOS <release>.0, …)` in the interface on this machine.

Usage::

    python3 scripts/generate_whats_new.py            # current SDK release
    python3 scripts/generate_whats_new.py --release 26
    python3 scripts/generate_whats_new.py --check    # fail if the doc is stale (same SDK)
    python3 scripts/generate_whats_new.py --validate # SDK-independent consistency check
"""

from __future__ import annotations

import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple

REPO = Path(__file__).resolve().parents[1]
OUT_DIR = REPO / "references"

FRAMEWORKS = [
    "SwiftUI", "SwiftUICore", "UIKit", "Foundation", "WidgetKit", "ActivityKit",
    "AppIntents", "SwiftData", "StoreKit", "Observation", "Charts", "Symbols",
]

KEYWORDS = (
    "struct", "class", "enum", "protocol", "actor", "func", "var", "let",
    "init", "typealias", "extension", "subscript", "case",
)

MODIFIERS = {
    "public", "open", "static", "final", "nonisolated", "isolated", "override",
    "mutating", "nonmutating", "indirect", "required", "convenience", "lazy",
    "weak", "unowned", "dynamic", "optional", "prefix", "postfix", "infix",
}


def sdk_path() -> Path:
    output = subprocess.check_output(
        ["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"], text=True
    ).strip()
    return Path(output)


def sdk_release(sdk: Path) -> int:
    match = re.search(r"iPhoneSimulator(\d+)\.", sdk.name)
    return int(match.group(1)) if match else 0


def interface_for(sdk: Path, framework: str) -> Optional[Path]:
    base = sdk / "System" / "Library" / "Frameworks" / f"{framework}.framework" / "Modules"
    if not base.exists():
        return None
    for candidate in sorted(base.glob(f"{framework}.swiftmodule/*.swiftinterface")):
        if "arm64-apple-ios-simulator" in candidate.name:
            return candidate
    candidates = sorted(base.glob(f"{framework}.swiftmodule/*.swiftinterface"))
    return candidates[0] if candidates else None


def strip_modifiers(tokens: List[str]) -> List[str]:
    index = 0
    while index < len(tokens):
        token = tokens[index]
        bare = token.lstrip("@").rstrip(",")
        if token.startswith("@") or bare in MODIFIERS:
            index += 1
            continue
        break
    return tokens[index:]


def declaration_of(line: str) -> Optional[Tuple[str, str]]:
    """Return ``(kind, name)`` for a public declaration line, else None."""

    stripped = line.strip()
    if "public " not in stripped and not stripped.startswith(("public", "open")):
        return None
    if stripped.startswith("//"):
        return None

    tokens = strip_modifiers(stripped.split())
    if not tokens:
        return None

    kind = tokens[0]
    if kind not in KEYWORDS:
        return None
    rest = tokens[1:]
    if kind == "case":
        name = rest[0].rstrip(",;") if rest else ""
    elif kind in ("var", "let"):
        name = rest[0].split(":")[0].rstrip("=,;") if rest else ""
    elif kind == "init":
        name = "init"
    else:
        name = rest[0].split("<")[0].split("(")[0].split(":")[0].rstrip("=,;{") if rest else ""
    name = name.replace("`", "")
    if not name or not re.match(r"^[A-Za-z_][\w.]*$", name):
        return None
    return kind, name


BOILERPLATE = {"hash", "isEqual", "encode", "decode", "==", "<", "copy", "deinit"}


def collect_availability(path: Path, release: int) -> Dict[str, Dict[str, object]]:
    """Map ``"kind:name"`` to metadata for declarations introduced in *release*."""

    found: Dict[str, Dict[str, object]] = {}
    lines = path.read_text(errors="ignore").splitlines()
    marker = f"@available(iOS {release}.0"

    index = 0
    while index < len(lines):
        if not lines[index].strip().startswith(marker):
            index += 1
            continue

        # Contiguous availability annotations belong to the declaration below.
        platforms: Dict[str, str] = {}
        while index < len(lines) and lines[index].strip().startswith("@available"):
            for platform, version in re.findall(r"(\w+) (\d+\.\d+)", lines[index]):
                platforms[platform.lower()] = version
            for unavailable in re.findall(r"@available\((\w+), unavailable\)", lines[index]):
                platforms[unavailable.lower()] = "unavailable"
            index += 1

        # Skip further attributes/comments, then read the first declaration.
        lookahead = index
        while lookahead < len(lines) and lookahead < index + 8:
            stripped = lines[lookahead].strip()
            if not stripped or stripped.startswith(("@", "//", "#if", "#endif")):
                lookahead += 1
                continue
            decl = declaration_of(lines[lookahead])
            if decl:
                kind, name = decl
                if name.startswith("_") or name in BOILERPLATE:
                    break
                key = f"{kind}:{name}"
                found.setdefault(key, {"kind": kind, "name": name, "platforms": platforms})
            break

    return found


def render(release: int, sdk: Path, per_framework: Dict[str, Dict[str, Dict[str, object]]]) -> str:
    total = sum(len(entries) for entries in per_framework.values())
    lines = [
        f"# What's new in iOS {release} — verified from the SDK",
        "",
        f"This file is **generated**, not written. It lists every declaration in the installed SDK that is annotated",
        f"`@available(iOS {release}.0, …)`, grouped by framework. Nothing here is recalled from memory: run",
        "`python3 scripts/generate_whats_new.py` to regenerate it against a different Xcode.",
        "",
        f"- SDK: `{sdk.name}`",
        f"- Declarations found: **{total}**",
        "",
        "> Availability annotations describe when an API became available, not whether it is finished or",
        "> recommended. Treat this as an index into the SDK, then read the declaration in Xcode.",
        "",
    ]

    for framework, entries in sorted(per_framework.items(), key=lambda item: -len(item[1])):
        if not entries:
            continue
        lines += [f"## {framework} — {len(entries)} new declaration(s)", ""]
        grouped: Dict[str, List[Dict[str, object]]] = defaultdict(list)
        for entry in entries.values():
            grouped[str(entry["kind"])].append(entry)

        order = ("struct", "class", "enum", "protocol", "actor", "func", "var", "let", "init",
                 "typealias", "case", "subscript", "macro")
        kinds = [kind for kind in order if kind in grouped]
        kinds += sorted(kind for kind in grouped if kind not in order)
        for kind in kinds:
            items = grouped.get(kind)
            if not items:
                continue
            names = sorted({str(item["name"]) for item in items})
            lines += [f"**{kind}** ({len(names)})", ""]
            for name in names:
                entry = next(item for item in items if str(item["name"]) == name)
                platforms: Dict[str, str] = entry["platforms"]  # type: ignore[assignment]
                extras = []
                for platform in ("macOS", "visionOS", "watchOS", "tvOS"):
                    value = platforms.get(platform.lower())
                    if value == "unavailable":
                        extras.append(f"{platform} unavailable")
                    elif value and value != f"{release}.0":
                        extras.append(f"{platform} {value}")
                suffix = f" — {', '.join(extras)}" if extras else ""
                lines.append(f"- `{name}`{suffix}")
            lines.append("")

    lines += [
        "---",
        "",
        "_Generated by `scripts/generate_whats_new.py`. Do not edit by hand._",
        "",
    ]
    return "\n".join(lines)


SECTION_RE = re.compile(r"^## (\w+) — (\d+) new declaration\(s\)$", re.MULTILINE)
TOTAL_RE = re.compile(r"Declarations found: \*\*(\d+)\*\*")
BULLET_RE = re.compile(r"^- `", re.MULTILINE)


def validate_doc(path: Path) -> List[str]:
    """Structural validation that does not depend on which SDK generated the file.

    CI cannot regenerate the document (the runner's Xcode differs from the one
    that produced it), but it can still prove the document is internally
    consistent: every section count must match its bullet count, and the total
    must match the sum of the sections.
    """

    errors: List[str] = []
    if not path.exists():
        return [f"missing generated reference: {path.name}"]

    text = path.read_text()
    total_match = TOTAL_RE.search(text)
    if not total_match:
        return ["declaration total is missing"]

    sections = list(SECTION_RE.finditer(text))
    if not sections:
        return ["no framework sections found"]

    bullets_total = 0
    for index, match in enumerate(sections):
        start = match.end()
        end = sections[index + 1].start() if index + 1 < len(sections) else len(text)
        bullets = len(BULLET_RE.findall(text[start:end]))
        declared = int(match.group(2))
        bullets_total += bullets
        if bullets != declared:
            errors.append(f"{match.group(1)}: heading claims {declared}, body lists {bullets}")

    declared_total = int(total_match.group(1))
    if declared_total != bullets_total:
        errors.append(f"total claims {declared_total}, sections list {bullets_total}")

    return errors


def main(argv: List[str]) -> int:
    sdk = sdk_path()
    release = sdk_release(sdk)
    if "--release" in argv:
        release = int(argv[argv.index("--release") + 1])

    per_framework: Dict[str, Dict[str, Dict[str, object]]] = {}
    for framework in FRAMEWORKS:
        interface = interface_for(sdk, framework)
        if interface is None:
            continue
        per_framework[framework] = collect_availability(interface, release)

    total = sum(len(entries) for entries in per_framework.values())
    if total == 0:
        print(f"no iOS {release} declarations found in {sdk.name}", file=sys.stderr)
        return 1

    content = render(release, sdk, per_framework)
    out = OUT_DIR / f"whats-new-ios-{release}.md"

    if "--validate" in argv:
        problems = validate_doc(OUT_DIR / f"whats-new-ios-{release}.md")
        if problems:
            for problem in problems:
                print(f"invalid: {problem}", file=sys.stderr)
            return 1
        print(f"references/whats-new-ios-{release}.md is structurally consistent")
        return 0

    if "--check" in argv:
        if not out.exists() or out.read_text() != content:
            print(f"stale: {out.relative_to(REPO)} — regenerate with scripts/generate_whats_new.py")
            return 1
        print(f"{out.relative_to(REPO)} is up to date ({total} declarations)")
        return 0

    out.write_text(content)
    print(f"wrote {out.relative_to(REPO)}: {total} declarations across {len(per_framework)} frameworks")
    for framework, entries in sorted(per_framework.items(), key=lambda item: -len(item[1])):
        if entries:
            print(f"  {framework:14} {len(entries)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
