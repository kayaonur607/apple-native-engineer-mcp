<p align="center">
  <img src="assets/hero.svg" alt="Apple Native Engineer" width="100%">
</p>

<h1 align="center">apple-native-engineer-mcp</h1>

<p align="center">
  <strong>Stop your AI from shipping web-looking SwiftUI.</strong><br>
  An engineering standard, 14 executable auditors and an MCP server that make Apple platform output<br>
  <em>measurably</em> native — every claim in this repository is verified by CI.
</p>

<p align="center">
  <a href="https://github.com/kayaonur607/apple-native-engineer-mcp/actions/workflows/ci.yml"><img src="https://github.com/kayaonur607/apple-native-engineer-mcp/actions/workflows/ci.yml/badge.svg" alt="CI"></a>
  <img src="https://img.shields.io/badge/tests-93_passing-30D158" alt="93 tests">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue" alt="MIT"></a>
  <img src="https://img.shields.io/badge/MCP-1.32-8A2BE2" alt="MCP">
  <img src="https://img.shields.io/badge/Swift-6.x-F05138" alt="Swift 6">
  <img src="https://img.shields.io/badge/iOS-26_|_27-000000" alt="iOS 26 / 27">
</p>

---

## The problem this solves

Ask any model to build an iOS screen and you get the same tells: `Color(red: 0.1, green: 0.1, blue: 0.1)` that
disappears in Dark Mode, `.font(.system(size: 28))` that ignores Dynamic Type, `.frame(width: 320)` that clips
localised copy, `NavigationView`, `ObservableObject`, hand-rolled "glassmorphism" stacked out of three
`.ultraThinMaterial` layers, and a `PrivacyInfo.xcprivacy` that doesn't exist — which is an automatic App Store
upload rejection.

None of that is a knowledge problem. It is a **feedback problem**: the agent has no way to check its own output
against Apple's rules.

This repository is that feedback loop. It ships:

1. **A standard** — the opinions a senior Apple engineer applies in review, written down once (`SKILL.md` +
   30 reference guides).
2. **14 auditors** — executable tools that turn those opinions into finding codes and exit codes.
3. **An MCP server** — all 13 checks exposed to Claude, Cursor, Codex or any MCP client, plus the knowledge base
   as resources and the workflows as prompts.

> [!IMPORTANT]
> **Nothing here is vibes.** Every number in this README is produced by `./scripts/verify.sh`, which runs 93
> tests, a link/count validator and a real Swift type-check. See [Proof](#proof).

---

## Quickstart

```bash
git clone https://github.com/kayaonur607/apple-native-engineer-mcp.git
cd apple-native-engineer-mcp

make doctor   # is this machine ready?
make demo     # 30 seconds: the audits running on a deliberately broken app
make verify   # everything CI runs, including 85 tests and a real Swift compile
```

`make demo` output, trimmed:

```
1/4 · What is this project?          → 7 findings: iOS 16 floor, no @Observable, NavigationView…
2/4 · What is wrong with the SwiftUI? → 14 findings: 3 errors (NavigationView, UIScreen.main, try!)
3/4 · Would the App Store accept it?  → icon is 512×512 with an alpha channel — rejected
4/4 · The verdict                     → BLOCKED, 19/100
```

The same gate on a project that follows the rules returns **READY FOR SUBMISSION, 100/100**.

### 1. Use it as an MCP server (recommended)

```bash
git clone https://github.com/kayaonur607/apple-native-engineer-mcp.git
cd apple-native-engineer-mcp/integrations/mcp-server
npm install
```

Add to your client (`~/Library/Application Support/Claude/claude_desktop_config.json`, or `.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["/absolute/path/to/apple-native-engineer-mcp/integrations/mcp-server/src/index.js"]
    }
  }
}
```

Verify it is alive before blaming the client:

```bash
node integrations/mcp-server/src/index.js --selftest
# {"name":"apple-native-engineer","version":"2.0.0",
#  "tools":[...13...],"resources":53,"prompts":12}
```

### 2. Use it as a skill (no server)

```bash
npx skills add kayaonur607/apple-native-engineer-mcp
```

Or symlink it yourself:

```bash
ln -s "$PWD" ~/.claude/skills/apple-native-engineer
```

### 3. Use the CLI directly (no AI at all)

```bash
python3 tools/project-inspector/inspect_project.py .
python3 tools/swiftui-linter/lint_swiftui.py .
python3 tools/release-readiness/generate_report.py . \
  --metadata metadata.json --icon AppIcon-1024.png --output RELEASE_REPORT.md
```

Python 3.10+ and the standard library. No virtualenv, no `pip install`, nothing to break.

---

## What it catches

Real output from the bundled `legacy-app` fixture (`./scripts/verify.sh` runs this every time):

```
$ python3 tools/swiftui-linter/lint_swiftui.py tests/fixtures/legacy-app
==========================================================================
  Apple Native Engineer — SwiftUI Lint
==========================================================================
  Status:       FAIL
  Findings:     14 (0 critical, 3 error, 8 warning, 3 info)
--------------------------------------------------------------------------
  ✖ SWU003 NavigationView is deprecated since iOS 16.
      → Use NavigationStack with typed navigation paths...
  ✖ SWU006 UIScreen.main.bounds is not multi-window, Stage Manager or visionOS safe.
  ✖ SWU014 try! crashes the process on any thrown error.
  ▲ SWU005 Fixed width on Text truncates at large Dynamic Type sizes.
  ▲ SWU001 Hardcoded hex colour breaks Dark Mode and Increase Contrast.
  ▲ SWU002 .foregroundColor(_:) is deprecated since iOS 17.
```

And the release gate refuses to certify it:

```
$ python3 tools/release-readiness/generate_report.py tests/fixtures/legacy-app \
    --metadata metadata.json --icon AppIcon-512.png
  Verdict:      BLOCKED
  Score:        19/100
  Blocking:     privacy, accessibility, widgets, assets, metadata
```

The clean fixture — a real SwiftUI app with `@Observable`, String Catalogs, Liquid Glass behind an availability
guard, a full Dynamic Island and a valid privacy manifest — scores **100/100 · READY FOR SUBMISSION**.

---

## The 14 CLI tools

| Tool | What it answers | Codes |
| :--- | :--- | :--- |
| [`project-inspector`](tools/project-inspector/) | What is this project, what does it target, what debt does it carry? | `PROJ*` |
| [`privacy-auditor`](tools/privacy-auditor/) | Are Required-Reason APIs declared with **valid** reason codes? | `PRIV*` |
| [`asset-validator`](tools/asset-validator/) | Is the icon 1024×1024 opaque PNG, and do screenshots match a slot? | `ASSET*` |
| [`metadata-validator`](tools/metadata-validator/) | Does the listing fit App Store Connect's character limits? | `META*` |
| [`localization-checker`](tools/localization-checker/) | Which strings can never be translated, and what breaks in RTL? | `L10N*` |
| [`widget-validator`](tools/widget-validator/) | Do the widget, Dynamic Island and Live Activity actually work? | `WID*` |
| [`swiftui-linter`](tools/swiftui-linter/) | 20 rules: deprecated API, hardcoded styling, identity churn. | `SWU*` |
| [`accessibility-auditor`](tools/accessibility-auditor/) | Real WCAG contrast maths, Dynamic Type, 44pt targets, VoiceOver. | `A11Y*` |
| [`liquid-glass-auditor`](tools/liquid-glass-auditor/) | Liquid Glass adopted correctly — or imitated with fake stacks? | `LG*` |
| [`sf-symbols-catalog`](tools/sf-symbols-catalog/) | Does this symbol exist, and does it exist on *your* deployment target? | `SFC*` |
| [`design-token-forge`](tools/design-token-forge/) | Token JSON → SwiftUI tokens + `.xcassets`, with contrast checks. | `TOK*` |
| [`screenshot-studio`](tools/screenshot-studio/) | Capture from a booted simulator, validate the slot. | `SHOT*` |
| [`app-store-connect`](tools/app-store-connect/) | Read-only ASC: apps, versions, builds. No silent mock. | `ASC*` |
| [`release-readiness`](tools/release-readiness/) | Weighted verdict across every gate — the only one that blocks. | `REL*` |

**What is genuinely new here**, compared with the usual "Apple docs RAG" MCP servers:

- **SF Symbol availability from the real catalogue.** 9,649 symbols extracted from `CoreGlyphs.bundle`, each
  mapped to the OS release that introduced it. The tool tells you `square.and.pencil` is fine on iOS 17 but a
  newer symbol is not — and suggests the closest real name when you typo.
- **Liquid Glass detection, verified against the SDK.** The auditor knows `.glassEffect(_:in:)`,
  `GlassEffectContainer`, `.glassEffectID`, `.scrollEdgeEffectStyle` and `.buttonStyle(.glass)` are iOS 26+, that
  `Glass` has exactly `.regular`, `.clear`, `.identity` with `.tint()` and `.interactive()`, and that the API is
  unavailable on visionOS. It flags the imitation pattern instead of the real one.
- **A release gate that cannot be fooled.** A gate with no input is `NOT INSPECTED`, scores zero and forces
  `BLOCKED`. A missing metadata file is not a passing metadata file — which is exactly how the previous version
  of this tool handed out 90/100 to a project it had barely looked at.
- **Contrast maths, not contrast guesses.** `#C7C7CC` on white is 1.68:1, computed from the WCAG relative
  luminance formula, in both appearances.
- **The documentation is checked against the SDK.** All 96 view modifiers taught in the reference guides are
  looked up in 21,998 symbols parsed from the installed `.swiftinterface` files; anything that does not exist
  fails CI. Two visionOS-only modifiers are allowlisted, each with a written reason.

---

## The 13 MCP tools

`inspect_apple_project` · `audit_privacy_manifest` · `validate_app_icon` · `validate_app_metadata` ·
`check_localization` · `validate_widgets` · `lint_swiftui` · `audit_accessibility` · `audit_liquid_glass` ·
`validate_sf_symbols` · `forge_design_tokens` · `generate_release_report` · `app_store_connect`

Built on the official `@modelcontextprotocol/sdk` (v1.32), not a hand-rolled JSON-RPC loop. That buys:

- **Structured output.** Every result carries a versioned envelope (`schema_version: "2.0"`) with `status`,
  `summary`, `findings[]` and `data{}` — validated against a declared `outputSchema`, so clients get typed fields
  instead of a blob of text.
- **Honest errors.** A missing path returns `isError: true` with a machine-readable code, never a stack trace.
- **53 resources.** The 31 reference guides, 12 checklists, 9 examples and `SKILL.md` are exposed as
  `apple-native://` resources, so the agent loads the design standard on demand instead of you pasting it.
- **12 prompts.** Every slash command (`/apple-native`, `/apple-native-design`, `/apple-native-release`, …) is a
  first-class MCP prompt with a `project` argument.

Tool annotations are set correctly too: audit tools are `readOnlyHint: true, destructiveHint: false`. The server
cannot mutate your project or your App Store account.

---

## The knowledge base

| Section | Count | What it is |
| :--- | ---: | :--- |
| [`SKILL.md`](SKILL.md) | — | The operating standard: what "native" means, decision tables, refusal rules |
| [`references/`](references/) | 31 reference guides | HIG foundations, Liquid Glass, SwiftUI engineering, StoreKit 2, SwiftData, privacy, performance |
| [`checklists/`](checklists/) | 12 checklists | Review protocols to run before a PR, a design review or a submission |
| [`examples/`](examples/) | 9 worked examples | Navigation, adaptive layout, animation, Live Activities, StoreKit paywalls |
| [`commands/`](commands/) | 12 commands | Slash-command specs that drive the tools |

All of it targets **iOS 26 / iPadOS 26 / macOS 26 and iOS 27**, with an iOS 17 floor for code that has to run on
older devices. Liquid Glass, `.scrollEdgeEffectStyle`, `@Observable`, Swift Testing and String Catalogs are the
defaults; `NavigationView`, `ObservableObject`, `foregroundColor` and fixed font sizes are called out as legacy.

---

## Proof

This is the part most repositories skip. Here is what `./scripts/verify.sh` actually does:

| Stage | Result | How it is measured |
| :--- | :--- | :--- |
| Repository validation | **pass** | Frontmatter, 20 required paths, every internal link, and every count in this README cross-checked against the filesystem |
| Python tests | **85 pass** | `python3 -m unittest` across 3.10 / 3.12 / 3.13 in CI |
| MCP protocol tests | **8 pass** | A real `Client` ↔ `McpServer` pair over the SDK's in-memory transport |
| Swift compilation | **pass** | `swiftc -typecheck` on both fixtures, `swiftc -parse` on all 118 documentation snippets |
| SF Symbols catalogue | **9,649 symbols** | Extracted from `CoreGlyphs.bundle`, internally consistent |
| SDK reference | **64 iOS 27 declarations** | Generated from the installed `.swiftinterface`, drift-checked in CI |
| Documented API | **94 verified, 2 allowlisted, 0 invented** | Every modifier in every guide looked up in the SDK |
| Snippet type-check | **35 compile, 83 classified fragments, 0 real errors** | `swiftc -typecheck` on all 118 blocks |

Both directions are tested, which is the point:

- the **clean** fixture must produce **zero** warnings across all auditors (no false positives)
- the **legacy** fixture must trip **every** rule it was built for (no false negatives)

`docs/PROOF.md` contains the raw terminal transcripts, including the intentionally noisy runs.

### How a claim gets into this repo

1. It is written as a rule, a docstring or a reference guide.
2. A tool implements it and emits a stable finding code.
3. A fixture reproduces the defect and a test asserts the code fires.
4. CI runs the test on every push.

If a rule can't survive step 3, it doesn't ship.

---

## Design rules the tools enforce

These are the rules that most often separate "looks like iOS" from "is iOS":

| Never | Always | Enforced by |
| :--- | :--- | :--- |
| Hardcoded hex / `Color.white` | Semantic colours, asset colours, `.primary` | `SWU001`, `SWU013`, `A11Y001` |
| `.font(.system(size:))` | Text styles that scale with Dynamic Type | `SWU012`, `A11Y010` |
| `.frame(width:)` on text | `.frame(maxWidth:)`, `ViewThatFits`, layout priority | `SWU005` |
| `scaleEffect(0)` | Springs from 0.9–0.95 | `SWU009` |
| `.ultraThinMaterial` + `.blur` | `.glassEffect(_:in:)` on iOS 26+, guarded | `LG001`, `LG010` |
| `.padding(.left)` | `.padding(.leading)` / `.horizontal` | `L10N010` |
| Missing privacy manifest | `PrivacyInfo.xcprivacy` with real reason codes | `PRIV001`, `PRIV010` |
| Icon with alpha | Opaque 1024×1024 PNG | `ASSET004` |

---

## Repository layout

```
apple-native-engineer-mcp/
├── SKILL.md                  # the standard an agent loads first
├── tools/                    # 14 CLI tools + tools/lib (shared runtime)
│   └── lib/apple_native/     #   report contract, Swift scanning, colour maths, Xcode parsing
├── integrations/mcp-server/  # official-SDK MCP server (tools + resources + prompts)
├── references/ checklists/ examples/ commands/
├── data/sf-symbols.json      # 9,649 SF Symbols with per-OS availability
├── tests/                    # 55 Python tests + two fixture projects
├── scripts/verify.sh         # the one command that proves the repo works
├── scripts/doctor.sh         # environment check (python, node, Xcode, SDK)
├── scripts/demo.sh           # 30-second tour on the bundled fixtures
└── .github/workflows/ci.yml  # repository · python ×3 · mcp · swift
```

---

## Compatibility

| | Supported |
| :--- | :--- |
| OS targets | iOS 17–27, iPadOS, macOS 14–27, watchOS 10+, visionOS 1+ |
| Language | Swift 6.x (tools also audit Swift 5 mode projects) |
| Xcode | 16+ for the Swift checks; the Python tools need no Xcode |
| Python | 3.10, 3.12, 3.13 (stdlib only) |
| Node | 20, 22 (MCP server) |
| Clients | Claude Desktop, Claude Code, Cursor, Codex, Copilot, Gemini CLI, OpenCode, any MCP client |

### Optional: live App Store Connect

Read-only, and it refuses to pretend:

```bash
export ASC_KEY_ID=XXXXXXXXXX
export ASC_ISSUER_ID=00000000-0000-0000-0000-000000000000
export ASC_PRIVATE_KEY_PATH=~/.appstoreconnect/AuthKey_XXXXXXXXXX.p8
python3 -m pip install cryptography      # required for ES256 signing

python3 tools/app-store-connect/cli.py verify
```

No credentials? You get a hard error explaining exactly what to set. `--mock` exists, is explicit, and says so in
its output. There is no silent fallback to synthetic data.

---

## Performance

The audits run before a build exists, so they have to be cheaper than the thing they check. Measured with
`make benchmark` on a synthetic 500-file / 7,500-line project (Darwin arm64, Python 3.14):

| Tool | Wall time |
| :--- | ---: |
| project-inspector | 82 ms |
| privacy-auditor | 107 ms |
| swiftui-linter | 88 ms |
| accessibility-auditor | 76 ms |
| localization-checker | 116 ms |
| liquid-glass-auditor | 78 ms |
| sf-symbols-catalog | 80 ms |
| release-readiness (runs the suite internally) | 317 ms |
| **all eight** | **922 ms** |

≈123 ms per 1,000 lines of Swift for the whole suite. No network, no Xcode, no build products — which is why it can
run on every agent turn rather than once a day in CI.

---

## Non-goals

- **Not a build system.** It never calls `xcodebuild` to produce your app; it checks the things that break *before*
  and *after* the build.
- **Not a documentation search engine.** Apple's docs are better at being Apple's docs. This is opinionated
  engineering review.
- **Not official.** Independent project, MIT licensed, not affiliated with Apple. Apple's guidelines are referenced
  for interoperability under nominative fair use.

---

## Contributing

New rules need three things: a finding code, a fixture that reproduces the defect, and a test that proves the code
fires. See [CONTRIBUTING.md](CONTRIBUTING.md). `./scripts/verify.sh` is the gate — if it is green, the PR is
reviewable.

## License

[MIT](LICENSE) © apple-native-engineer-mcp contributors
