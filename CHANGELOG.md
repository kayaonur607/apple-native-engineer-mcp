# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.5.2] — 2026-11-07

Found by using the server on a published Expo app.

### Fixed

- Git-ignored Expo `ios/` hosts are recognised: release plans start with `npx expo prebuild --clean`, and version and build number come from `app.json`.
- No Swift-architecture advice (SwiftUI APIs, Swift 6, Swift Testing) for generated cross-platform hosts.
- Privacy findings explain that framework runtimes and plugins use required-reason APIs.

### Changed

- React Native screen routing for captures is now verified; the guide lists the splash and Expo Router pitfalls.

## [2.5.1] — 2026-11-07

Includes everything listed under 2.5.0. The v2.5.0 tag was pushed, but its release gate failed and no GitHub Release was published.

### Fixed

- Dry-run capture plans no longer wait for a cold Simulator service (the release runner timed out after 60 s).

## [2.5.0] — 2026-11-07

### Added

- `audit_cross_platform`: Apple-native checks for Flutter, React Native, Expo, Capacitor, .NET MAUI and Kotlin Multiplatform apps through their iOS host.
- Host projects in `ios/`, `macos/`, `ios/App`, `Platforms/iOS` and `iosApp/` are found by every tool.
- `plan_distribution` plans `flutter build ipa`, EAS build/submit, `cap sync`, `dotnet publish` and KMP archives.
- `XPL020`/`PROJ022`: deployment target below the installed SDK's minimum.
- Capture: per-screen environment variables and a warning for custom-scheme deep links.
- Prompts for Flutter, React Native/Expo and other cross-platform stacks; three new references.
- Recorded Flutter run: template build failure found, fixed, captured and framed.

### Changed

- `audit_project` runs nine audits; `review_diff` also reviews changed Dart and JS/TS files.

## [2.4.0] — 2026-11-07

### Added

- `capture_screenshots`: real Simulator captures across devices, locales and light/dark from one plan, 9:41 status bar, launch-argument routing, automatic RGB flattening and a provenance manifest.
- `audit_screenshots` and `get_app_store_specs`: Apple's current slot table (incl. iPhone Duo, Watch Ultra 3, Apple TV), alpha, 1–10 per set and required sets per platform.
- Marketing frames: localized captions, drawn device frame with Dynamic Island, RTL, native CoreGraphics/San Francisco PNG rendering.
- `plan_distribution`: preflight, ExportOptions and ordered archive, TestFlight/App Store upload and Developer ID notarization commands. Executes nothing.
- `search_apple_guidelines`: offline index of 158 HIG pages.
- Nine prompts: iOS, iPadOS, iPhone Duo, macOS, watchOS, tvOS, visionOS, new screen, distribute.
- References: tvOS, iPhone Duo, distribution and release, App Store product page assets.
- README with recorded evidence and new SVG visuals.

### Fixed

- HIG tables rendered as raw data; links now keep Apple's titles and URLs.
- Mac screenshot slots listed an unsupported 3840×2160 size.
- Outdated screenshot and design prompts.

## [2.3.0] — 2026-11-07

- GitHub release launcher validates existing cache directories before activation, including rollback installations.
- Fix SWU010 false positives on explicit value animations and TimelineView schedules.
- Fix SWU005 false positives across sibling views; retain nested Text/modifier detection with regression tests.
- Add free community pilot and open-source portfolio guidance; no paid tier or license key.
- Add a one-command dependency installer that prints an absolute-path MCP configuration.
- Record an external Apple Food Truck audit without claiming measured accuracy.
- Compile, launch and capture a controlled SwiftUI app in an actual simulator in light and dark.
- Enable GitHub immutable releases for future published versions.

## [2.2.1] — 2026-11-07

Includes the v2.2.0 developer/designer onboarding, automatic GitHub release updates, version-aware AI guidance and animated evidence walkthrough, with the release portability fixes below.

### Fixed

- GitHub release launcher distribution: the release verification gate now invokes the same npm test script that passes on Node 20/22, instead of passing a test directory unsupported by Node 22.
- Preserve full Python and MCP failure logs when a release gate fails.
- Exact SDK reference regeneration is checked only against the SDK recorded in that reference. Other SDKs still run the structural validation and report the exact reproduction check as skipped.
- Add macOS Python regression coverage alongside the existing Linux matrix.

The v2.2.0 source tag was pushed, but its release gate failed and no GitHub Release was published. The recorded v2.2.0 animation remains valid demonstration evidence. v2.2.1 is the first stable published candidate for this GitHub-only workflow.

## [2.2.0] — 2026-11-07

### Added

- Developer/designer onboarding with `/apple-native-start`, task routing, Apple HIG/API provenance, and explicit build/runtime evidence boundaries.
- GitHub release launcher: checks published stable releases at MCP startup, installs into isolated version/commit directories, and activates only after a smoke test.
- Offline fallback to the last working installation, atomic activation, concurrent update locking, version pinning and an automatic update opt-out.
- `apple-native://release` exposes the installed version, release notes and update policy to the AI client. Connection instructions announce the version and relevant changes.
- Reproducible MCP demonstration evidence and a commercial/video production plan.
- Rewritten product README with measured audit/asset visuals, a 64-second animated, captioned usage video, GIF preview, raw stdio session and media checksums.

### Changed

- GitHub is the sole product distribution and release channel. npm publication is disabled; npm is used only to install locked runtime dependencies.
- Version tags use `mcp-vMAJOR.MINOR.PATCH`. GitHub Release notes and this changelog describe each version.
- Updates take effect on the next MCP connection/restart. Existing sessions and customer source trees are never replaced by the launcher.
- Static audits no longer imply runtime validation or Apple approval.

## [2.1.0] — 2026-11-05

The MCP server stops being a wrapper and becomes the product: sixteen tools, a transport for containers and
shared machines, and privacy claims that a test enforces.

### Added

- **App Store Connect depth** — read-only access now covers `app_details` (identity and content-rights declaration),
  `localizations` (listing copy per locale) and `screenshots` (sets, display type, delivery state, pixel size), in
  addition to apps, versions and builds. The CLI gained `app`, `localizations` and `screenshots`; the MCP tool
  exposes them through its `operation` enum. Still GET-only.
- **Apple documentation research (live)** — `tools/apple-docs-research/`: search a framework index (8,000+ symbols),
  read a page as Markdown, inspect per-platform availability, read HIG pages. Reads the JSON API
  developer.apple.com itself uses, refuses any other host, caches for seven days, and returns `source_url` plus
  `fetched_at` with every answer.
- **Icon generation** — `icon-studio prepare` turns one 1024×1024 master into 18 slots plus `Contents.json`, with a
  pure-Python PNG codec and box-filter downscale. `verify` re-reads every slot; `preview` renders it small.
- **ASO analysis** — deterministic budgets, duplicate/wasted keyword detection, coverage against visible copy,
  risky-claim detection, and keyword candidates extracted from the developer's own description. It states in its
  own output that no search-volume or competitor data is used.
- **Marketing screenshot composition** — exact-size SVG frames around real captures (background, headline,
  subheadline, embedded screenshot, three themes), optionally rasterised when a renderer is installed.
- **App Store Review risk engine** — `tools/app-store-review/`: usage descriptions against real sensor use (5.1.1),
  placeholder copy (2.1), account creation without deletion (5.1.1(v)), external payment providers (3.1.1),
  web-wrapper apps (4.2), private API usage (2.5.1) and listing URLs (2.3.1). Every finding names the section and
  the file.
- **Capability modules** — the sixteen tools are grouped into nine modules (`core`, `swift-engineering`,
  `sf-symbols`, `design-tokens`, `privacy-security-audit`, `app-store-review`, `app-store-assets`,
  `release-readiness`, `app-store-connect`) and gated by `APPLE_NATIVE_MODULES`. `core` cannot be disabled, an
  unknown id stops startup with the valid list, and a disabled tool is absent from `tools/list` and errors when
  called. Ten tests enforce the rules in `test/modules.test.js`; the contract is written down in
  `docs/MODULES.md`.
- **Roadmap** — `docs/ROADMAP.md` lists every capability as implemented, partial or not started, with what is
  missing. A claim that cannot be demonstrated is a bug in that document.
- **Logo** — `assets/logo.svg`, a native squircle mark (brackets plus a check) used at the top of the README.
- **`review_diff`** — reads `git diff --name-only` (against `HEAD`, the index with `staged`, or any `base`
  revision), keeps the changed `.swift` files and runs the SwiftUI, accessibility and Liquid Glass auditors on
  each one. Findings are grouped under `data.files` and every finding names the auditor that produced it. This is
  the tool an agent should call in an edit loop: a project that was already non-compliant does not drown the
  review in pre-existing findings.
- **`check_environment`** — diagnoses the server's own runtime: Node and Python versions against their minimums,
  the presence of the auditors and the reference guides, git, Xcode and its iOS SDK, App Store Connect credentials
  (presence only, never the value) and the telemetry mode. Run it before reporting a bug.
- **Streamable HTTP transport** — `node src/index.js --http [port]` serves `POST /mcp` and an unauthenticated
  `GET /health`, stateless, one server instance per request. The defaults are deliberately unfriendly: loopback
  bind only, `--allow-remote` required for anything else, a hard `Origin` check as the DNS-rebinding defence, and
  `application/json` only under a 4 MiB cap. There is no CORS support, by design.
- **Progress notifications** — `audit_project` and `review_diff` emit one `notifications/progress` per completed
  audit when the client supplies a `progressToken`, instead of going silent for several seconds.
- **Cancellation** — the MCP request `AbortSignal` is threaded into the child-process runner; a cancelled call
  kills its child and returns `TOOL_CANCELLED` rather than orphaning a process.
- **Self-contained npm package** — `scripts/pack-vendor.mjs` stages the auditors and the knowledge base into
  `vendor/` on `prepack`, so `npx apple-native-engineer-mcp` works without a repository checkout. Development
  still resolves the live repository, so an edited auditor takes effect immediately. Verified end-to-end by
  packing, installing in a clean directory and running a real tool call.
- **Publishing metadata and pipeline** — `mcpName`, keywords, repository, `files` and a `Dockerfile` (two-stage,
  non-root, `HEALTHCHECK`) plus `smithery.yaml`, `server.json` for the MCP registry, and
  `.github/workflows/publish.yml`, which publishes with provenance on an `mcp-v*` tag and then installs the
  published tarball and runs `--selftest` against it.
- **`--doctor` and `--telemetry-preview`** — `--doctor` prints the same environment report `check_environment`
  returns, with a matching exit code (0 healthy, 1 degraded, 2 blocked), so a CI job can gate on it.
  `--telemetry-preview` prints the exact JSON that telemetry would write, including the closed five-key event
  shape.
- **Publish-metadata test** — the server is described in `package.json`, `server.json`, `smithery.yaml` and the
  `Dockerfile`, each read by a different pipeline. One test asserts a single version across all four, that
  `mcpName` equals the registry name, that every URL points at the real repository, that the tarball ships
  `vendor/`, and that every local `COPY` source exists.
- **`docs/PUBLISHING.md`** — the release runbook: which files carry the version, how to verify the packed tarball
  rather than the source tree, the `mcp-v*` tag that publishes with provenance, the registry submissions npm does
  not perform, and how to roll back (deprecate, never unpublish).
- **`.mcp.json`** — project-scoped MCP configuration, so a client that reads it discovers the server without a
  hand-edited `claude_desktop_config.json`.

### Changed

- **All 29 reference guides rewritten against the installed SDK.** Every symbol, modifier and framework name is
  grepped from `iPhoneOS27.2.sdk` / `XROS27.2.sdk` rather than recalled; every finding code cited in a guide now
  exists in the tool that emits it (113 codes cross-checked). Guides that described the wrong OS for Liquid Glass,
  listed one required-reason code per privacy category, or cited a session number nobody published are corrected
  in place, with the correction stated where it matters.
- **Snippet verification is platform-aware.** A fence may name its platform — ` ```swift visionOS ` — and the
  type-checker compiles it against that platform's SDK and target instead of the iOS SDK. Eight visionOS snippets
  are now genuinely type-checked; before, they were checked against iOS, where `.windowStyle(.volumetric)` and
  `defaultSize(width:height:depth:)` do not exist, and the harness reported the mismatch as three documentation
  bugs. One real bug surfaced: `RealityKit` declares its own `Scene`, so importing it next to an `App` makes
  `some Scene` ambiguous. The guide now keeps the scene and the RealityKit content in separate files.
- **MCP server documentation rewritten** — install matrix (npx, repository, Docker), HTTP mode, the tool table,
  the result envelope, the privacy model and the limits, each stated rather than implied.
- **`--http` configuration errors** now print one sentence and exit 2 instead of a stack trace.
- **Envelope, resource and prompt counts corrected in the README** — 16 tools, 53 resources, 12 prompts, and the
  badge now tracks the real suite size (138 tests).
- **`CHANGELOG`, `SECURITY.md` and `docs/PROOF.md` brought up to date.** `SECURITY.md` had a supported-versions
  table that stopped at 1.0.x and no mention of the unauthenticated HTTP transport; both are fixed, and the
  security scope is now written down instead of implied.

### Fixed

- **`SKILL.md` lagged the server.** It still described the six-call loop and claimed version 2.0.0. The operating
  loop now leads with `audit_project` and re-audits with `review_diff`, and the metadata version matches the
  package.
- **README quickstart said 93 tests** while the suite had grown to 138. The prose count is now part of the review
  checklist for any change that adds tests.
- **CI never exercised the npm artefact.** `pack -> install -> --selftest -> --doctor` and the `vendor/` drift
  check ran only from the publish workflow, so a packaging regression could only be found at release time. They
  now run on every push.

- **The umbrella prompt was named `apple-native-apple-native`.** `commands/apple-native.md` was being namespaced
  like every other command. It is now `apple-native`, and a test asserts that no prompt is double-prefixed.
- **`graph` cycles in the server modules** — identity moved to `src/constants.js` so `environment.js` can report
  the server name without importing `server.js`.
- **`git` detection no longer parses stderr.** "Not a git repository" is decided from `git rev-parse
  --is-inside-work-tree`'s exit status, because git's messages are localised and a translated one used to be
  reported as `GIT_DIFF_FAILED`.
- **Three auditors rejected a single file.** `lint_swiftui`, `audit_accessibility` and `audit_liquid_glass` now
  accept a `.swift` path as their target (via `swiftscan.iter_files` and `guard_directory(allow_file=True)`), which
  is what makes a file-scoped review possible from the CLI as well as from MCP.
- **SDK declarations were being compiled as if they were code.** Two guides quote an interface signature
  (`EnvironmentValues.colorSchemeContrast`, `RoundedRectangle`) in a `swift` fence; the type-checker read them as
  snippets and reported an error in the guide. They are now `text` fences, which is what they always were.

### Security

- **Telemetry is off by default and enforced by an allowlist.** When enabled it records `schema`, `tool`,
  `outcome`, `duration_bucket` and `day` — nothing else. Unknown fields are dropped, unknown tools are refused,
  and `anonymous` mode requires an HTTPS endpoint you supply (there is no default endpoint, so there is nothing
  to phone home to). `test/telemetry.test.js` feeds the sanitiser paths, file names, prompts, credentials and
  identifiers, and fails if any of them survive.
- **The HTTP transport has no authentication.** That is stated in the README, in `SECURITY.md` and in the startup
  banner, and a non-loopback bind is refused without an explicit flag.

## [2.0.0] — 2026-11-05

A ground-up rebuild. Version 1 shipped the right idea with an unverified knowledge base, a MCP server that
reimplemented JSON-RPC by hand, and a release gate that awarded 90/100 to projects it had never inspected.
Version 2 replaces all three.

### Added

- **Five new auditors**
  - `swiftui-linter` — 20 rules across deprecated API, hardcoded styling, view identity and robustness.
  - `accessibility-auditor` — real WCAG contrast maths in both appearances, Dynamic Type, 44pt targets, VoiceOver
    labelling.
  - `liquid-glass-auditor` — iOS 26 Liquid Glass adoption vs. imitation, with availability-guard detection.
  - `sf-symbols-catalog` — 9,649 symbols extracted from `CoreGlyphs.bundle`, with per-OS availability and typo
    suggestions.
  - `design-token-forge` — token JSON → SwiftUI constants + `.xcassets` colour sets, with contrast validation.
- **Shared runtime library** (`tools/lib/apple_native/`) — one report contract, one Swift scanner, one colour-maths
  module, one Xcode parser. Tools shrank by an order of magnitude.
- **Stable JSON envelope** (`schema_version: "2.0"`) with severity ordering and documented exit codes
  (0 pass, 1 warnings under `--strict`, 2 fail).
- **MCP server rebuilt on the official SDK** (v1.32): 13 tools, 52 resources, 10 prompts, declared `outputSchema`,
  correct tool annotations, real `isError` handling.
- **Knowledge base exposed as MCP resources** — the 30 references, 12 checklists and 9 examples are addressable
  as `apple-native://` URIs instead of being pasted into prompts.
- **Generated SDK reference** — `references/whats-new-ios-27.md` lists the 64 declarations the installed SDK
  annotates `@available(iOS 27.0, …)`, grouped by framework. Generated, not recalled, and drift-checked in CI.
- **Snippet type-checking** — `scripts/typecheck_snippets.py` compiles all 118 documented Swift blocks, separates
  fragment noise from real errors, and runs in `--strict` mode in CI. Its first run found 14 occurrences of the
  invalid `dampingRatio:` label across six guides.
- **Documentation API verification** — `scripts/check_api_claims.py` indexes 21,998 SDK symbols and proves that
  every SwiftUI modifier taught in the guides exists, with a two-entry, reasoned allowlist for visionOS-only API.
- **Developer experience** — `make doctor` (toolchain check with the exact fix for each missing piece),
  `make demo` (a 30-second tour of the audits on the broken fixture) and a `Makefile` that delegates to the same
  scripts CI runs.
- **Benchmark** — `make benchmark` times all eight auditors on a synthetic 500-file project: 922 ms total,
  ~123 ms per 1,000 lines of Swift.
- **Template self-tests** — the metadata, icon and report templates must pass the tools they template, and the
  screenshot spec's dimensions must be recognised by the validator.
- **Verification harness** — `scripts/verify.sh` runs repository validation, 55 Python tests, 8 MCP protocol tests
  and real `swiftc` compilation; `docs/PROOF.md` records the transcripts.
- **Two fixture projects** — `clean-app` (must produce zero findings) and `legacy-app` (must trip every rule), so
  both false positives and false negatives are test failures.
- **CI in the right place** — `.github/workflows/ci.yml` (v1's workflow lived in `ci/workflows/`, where GitHub
  Actions never looked).

### Changed

- **Release gate is now honest.** A gate with no input is `NOT INSPECTED`, scores zero and forces `BLOCKED`.
  Any error or critical finding zeroes its gate. `READY` requires every applicable gate to pass *and* a score of
  at least 90. The weights are explicit: privacy 25, assets 15, metadata 15, project 15, localisation 10,
  widgets 10, accessibility 10.
- **App Store Connect never fakes success.** Missing credentials are a hard error with the exact variables to set;
  `--mock` is explicit and announces itself; a missing `cryptography` install is reported instead of emitting a
  fake ES256 signature.
- **Localisation checker tells the truth.** `Text("literal")` is a `LocalizedStringKey` and is *not* reported.
  The tool now flags `Text(verbatim:)`, UIKit string assignments and `Text(resolvedString)`.
- **Apple platform baseline moved to iOS 26/27**, iOS 17 floor. Liquid Glass, `@Observable`, Swift 6 language mode
  and String Catalogs are the defaults.
- **README rewritten around evidence** — every count is cross-checked by `scripts/validate_repo.py`.

### Fixed

- CI workflow was in `ci/workflows/` and never executed; moved to `.github/workflows/`.
- `npx skills add` commands referenced a repository name that does not exist.
- Deployment targets such as `17` compared less-than `17.0` (tuple comparison), producing false "outdated OS"
  findings.
- String literals were blanked before value extraction, so SF Symbol names and colour hex codes were silently
  lost.
- Dynamic Island region detection missed `compactLeading:` / `compactTrailing:` without a leading dot.
- Version claims: Liquid Glass was documented as iOS 18 / macOS Sequoia. It is iOS 26 / macOS 26.
- Tool counts disagreed across README, MCP docs and reality (8 vs 9 vs 10).
- Personal absolute paths (`/Users/<name>/Desktop/...`) leaked into documentation.

### Removed

- `ci/` (superseded by `.github/workflows/`).
- `SOURCES.md` and `COMMANDS.md` (their content moved into `references/` and `commands/`).
- Silent mock fallback in the App Store Connect client.

## [1.0.0] — 2026-11-04

Initial release: 9 CLI tools, a hand-rolled stdio JSON-RPC server, 30 reference guides, 12 checklists, 9 examples
and 18 unit tests.
