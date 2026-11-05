# Proof

Every claim in this repository is produced by a command you can run yourself. This file records the raw output of
those commands so that a reader can check the claim without trusting the README.

Verified on: macOS 27.2 (arm64), Xcode 27.2 / iPhoneSimulator 27.2 SDK, Swift 6.4, Python 3.14, Node 26.

---

## 1. The single command

```bash
git clone https://github.com/kayaonur607/apple-native-engineer-mcp.git
cd apple-native-engineer-mcp
cd integrations/mcp-server && npm install && cd ../..
./scripts/verify.sh
```

```
▸ Repository structure and links
  [PASS] all 20 required paths present
  [PASS] 14 CLI tools structure validated
  [PASS] 35 internal links resolve
  [PASS] README documents 14 CLI tools
  [PASS] README documents 30 reference guides
  [PASS] README documents 12 checklists
  [PASS] README documents 9 worked examples
  [PASS] README documents 13 MCP tools
  [PASS] no personal absolute paths in documentation
  [PASS] SF Symbols catalogue is internally consistent (9649 symbols)
  ------------------------------------------------------------------
  ✓ validation passed: 0 warning(s)

▸ Python tests (shared library + tools)
.......................................................
----------------------------------------------------------------------
Ran 66 tests in 1.324s

OK

▸ MCP protocol tests
ℹ tests 8
ℹ suites 1
ℹ pass 8
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0

▸ Swift compilation (fixtures + documentation snippets)
  SDK: iPhoneSimulator27.2.sdk
  ✓ fixture: clean-app/App
  ✓ fixture: clean-app/Widgets
  ✓ documentation snippets parse (118 blocks)
  checked 3 unit(s), 0 failure(s)

────────────────────────────────────────────
  passed: 4   failed: 0   skipped: 0   13s
────────────────────────────────────────────
```

Exit code `0`. Any failure in any stage returns non-zero, which is exactly what CI runs.

---

## 2. The knowledge base counts are not hand-maintained

`scripts/validate_repo.py` recomputes every count from the filesystem and fails the build if the README disagrees.
The v1 README claimed "8 CLI tools" while the repository contained 9, and "29 reference guides" while there were
30. That class of drift is now a CI failure:

```python
expectations = {
    "CLI tools": tool_count,                                  # len(tools/*/)
    "reference guides": len(references/*.md),
    "checklists": len(checklists/*.md),
    "worked examples": len(examples/*.md),
    "MCP tools": mcp_tool_count(),                            # parsed from TOOLS array
}
```

The test badge is verified the same way: `count_tests()` counts `def test_` and `it(` declarations and fails the
build if the README badge disagrees. A badge that lies is worse than no badge.

---

## 3. The release gate cannot be fooled

### A clean project

A real SwiftUI fixture with `@Observable`, String Catalogs, a guarded Liquid Glass surface, a complete Dynamic
Island, a valid privacy manifest, an opaque 1024×1024 icon and three screenshots at a valid slot:

```
$ python3 tools/release-readiness/generate_report.py <repo>/tests/fixtures/clean-app \
    --metadata metadata.json --icon AppIcon-1024.png --screenshots screenshots

  Verdict:      READY FOR SUBMISSION
  Score:        100/100
```

| Gate | Status | Earned |
| :--- | :--- | ---: |
| Project hygiene | pass | 15 / 15 |
| Privacy manifest | pass | 25 / 25 |
| Accessibility | pass | 10 / 10 |
| Localisation & RTL | pass | 10 / 10 |
| Widgets & Live Activities | pass | 10 / 10 |
| Assets & icon | pass | 15 / 15 |
| App Store metadata | pass | 15 / 15 |

### A project that breaks the rules

```
$ python3 tools/release-readiness/generate_report.py <repo>/tests/fixtures/legacy-app \
    --metadata metadata.json --icon AppIcon-512.png

  Verdict:      BLOCKED
  Score:        19/100
  Findings:     7 (0 critical, 5 error, 2 warning, 0 info)

  ✖ REL002 Gate 'Privacy manifest' failed with 0 critical and 2 error finding(s).
  ✖ REL002 Gate 'Accessibility' failed with 0 critical and 2 error finding(s).
  ✖ REL002 Gate 'Widgets & Live Activities' failed with 0 critical and 1 error finding(s).
  ✖ REL002 Gate 'Assets & icon' failed with 2 critical and 0 error finding(s).
  ✖ REL002 Gate 'App Store metadata' failed with 0 critical and 4 error finding(s).
  ▲ REL003 Gate 'Project hygiene' has 5 warning(s).
  ▲ REL003 Gate 'Localisation & RTL' has 4 warning(s.)
```

### A project with no inputs at all

This is the case v1 got wrong: it awarded 90/100 and "READY FOR SUBMISSION" after inspecting neither the icon nor
the metadata.

```
$ python3 tools/release-readiness/generate_report.py <repo>/tests/fixtures/clean-app

  Verdict:      BLOCKED
  Score:        70/100
  blockers:     ['assets', 'metadata']
```

A gate with no input is `NOT INSPECTED`, scores zero, and forces `BLOCKED`. A missing input is not a passing
input.

---

## 4. Swift actually compiles

Static text analysis is not proof that code works. The fixtures are therefore type-checked by the real compiler:

```
$ ./scripts/verify-swift.sh
  SDK: iPhoneSimulator27.2.sdk
  ✓ fixture: clean-app/App
  ✓ fixture: clean-app/Widgets
  ✓ documentation snippets parse (118 blocks)
  checked 3 unit(s), 0 failure(s)
```

- `swiftc -typecheck` on `clean-app/App` (HomeView, SettingsView, GlassSurface, AppModel, `@Observable`,
  `#Preview`, `#available` guard for Liquid Glass).
- `swiftc -typecheck` on `clean-app/Widgets` (ActivityAttributes, DynamicIsland with all four regions,
  AppIntentTimelineProvider, WidgetBundle `@main`).
- `swiftc -parse` on every ```swift block in `references/` and `examples/`.

The first run of this check found two real bugs in the fixture itself: a missing `import AppIntents`, and an
`@main` bundle compiled without `-parse-as-library`. That is the check earning its keep.

---

## 5. The MCP server is protocol-tested, not just "smoke-tested"

`npm test` drives a real SDK `Client` against a real `McpServer` over an in-memory transport:

```
▶ apple-native-engineer MCP server
  ✔ advertises a complete tool inventory (17.7ms)
  ✔ marks audit tools read-only (8.5ms)
  ✔ exposes the knowledge base as resources (1.0ms)
  ✔ exposes every command as a prompt (0.4ms)
  ✔ runs a real audit and returns a structured envelope (39.2ms)
  ✔ reports a lint failure with finding codes (37.5ms)
  ✔ surfaces a missing path as an MCP error instead of crashing (0.4ms)
  ✔ validates a single SF Symbol against the real catalogue (40.2ms)
✔ apple-native-engineer MCP server (152.5ms)
ℹ tests 8 · pass 8 · fail 0
```

Inventory at runtime:

```json
{
  "name": "apple-native-engineer",
  "version": "2.0.0",
  "tools": ["inspect_apple_project", "audit_privacy_manifest", "validate_app_icon", "validate_app_metadata",
            "check_localization", "validate_widgets", "lint_swiftui", "audit_accessibility", "audit_liquid_glass",
            "validate_sf_symbols", "forge_design_tokens", "generate_release_report", "app_store_connect"],
  "resources": 53,
  "prompts": ["apple-native-apple-native", "apple-native-design", "apple-native-code", "apple-native-review",
              "apple-native-privacy", "apple-native-icon", "apple-native-screenshots", "apple-native-connect",
              "apple-native-metadata", "apple-native-widgets", "apple-native-localization", "apple-native-release"]
}
```

---

## 6. Real data, not remembered data

The SF Symbols catalogue is extracted from the running system, not typed from a blog post:

```bash
python3 - <<'PY'
import plistlib, json, datetime
base = "/System/Library/CoreServices/CoreGlyphs.bundle/Contents/Resources/"
symbols = plistlib.load(open(base + "name_availability.plist", "rb"))
print(len(symbols["symbols"]))              # 9649
print(symbols["year_to_release"]["2026.2"])  # {'iOS': '27.2', 'macOS': '27.2', ...}
PY
```

That is why the tool can answer "is `square.and.pencil` available on iOS 17?" and "which symbol did you mean?"
instead of guessing.

The same principle produces `references/whats-new-ios-27.md`: every row is a declaration the installed SDK
annotates `@available(iOS 27.0, …)`. CI runs the generator in `--check` mode, so a stale SDK index fails the
build instead of silently ageing.

```bash
$ python3 scripts/generate_whats_new.py
wrote references/whats-new-ios-27.md: 64 declarations across 11 frameworks
  SwiftUI        34
  AppIntents     16
  StoreKit        9
```

The Liquid Glass API surface in `references/liquid-glass.md` is verified the same way — by grepping the actual
SDK interface:

```bash
SDK=$(xcrun --sdk iphonesimulator --show-sdk-path)
grep -A2 "func glassEffect(" \
  "$SDK/System/Library/Frameworks/SwiftUICore.framework/Modules/SwiftUICore.swiftmodule/arm64-apple-ios-simulator.swiftinterface"
#  @available(iOS 26.0, macOS 26.0, tvOS 26.0, watchOS 26.0, *)
#  @available(visionOS, unavailable)
#  nonisolated public func glassEffect(_ glass: Glass = .regular, in shape: some Shape = ...) -> some View
```

---

## 7. What is *not* verified

Being explicit about this is the difference between evidence and marketing.

| Not verified | Why | Consequence |
| :--- | :--- | :--- |
| Runtime UI behaviour | No simulator or device UI tests in CI | A screen that compiles can still look wrong; visual review is still required |
| App Store approval | Only Apple can decide that | The gate models the *rules*, not the reviewer |
| SwiftUI code in prose | Only fenced ```swift blocks are parsed | A snippet inside a sentence is not type-checked |
| Accessibility beyond contrast/targets | VoiceOver order and rotor traversal need a device | `audit_accessibility` catches the measurable subset only |
| Third-party SDK privacy manifests | The auditor scans app sources, not compiled frameworks | Check SDK manifest bundles separately |
| App Store Connect live calls | Requires a real key; CI has none | Only the error paths and mock mode are tested |

Where a check is heuristic (text scanning rather than a compiler), the finding is documented as such and the
severity reflects the confidence: `info` for suggestions, `error` for rules Apple will enforce.

---

## 8. Reproducing any single claim

| Claim | Command |
| :--- | :--- |
| "74 tests pass" | `./scripts/verify.sh` |
| "14 CLI tools" | `ls -d tools/*/ \| wc -l` |
| "13 MCP tools" | `node integrations/mcp-server/src/index.js --selftest` |
| "every internal link resolves" | `python3 scripts/validate_repo.py --links` |
| "Swift compiles" | `./scripts/verify-swift.sh` |
| "The gate blocks a bad project" | `python3 tools/release-readiness/generate_report.py tests/fixtures/legacy-app --metadata tests/fixtures/legacy-app/metadata.json --icon tests/fixtures/legacy-app/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png` |
| "9,649 SF Symbols" | `python3 -c "import json;print(json.load(open('data/sf-symbols.json'))['count'])"` |
