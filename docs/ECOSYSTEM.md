# Optional ecosystem integrations

Research reviewed 2026-11-06. These are complementary upstream projects, not bundled dependencies or implemented adapters.
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

## Architecture boundary

The MCP server continues to wrap the existing Python auditors. Shared envelopes carry stable finding codes.
Generated files have explicit writable annotations. Local audits remain independent of ASC authentication and network
research. Build/test/device evidence remains distinct from static findings; missing evidence must be stated explicitly.

Future adapters should accept structured artifacts rather than arbitrary shell command strings, declare write/network
capabilities, reject empty evidence, retain provenance and have cancellation/time/output limits. Account writes require
an explicit preview and approval workflow before they can be implemented.
