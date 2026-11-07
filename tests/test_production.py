"""Store production and distribution: specs, capture plans, audits, composition, release plans.

Nothing here boots a simulator or contacts Apple. The capture tool is driven
through a fake ``simctl`` runner, so the real command sequence is asserted
without side effects.
"""

from __future__ import annotations

import json
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

from support import CLEAN, FIXTURES, REPO_ROOT, TOOLS, codes, load_module, run_tool

from apple_native.imaging import SCREENSHOT_SPECS, load_app_store_specs, match_screenshot_spec
from apple_native.report import Report

sys.path.insert(0, str(TOOLS / "apple-docs-research"))
import apple_docs  # noqa: E402

capture_batch = load_module("capture_batch", "screenshot-studio/capture_batch.py")
compose = load_module("compose_marketing", "screenshot-studio/compose_marketing.py")

DISTRIBUTION = FIXTURES / "distribution-app"


def write_png(path: Path, width: int, height: int, alpha: bool) -> None:
    channels = 4 if alpha else 3
    row = b"\x00" + b"\x40" * (width * channels)
    raw = row * height

    def chunk(kind: bytes, payload: bytes) -> bytes:
        return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload))

    header = struct.pack(">IIBBBBB", width, height, 8, 6 if alpha else 2, 0, 0, 0)
    path.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) + chunk(b"IDAT", zlib.compress(raw))
                     + chunk(b"IEND", b""))


class SpecificationTests(unittest.TestCase):
    def test_specs_are_dated_sourced_and_consistent(self):
        specs = load_app_store_specs()
        self.assertRegex(specs["retrieved"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertTrue(specs["sources"]["screenshots"].startswith("https://developer.apple.com/"))
        ids = [slot["id"] for slot in specs["screenshots"]["slots"]]
        self.assertEqual(len(ids), len(set(ids)))
        for slot in specs["screenshots"]["slots"]:
            self.assertTrue(slot["portrait"] or slot["landscape"], slot["id"])
            for width, height in slot["portrait"]:
                self.assertGreater(height, width, slot["id"])
            for width, height in slot["landscape"]:
                self.assertGreater(width, height, slot["id"])

    def test_current_apple_sizes(self):
        self.assertEqual(match_screenshot_spec(1206, 2622)[0], 'iPhone 6.3"')
        self.assertEqual(match_screenshot_spec(1260, 2736)[0], 'iPhone 6.9"')
        self.assertEqual(match_screenshot_spec(422, 514)[0], "Apple Watch Ultra 3/4")
        self.assertEqual(match_screenshot_spec(2007, 2853)[0], "iPhone Duo inner display")
        self.assertEqual(match_screenshot_spec(1920, 1080)[0], "Apple TV")

    def test_mac_accepts_only_published_sizes(self):
        self.assertNotIn((3840, 2160), SCREENSHOT_SPECS["Mac"]["landscape"])
        self.assertEqual(SCREENSHOT_SPECS["Mac"]["portrait"], ())


class ScreenshotAuditTests(unittest.TestCase):
    def test_alpha_and_set_size_are_reported(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "en-US"
            root.mkdir()
            for index in range(11):
                write_png(root / f"{index:02}.png", 1206, 2622, alpha=index == 0)
            envelope = run_tool("screenshot-studio/screenshot_studio.py", "--screenshots", tmp, "--platforms", "ios")
            found = codes(envelope)
            self.assertIn("SHOT013", found)
            self.assertIn("SHOT021", found)
            self.assertEqual(envelope["data"]["locales"], ["en-US"])
            self.assertEqual(envelope["data"]["sets"]["en-US"]["iphone-6.3"]["count"], 11)

    def test_watch_sizes_must_match_across_locales(self):
        with tempfile.TemporaryDirectory() as tmp:
            for locale, size in (("en-US", (422, 514)), ("de-DE", (416, 496))):
                (Path(tmp) / locale).mkdir()
                write_png(Path(tmp) / locale / "01.png", *size, alpha=False)
            envelope = run_tool("screenshot-studio/screenshot_studio.py", "--screenshots", tmp)
            self.assertIn("SHOT023", codes(envelope))

    def test_unknown_platform_is_an_error(self):
        envelope = run_tool("screenshot-studio/screenshot_studio.py", "--screenshots", str(CLEAN / "screenshots"),
                            "--platforms", "symbian", expect=2)
        self.assertIn("SHOT031", codes(envelope))


class CapturePlanTests(unittest.TestCase):
    def plan(self, **overrides):
        payload = {"bundle_id": "dev.example.app", "devices": ["iphone-6.9"], "locales": ["en-US", "tr-TR"],
                   "appearances": ["light"], "screens": [{"name": "01-home", "arguments": ["-screen", "home"]}]}
        payload.update(overrides)
        handle = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False)
        json.dump(payload, handle)
        handle.close()
        self.addCleanup(Path(handle.name).unlink)
        return Path(handle.name)

    def test_rejects_invalid_plans(self):
        for overrides in ({"bundle_id": "bad id"}, {"locales": ["english"]}, {"appearances": ["sepia"]},
                          {"screens": [{"name": "../escape"}]}, {"devices": []},
                          {"status_bar": {"carrier": "x"}}):
            with self.assertRaises(capture_batch.PlanError, msg=overrides):
                capture_batch.load_plan(self.plan(**overrides))

    def test_slot_ids_resolve_to_simulators(self):
        self.assertEqual(capture_batch.device_name_for("iphone-6.9"), "iPhone 18 Pro Max")
        self.assertEqual(capture_batch.device_name_for("iPad Pro 13-inch (M5)"), "iPad Pro 13-inch (M5)")
        with self.assertRaises(capture_batch.PlanError):
            capture_batch.device_name_for("iphone-3.5")

    def test_locale_arguments(self):
        self.assertEqual(capture_batch.apple_locale("tr-TR"), "tr_TR")
        self.assertEqual(capture_batch.apple_locale("zh-Hans-CN"), "zh_CN")
        self.assertEqual(capture_batch.apple_locale("de"), "de")

    def test_executes_the_expected_simctl_sequence(self):
        calls = []
        inventory = {"devices": {"com.apple.CoreSimulator.SimRuntime.iOS-27-2": [
            {"name": "iPhone 18 Pro Max", "udid": "UDID-1", "state": "Shutdown", "isAvailable": True}]},
            "devicetypes": [], "runtimes": []}

        def runner(command, timeout):
            calls.append(command)
            if command[2:4] == ["list", "--json"]:
                return subprocess.CompletedProcess(command, 0, json.dumps(inventory), "")
            if command[2:4] == ["io", "UDID-1"]:
                write_png(Path(command[-1]), 1320, 2868, alpha=False)
            return subprocess.CompletedProcess(command, 0, "", "")

        plan = capture_batch.load_plan(self.plan())
        with tempfile.TemporaryDirectory() as tmp:
            report = Report(tool="capture-batch", target="test", version="test")
            capture_batch.capture(plan, Path(tmp), report, dry_run=False, runner=runner, sleep=lambda _: None)
            manifest = json.loads((Path(tmp) / "manifest.json").read_text())
            self.assertEqual(len(manifest["captures"]), 2)
            self.assertTrue((Path(tmp) / "tr-TR" / "iphone-18-pro-max" / "01-home.png").exists())
        verbs = [command[2] for command in calls]
        self.assertEqual(verbs[:5], ["list", "boot", "bootstatus", "status_bar", "ui"])
        launches = [command for command in calls if command[2] == "launch"]
        self.assertIn("tr_TR", launches[1])
        self.assertIn("-screen", launches[0])
        self.assertNotIn("CAP031", [finding.code for finding in report.findings])


    def test_reuses_a_simulator_it_created_before(self):
        inventory = {"devices": {"rt": [{"name": "ANE iPhone 18 Pro Max", "udid": "OLD", "state": "Shutdown"}]},
                     "devicetypes": [{"name": "iPhone 18 Pro Max", "identifier": "type"}], "runtimes": []}
        calls = []

        def runner(command, timeout):
            calls.append(command)
            return subprocess.CompletedProcess(command, 0, json.dumps(inventory), "")

        simulator = capture_batch.Simulator(runner, [], dry_run=False)
        self.assertEqual(simulator.resolve("iPhone 18 Pro Max")["udid"], "OLD")
        self.assertFalse(any(command[2] == "create" for command in calls))


class CompositionTests(unittest.TestCase):
    def test_caption_lookup_falls_back_by_language_then_star(self):
        captions = {"tr": {"01-home": {"headline": "Merhaba"}}, "*": {"*": {"headline": "Hello"}}}
        self.assertEqual(compose.caption_for(captions, "tr-TR", "01-home-light"), ({"headline": "Merhaba"}, "tr"))
        self.assertEqual(compose.caption_for(captions, "de-DE", "01-home")[1], "*")

    def test_rtl_and_device_frame_layout(self):
        layout = compose.build_layout((1320, 2868), (1320, 2868), "مرحبا", "", "dark", "caption-top", "auto",
                                      compose.is_rtl("ar-SA"), "center")
        self.assertTrue(layout["texts"][0]["rtl"])
        self.assertEqual(layout["frame"], "device")
        self.assertIn("island", layout)
        image = layout["image"]
        self.assertAlmostEqual(image["height"] / image["width"], 2868 / 1320, places=2)
        self.assertLessEqual(layout["device"]["y"] + layout["device"]["height"], 2868)

    def test_landscape_uses_rounded_capture(self):
        layout = compose.build_layout((2880, 1800), (2880, 1800), "Mac", "", "light", "caption-top", "auto",
                                      False, "center")
        self.assertEqual(layout["frame"], "none")
        self.assertNotIn("device", layout)

    def test_watch_captures_are_not_framed(self):
        with tempfile.TemporaryDirectory() as tmp:
            write_png(Path(tmp) / "watch.png", 422, 514, alpha=False)
            envelope = run_tool("screenshot-studio/compose_marketing.py", "--screenshots", tmp, "--out",
                                str(Path(tmp) / "out"))
            self.assertIn("SHOT114", codes(envelope))
            self.assertEqual(envelope["data"]["composed"], 0)


class DistributionTests(unittest.TestCase):
    def test_app_store_plan(self):
        envelope = run_tool("distribution/plan_distribution.py", str(DISTRIBUTION))
        found = codes(envelope)
        self.assertIn("DST030", found)
        self.assertIn("DST042", found)
        data = envelope["data"]
        self.assertEqual(data["platform"], "iOS")
        self.assertEqual(data["scheme"], "Planner")
        self.assertEqual([step["step"] for step in data["steps"]][:4], ["archive", "export", "validate", "upload"])
        self.assertTrue(any(step.get("requires_approval") for step in data["steps"]))

    def test_direct_upload_uses_export_destination(self):
        envelope = run_tool("distribution/plan_distribution.py", str(DISTRIBUTION), "--upload")
        self.assertEqual(envelope["data"]["export_options"]["destination"], "upload")
        self.assertEqual(envelope["data"]["steps"][1]["step"], "upload")

    def test_developer_id_requires_hardened_runtime(self):
        envelope = run_tool("distribution/plan_distribution.py", str(DISTRIBUTION), "--method", "developer-id",
                            "--platform", "macOS", expect=2)
        self.assertIn("DST040", codes(envelope))
        self.assertIn("notarize", [step["step"] for step in envelope["data"]["steps"]])

    def test_mac_app_store_requires_sandbox_and_methods_match_platforms(self):
        envelope = run_tool("distribution/plan_distribution.py", str(DISTRIBUTION), "--method", "mac-app-store",
                            "--platform", "macOS", expect=2)
        self.assertIn("DST041", codes(envelope))
        envelope = run_tool("distribution/plan_distribution.py", str(DISTRIBUTION), "--method", "developer-id",
                            expect=2)
        self.assertIn("DST060", codes(envelope))

    def test_swift_package_cannot_be_archived(self):
        envelope = run_tool("distribution/plan_distribution.py", str(CLEAN), expect=2)
        self.assertIn("DST001", codes(envelope))


class GuidelinesTests(unittest.TestCase):
    def test_table_cells_render_as_markdown(self):
        cell = lambda text: [{"type": "paragraph", "inlineContent": [{"type": "text", "text": text}]}]
        block = {"type": "table", "header": "row",
                 "rows": [[cell("Platform"), cell("Size")], [cell("tvOS"), cell("800x480 px")]]}
        rendered = apple_docs.render_block(block)
        self.assertIn("| Platform | Size |", rendered)
        self.assertIn("| --- | --- |", rendered)
        self.assertIn("| tvOS | 800x480 px |", rendered)
        self.assertNotIn("inlineContent", rendered)

    def test_catalogue_search_is_offline_and_ranked(self):
        report = apple_docs.operation_guidelines_search("tvos", None, 3)
        self.assertEqual(report.data["matches"][0]["slug"], "designing-for-tvos")
        report = apple_docs.operation_guidelines_search("", "Inputs", 50)
        self.assertTrue(all(match["section"] == "Inputs" for match in report.data["matches"]))

    def test_catalogue_is_well_formed(self):
        result = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "build_hig_catalog.py"), "--check"],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
