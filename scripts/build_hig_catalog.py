#!/usr/bin/env python3
"""Rebuild data/hig-catalog.json from Apple's Human Interface Guidelines index.

The catalogue lets an agent find the right HIG page offline (title, abstract,
section, URL) before fetching it live with `find_apple_guidelines`. It is a map
of Apple's own table of contents, not a copy of the guidance itself.

Usage::

    python3 scripts/build_hig_catalog.py            # fetch and rewrite
    python3 scripts/build_hig_catalog.py --check    # fail if the file is malformed
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools" / "lib"))
sys.path.insert(0, str(ROOT / "tools" / "apple-docs-research"))

import apple_docs  # noqa: E402

OUT = ROOT / "data" / "hig-catalog.json"
BASE = f"{apple_docs.DATA_BASE}/design/human-interface-guidelines"
HIG_ROOT = "https://developer.apple.com/design/human-interface-guidelines"


def fetch(fetcher, slug: str) -> dict:
    return fetcher.fetch(f"{BASE}/{slug}.json")


def text_of(items) -> str:
    return "".join(item.get("text", "") for item in items or [] if isinstance(item, dict)).strip()


def children(payload: dict):
    references = payload.get("references", {})
    for section in payload.get("topicSections", []) or []:
        for identifier in section.get("identifiers", []):
            reference = references.get(identifier, {})
            url = reference.get("url", "")
            if not url.startswith("/design/human-interface-guidelines/"):
                continue
            yield {
                "slug": url.rsplit("/", 1)[-1],
                "title": reference.get("title", ""),
                "abstract": text_of(reference.get("abstract")),
                "url": f"https://developer.apple.com{url}",
            }


def build() -> dict:
    fetcher = apple_docs.HttpFetcher()
    root = fetcher.fetch(f"{BASE}.json")
    pages = []
    for section in children(root):
        payload = fetch(fetcher, section["slug"])
        for entry in children(payload):
            grandchildren = list(children(fetch(fetcher, entry["slug"]))) if section["slug"] == "components" else []
            if grandchildren:
                for leaf in grandchildren:
                    pages.append({**leaf, "section": section["title"], "group": entry["title"]})
            else:
                pages.append({**entry, "section": section["title"], "group": None})
    return {
        "schema_version": "1",
        "source": HIG_ROOT,
        "retrieved": time.strftime("%Y-%m-%d", time.gmtime()),
        "note": "Apple's HIG table of contents (titles, abstracts, URLs). Fetch a page with find_apple_guidelines for the guidance itself.",
        "count": len(pages),
        "pages": pages,
    }


def check(path: Path = OUT) -> int:
    catalogue = json.loads(path.read_text(encoding="utf-8"))
    slugs = [page["slug"] for page in catalogue["pages"]]
    problems = []
    if catalogue.get("count") != len(slugs):
        problems.append("count does not match pages")
    if len(set(slugs)) != len(slugs):
        problems.append("duplicate slugs")
    if any(not page.get("title") or not page.get("url", "").startswith(HIG_ROOT) for page in catalogue["pages"]):
        problems.append("page without a title or an Apple HIG URL")
    for problem in problems:
        print(f"hig-catalog: {problem}", file=sys.stderr)
    return 1 if problems else 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    if args.check:
        return check()
    catalogue = build()
    OUT.write_text(json.dumps(catalogue, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {catalogue['count']} HIG pages to {OUT.relative_to(ROOT)}")
    return check()


if __name__ == "__main__":
    raise SystemExit(main())
