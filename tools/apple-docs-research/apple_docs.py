#!/usr/bin/env python3
"""Apple Documentation Research — read Apple's own documentation, with citations.

Apple's documentation site is served by a public JSON API that the site itself
uses (`developer.apple.com/tutorials/data/...`). That is what this tool reads: no
scraping of rendered HTML, no model recall, no invented quotes.

Three operations, one contract:

* ``search``       find symbol paths by title inside a framework index
* ``read``         fetch a page and render it as Markdown with provenance
* ``availability`` read the platform availability table for one symbol

Every response carries ``source_url`` and ``fetched_at`` so an answer can be
checked. If the network is unavailable and nothing is cached, the tool fails
loudly instead of guessing.

Usage::

    python3 tools/apple-docs-research/apple_docs.py read swiftui/view/glassEffect(_:in:)
    python3 tools/apple-docs-research/apple_docs.py search "navigation stack" --framework swiftui
    python3 tools/apple-docs-research/apple_docs.py availability swiftui/navigationstack
    python3 tools/apple-docs-research/apple_docs.py guidelines buttons
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "lib"))

from apple_native import __version__
from apple_native.cli import build_parser, emit
from apple_native.report import Report
from apple_native.http import open_trusted

DATA_BASE = "https://developer.apple.com/tutorials/data"
ALLOWED_HOSTS = {"developer.apple.com"}
USER_AGENT = "apple-native-engineer-mcp/2.1 (+https://github.com/kayaonur607/apple-native-engineer-mcp)"
DEFAULT_CACHE = Path.home() / ".cache" / "apple-native-engineer" / "apple-docs"
DEFAULT_MAX_AGE = 7 * 24 * 3600


class ResearchError(RuntimeError):
    """Raised when a document cannot be retrieved or understood."""


# --------------------------------------------------------------------------- #
# Fetching and caching
# --------------------------------------------------------------------------- #


@dataclass
class Document:
    url: str
    payload: dict
    fetched_at: int
    from_cache: bool = False
    from_network: bool = False


class Cache:
    def __init__(self, directory: Path, max_age: int = DEFAULT_MAX_AGE) -> None:
        self.directory = directory
        self.max_age = max_age
        self.directory.mkdir(parents=True, exist_ok=True)

    def _path(self, url: str) -> Path:
        digest = hashlib.sha256(url.encode()).hexdigest()[:32]
        return self.directory / f"{digest}.json"

    def read(self, url: str) -> Optional[Document]:
        path = self._path(url)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text())
        except (OSError, json.JSONDecodeError):
            return None
        stored_at = int(payload.get("_stored_at", 0))
        if time.time() - stored_at > self.max_age:
            return None
        return Document(url=url, payload=payload.get("body", {}), fetched_at=stored_at, from_cache=True)

    def write(self, url: str, body: dict) -> int:
        now = int(time.time())
        self._path(url).write_text(json.dumps({"_stored_at": now, "_url": url, "body": body}))
        return now


class HttpFetcher:
    """Fetches JSON from developer.apple.com only, with a polite user agent."""

    def __init__(self, timeout: float = 20.0, retries: int = 2) -> None:
        self.timeout = timeout
        self.retries = retries

    def fetch(self, url: str) -> dict:
        host = urllib.parse.urlparse(url).hostname or ""
        if host not in ALLOWED_HOSTS:
            raise ResearchError(f"refusing to fetch {host or 'unknown host'}: only developer.apple.com is allowed")

        last_error = ""
        for attempt in range(self.retries + 1):
            request = urllib.request.Request(url, headers={
                "User-Agent": USER_AGENT,
                "Accept": "application/json",
            })
            try:
                with open_trusted(request, ALLOWED_HOSTS, timeout=self.timeout) as response:
                    return json.loads(response.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                if exc.code == 404:
                    raise ResearchError(f"Apple has no document at {url} (404)") from exc
                last_error = f"HTTP {exc.code}"
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                last_error = str(exc)
            if attempt < self.retries:
                time.sleep(1.5 ** attempt)
        raise ResearchError(f"could not fetch {url}: {last_error}")


class FileFetcher:
    """Reads saved payloads from disk; used by tests and by --from-fixture."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory

    def fetch(self, url: str) -> dict:
        digest = hashlib.sha256(url.encode()).hexdigest()[:32]
        candidate = self.directory / f"{digest}.json"
        if not candidate.exists():
            raise ResearchError(f"fixture not found for {url} ({candidate.name})")
        return json.loads(candidate.read_text())


def load(url: str, cache: Cache, fetcher, refresh: bool = False, offline: bool = False) -> Document:
    if not refresh:
        cached = cache.read(url)
        if cached is not None:
            return cached
    if offline:
        raise ResearchError(f"offline and not cached: {url}")
    body = fetcher.fetch(url)
    fetched_at = cache.write(url, body)
    return Document(url=url, payload=body, fetched_at=fetched_at, from_network=True)


# --------------------------------------------------------------------------- #
# Normalising a path
# --------------------------------------------------------------------------- #


def normalise_path(raw: str) -> tuple[str, str]:
    """Return ``(kind, path)`` where kind is ``documentation`` or ``design``."""

    value = raw.strip()
    if value.startswith("http"):
        parsed = urllib.parse.urlparse(value)
        if parsed.hostname not in ALLOWED_HOSTS:
            raise ResearchError("only developer.apple.com URLs are accepted")
        value = parsed.path

    value = value.split("#", 1)[0].rstrip("/")
    value = re.sub(r"^/documentation/", "", value)
    value = re.sub(r"^/design/human-interface-guidelines/", "HIG:", value)
    if value.startswith("HIG:"):
        return "design", value[4:]
    return "documentation", value


def document_url(kind: str, path: str) -> str:
    if kind == "design":
        return f"{DATA_BASE}/design/human-interface-guidelines/{path}.json"
    return f"{DATA_BASE}/documentation/{path}.json"


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


#: The ``references`` map of the payload being rendered, so inline links can
#: show Apple's own titles and URLs instead of bare identifiers.
_REFERENCES: Dict[str, dict] = {}


def inline_text(items: Optional[Iterable[dict]]) -> str:
    parts: List[str] = []
    for item in items or []:
        kind = item.get("type")
        if kind == "text":
            parts.append(item.get("text", ""))
        elif kind == "codeVoice":
            parts.append(f"`{item.get('code', '')}`")
        elif kind == "reference":
            identifier = item.get("identifier", "")
            reference = _REFERENCES.get(identifier, {})
            title = inline_text(item.get("overridingTitleInlineContent")) or reference.get("title")
            url = reference.get("url", "")
            if url.startswith("/"):
                url = f"https://developer.apple.com{url}"
            label = title or identifier.split("/")[-1]
            parts.append(f"[{label}]({url})" if url else label)
        elif kind == "emphasis" or kind == "strong":
            parts.append(inline_text(item.get("inlineContent")))
        else:
            parts.append(inline_text(item.get("inlineContent")))
    return "".join(parts).strip()


def table_cell(cell: Any) -> str:
    """Render one DocC table cell (a list of blocks, or a single block) on one line."""

    if isinstance(cell, dict):
        if "inlineContent" in cell:
            return inline_text(cell.get("inlineContent")).replace("|", "\\|")
        return render_block(cell).strip().replace("\n", " ").replace("|", "\\|")
    if isinstance(cell, list):
        return " ".join(table_cell(part) for part in cell).strip()
    return str(cell)


def render_block(block: Any, depth: int = 0) -> str:
    if not isinstance(block, dict):
        if isinstance(block, list):
            # A DocC table row is a list of cells; each cell is a list of blocks.
            return " | ".join(table_cell(cell) for cell in block)
        return ""
    kind = block.get("type")
    if kind == "heading":
        level = block.get("level", 2)
        return f"{'#' * min(level + 1, 6)} {block.get('text', '')}\n"
    if kind == "paragraph":
        return inline_text(block.get("inlineContent")) + "\n"
    if kind == "codeListing":
        code = "\n".join(block.get("code", []))
        language = (block.get("syntax") or "swift").lower()
        return f"```{language}\n{code}\n```\n"
    if kind == "aside":
        label = block.get("name") or block.get("style") or "Note"
        body = "\n".join(render_block(item, depth + 1) for item in block.get("content", []))
        return f"> **{label}.** {body.strip()}\n"
    if kind in ("unorderedList", "orderedList"):
        lines = []
        for index, item in enumerate(block.get("items", []), start=1):
            bullet = "-" if kind == "unorderedList" else f"{index}."
            content = " ".join(render_block(part, depth + 1).strip() for part in item.get("content", []))
            lines.append(f"{bullet} {content}")
        return "\n".join(lines) + "\n"
    if kind == "termList":
        lines = []
        for item in block.get("items", []):
            term = inline_text(item.get("term", {}).get("inlineContent"))
            definition = " ".join(render_block(part, depth + 1).strip() for part in item.get("definition", []))
            lines.append(f"- **{term}** — {definition}")
        return "\n".join(lines) + "\n"
    if kind == "row":
        cells = [inline_text(cell.get("inlineContent")) for cell in block.get("columns", block.get("content", []))]
        return " | ".join(cells)
    if kind == "table":
        rows = block.get("rows", [])
        rendered = [render_block(row, depth + 1) for row in rows]
        rendered = [row for row in rendered if row.strip(" |")]
        if not rendered:
            return ""
        lines = [f"| {rendered[0]} |"]
        columns = rendered[0].count(" | ") + 1
        if block.get("header") in ("row", "both"):
            lines.append("|" + " --- |" * columns)
        else:
            lines.insert(0, "|" + "   |" * columns)
            lines.insert(1, "|" + " --- |" * columns)
        lines.extend(f"| {row} |" for row in rendered[1:])
        return "\n".join(lines) + "\n"
    if kind == "links":
        return "\n".join(f"- {inline_text([item]) if isinstance(item, dict) else item}" for item in block.get("items", [])) + "\n"
    return ""


def render_sections(payload: dict) -> str:
    chunks: List[str] = []
    for section in payload.get("primaryContentSections", []):
        kind = section.get("kind")
        if kind == "declarations":
            for declaration in section.get("declarations", []):
                code = "".join(token.get("text", "") for token in declaration.get("tokens", []))
                if code.strip():
                    chunks.append(f"```swift\n{code.strip()}\n```\n")
        elif kind == "content":
            for block in section.get("content", []):
                rendered = render_block(block)
                if rendered:
                    chunks.append(rendered)
        elif kind == "parameters":
            parameters = section.get("parameters", [])
            if parameters:
                lines = ["**Parameters**", ""]
                for parameter in parameters:
                    text = " ".join(render_block(b) for b in parameter.get("content", []))
                    lines.append(f"- `{parameter.get('name')}` — {text.strip()}")
                chunks.append("\n".join(lines) + "\n")
    return "\n".join(chunks).strip() + "\n"


def platform_table(payload: dict) -> List[Dict[str, Any]]:
    rows = []
    for platform in payload.get("metadata", {}).get("platforms", []) or []:
        rows.append({
            "platform": platform.get("name"),
            "introduced": platform.get("introducedAt"),
            "deprecated": platform.get("deprecatedAt"),
            "beta": bool(platform.get("beta")),
            "unavailable": bool(platform.get("unavailable")),
        })
    return rows


def related_symbols(payload: dict) -> List[Dict[str, str]]:
    references = payload.get("references", {})
    related: List[Dict[str, str]] = []
    for section in payload.get("topicSections", []) or []:
        title = section.get("title", "Related")
        for identifier in section.get("identifiers", [])[:12]:
            reference = references.get(identifier, {})
            if reference.get("title"):
                related.append({"group": title, "title": reference["title"], "path": reference.get("url", "")})
    return related


def read_document(payload: dict) -> Dict[str, Any]:
    global _REFERENCES
    _REFERENCES = payload.get("references", {}) or {}
    metadata = payload.get("metadata", {})
    return {
        "title": metadata.get("title"),
        "role": metadata.get("roleHeading"),
        "abstract": inline_text(payload.get("abstract")),
        "platforms": platform_table(payload),
        "markdown": render_sections(payload),
        "related": related_symbols(payload),
        "symbols": [symbol.get("title") for symbol in payload.get("metadata", {}).get("symbolKinds", []) or []],
    }


# --------------------------------------------------------------------------- #
# Operations
# --------------------------------------------------------------------------- #


def operation_read(raw_path: str, cache: Cache, fetcher, refresh: bool, offline: bool) -> Report:
    kind, path = normalise_path(raw_path)
    url = document_url(kind, path)
    report = Report(tool="apple-docs-research", target=raw_path, version=__version__)
    document = load(url, cache, fetcher, refresh=refresh, offline=offline)
    rendered = read_document(document.payload)

    if not rendered["title"] and not rendered["markdown"]:
        report.error("DOC001", f"Apple returned a document without a title or body: {url}")
        return report

    report.data = {
        "title": rendered["title"],
        "role": rendered["role"],
        "abstract": rendered["abstract"],
        "platforms": rendered["platforms"],
        "markdown": rendered["markdown"],
        "related": rendered["related"][:20],
        "source_url": url,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(document.fetched_at)),
        "from_cache": document.from_cache,
    }
    if document.from_cache:
        report.info("DOC010", "Served from the local cache; re-run with --refresh for the current page.")
    if any(row["deprecated"] for row in rendered["platforms"]):
        report.warn("DOC011", "This API is deprecated on at least one platform.")
    return report


def operation_availability(raw_path: str, cache: Cache, fetcher, refresh: bool, offline: bool) -> Report:
    kind, path = normalise_path(raw_path)
    url = document_url(kind, path)
    report = Report(tool="apple-docs-research", target=raw_path, version=__version__)
    document = load(url, cache, fetcher, refresh=refresh, offline=offline)
    rows = platform_table(document.payload)

    report.data = {
        "title": document.payload.get("metadata", {}).get("title"),
        "platforms": rows,
        "source_url": url,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(document.fetched_at)),
    }
    if not rows:
        report.warn("DOC020", "Apple publishes no platform availability for this page.")
    return report


def operation_search(query: str, framework: str, cache: Cache, fetcher, refresh: bool,
                     offline: bool, limit: int) -> Report:
    report = Report(tool="apple-docs-research", target=query, version=__version__)
    index_url = f"{DATA_BASE}/index/{framework}"
    document = load(index_url, cache, fetcher, refresh=refresh, offline=offline)

    nodes: List[Dict[str, str]] = []

    def walk(entries: Optional[Iterable[dict]]) -> None:
        for entry in entries or []:
            if not isinstance(entry, dict):
                continue
            title = entry.get("title")
            path = entry.get("path")
            if title and path:
                nodes.append({"title": title, "path": path})
            walk(entry.get("children"))

    walk(document.payload.get("interfaceLanguages", {}).get("swift", []))

    query_lower = query.lower()
    scored = []
    for node in nodes:
        title = node["title"].lower()
        if query_lower in title:
            scored.append((0 if title == query_lower else (1 if title.startswith(query_lower) else 2), node))
    scored.sort(key=lambda item: (item[0], len(item[1]["title"])))
    matches = [node for _, node in scored[:limit]]

    report.data = {
        "framework": framework,
        "query": query,
        "matches": matches,
        "indexed_symbols": len(nodes),
        "source_url": index_url,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(document.fetched_at)),
    }
    if not matches:
        report.warn("DOC030", f"No symbol matched '{query}' in the {framework} index.",
                    hint="Try a shorter query, or pass --framework for another module (e.g. uikit, appkit).")
    return report


def operation_guidelines(page: str, cache: Cache, fetcher, refresh: bool, offline: bool) -> Report:
    report = Report(tool="apple-docs-research", target=page, version=__version__)
    url = document_url("design", page.strip("/"))
    document = load(url, cache, fetcher, refresh=refresh, offline=offline)
    rendered = read_document(document.payload)
    report.data = {
        "title": rendered["title"],
        "abstract": rendered["abstract"],
        "markdown": rendered["markdown"],
        "source_url": url,
        "fetched_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(document.fetched_at)),
        "from_cache": document.from_cache,
    }
    if not rendered["markdown"] and not rendered["abstract"]:
        report.warn("DOC040", "This Human Interface Guidelines page rendered empty; open the source URL.")
    return report


HIG_CATALOG = Path(__file__).resolve().parents[2] / "data" / "hig-catalog.json"

#: Words that point at a platform's "Designing for …" page.
PLATFORM_PAGES = {
    "ios": "designing-for-ios", "iphone": "designing-for-ios", "ipados": "designing-for-ipados",
    "ipad": "designing-for-ipados", "macos": "designing-for-macos", "mac": "designing-for-macos",
    "tvos": "designing-for-tvos", "tv": "designing-for-tvos", "visionos": "designing-for-visionos",
    "vision": "designing-for-visionos", "watchos": "designing-for-watchos", "watch": "designing-for-watchos",
    "duo": "designing-for-iphone-duo", "foldable": "designing-for-iphone-duo", "games": "designing-for-games",
}


def operation_guidelines_search(query: str, section: Optional[str], limit: int,
                                catalog_path: Path = HIG_CATALOG) -> Report:
    """Rank HIG pages from the offline table of contents. No network."""

    report = Report(tool="apple-docs-research", target=query or "(all)", version=__version__)
    try:
        catalogue = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        report.error("DOC050", f"HIG catalogue unavailable: {exc}",
                     hint="Run python3 scripts/build_hig_catalog.py to rebuild data/hig-catalog.json.")
        return report

    pages = catalogue.get("pages", [])
    if section:
        wanted = section.strip().lower()
        pages = [page for page in pages if wanted in (page.get("section") or "").lower()
                 or wanted in (page.get("group") or "").lower()]

    terms = [term for term in re.split(r"[^a-z0-9]+", (query or "").lower()) if term]
    scored = []
    for page in pages:
        slug = page["slug"]
        title = page["title"].lower()
        abstract = (page.get("abstract") or "").lower()
        score = 0
        for term in terms:
            if PLATFORM_PAGES.get(term) == slug:
                score += 12
            if term == slug or term in slug.split("-"):
                score += 8
            elif term in slug:
                score += 5
            if term in title:
                score += 6
            if term in abstract:
                score += 2
        if not terms:
            score = 1
        if score:
            scored.append((score, page))
    scored.sort(key=lambda item: (-item[0], item[1]["slug"]))
    matches = [{**page, "score": score} for score, page in scored[:max(1, limit)]]

    report.data = {
        "query": query,
        "section": section,
        "matches": matches,
        "catalogued_pages": catalogue.get("count"),
        "catalog_retrieved": catalogue.get("retrieved"),
        "source_url": catalogue.get("source"),
        "next_step": "Call find_apple_guidelines with a match's slug to read the live page and cite its URL.",
    }
    if not matches:
        report.warn("DOC051", f"No HIG page matched '{query}'.",
                    hint="Try one concrete noun (e.g. 'tab', 'sheet', 'widgets') or drop the section filter.")
    return report


def main(argv=None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="apple-docs-research",
        description="Read Apple's official documentation with citations, from the JSON API the site itself uses.",
        epilog="Exit codes: 0 success, 1 warnings with --strict, 2 failure.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = parser.add_subparsers(dest="command", required=True)

    read_cmd = sub.add_parser("read", help="Fetch a documentation page and render it as Markdown")
    read_cmd.add_argument("path", help="Symbol path, e.g. swiftui/view/glassEffect(_:in:) or a developer.apple.com URL")

    availability_cmd = sub.add_parser("availability", help="Platform availability for one symbol")
    availability_cmd.add_argument("path")

    search_cmd = sub.add_parser("search", help="Search a framework's symbol index")
    search_cmd.add_argument("query")
    search_cmd.add_argument("--framework", default="swiftui", help="swiftui (default), uikit, appkit, foundation, …")
    search_cmd.add_argument("--limit", type=int, default=10)

    guidelines_cmd = sub.add_parser("guidelines", help="Read a Human Interface Guidelines page")
    guidelines_cmd.add_argument("page", help="e.g. buttons, navigation-and-search, materials")

    hig_search_cmd = sub.add_parser("guidelines-search",
                                    help="Find Human Interface Guidelines pages in the offline catalogue")
    hig_search_cmd.add_argument("query", nargs="?", default="", help="e.g. 'tab bar', 'tvos focus', 'onboarding'")
    hig_search_cmd.add_argument("--section", help="Foundations, Patterns, Components, Inputs, Technologies, …")
    hig_search_cmd.add_argument("--limit", type=int, default=10)

    for command in (read_cmd, availability_cmd, search_cmd, guidelines_cmd, hig_search_cmd):
        command.add_argument("--json", action="store_true", help="Emit the machine-readable envelope")
        command.add_argument("--strict", action="store_true")
        command.add_argument("--color", choices=("auto", "always", "never"), default="auto")
        command.add_argument("--refresh", action="store_true", help="Bypass the cache")
        command.add_argument("--offline", action="store_true", help="Use the cache only; never touch the network")
        command.add_argument("--cache-dir", default=str(DEFAULT_CACHE))
        command.add_argument("--max-age", type=int, default=DEFAULT_MAX_AGE, help="Cache lifetime in seconds")
        command.add_argument("--fixtures", help="Read payloads from a directory instead of the network (tests)")

    args = parser.parse_args(argv)
    if getattr(args, "fixtures", None):
        # Fixtures must be hermetic: never let a warm user cache answer a test.
        import tempfile as _tempfile
        cache = Cache(Path(_tempfile.mkdtemp(prefix="anm-docs-")), max_age=args.max_age)
        fetcher = FileFetcher(Path(args.fixtures))
    else:
        cache = Cache(Path(args.cache_dir).expanduser(), max_age=args.max_age)
        fetcher = HttpFetcher()

    try:
        if args.command == "guidelines-search":
            report = operation_guidelines_search(args.query, args.section, args.limit)
        elif args.command == "read":
            report = operation_read(args.path, cache, fetcher, args.refresh, args.offline)
        elif args.command == "availability":
            report = operation_availability(args.path, cache, fetcher, args.refresh, args.offline)
        elif args.command == "search":
            report = operation_search(args.query, args.framework, cache, fetcher,
                                      args.refresh, args.offline, args.limit)
        else:
            report = operation_guidelines(args.page, cache, fetcher, args.refresh, args.offline)
    except ResearchError as exc:
        report = Report(tool="apple-docs-research", target=getattr(args, "path", args.command), version=__version__)
        report.error("DOC000", str(exc),
                     hint="Check the path, or drop --offline to allow a live fetch from developer.apple.com.")

    return emit(report, args, title="Apple Native Engineer — Apple documentation")


if __name__ == "__main__":
    raise SystemExit(main())
