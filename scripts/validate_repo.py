#!/usr/bin/env python3
"""Repository validator — structure, frontmatter, links and documented counts.

This exists because documentation drifts: a README that claims "8 tools" when
the repository ships 13 is a lie that only a machine notices. Every count in
README.md is therefore cross-checked against the filesystem.

Usage::

    python3 scripts/validate_repo.py            # full validation
    python3 scripts/validate_repo.py --links    # link integrity only
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Tuple

REPO = Path(__file__).resolve().parents[1]

GREEN = "\033[0;32m"
RED = "\033[0;31m"
YELLOW = "\033[1;33m"
BLUE = "\033[0;34m"
RESET = "\033[0m"

errors: List[str] = []
warnings: List[str] = []


def ok(message: str) -> None:
    print(f"{GREEN}[PASS]{RESET} {message}")


def fail(message: str) -> None:
    errors.append(message)
    print(f"{RED}[FAIL]{RESET} {message}")


def warn(message: str) -> None:
    warnings.append(message)
    print(f"{YELLOW}[WARN]{RESET} {message}")


def info(message: str) -> None:
    print(f"{BLUE}[INFO]{RESET} {message}")


# -- frontmatter ------------------------------------------------------------

def parse_frontmatter(text: str) -> Dict[str, str]:
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    block = text[4:end]
    result: Dict[str, str] = {}
    key = None
    for line in block.splitlines():
        if not line.strip():
            continue
        if re.match(r"^[A-Za-z_]+:", line):
            key, _, value = line.partition(":")
            key = key.strip()
            result[key] = value.strip().strip('"').strip("'")
        elif key:
            result[key] += " " + line.strip()
    return result


def check_skill() -> None:
    path = REPO / "SKILL.md"
    if not path.exists():
        fail("SKILL.md is missing")
        return
    text = path.read_text()
    front = parse_frontmatter(text)
    if not front:
        fail("SKILL.md has no YAML frontmatter")
        return

    name = front.get("name", "")
    description = front.get("description", "")
    if not re.match(r"^[a-z0-9][a-z0-9-]{0,63}$", name):
        fail(f"SKILL.md name is not a valid skill slug: {name!r}")
    elif len(name) > 64:
        fail("SKILL.md name exceeds 64 characters")
    else:
        ok(f"skill name '{name}' is valid")

    if not 20 <= len(description) <= 1024:
        fail(f"SKILL.md description must be 20-1024 characters (got {len(description)})")
    else:
        ok(f"skill description is {len(description)} characters")

    for field in ("license", "compatibility"):
        if field not in front:
            warn(f"SKILL.md frontmatter is missing '{field}'")


# -- structure --------------------------------------------------------------

REQUIRED = [
    "README.md", "SKILL.md", "LICENSE", "CHANGELOG.md", "CONTRIBUTING.md",
    "SECURITY.md", "CODE_OF_CONDUCT.md",
    "references", "checklists", "examples", "commands", "tools", "tests",
    "integrations/mcp-server/src/index.js",
    "integrations/mcp-server/package.json",
    "tools/lib/apple_native", "data/sf-symbols.json",
    "scripts/verify.sh", "scripts/verify-swift.sh",
    ".github/workflows/ci.yml",
]


def check_structure() -> None:
    missing = [item for item in REQUIRED if not (REPO / item).exists()]
    if missing:
        for item in missing:
            fail(f"required path missing: {item}")
    else:
        ok(f"all {len(REQUIRED)} required paths present")


def tool_dirs() -> List[Path]:
    return sorted(p for p in (REPO / "tools").iterdir() if p.is_dir() and p.name != "lib")


def check_tools() -> int:
    tools = tool_dirs()
    if not tools:
        fail("no tool directories found under tools/")
        return 0

    for tool in tools:
        scripts = list(tool.glob("*.py"))
        if not scripts:
            fail(f"{tool.name}: no Python entry point")
            continue
        if not (tool / "README.md").exists():
            warn(f"{tool.name}: no README.md")
        entry = next((s for s in scripts if "__main__" in s.read_text(errors="ignore")), scripts[0])
        source = entry.read_text()
        if not any(marker in source for marker in ('build_parser', '"--json"', "'--json'")):
            fail(f"{tool.name}: entry point does not support --json")
        if not source.lstrip().startswith("#!"):
            warn(f"{tool.name}: entry point has no shebang")
        docstring = source.split('"""')
        if len(docstring) < 3 or len(docstring[1]) < 60:
            warn(f"{tool.name}: module docstring is too thin to explain the tool")
    ok(f"{len(tools)} CLI tools structure validated")
    return len(tools)


# -- links ------------------------------------------------------------------

LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def markdown_files() -> List[Path]:
    files = [REPO / "README.md", REPO / "SKILL.md", REPO / "CHANGELOG.md",
             REPO / "CONTRIBUTING.md", REPO / "SECURITY.md", REPO / "CODE_OF_CONDUCT.md"]
    for directory in ("references", "checklists", "examples", "commands", "integrations",
                      "tools", "docs"):
        base = REPO / directory
        if base.exists():
            files.extend(
                path for path in base.rglob("*.md")
                if "node_modules" not in path.parts and ".swiftwork" not in path.parts
            )
    return [f for f in files if f.exists()]


def strip_code_fences(text: str) -> str:
    """Remove fenced code blocks so example syntax is not treated as links."""

    return re.sub(r"```.*?```", "", text, flags=re.DOTALL)


def check_links() -> int:
    checked = 0
    broken: List[Tuple[Path, str]] = []
    for md in markdown_files():
        for target in LINK_RE.findall(strip_code_fences(md.read_text(errors="ignore"))):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            if " " in target:  # prose inside backticks, e.g. `[noun](inflect: true)`
                continue
            clean = target.split("#", 1)[0]
            if not clean:
                continue
            clean = clean.removeprefix("file:///").removeprefix("file://")
            candidate = (md.parent / clean).resolve()
            checked += 1
            if not candidate.exists():
                broken.append((md, target))
    if broken:
        for md, target in broken[:20]:
            fail(f"broken link in {md.relative_to(REPO)}: {target}")
    else:
        ok(f"{checked} internal links resolve")
    return checked


# -- documented counts ------------------------------------------------------

def count_tests() -> int:
    """Count declared tests without running them (fast, deterministic)."""

    python_tests = 0
    for path in (REPO / "tests").glob("test_*.py"):
        python_tests += len(re.findall(r"^\s+def test_", path.read_text(errors="ignore"), re.MULTILINE))
    js_tests = 0
    for path in (REPO / "integrations" / "mcp-server" / "test").glob("*.test.js"):
        js_tests += len(re.findall(r"^\s+it\(", path.read_text(errors="ignore"), re.MULTILINE))
    return python_tests + js_tests


def mcp_tool_count() -> int:
    source = (REPO / "integrations/mcp-server/src/tools.js").read_text()
    block = source.split("TOOL_SPECS = [", 1)[-1]
    return len(re.findall(r'^\s{4}name: "', block, re.MULTILINE))

def check_counts(tool_count: int) -> None:
    readme = (REPO / "README.md").read_text()
    expectations = {
        "CLI tools": tool_count,
        "reference guides": len(list((REPO / "references").glob("*.md"))),
        "checklists": len(list((REPO / "checklists").glob("*.md"))),
        "worked examples": len(list((REPO / "examples").glob("*.md"))),
        "MCP tools": mcp_tool_count(),
    }
    test_count = count_tests()
    readme = (REPO / "README.md").read_text()
    if f"tests-{test_count}_passing" in readme:
        ok(f"README badge states {test_count} tests")
    else:
        fail(f"README badge does not state 'tests-{test_count}_passing' (suite has {test_count} tests)")

    for label, count in expectations.items():
        pattern = re.compile(rf"\b{count}\s+{re.escape(label)}\b")
        if pattern.search(readme):
            ok(f"README documents {count} {label}")
        else:
            fail(f"README does not state '{count} {label}' (filesystem says {count})")


# -- hygiene ----------------------------------------------------------------

def check_hygiene() -> None:
    offenders = []
    for md in markdown_files():
        for line_no, line in enumerate(md.read_text(errors="ignore").splitlines(), 1):
            if re.search(r"/Users/(?!YOUR_USERNAME|you|username)[A-Za-z0-9._-]+/", line):
                offenders.append(f"{md.relative_to(REPO)}:{line_no}")
    if offenders:
        for offender in offenders[:10]:
            fail(f"personal absolute path leaked: {offender}")
    else:
        ok("no personal absolute paths in documentation")

    catalogue = json.loads((REPO / "data" / "sf-symbols.json").read_text())
    if catalogue.get("count") != len(catalogue.get("symbols", {})):
        fail("data/sf-symbols.json count does not match its symbol map")
    else:
        ok(f"SF Symbols catalogue is internally consistent ({catalogue['count']} symbols)")


def main(argv: List[str]) -> int:
    print("=" * 66)
    print("  apple-native-engineer-mcp · repository validation")
    print("=" * 66)
    info(f"repository root: {REPO}")

    if "--links" in argv:
        check_links()
    else:
        check_skill()
        check_structure()
        tool_count = check_tools()
        check_links()
        check_counts(tool_count)
        check_hygiene()

    print("-" * 66)
    if errors:
        print(f"{RED}✗ validation failed{RESET}: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    print(f"{GREEN}✓ validation passed{RESET}: {len(warnings)} warning(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
