"""Swift source scanning utilities.

Everything the toolkit does with Swift source is textual: the tools must run
before a build exists, on a laptop, without SourceKit. To keep the analysis
honest we neutralise comments and string literals first, so that a
``// .foregroundColor(.red)`` in a comment is never reported as a real usage.

Line numbers and column offsets are preserved by replacing the removed
characters with spaces, which means every regex match can be mapped back to the
original file position.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

SWIFT_EXTS = {".swift"}
SKIP_DIRS = {
    ".git", ".build", "DerivedData", "build", "Pods", "Carthage",
    ".swiftpm", "node_modules", "venv", ".venv", "__pycache__",
}


def iter_files(root: Path, suffixes: Iterable[str] = (".swift",)) -> Iterator[Path]:
    """Yield files under *root* with one of *suffixes*, skipping build output."""

    wanted = {s.lower() for s in suffixes}
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in wanted:
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _blank(chunk: str) -> str:
    """Replace every non-newline character with a space (keeps offsets)."""

    return "".join("\n" if ch == "\n" else " " for ch in chunk)


def _strip(source: str, blank_strings: bool) -> str:
    """Return *source* with comments blanked out, optionally blanking literals."""

    out: List[str] = []
    i = 0
    n = len(source)

    while i < n:
        ch = source[i]
        nxt = source[i + 1] if i + 1 < n else ""

        # Line comment
        if ch == "/" and nxt == "/":
            end = source.find("\n", i)
            if end == -1:
                end = n
            out.append(_blank(source[i:end]))
            i = end
            continue

        # Block comment (Swift supports nested block comments)
        if ch == "/" and nxt == "*":
            depth = 0
            j = i
            while j < n:
                if source.startswith("/*", j):
                    depth += 1
                    j += 2
                elif source.startswith("*/", j):
                    depth -= 1
                    j += 2
                    if depth == 0:
                        break
                else:
                    j += 1
            out.append(_blank(source[i:j]))
            i = j
            continue

        # Raw string literals: #"..."#, ##"..."##
        if blank_strings and ch == "#":
            match = re.match(r'(#+)"', source[i:])
            if match:
                hashes = match.group(1)
                closing = '"' + hashes
                start_content = i + len(hashes) + 1
                end = source.find(closing, start_content)
                if end == -1:
                    end = n
                    stop = n
                else:
                    stop = end + len(closing)
                out.append('"' + _blank(source[start_content:end]) + '"')
                i = stop
                continue

        # Multi-line string literal: """..."""
        if blank_strings and source.startswith('"""', i):
            end = source.find('"""', i + 3)
            if end == -1:
                out.append(_blank(source[i:]))
                i = n
            else:
                out.append('"""' + _blank(source[i + 3:end]) + '"""')
                i = end + 3
            continue

        # Single-line string literal
        if blank_strings and ch == '"':
            j = i + 1
            while j < n:
                if source[j] == "\\":
                    j += 2
                    continue
                if source[j] == '"':
                    j += 1
                    break
                if source[j] == "\n":  # unterminated - bail out at newline
                    break
                j += 1
            out.append('"' + _blank(source[i + 1:max(j - 1, i + 1)]) + '"')
            i = j
            continue

        out.append(ch)
        i += 1

    return "".join(out)


def strip_comments(source: str) -> str:
    """Blank comment text but keep string literals intact.

    Use this when the *value* inside a literal matters (SF Symbol names, colour
    hex codes, user-facing copy). Use :func:`strip_comments_and_strings` when
    matching code so that a comment mentioning an API is never counted as usage.
    """

    return _strip(source, blank_strings=False)


def strip_comments_and_strings(source: str) -> str:
    """Blank both comments and string literals, preserving offsets."""

    return _strip(source, blank_strings=True)


@dataclass
class SwiftFile:
    """A Swift file plus its comment-free projection."""

    path: Path
    relative: str
    raw: str
    clean: str
    code: str = ""

    @property
    def lines(self) -> List[str]:
        return self.clean.splitlines()

    def line_of(self, offset: int) -> int:
        return self.clean.count("\n", 0, offset) + 1

    def column_of(self, offset: int) -> int:
        last_newline = self.clean.rfind("\n", 0, offset)
        return offset - last_newline

    def line_text(self, line_number: int) -> str:
        lines = self.clean.splitlines()
        if 1 <= line_number <= len(lines):
            return lines[line_number - 1]
        return ""


def load_swift_files(root: Path) -> List[SwiftFile]:
    files: List[SwiftFile] = []
    for path in iter_files(root, (".swift",)):
        try:
            raw = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        files.append(
            SwiftFile(
                path=path,
                relative=str(path.relative_to(root)) if path.is_relative_to(root) else str(path),
                raw=raw,
                clean=strip_comments_and_strings(raw),
                code=strip_comments(raw),
            )
        )
    return files


def find_all(pattern: str, source: str, flags: int = 0) -> Iterator[re.Match]:
    return re.finditer(pattern, source, flags)


def imports_of(source: str) -> List[str]:
    return re.findall(r"^\s*import\s+([A-Za-z_][\w.]*)", source, re.MULTILINE)


def has_symbol(source: str, name: str) -> bool:
    return re.search(rf"\b{re.escape(name)}\b", source) is not None


def declared_types(source: str) -> Dict[str, str]:
    """Map type name -> declaration keyword (struct/class/enum/actor/protocol)."""

    result: Dict[str, str] = {}
    for match in re.finditer(
        r"\b(struct|class|enum|actor|protocol)\s+([A-Z][A-Za-z0-9_]*)", source
    ):
        result[match.group(2)] = match.group(1)
    return result


def enclosing_type(source: str, offset: int) -> Optional[str]:
    """Best-effort name of the nearest type declared before *offset*."""

    names = [
        (m.end(), m.group(2))
        for m in re.finditer(r"\b(?:struct|class|enum|actor|protocol|extension)\s+([A-Z][A-Za-z0-9_]*)", source)
        if m.end() <= offset
    ]
    if not names:
        return None
    return names[-1][1]


def count_matches(pattern: str, source: str) -> int:
    return len(re.findall(pattern, source))


def normalise_identifier(text: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "", text).lower()
