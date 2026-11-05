"""Golden tests: every tool on a clean project and on a deliberately broken one.

The clean fixture must stay silent (no false positives) and the legacy fixture
must fire the expected rules (no false negatives). Both directions matter: a
linter that never fails is as useless as one that always does.
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

from support import CLEAN, LEGACY, REPO_ROOT, TOOLS, codes, load_module, run_tool


class ProjectInspectorTests(unittest.TestCase):
    def test_clean_project_passes(self):
        envelope = run_tool("project-inspector/inspect_project.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["project_kind"], "swift-package")
        self.assertEqual(envelope["data"]["deployment_targets"]["iOS"], "17")
        self.assertIn("SwiftUI", envelope["data"]["frameworks"])
        self.assertIn("Observation (@Observable)", envelope["data"]["architecture"])

    def test_legacy_project_warns_about_debt(self):
        envelope = run_tool("project-inspector/inspect_project.py", str(LEGACY))
        found = codes(envelope)
        self.assertIn("PROJ003", found, "iOS 16 deployment target must be flagged")
        self.assertIn("PROJ007", found, "ObservableObject without @Observable must be flagged")
        self.assertIn("PROJ008", found, "NavigationView must be flagged")


class PrivacyAuditorTests(unittest.TestCase):
    def test_clean_manifest_passes(self):
        envelope = run_tool("privacy-auditor/audit_privacy.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["manifest"], "App/PrivacyInfo.xcprivacy")
        self.assertIn("NSPrivacyAccessedAPICategoryUserDefaults", envelope["data"]["declared_categories"])

    def test_missing_manifest_fails(self):
        envelope = run_tool("privacy-auditor/audit_privacy.py", str(LEGACY), expect=2)
        found = codes(envelope)
        self.assertIn("PRIV001", found)
        self.assertIn("PRIV010", found)


class AssetValidatorTests(unittest.TestCase):
    def test_clean_icon_passes(self):
        icon = CLEAN / "Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
        envelope = run_tool("asset-validator/validate_assets.py", str(CLEAN), "--icon", str(icon), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["icon"]["width"], 1024)

    def test_wrong_size_and_alpha_fail(self):
        icon = LEGACY / "Assets.xcassets/AppIcon.appiconset/AppIcon-512.png"
        envelope = run_tool("asset-validator/validate_assets.py", str(LEGACY), "--icon", str(icon), expect=2)
        found = codes(envelope)
        self.assertIn("ASSET003", found, "512x512 must be rejected")
        self.assertIn("ASSET004", found, "alpha channel must be rejected")

    def test_screenshot_slots(self):
        envelope = run_tool(
            "asset-validator/validate_assets.py", str(CLEAN),
            "--screenshots", str(CLEAN / "screenshots"), expect=0,
        )
        self.assertEqual(envelope["data"]["screenshots"]["unmatched"], 0)


class MetadataValidatorTests(unittest.TestCase):
    def test_clean_metadata_passes(self):
        envelope = run_tool("metadata-validator/validate_metadata.py", str(CLEAN / "metadata.json"), expect=0)
        self.assertEqual(envelope["status"], "pass")

    def test_legacy_metadata_fails(self):
        envelope = run_tool("metadata-validator/validate_metadata.py", str(LEGACY / "metadata.json"), expect=2)
        found = codes(envelope)
        self.assertIn("META001", found, "name over 30 characters")
        self.assertIn("META004", found, "missing privacy_url")
        self.assertIn("META005", found, "http:// support URL")
        self.assertIn("META007", found, "duplicate keywords")

    def test_missing_file_is_a_clean_failure(self):
        envelope = run_tool("metadata-validator/validate_metadata.py", str(CLEAN / "nope.json"), expect=2)
        self.assertIn("META000", codes(envelope))


class LocalizationTests(unittest.TestCase):
    def test_clean_project_passes(self):
        envelope = run_tool("localization-checker/check_localization.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["hardcoded_strings"], 0)

    def test_legacy_project_flags_unlocalisable_strings(self):
        envelope = run_tool("localization-checker/check_localization.py", str(LEGACY))
        found = codes(envelope)
        self.assertIn("L10N001", found, "Text(verbatim:) bypasses localisation")
        self.assertIn("L10N002", found, "UIKit String assignment")
        self.assertIn("L10N010", found, ".padding(.left) does not mirror in RTL")

    def test_plain_text_literal_is_not_flagged(self):
        """Text(\"Hello\") is a LocalizedStringKey and must not be reported."""
        envelope = run_tool("localization-checker/check_localization.py", str(CLEAN))
        messages = " ".join(finding["message"] for finding in envelope["findings"])
        self.assertNotIn("Text(\"Recent\")", messages)


class WidgetTests(unittest.TestCase):
    def test_clean_widget_passes(self):
        envelope = run_tool("widget-validator/validate_widget.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertTrue(envelope["data"]["live_activity_flag"])
        self.assertIn("accessoryRectangular", envelope["data"]["supported_families"])

    def test_legacy_widget_fails(self):
        envelope = run_tool("widget-validator/validate_widget.py", str(LEGACY), expect=2)
        found = codes(envelope)
        self.assertIn("WID032", found, "no timeline provider")
        self.assertIn("WID031", found, "no supportedFamilies")


class SwiftUILinterTests(unittest.TestCase):
    def test_clean_project_has_no_violations(self):
        envelope = run_tool("swiftui-linter/lint_swiftui.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["violations"], 0)

    def test_legacy_project_hits_expected_rules(self):
        envelope = run_tool("swiftui-linter/lint_swiftui.py", str(LEGACY), expect=2)
        found = codes(envelope)
        for code in ("SWU001", "SWU002", "SWU003", "SWU006", "SWU014", "SWU011"):
            self.assertIn(code, found)

    def test_rules_are_self_documented(self):
        module = load_module("lint_swiftui_rules", "swiftui-linter/lint_swiftui.py")
        self.assertGreaterEqual(len(module.RULES), 20)
        rule_codes = [rule.code for rule in module.RULES]
        self.assertEqual(len(rule_codes), len(set(rule_codes)), "rule codes must be unique")
        for rule in module.RULES:
            self.assertTrue(rule.hint, f"{rule.code} must explain how to fix the finding")

    def test_a_single_file_can_be_linted(self):
        """A diff review passes one changed file, not a project directory."""

        source = LEGACY / "App" / "LegacyContentView.swift"
        envelope = run_tool("swiftui-linter/lint_swiftui.py", str(source), expect=2)
        self.assertEqual(envelope["target"], str(source.resolve()))
        self.assertIn("SWU003", codes(envelope))
        self.assertEqual({finding["file"] for finding in envelope["findings"]}, {"LegacyContentView.swift"})

    def test_a_non_swift_file_is_rejected_with_a_reason(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as handle:
            handle.write("not swift\n")
            stray = Path(handle.name)
        try:
            envelope = run_tool("swiftui-linter/lint_swiftui.py", str(stray), expect=2)
        finally:
            stray.unlink()
        self.assertEqual(codes(envelope), ["GEN002"])
        self.assertIn("single .swift file", envelope["findings"][0]["hint"])


class AccessibilityTests(unittest.TestCase):
    def test_clean_project_passes(self):
        envelope = run_tool("accessibility-auditor/audit_accessibility.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")

    def test_legacy_project_fails_contrast_and_targets(self):
        envelope = run_tool("accessibility-auditor/audit_accessibility.py", str(LEGACY), expect=2)
        found = codes(envelope)
        self.assertIn("A11Y001", found, "1.68:1 contrast must be an error")
        self.assertIn("A11Y020", found, "32pt tap target must be an error")
        self.assertIn("A11Y010", found, "fixed font size")


class LiquidGlassTests(unittest.TestCase):
    def test_clean_project_is_compatible(self):
        envelope = run_tool("liquid-glass-auditor/audit_liquid_glass.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertEqual(envelope["data"]["glass_usages"], 1)
        self.assertEqual(envelope["data"]["guarded_usages"], 1)

    def test_unguarded_glass_on_ios_16_fails(self):
        envelope = run_tool("liquid-glass-auditor/audit_liquid_glass.py", str(LEGACY), expect=2)
        found = codes(envelope)
        self.assertIn("LG001", found, "iOS 26 API on an iOS 16 target without a guard")
        self.assertIn("LG010", found, "fake glass stack")


class SFSymbolTests(unittest.TestCase):
    def test_clean_symbols_pass(self):
        envelope = run_tool("sf-symbols-catalog/check_symbols.py", str(CLEAN), expect=0)
        self.assertEqual(envelope["status"], "pass")
        self.assertGreaterEqual(envelope["data"]["symbols_used"], 2)

    def test_typo_is_caught_with_suggestion(self):
        envelope = run_tool("sf-symbols-catalog/check_symbols.py", str(LEGACY), expect=2)
        findings = [f for f in envelope["findings"] if f["code"] == "SFC010"]
        self.assertTrue(findings)
        self.assertIn("gearshape", json.dumps(findings[0]))

    def test_single_symbol_lookup(self):
        envelope = run_tool("sf-symbols-catalog/check_symbols.py", "--name", "square.and.pencil", ".")
        self.assertEqual(envelope["status"], "pass")
        self.assertIn("exists", envelope["findings"][0]["message"])

    def test_catalogue_is_populated(self):
        payload = json.loads((REPO_ROOT / "data" / "sf-symbols.json").read_text())
        self.assertGreater(payload["count"], 8000)
        self.assertIn("house", payload["symbols"])


class DesignTokenForgeTests(unittest.TestCase):
    TOKENS = {
        "name": "Acme",
        "colors": {
            "brand": {"light": "#0040DD", "dark": "#7CB0FF"},
            "canvas": {"light": "#FFFFFF", "dark": "#000000"},
        },
        "spacing": {"sm": 8, "md": 16},
        "radius": {"card": 20},
        "typography": {"title": {"style": "title", "weight": "bold"}},
        "contrastPairs": [{"foreground": "brand", "background": "canvas"}],
    }

    def test_generates_swift_tokens(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tokens.json"
            source.write_text(json.dumps(self.TOKENS))
            out = Path(tmp) / "Tokens.swift"
            envelope = run_tool("design-token-forge/forge_tokens.py", str(source), "--out", str(out))
            self.assertEqual(envelope["status"], "pass")
            generated = out.read_text()
            self.assertIn("public enum Acme", generated)
            self.assertIn("Color.token(light:", generated)
            self.assertIn("CGFloat = 16", generated)
            self.assertIn("Font.system(.title, weight: .bold)", generated)

    def test_contrast_pair_is_checked(self):
        tokens = {
            "colors": {
                "text": {"light": "#C7C7CC", "dark": "#C7C7CC"},
                "canvas": {"light": "#FFFFFF", "dark": "#000000"},
            },
            "contrastPairs": [{"foreground": "text", "background": "canvas"}],
        }
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tokens.json"
            source.write_text(json.dumps(tokens))
            envelope = run_tool("design-token-forge/forge_tokens.py", str(source))
            self.assertIn("TOK011", codes(envelope))

    def test_invalid_hex_is_rejected(self):
        tokens = {"colors": {"brand": {"light": "not-a-colour", "dark": "#000"}}}
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tokens.json"
            source.write_text(json.dumps(tokens))
            envelope = run_tool("design-token-forge/forge_tokens.py", str(source), expect=2)
            self.assertIn("TOK003", codes(envelope))

    def test_assets_are_emitted(self):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "tokens.json"
            source.write_text(json.dumps(self.TOKENS))
            assets = Path(tmp) / "Assets.xcassets"
            run_tool("design-token-forge/forge_tokens.py", str(source), "--xcassets", str(assets))
            colour_set = assets / "brand.colorset" / "Contents.json"
            self.assertTrue(colour_set.exists())
            payload = json.loads(colour_set.read_text())
            self.assertEqual(len(payload["colors"]), 2, "light and dark entries")


class MarketingCompositionTests(unittest.TestCase):
    def test_composes_exact_size_svg(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "frames"
            envelope = run_tool("screenshot-studio/compose_marketing.py",
                                "--screenshots", str(CLEAN / "screenshots"),
                                "--out", str(out), "--headline", "Plan your week",
                                "--subhead", "Native on iPhone", expect=0)
            self.assertEqual(envelope["data"]["composed"], 3)
            svg = (out / "home.svg").read_text()
            self.assertIn('viewBox="0 0 1320 2868"', svg)
            self.assertIn("Plan your week", svg)
            self.assertIn("data:image/png;base64,", svg, "the screenshot must be embedded, not referenced")

    def test_missing_directory_fails(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            envelope = run_tool("screenshot-studio/compose_marketing.py",
                                "--screenshots", str(Path(tmp) / "nope"),
                                "--out", str(Path(tmp) / "out"), expect=2)
            self.assertIn("SHOT100", codes(envelope))

    def test_warns_when_fewer_than_three(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            shots = Path(tmp) / "one"
            shots.mkdir()
            (shots / "a.png").write_bytes((CLEAN / "screenshots/home.png").read_bytes())
            envelope = run_tool("screenshot-studio/compose_marketing.py",
                                "--screenshots", str(shots), "--out", str(Path(tmp) / "out"), expect=0)
            self.assertIn("SHOT113", codes(envelope))


class IconStudioTests(unittest.TestCase):
    def test_generates_a_complete_set_and_verifies_it(self):
        import tempfile
        master = CLEAN / "Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "AppIcon.appiconset"
            generated = run_tool("icon-studio/icon_studio.py", "prepare", str(master), "--out", str(out), expect=0)
            self.assertEqual(generated["data"]["slots"], 18)
            self.assertEqual(len(list(out.glob("*.png"))), 18)
            self.assertTrue((out / "Contents.json").exists())

            verified = run_tool("icon-studio/icon_studio.py", "verify", str(out), expect=0)
            self.assertEqual(verified["data"]["missing"], 0)
            self.assertEqual(verified["data"]["wrong_size"], 0)

    def test_refuses_a_transparent_master(self):
        legacy = LEGACY / "Assets.xcassets/AppIcon.appiconset/AppIcon-512.png"
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "set"
            envelope = run_tool("icon-studio/icon_studio.py", "prepare", str(legacy), "--out", str(out), expect=2)
            found = codes(envelope)
            self.assertIn("ICON003", found, "512x512 master must be rejected")
            self.assertIn("ICON004", found, "alpha channel must be rejected")

    def test_preview_is_smaller(self):
        import tempfile
        master = CLEAN / "Assets.xcassets/AppIcon.appiconset/AppIcon-1024.png"
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "preview.png"
            envelope = run_tool("icon-studio/icon_studio.py", "preview", str(master),
                                "--at", "120", "--out", str(out), expect=0)
            self.assertEqual(envelope["data"]["width"], 120)
            self.assertTrue(out.exists())

    def test_verify_reports_a_missing_file(self):
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            asset_set = Path(tmp) / "Broken.appiconset"
            asset_set.mkdir()
            (asset_set / "Contents.json").write_text(json.dumps({
                "images": [{"filename": "nope.png", "idiom": "iphone", "scale": "2x", "size": "20x20"}],
                "info": {"author": "xcode", "version": 1},
            }))
            envelope = run_tool("icon-studio/icon_studio.py", "verify", str(asset_set), expect=2)
            self.assertIn("ICON021", codes(envelope))


class ASOTests(unittest.TestCase):
    def test_clean_listing_passes_with_coverage_hints(self):
        envelope = run_tool("aso-engine/aso.py", str(CLEAN / "metadata.json"), expect=0)
        self.assertEqual(envelope["status"], "pass")
        found = codes(envelope)
        self.assertIn("ASO012", found, "keywords absent from visible copy are a coverage hint")
        analysis = envelope["data"]["analysis"]
        self.assertIn("default", analysis, "a flat listing is analysed as the default locale")
        self.assertGreater(len(analysis["default"]["keyword_suggestions"]), 0)

    def test_legacy_listing_fails_on_budget_and_claims(self):
        envelope = run_tool("aso-engine/aso.py", str(LEGACY / "metadata.json"), expect=2)
        found = codes(envelope)
        self.assertIn("ASO001", found, "name over 30 characters")
        self.assertIn("ASO020", found, "‘best’ is an unverifiable claim")

    def test_reports_that_it_invents_nothing(self):
        envelope = run_tool("aso-engine/aso.py", str(CLEAN / "metadata.json"), expect=0)
        method = envelope["data"]["method"].lower()
        self.assertIn("no search-volume", method)
        self.assertIn("or invented", method)


class ScreenshotStudioTests(unittest.TestCase):
    def test_audits_known_slots(self):
        envelope = run_tool("screenshot-studio/screenshot_studio.py",
                            "--screenshots", str(CLEAN / "screenshots"), expect=0)
        self.assertEqual(envelope["data"]["screenshot_count"], 3)
        self.assertEqual(envelope["status"], "pass")


class AppStoreConnectTests(unittest.TestCase):
    def test_mock_is_explicit(self):
        envelope = run_tool("app-store-connect/cli.py", "--mock", "verify")
        self.assertEqual(envelope["data"]["mode"], "mock")
        self.assertIn("ASC010", codes(envelope), "mock mode must be announced as a warning")

    def test_missing_credentials_do_not_fall_back_to_mock(self):
        import os
        environment = {k: v for k, v in os.environ.items() if not k.startswith("ASC_")}
        import subprocess
        proc = subprocess.run(
            [sys.executable, str(TOOLS / "app-store-connect/cli.py"), "verify", "--json"],
            capture_output=True, text=True, env=environment,
        )
        self.assertEqual(proc.returncode, 2, "a missing credential must be a hard failure")
        payload = json.loads(proc.stdout)
        self.assertIn("ASC001", codes(payload))
        self.assertNotIn("mock", json.dumps(payload["data"]).lower())


if __name__ == "__main__":
    unittest.main()
