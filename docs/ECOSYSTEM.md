# Optional ecosystem integrations

Research reviewed 2026-11-07. These are complementary upstream projects, not bundled dependencies or implemented adapters.
This revision adds a local xcresult summary utility; it does not install or invoke any of these projects.

| Upstream source | Useful boundary | Integration decision |
| --- | --- | --- |
| [MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP) | Xcode build/test and simulator operations | Run separately; preserve the command, commit, destination, exit status and result bundle. Read the bundle with this repository's optional evidence CLI. |
| [Mobile MCP](https://github.com/mobile-next/mobile-mcp) | Device/simulator interaction and screen evidence | Keep separate from read-only source audits. Record expected/actual journey steps and real screenshots. Device accessibility trees alone do not prove VoiceOver usability. |
| [Swift Concurrency](https://github.com/AvdLee/Swift-Concurrency-Agent-Skill) | Actor isolation, Sendable, cancellation and migration review | Load only for concurrency work; verify advice with the actual language mode, compiler and build settings. |
| [SwiftUI Expert](https://github.com/AvdLee/SwiftUI-Agent-Skill) / [SwiftUI Pro](https://github.com/twostraws/SwiftUI-Agent-Skill) | State ownership, identity, composition, navigation and performance | Use expert review for judgment; do not make style preferences automatic release blockers. |
| [Swift Testing](https://github.com/AvdLee/Swift-Testing-Agent-Skill) | Async testing, test architecture and XCTest migration | Choose behavioral tests for the change and inspect executed test counts. |
| [Sosumi](https://github.com/NSHipster/sosumi.ai) | Apple documentation and WWDC research | Optional separate research source; keep provenance and date, and reconcile historical talks with current availability. No WWDC fetch adapter exists here yet. |

No upstream implementation or skill text was copied for this work. Before vendoring anything, pin an upstream commit,
inspect its license and retain required notices. External MCPs have their own network, execution and privacy policies;
enabling a local module here does not configure or authorize them.

## Agent skills that pair well (reviewed 2026-11-07)

These skill collections were used as **research input** for v2.4 — to check which jobs developers actually ask
agents to do and where this server's evidence was missing. No skill text or code was copied; every fact in the
new tools and references was re-derived from Apple's own pages (`find_apple_guidelines`, App Store Connect help)
or from the installed Xcode 27.2 tools (`xcodebuild -help`, `simctl`, `altool`, `notarytool`).

| Upstream | What it is good at | How it complements this server |
| --- | --- | --- |
| [swift-ios-skills](https://github.com/dpearson2699/swift-ios-skills) | Framework-by-framework guidance (WidgetKit, StoreKit, ActivityKit, AlarmKit, …) and SwiftUI Liquid Glass | Load the framework skill for implementation detail; verify every API with `inspect_apple_api_availability` |
| [apple-design-skill](https://github.com/dickwu/apple-design-skill) | Design review grounded in HIG pages | Use for critique; cite the live page from `find_apple_guidelines` and capture the result |
| [ios-marketing-capture](https://github.com/ParthJadhav/ios-marketing-capture) | Marketing screenshot pages built in a web stack | This server stays native: Simulator captures, CoreGraphics/San Francisco rendering, Apple's slot table |
| [SwiftUI Expert](https://github.com/AvdLee/SwiftUI-Agent-Skill) | State, identity, performance judgment | Pair with `review_diff`; style advice is not a release blocker |

Lessons adopted from this review: capture must be **localized and per-device in one plan**; Simulator PNGs must
be **flattened** (they carry alpha); screenshot copy needs **per-locale fallbacks reported**, not silently reused;
distribution guidance must name **exact ExportOptions keys** from the installed Xcode; and HIG pages must be
**discoverable by topic** before they can be cited.

## Cross-platform servers and skills (reviewed on GitHub, 2026-11-07)

| Upstream | Stars / license at review | How it complements this server |
| --- | --- | --- |
| [Dart and Flutter MCP server](https://docs.flutter.dev/ai/mcp-server) ([dart-lang/ai](https://github.com/dart-lang/ai)) | 294 · BSD-3 | Dart analysis, pub.dev, tests and runtime errors; this server adds HIG, the iOS host, captures and release |
| [flutter/agent-plugins](https://github.com/flutter/agent-plugins) | 3,161 · BSD-3 | Official Flutter skills (localization setup, responsive layout, routing, tests) |
| [Expo MCP server](https://docs.expo.dev/mcp/) and [expo/skills](https://github.com/expo/skills) | 4,080 · MIT | Expo docs, compatible installs, EAS; `expo-ui`/`expo-native-ui` informed the `RNA020` and `EXP*` rules |
| [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | 1,701 · MIT | React Native performance, upgrades, React Navigation, tvOS |
| [margelo/react-native-skills](https://github.com/margelo/react-native-skills) | 179 | Nitro/Swift native modules, VisionCamera |
| [FormidableLabs/eslint-plugin-react-native-a11y](https://github.com/FormidableLabs/eslint-plugin-react-native-a11y) | 307 · MIT | Exhaustive RN accessibility lint for CI; `audit_cross_platform` covers the Apple-specific subset |

Facts used by the new rules were taken from the frameworks' own documentation (Flutter platform adaptations and
internationalization, React Native SafeAreaView and accessibility, Expo app config) and from runs on this machine
(Flutter 3.44.8, Xcode 27.2). No upstream code or skill text was copied.

## Architecture boundary

The MCP server continues to wrap the existing Python auditors. Shared envelopes carry stable finding codes.
Generated files have explicit writable annotations. Local audits remain independent of ASC authentication and network
research. Build/test/device evidence remains distinct from static findings; missing evidence must be stated explicitly.

Future adapters should accept structured artifacts rather than arbitrary shell command strings, declare write/network
capabilities, reject empty evidence, retain provenance and have cancellation/time/output limits. Account writes require
an explicit preview and approval workflow before they can be implemented.
