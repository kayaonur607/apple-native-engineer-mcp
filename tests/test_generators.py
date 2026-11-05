"""Tests for the generated SDK reference and its parsers.

The generator reads real `.swiftinterface` files, which do not exist on CI's
Linux runners, so these tests exercise the parsing logic against fixtures that
mirror the real annotation layout.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

from support import REPO_ROOT

sys.path.insert(0, str(REPO_ROOT / "scripts"))


def load_generator():
    path = REPO_ROOT / "scripts" / "generate_whats_new.py"
    spec = importlib.util.spec_from_file_location("generate_whats_new", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules["generate_whats_new"] = module
    spec.loader.exec_module(module)
    return module


GEN = load_generator()

INTERFACE = '''
@available(iOS 26.0, macOS 15.0, *)
public struct OldThing {
}

@available(iOS 27.0, macOS 27.0, visionOS 27.0, *)
@available(watchOS, unavailable)
public protocol Document : ReadableDocument {
}

@available(iOS 27.0, macOS 27.0, *)
nonisolated public func toolbarOverflowMenu(_ enabled: Bool) -> some View

@available(iOS 27.0, macOS 27.0, *)
@_alwaysEmitIntoClient public static var statusBar: StatusBarStyle { get }

@available(iOS 27.0, macOS 27.0, *)
public func hash(into hasher: inout Hasher)

@available(iOS 27.0, macOS 27.0, *)
public struct _PrivateThing {
}
'''


class DeclarationParsingTests(unittest.TestCase):
    def test_struct(self):
        self.assertEqual(GEN.declaration_of("public struct Foo {"), ("struct", "Foo"))

    def test_protocol_with_conformance(self):
        self.assertEqual(GEN.declaration_of("public protocol Document : ReadableDocument {"), ("protocol", "Document"))

    def test_modifiers_before_public(self):
        self.assertEqual(GEN.declaration_of("nonisolated public func toolbarOverflowMenu(_ x: Bool) -> Int"),
                         ("func", "toolbarOverflowMenu"))

    def test_static_var(self):
        self.assertEqual(GEN.declaration_of("public static var statusBar: StatusBarStyle { get }"), ("var", "statusBar"))

    def test_generic_struct(self):
        self.assertEqual(GEN.declaration_of("public struct Container<Content> {"), ("struct", "Container"))

    def test_private_declarations_are_ignored(self):
        self.assertIsNone(GEN.declaration_of("    var hidden: Int"))


class AvailabilityCollectionTests(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.TemporaryDirectory()
        self.path = Path(self.tempdir.name) / "Test.swiftinterface"
        self.path.write_text(INTERFACE)

    def tearDown(self):
        self.tempdir.cleanup()

    def test_collects_only_the_requested_release(self):
        found = GEN.collect_availability(self.path, 27)
        names = {entry["name"] for entry in found.values()}
        self.assertIn("Document", names)
        self.assertIn("toolbarOverflowMenu", names)
        self.assertNotIn("OldThing", names, "iOS 26 declaration must not appear in the 27 list")

    def test_platform_metadata(self):
        found = GEN.collect_availability(self.path, 27)
        document = found["protocol:Document"]
        self.assertEqual(document["platforms"]["ios"], "27.0")
        self.assertEqual(document["platforms"]["watchos"], "unavailable")

    def test_boilerplate_and_private_names_are_filtered(self):
        found = GEN.collect_availability(self.path, 27)
        names = {entry["name"] for entry in found.values()}
        self.assertNotIn("hash", names)
        self.assertNotIn("_PrivateThing", names)


class RenderTests(unittest.TestCase):
    def test_render_is_deterministic(self):
        entries = {
            "struct:Foo": {"kind": "struct", "name": "Foo", "platforms": {"ios": "27.0"}},
            "func:bar": {"kind": "func", "name": "bar", "platforms": {"ios": "27.0", "watchos": "unavailable"}},
        }
        sdk = Path("/Xcode/iPhoneSimulator27.2.sdk")
        first = GEN.render(27, sdk, {"SwiftUI": entries})
        second = GEN.render(27, sdk, {"SwiftUI": entries})
        self.assertEqual(first, second, "regenerating must not churn the file")
        self.assertIn("Declarations found: **2**", first)
        self.assertIn("`Foo`", first)
        self.assertIn("watchOS unavailable", first)
        self.assertIn("iPhoneSimulator27.2.sdk", first)

    def test_checked_in_reference_matches_its_generator(self):
        """If an SDK is installed, the committed reference must be current."""

        try:
            import subprocess
            subprocess.run(["xcrun", "--sdk", "iphonesimulator", "--show-sdk-path"],
                           check=True, capture_output=True)
        except Exception:
            self.skipTest("no Xcode SDK on this machine")

        proc = __import__("subprocess").run(
            [sys.executable, str(REPO_ROOT / "scripts" / "generate_whats_new.py"), "--check"],
            capture_output=True, text=True,
        )
        self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)


if __name__ == "__main__":
    unittest.main()
