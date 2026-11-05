# Roadmap and capability matrix

This repository's argument is that claims should be checkable. That applies to the roadmap too: a capability is
listed as **implemented** only when a tool implements it, a test exercises it and `./scripts/verify.sh` runs that
test. Everything else says so.

Last reviewed: 2026-11-06 · SDK 27.2 · Xcode 27.2

---

## Capability matrix

| Capability | Status | What exists today | What is missing |
| :--- | :--- | :--- | :--- |
| Project inspection | **Implemented** | `project-inspector`: project kind, targets, OS floors, Swift version, frameworks, architecture signals, debt findings | — |
| SwiftUI lint | **Implemented** | 20 rules with finding codes, fix hints and Apple documentation links | No autofix, no SwiftLint/SwiftFormat bridge |
| Accessibility audit | **Implemented** | WCAG contrast maths in both appearances, Dynamic Type, 44pt targets, VoiceOver labels | VoiceOver order/rotor traversal needs a device |
| Liquid Glass audit | **Implemented** | Verified iOS 26 API table, availability-guard detection, imitation detection | visionOS glass APIs are allowlisted, not compiled |
| SF Symbols | **Implemented** | 9,649 symbols from `CoreGlyphs.bundle`, per-OS availability, typo suggestions | — |
| Privacy manifest audit | **Implemented** | Required-Reason categories, valid reason codes, tracking domains, collected data | Third-party SDK manifests are not scanned |
| Localisation audit | **Implemented** | `Text(verbatim:)`, UIKit strings, RTL layout, String Catalog completeness | Format-specifier validation is shallow |
| Widgets and Live Activities | **Implemented** | Dynamic Island regions, Info.plist flag, families, providers, App Groups | — |
| Metadata validation | **Implemented** | Character limits, URL rules, keyword duplicates, screenshot counts | Does not suggest copy (see ASO) |
| Icon validation | **Implemented** | 1024×1024, PNG, alpha, asset catalogue consistency | — |
| Icon generation | **Implemented** | `icon-studio prepare`: one 1024 master → 18 slots + Contents.json, pure-Python PNG codec and box-filter downscale | No generative artwork; the master is the designer's |
| Screenshot capture | **Partial** | `xcrun simctl` capture + App Store slot validation | No multi-locale batch orchestration |
| Screenshot composition | **Implemented (SVG v1)** | Exact-size marketing frames around real captures: background, headline, subheadline, embedded screenshot, three themes, optional rasterisation when a renderer exists | No device-frame artwork, no automatic localisation of headlines |
| Release gate | **Implemented** | Seven weighted gates, `NOT INSPECTED` blocks, score, Markdown report | — |
| App Store Connect | **Partial (read-only)** | ES256 JWT, `apps`, `appStoreVersions`, `builds`, rate limiting, hard failure without credentials | No writes, no submission, no screenshot upload |
| App Store Review analysis | **Implemented (v1)** | `app-store-review`: usage descriptions vs sensor use (5.1.1), placeholder copy (2.1), account deletion (5.1.1(v)), external payments (3.1.1), web wrapper (4.2), private API (2.5.1), metadata URLs (2.3.1) — each finding cites the section and the evidence | Not a full guideline crawl; entitlement and IAP receipt flows are out of scope |
| Apple documentation research | **Implemented (v1)** | Live retrieval from developer.apple.com's JSON API: symbol search across framework indexes, page rendering as Markdown, per-platform availability, HIG pages — each with source URL and fetch timestamp, cached, and refusing non-Apple hosts | No PDF parsing, no WWDC transcript search, no offline mirror of the whole site |
| ASO | **Implemented (honest v1)** | Budget arithmetic, duplicate/wasted keywords, coverage against visible copy, risky-claim detection, candidates extracted from the developer's own description | No search-volume or competitor data — and it says so instead of inventing numbers |


| Capability modules | **Implemented** | Nine modules, `APPLE_NATIVE_MODULES`, isolation tests | No lazy dependency installation (there are no optional deps to install) |
| MCP transports | **Implemented** | stdio and Streamable HTTP (`--http`), loopback-only default, Origin check | No auth for remote use (deliberately refused) |
| Privacy controls | **Implemented** | Telemetry off by default, closed five-key schema, sanitiser tests, no source uploads | Session-level consent prompts are a client concern |
| Native macOS app | **Parked** | Working build on branch `wip/app-studio` (findings UI, gate, assistant) | Not in `main`; tool calling and streaming not built |

---

## Phases

### Phase 1 — Foundations (done)

Repository audit, verified knowledge base, 14 CLI auditors, 16 MCP tools, shared report contract, CI that runs
everything, capability modules.

### Phase 2 — Apple documentation research (v1 shipped)

`tools/apple-docs-research/` reads the JSON API that developer.apple.com itself uses:

- **allowlist** — only `developer.apple.com`, everything else is refused before a socket opens,
- **search** — 8,000+ symbols per framework index, ranked exact → prefix → substring,
- **read** — page rendered as Markdown: declaration, overview, code listings, parameters,
- **availability** — the per-platform table Apple publishes (the answer to "does this exist on iOS 17? 26?"),
- **HIG** — Human Interface Guidelines pages as Markdown,
- **provenance** — every result carries `source_url` and `fetched_at`; cached for 7 days, `--refresh` to bypass,
  `--offline` to refuse the network,
- **failure** — a missing page is an error, never a plausible guess.

Next in this phase: PDF and WWDC transcript retrieval, an offline mirror for air-gapped machines.

### Phase 3 — App Store lifecycle

- Guidelines engine: map each Review Guideline section to checks, evidence and severity.
- Metadata write path (preview → approve → apply → read back), gated behind an explicit module.
- ASO assistant: keyword extraction, character budgets, localisation variants — recommendations only, never
  invented claims.

### Phase 4 — Visual production

- Icon studio: original artwork directions, then the existing validator as the gate.
- Screenshot studio: capture, then composition onto device frames with localisation-aware text.
- Both must distinguish *actual screenshots* from *marketing compositions* in the output, always.

### Phase 5 — The app

The parked macOS app becomes the surface for phases 2–4: findings, gate, documentation research and the assistant in
one window, with tool calling wired to the same registry the server uses.

---

## How to read this document

If a capability is listed as implemented and you cannot find the tool or the test, that is a bug in this document —
open an issue. The project's whole premise is that "it works" is a claim requiring evidence.
