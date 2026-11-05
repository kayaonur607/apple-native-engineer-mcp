"""Apple documentation research engine: parsing, caching and refusal behaviour.

No test touches the network. Saved payloads live in `tests/fixtures/apple-docs`
and are addressed by the same hash the cache uses, so the engine can be driven
through its real code path with `--fixtures`.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from support import REPO_ROOT, TOOLS

sys.path.insert(0, str(TOOLS / "apple-docs-research"))

import apple_docs  # noqa: E402

FIXTURES = REPO_ROOT / "tests" / "fixtures" / "apple-docs"


def run(args, expect=None):
    command = [str(TOOLS / "apple-docs-research" / "apple_docs.py"), *args,
               "--json", "--fixtures", str(FIXTURES)]
    import subprocess
    proc = subprocess.run([sys.executable, *command], capture_output=True, text=True)
    if expect is not None:
        assert proc.returncode == expect, f"{proc.stdout[:600]}\n{proc.stderr[:600]}"
    return json.loads(proc.stdout)


class PathTests(unittest.TestCase):
    def test_normalises_symbol_paths(self):
        self.assertEqual(apple_docs.normalise_path("swiftui/navigationstack"), ("documentation", "swiftui/navigationstack"))
        self.assertEqual(apple_docs.normalise_path("/documentation/swiftui/"), ("documentation", "swiftui"))

    def test_accepts_apple_urls_and_rejects_others(self):
        self.assertEqual(
            apple_docs.normalise_path("https://developer.apple.com/documentation/uikit/uiview"),
            ("documentation", "uikit/uiview"),
        )
        with self.assertRaises(apple_docs.ResearchError):
            apple_docs.normalise_path("https://example.com/documentation/evil")

    def test_hig_paths(self):
        kind, path = apple_docs.normalise_path("https://developer.apple.com/design/human-interface-guidelines/buttons")
        self.assertEqual((kind, path), ("design", "buttons"))


class FetchGuardTests(unittest.TestCase):
    def test_refuses_other_hosts(self):
        with self.assertRaises(apple_docs.ResearchError):
            apple_docs.HttpFetcher().fetch("https://evil.example.com/docs.json")

    def test_offline_without_cache_fails_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = apple_docs.Cache(Path(tmp))
            with self.assertRaises(apple_docs.ResearchError):
                apple_docs.load("https://developer.apple.com/x.json", cache, apple_docs.FileFetcher(FIXTURES),
                                offline=True)


class ReadTests(unittest.TestCase):
    def test_reads_and_renders_a_page(self):
        payload = run(["read", "swiftui/navigationstack"], expect=0)
        data = payload["data"]
        self.assertEqual(data["title"], "NavigationStack")
        self.assertIn("root view", data["abstract"].lower())
        self.assertIn("NavigationStack", data["markdown"])
        self.assertIn("```swift", data["markdown"])
        self.assertEqual(data["source_url"], apple_docs.document_url("documentation", "swiftui/navigationstack"))
        self.assertTrue(data["fetched_at"].endswith("Z"), "provenance must carry a timestamp")

    def test_platform_table_is_structured(self):
        payload = run(["availability", "swiftui/view/glassEffect(_:in:)"], expect=0)
        platforms = {row["platform"]: row for row in payload["data"]["platforms"]}
        self.assertEqual(platforms["iOS"]["introduced"], "26.0")
        # Apple omits visionOS entirely for this API; absence means unavailable,
        # which is why the tool reports supported platforms rather than inventing rows.
        self.assertNotIn("visionOS", platforms)

    def test_missing_page_is_an_error_not_a_guess(self):
        payload = run(["read", "swiftui/definitely-not-a-symbol"], expect=2)
        self.assertEqual(payload["status"], "fail")
        self.assertEqual(payload["findings"][0]["code"], "DOC000")


class SearchTests(unittest.TestCase):
    def test_ranks_exact_matches_first(self):
        payload = run(["search", "navigation", "--limit", "4"], expect=0)
        titles = [match["title"] for match in payload["data"]["matches"]]
        self.assertEqual(len(titles), 3)
        self.assertIn("NavigationStack", titles)
        self.assertIn("NavigationView", titles)
        self.assertNotIn("TabView", titles, "non-matching symbols must not be listed")

    def test_empty_result_warns(self):
        payload = run(["search", "zzzz-nothing"], expect=0)
        self.assertEqual(payload["status"], "warn")
        self.assertEqual(payload["findings"][0]["code"], "DOC030")


class GuidelinesTests(unittest.TestCase):
    def test_reads_a_hig_page(self):
        payload = run(["guidelines", "buttons"], expect=0)
        self.assertEqual(payload["data"]["title"], "Buttons")
        self.assertGreater(len(payload["data"]["markdown"]), 2_000)


class CacheTests(unittest.TestCase):
    def test_round_trip_and_expiry(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache = apple_docs.Cache(Path(tmp), max_age=3600)
            fetched_at = cache.write("https://developer.apple.com/x.json", {"a": 1})
            hit = cache.read("https://developer.apple.com/x.json")
            self.assertIsNotNone(hit)
            self.assertEqual(hit.payload, {"a": 1})
            self.assertTrue(hit.from_cache)
            self.assertLessEqual(hit.fetched_at, fetched_at)

            expired = apple_docs.Cache(Path(tmp), max_age=-1)
            self.assertIsNone(expired.read("https://developer.apple.com/x.json"))


if __name__ == "__main__":
    unittest.main()
