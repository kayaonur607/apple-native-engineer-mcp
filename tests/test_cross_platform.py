"""Cross-platform apps: framework detection, host discovery, Apple-native checks and release plans.

Each rule is exercised in both directions: the defect fixtures must fire it and
idiomatic code must stay silent.
"""

from __future__ import annotations

import json
import tempfile
import textwrap
import unittest
from pathlib import Path

from support import CLEAN, FIXTURES, codes, run_tool

from apple_native.frameworks import detect, xcode_containers
from apple_native.xcode import discover

FLUTTER = FIXTURES / "flutter-app"
EXPO = FIXTURES / "react-native-app"


def write(root: Path, files: dict) -> None:
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content))


PBX = """// !$*UTF8*$!
{ objects = { A = { isa = PBXProject; knownRegions = ( en, tr, Base, ); };
  B = { isa = XCBuildConfiguration; buildSettings = { PRODUCT_BUNDLE_IDENTIFIER = dev.example.app;
  IPHONEOS_DEPLOYMENT_TARGET = 17.0; SDKROOT = iphoneos; }; name = Release; }; }; }
"""


class DetectionTests(unittest.TestCase):
    def test_flutter_and_expo_fixtures(self):
        flutter = detect(FLUTTER)
        self.assertEqual((flutter.framework, flutter.hosts, flutter.app_version), ("flutter", {"iOS": "ios"}, "1.4.0+12"))
        expo = detect(EXPO)
        self.assertEqual(expo.framework, "expo")
        self.assertTrue(expo.managed)
        self.assertEqual(detect(CLEAN).framework, "native")

    def test_capacitor_maui_and_kmp(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {"package.json": '{"dependencies": {"@capacitor/core": "7.0.0"}}', "ios/App/.keep": ""})
            info = detect(root)
            self.assertEqual((info.framework, info.hosts.get("iOS")), ("capacitor", "ios/App"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {"App.csproj": "<Project><PropertyGroup><TargetFrameworks>net10.0-ios;net10.0-android"
                                       "</TargetFrameworks><UseMaui>true</UseMaui></PropertyGroup></Project>",
                         "Platforms/iOS/Info.plist": "<plist/>"})
            info = detect(root)
            self.assertEqual((info.framework, info.hosts.get("iOS")), ("maui", "Platforms/iOS"))
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {"settings.gradle.kts": "", "iosApp/iosApp.xcodeproj/project.pbxproj": PBX})
            info = detect(root)
            self.assertEqual((info.framework, info.hosts.get("iOS")), ("kmp", "iosApp"))

    def test_host_projects_are_discovered_below_the_root(self):
        project = discover(FLUTTER)
        self.assertEqual(project.project_files, ["ios/Runner.xcodeproj"])
        self.assertEqual(project.deployment_targets.get("iOS"), "13.0")
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {"node_modules/lib/Lib.xcodeproj/project.pbxproj": PBX,
                         "ios/App.xcworkspace/contents.xcworkspacedata": "<Workspace/>",
                         "ios/App.xcodeproj/project.pbxproj": PBX})
            names = [str(path.relative_to(root)) for path in xcode_containers(root)]
            self.assertEqual(names, ["ios/App.xcworkspace", "ios/App.xcodeproj"])


class FlutterTests(unittest.TestCase):
    def test_defects_are_reported(self):
        found = codes(run_tool("cross-platform-auditor/audit_cross_platform.py", str(FLUTTER), expect=2))
        for code in ("FLT001", "FLT002", "FLT003", "FLT004", "FLT005", "FLT007", "FLT009", "XPL010", "XPL012"):
            self.assertIn(code, found)

    def test_idiomatic_flutter_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {
                "pubspec.yaml": "name: ok\nversion: 1.0.0+1\ndependencies:\n  flutter:\n    sdk: flutter\n  camera: ^0.11.0\n",
                "lib/l10n/app_tr.arb": '{"@@locale": "tr"}',
                "lib/main.dart": """
                    import 'dart:io';
                    import 'package:flutter/cupertino.dart';
                    import 'package:flutter/material.dart';
                    final app = MaterialApp(theme: ThemeData(), darkTheme: ThemeData.dark(), home: Home());
                    Widget bar(int i) => Platform.isIOS ? CupertinoTabBar(items: const []) : NavigationBar(destinations: const []);
                    Widget body(bool v) => Column(children: [
                      Switch.adaptive(value: v, onChanged: null),
                      const CircularProgressIndicator.adaptive(),
                      IconButton(tooltip: 'Add habit', icon: const Icon(Icons.add), onPressed: () {}),
                      Image.asset('a.png', semanticLabel: 'Streak chart'),
                      Padding(padding: const EdgeInsetsDirectional.only(start: 16)),
                    ]);
                """,
                "ios/Runner.xcodeproj/project.pbxproj": PBX,
                "ios/Runner/Info.plist": """<?xml version="1.0" encoding="UTF-8"?>
                    <plist version="1.0"><dict>
                    <key>NSCameraUsageDescription</key><string>Scan a habit card to add it.</string>
                    <key>NSMicrophoneUsageDescription</key><string>Record a voice note for a habit.</string>
                    </dict></plist>""",
                "ios/Runner/PrivacyInfo.xcprivacy": "<plist/>",
            })
            envelope = run_tool("cross-platform-auditor/audit_cross_platform.py", tmp, expect=0)
            noisy = [code for code in codes(envelope) if code[:3] in ("FLT", "XPL") and code not in
                     ("XPL001", "FLT020", "FLT010")]
            self.assertEqual(noisy, [], envelope["findings"])


class ReactNativeTests(unittest.TestCase):
    def test_defects_are_reported(self):
        found = codes(run_tool("cross-platform-auditor/audit_cross_platform.py", str(EXPO), expect=2))
        for code in ("RNA001", "RNA002", "RNA003", "RNA004", "RNA005", "EXP001", "EXP002", "EXP003", "EXP004",
                     "XPL011", "RNA020"):
            self.assertIn(code, found)

    def test_idiomatic_expo_is_quiet(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {
                "package.json": json.dumps({"dependencies": {"expo": "~56.0.0", "react-native": "0.84.0",
                                                             "expo-camera": "~17.0.0", "@expo/ui": "~1.0.0",
                                                             "expo-glass-effect": "~1.0.0", "expo-symbols": "~1.0.0"}}),
                "app.json": json.dumps({"expo": {
                    "userInterfaceStyle": "automatic",
                    "plugins": [["expo-camera", {"cameraPermission": "Scan a habit card to add it."}]],
                    "ios": {"bundleIdentifier": "dev.example.app", "buildNumber": "1", "icon": "./assets/app.icon",
                            "config": {"usesNonExemptEncryption": False},
                            "privacyManifests": {"NSPrivacyAccessedAPITypes": []}}}}),
                "src/today.tsx": """
                    import { Pressable, Text, useColorScheme, useWindowDimensions } from 'react-native';
                    import { SymbolView } from 'expo-symbols';
                    export function Today() {
                      const scheme = useColorScheme();
                      const { width } = useWindowDimensions();
                      return (
                        <Pressable accessibilityLabel="Add habit" accessibilityRole="button" onPress={() => {}}>
                          <SymbolView name="plus" />
                        </Pressable>
                      );
                    }
                    const styles = { row: { marginStart: 16, color: scheme === 'dark' ? '#fff' : '#000' } };
                """,
            })
            envelope = run_tool("cross-platform-auditor/audit_cross_platform.py", tmp, expect=0)
            self.assertEqual([c for c in codes(envelope) if c not in ("XPL001",)], [], envelope["findings"])


class OtherFrameworkTests(unittest.TestCase):
    def test_capacitor_remote_url_is_a_review_risk(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(Path(tmp), {"package.json": '{"dependencies": {"@capacitor/core": "7.0.0"}}',
                              "capacitor.config.json": '{"appId": "dev.example", "server": {"url": "https://example.com"}}'})
            self.assertIn("CPC001", codes(run_tool("cross-platform-auditor/audit_cross_platform.py", tmp, expect=2)))

    def test_native_projects_are_left_to_the_swift_auditors(self):
        self.assertEqual(codes(run_tool("cross-platform-auditor/audit_cross_platform.py", str(CLEAN), expect=0)), ["XPL000"])


class DistributionTests(unittest.TestCase):
    def test_flutter_plan_uses_flutter_build_ipa(self):
        data = run_tool("distribution/plan_distribution.py", str(FLUTTER))["data"]
        commands = [step["command"] for step in data["steps"]]
        self.assertEqual(commands[0], "flutter pub get")
        self.assertTrue(commands[1].startswith("flutter build ipa --release --export-options-plist="))
        self.assertIn("build/ios/ipa/*.ipa", " ".join(commands))
        self.assertEqual(data["versions"], ["1.4.0 (pubspec.yaml)"])
        self.assertEqual(data["build_numbers"], ["12 (pubspec.yaml)"])

    def test_expo_managed_plan_uses_eas(self):
        envelope = run_tool("distribution/plan_distribution.py", str(EXPO), expect=2)
        self.assertIn("DST003", codes(envelope))
        self.assertNotIn("DST001", codes(envelope))
        steps = {step["step"]: step for step in envelope["data"]["steps"]}
        self.assertIn("eas-cli@latest build -p ios", steps["build"]["command"])
        self.assertTrue(steps["upload"]["requires_approval"])

    def test_capacitor_plan_syncs_before_archiving(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, {"package.json": '{"dependencies": {"@capacitor/core": "7.0.0"}}',
                         "ios/App/App.xcodeproj/project.pbxproj": PBX})
            steps = run_tool("distribution/plan_distribution.py", tmp)["data"]["steps"]
            self.assertIn("npx cap sync ios", steps[0]["command"])
            self.assertIn("-project ios/App/App.xcodeproj", steps[1]["command"])


if __name__ == "__main__":
    unittest.main()
