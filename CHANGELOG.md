# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
