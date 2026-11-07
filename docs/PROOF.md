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

<!-- proof:begin -->
Recorded by `./scripts/update_proof.py` on 2026-11-07. Re-run it after any change that could affect these numbers.

```
▸ Repository structure and links
  [PASS] SF Symbols catalogue is internally consistent (9649 symbols)
  ------------------------------------------------------------------
  ✓ validation passed: 0 warning(s)

▸ Python tests (shared library + tools)
........................................................................................................................................................................
----------------------------------------------------------------------
Ran 168 tests in 5.211s


▸ MCP protocol tests
ℹ tests 88
ℹ suites 16
ℹ pass 88
ℹ fail 0
ℹ cancelled 0
ℹ skipped 0
ℹ todo 0
ℹ duration_ms 2013.429167

▸ Swift compilation (fixtures + documentation snippets)
  SDK: iPhoneSimulator27.2.sdk
  ✓ fixture: clean-app/App
  ✓ fixture: clean-app/Widgets
  ✓ example: screenshot-pipeline
163
  ✓ documentation snippets parse (163 blocks)
  type-checking every snippet against the iOS SDK...
  Type-check clean: 74
  Fragments:        89
  Real errors:      0
  checked 4 unit(s), 0 failure(s)

▸ Documentation API claims
SDK index:        21,998 symbols from iPhoneSimulator27.2.sdk
Documents:        48
Modifiers taught: 129
Verified:         127
Allowlisted:      2
Unverified:       0

────────────────────────────────────────────
  passed: 5   failed: 0   skipped: 0   58s
────────────────────────────────────────────
```
<!-- proof:end -->

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

  Verdict:      READY FOR SUBMISSION (historical; current wording: CONFIGURED STATIC CHECKS PASSED)
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
  ✓ documentation snippets parse (162 blocks)
  Type-check clean: 73
  Fragments:        89
  Real errors:      0
  checked 3 unit(s), 0 failure(s)
```

- `swiftc -typecheck` on `clean-app/App` (HomeView, SettingsView, GlassSurface, AppModel, `@Observable`,
  `#Preview`, `#available` guard for Liquid Glass).
- `swiftc -typecheck` on `clean-app/Widgets` (ActivityAttributes, DynamicIsland with all four regions,
  AppIntentTimelineProvider, WidgetBundle `@main`).
- `swiftc -parse` on every ```swift block in `references/` and `examples/`.
- `swiftc -typecheck` on those blocks too, against the SDK the snippet targets, with a classifier that separates
  fragment noise from real errors:

```
SDK:              ios → iPhoneSimulator27.2.sdk, visionos → XROS27.2.sdk
Snippets:         162
Per platform:     ios 154, visionos 8
Type-check clean: 73
Fragments:        89
Real errors:      0
```

Platform-specific guidance is tagged in the fence — ` ```swift visionOS ` — and compiled against that platform's
SDK and target instead of being skipped or checked against iOS. Before this existed, the visionOS guide was being
typechecked against the iOS SDK, where `defaultSize(width:height:depth:)` and `.windowStyle(.volumetric)` do not
exist; the check reported three "errors" that were really the harness checking the wrong platform. One genuine
bug surfaced from the fix: `RealityKit` declares its own `Scene`, so importing it next to an `App` makes
`some Scene` ambiguous. The guide now keeps the app's scene and the RealityKit content in separate files.

The classifier is not hand-waving. A block with an undefined symbol (`cannot find 'Foo' in scope`) is a fragment;
a block with a wrong argument label is a bug in the guide. The first run of this check found **14 occurrences of
`.spring(response:dampingRatio:)`** across six guides — an argument label SwiftUI does not have. Every one is now
`.spring(response:dampingFraction:)`, and the check fails CI if the pattern returns.

The first run of this check found two real bugs in the fixture itself: a missing `import AppIntents`, and an
`@main` bundle compiled without `-parse-as-library`. That is the check earning its keep.

---

## 5. Historical MCP examples (v2.1.0)

The examples below record earlier runs; the current verification transcript is in §1. Current version, inventory and recorded demo are available through `--selftest` and [the raw stdio session](../assets/demo/session.json).

`npm test` drives a real SDK `Client` against a real `McpServer` over an in-memory transport, binds a real HTTP
socket for the Streamable HTTP transport, and builds a throwaway git repository for `review_diff`:

```
▶ command line
  ✔ prints its version
  ✔ documents every flag it accepts
  ✔ reports a complete inventory without a client
  ✔ exits 0 from --doctor when the machine can run everything
  ✔ rejects an invalid port with a sentence, not a stack trace
▶ review_diff
  ✔ reports nothing when the working tree is clean
  ✔ catches only the defect introduced by the change
  ✔ passes when the change is clean even though the project is not
  ✔ reviews the index when staged is set
  ✔ says so instead of failing when the diff contains no Swift
  ✔ explains that a non-repository directory cannot be diffed
▶ check_environment
  ✔ reports the runtime it actually found
▶ streamable HTTP transport
  ✔ binds a real port and reports its own URL
  ✔ answers /health without touching the protocol layer
  ✔ completes an MCP initialize handshake over POST /mcp
  ✔ rejects a cross-origin browser request
  ✔ rejects a non-JSON content type
  ✔ rejects an unparseable body with 400 rather than crashing
  ✔ refuses GET /mcp in stateless mode
  ✔ documents the endpoint on an unknown path
▶ network exposure
  ✔ refuses a non-loopback bind without --allow-remote
▶ apple-native-engineer MCP server
  ✔ advertises a complete tool inventory
  ✔ marks audit tools read-only
  ✔ exposes the knowledge base as resources
  ✔ exposes every command as a prompt
  ✔ names the umbrella prompt once, without a duplicated prefix
  ✔ renders a prompt with its workflow body and optional focus
  ✔ runs a real audit and returns a structured envelope
  ✔ reports a lint failure with finding codes
  ✔ surfaces a missing path as an MCP error instead of crashing
  ✔ validates a single SF Symbol against the real catalogue
  ✔ audits the whole project in one call and merges every report
  ✔ reports progress for a long composite instead of going silent
▶ telemetry is off unless explicitly enabled
  ✔ defaults to off
  ✔ treats an unrecognised value as off rather than collecting
  ✔ requires https for the anonymous endpoint
▶ the event shape is closed
  ✔ drops every unexpected field, including hostile ones
  ✔ coerces unknown outcomes to error instead of passing them through
  ✔ rejects a malformed day
  ✔ buckets duration instead of recording milliseconds
▶ local recording
  ✔ writes one aggregate line and nothing else
  ✔ refuses to record a tool that does not exist
▶ publish metadata
  ✔ uses one version everywhere
  ✔ names the package the registry points at
  ✔ points every URL at the repository that actually exists
  ✔ ships the runtime it needs and nothing more
  ✔ declares the same tools the server registers
  ✔ has a Dockerfile that copies paths that exist
  ✔ describes itself to Smithery without inventing configuration
▶ the preview is the same data that would be written
  ✔ contains only the closed event shape plus explanatory metadata
  ✔ reports no file and no endpoint when telemetry is off
ℹ tests 51 · pass 51 · fail 0
```

Inventory at runtime:

```json
{
  "name": "apple-native-engineer",
  "version": "2.1.0",
  "transport": "stdio",
  "tools": ["review_diff", "check_environment", "audit_project", "inspect_apple_project",
            "audit_privacy_manifest", "validate_app_icon", "validate_app_metadata", "check_localization",
            "validate_widgets", "lint_swiftui", "audit_accessibility", "audit_liquid_glass",
            "validate_sf_symbols", "forge_design_tokens", "generate_release_report", "app_store_connect"],
  "resources": 53,
  "prompts": ["apple-native", "apple-native-code", "apple-native-connect", "apple-native-design",
              "apple-native-icon", "apple-native-localization", "apple-native-metadata", "apple-native-privacy",
              "apple-native-release", "apple-native-review", "apple-native-screenshots", "apple-native-widgets"],
  "telemetry": "off"
}
```

The umbrella prompt is `apple-native`, not `apple-native-apple-native` — that double prefix was a real bug, and
one of the tests above exists to keep it from coming back.

### The HTTP transport, by hand

```
$ node src/index.js --http 3931
apple-native-engineer v2.1.0 ready (streamable-http)
  MCP endpoint: POST http://127.0.0.1:3931/mcp
  health:       GET  http://127.0.0.1:3931/health
  bound to loopback only; other machines cannot reach it

$ curl -s http://127.0.0.1:3931/health
{"name":"apple-native-engineer","version":"2.1.0","transport":"streamable-http","status":"ok",
 "uptime_seconds":1,"tools":16,"telemetry":"off"}

$ curl -s -o /dev/null -w '%{http_code}\n' -X POST http://127.0.0.1:3931/mcp \
    -H 'origin: https://evil.example' -H 'content-type: application/json' -d '{}'
403

$ node src/index.js --http --http-host 0.0.0.0
error: Refusing to bind 0.0.0.0: this server runs project audits and has no authentication.
Pass --allow-remote only when a reverse proxy in front of it authenticates callers.
(exits 2)
```

### `review_diff` on a one-file change

A throwaway repository: `App/ContentView.swift` is modified, `App/Legacy.swift` already contained the same
defects in the baseline commit and is left untouched.

```
$ cd integrations/mcp-server && node --input-type=module -e '
  const { TOOL_SPECS } = await import("./src/tools.js");
  const run = await TOOL_SPECS.find(s => s.name === "review_diff").run({ path: "/tmp/diffdemo" });
  console.log(run.summary);
  for (const [file, info] of Object.entries(run.envelope.data.files))
    console.log(`${file} · ${info.status.toUpperCase()} · ${info.findings} finding(s)`);
  for (const f of run.envelope.findings) console.log(`  ${f.severity.padEnd(7)} ${f.code} — ${f.message}`);
'

diff-review · FAIL · 1 changed file(s) · 5 finding(s)
App/ContentView.swift · FAIL · 5 finding(s)
  warning SWU001 — Hardcoded hex colour breaks Dark Mode and Increase Contrast.
  warning SWU002 — .foregroundColor(_:) is deprecated since iOS 17.
  error   SWU003 — NavigationView is deprecated since iOS 16.
  warning A11Y002 — Text colour #FF0000 is 4.00:1 at worst; below the 4.5:1 AA threshold for body text
                    (light 4.00:1, dark 4.26:1).
  info    LG020 — No Liquid Glass APIs detected.
```

`App/Legacy.swift` does not appear — it is unmodified, and a review is about the change, not the checkout. The
same run over the whole project would have reported the legacy file too, which is exactly why a full sweep is the
wrong tool inside an edit loop. One of the tests in the transcript above asserts this scoping.

---

## 6. The documentation cannot invent API

A snippet that parses can still call something that does not exist. `scripts/check_api_claims.py` indexes every
public declaration in the installed SDK's Swift interfaces, extracts every modifier written at the start of a line
inside a ```swift block, and looks each one up:

```
$ python3 scripts/check_api_claims.py
SDK index:        21,998 symbols from iPhoneSimulator27.2.sdk
Documents:        40
Modifiers taught: 129
Verified:         127
Allowlisted:      2
Unverified:       0
```

The two allowlisted entries are `glassBackgroundEffect` and `immersionStyle`, both visionOS-only modifiers whose
declarations live in the visionOS interface that this check does not index. They are listed in
`data/api-allowlist.json` with a written reason — the only way to silence the check, and it is visible in review.

---

## 7. Cost of an audit

```
$ python3 scripts/benchmark.py --files 500
Machine:  Darwin arm64 · Python 3.14.7
Project:  500 Swift files, 7,500 lines

tool                     status       ms  findings
----------------------------------------------------
project-inspector        warn       82.2         6
privacy-auditor          fail      106.9         2
swiftui-linter           fail       88.2      1000
accessibility-auditor    fail       76.0       625
localization-checker     pass      115.5         2
liquid-glass-auditor     pass       78.1         1
sf-symbols-catalog       pass       79.5         0
release-readiness        fail      316.7         7
----------------------------------------------------
all 8 tools                        943.1

125.7 ms per 1,000 lines of Swift across the whole suite
```

Numbers vary by machine; the shape does not. Every tool is a fresh process that reads the sources once, so the
cost scales linearly with the codebase and never with the dependency graph.

---

## 8. Real data, not remembered data

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

## 9. What is *not* verified

Being explicit about this is the difference between evidence and marketing.

| Not verified | Why | Consequence |
| :--- | :--- | :--- |
| Runtime UI behaviour | No simulator or device UI tests in CI | A screen that compiles can still look wrong; visual review is still required |
| App Store approval | Only Apple can decide that | The gate models the *rules*, not the reviewer |
| Snippets in prose | Only fenced ```swift blocks are parsed | A snippet inside a sentence is not type-checked |
| A snippet's platform | Declared by the fence (` ```swift visionOS `); untagged means iOS | An untagged macOS snippet would be checked against the iOS SDK |
| Accessibility beyond contrast/targets | VoiceOver order and rotor traversal need a device | `audit_accessibility` catches the measurable subset only |
| Third-party SDK privacy manifests | The auditor scans app sources, not compiled frameworks | Check SDK manifest bundles separately |
| App Store Connect live calls | Requires a real key; CI has none | Only the error paths and mock mode are tested |

Where a check is heuristic (text scanning rather than a compiler), the finding is documented as such and the
severity reflects the confidence: `info` for suggestions, `error` for rules Apple will enforce.

---

## 10. Reproducing any single claim

| Claim | Command |
| :--- | :--- |
| "138 tests pass" | `./scripts/verify.sh` |
| "20 CLI tools" | `ls -d tools/*/ \| wc -l` |
| "31 MCP tools" | `node integrations/mcp-server/src/index.js --selftest` |
| "the HTTP transport rejects a foreign origin" | `node integrations/mcp-server/src/index.js --http 3931 &` then the `curl` above |
| "a review only reports the diff" | `cd integrations/mcp-server && npm test` (`review_diff` suite) |
| "telemetry records nothing identifying" | `node integrations/mcp-server/src/index.js --telemetry-preview` |
| "every internal link resolves" | `python3 scripts/validate_repo.py --links` |
| "Swift compiles" | `./scripts/verify-swift.sh` |
| "The gate blocks a bad project" | `python3 tools/release-readiness/generate_report.py tests/fixtures/legacy-app --metadata tests/fixtures/legacy-app/metadata.json --icon tests/fixtures/legacy-app/Assets.xcassets/AppIcon.appiconset/AppIcon-512.png` |
| "9,649 SF Symbols" | `python3 -c "import json;print(json.load(open('data/sf-symbols.json'))['count'])"` |
