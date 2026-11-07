# Apple developer and designer workflows

This guide routes intent to the server's existing capabilities. Discover the current tool inventory: modules may be disabled.

| User goal | First action | Evidence to collect |
| --- | --- | --- |
| Build a new app from an idea | `/apple-native-start`, then `inspect_apple_project` once a project exists | Platforms, deployment floor, first runnable slice, build result |
| Cross-platform app (Flutter, React Native, Expo, Capacitor, MAUI, KMP) | `audit_cross_platform`, then `/apple-native-flutter`, `-react-native` or `-cross-platform` | Framework, iOS host, `FLT`/`RNA`/`EXP`/`XPL` findings, Simulator captures |
| Understand an existing app | `inspect_apple_project`, then `audit_project` | Targets, deployment floors, attributed finding codes |
| Design a native screen | `/apple-native-new-screen`; `search_apple_guidelines` → `find_apple_guidelines` | HIG source URLs, screen states, semantic type/colour decisions |
| Platform-specific work | `/apple-native-ios`, `-ipados`, `-macos`, `-watchos`, `-tvos`, `-visionos`, `-iphone-duo` | Platform reference, verified API availability, captures on that platform |
| Implement or fix SwiftUI | Inspect project, research API availability | Actual build result, `review_diff`, runtime observations where available |
| Choose SF Symbols | `validate_sf_symbols` | Symbol existence and platform availability |
| Create a design system | `forge_design_tokens` | Generated SwiftUI and asset files; validate the resulting app |
| App icon | `get_app_store_specs`, `prepare_icon_assets`, `verify_icon_set` | Per-platform icon canvas, generated slots, verification |
| App Store screenshots | `/apple-native-screenshots`: `capture_screenshots` → `audit_screenshots` → `compose_marketing_screenshots` | Real captures with manifest, opaque PNGs at slot sizes, per-locale coverage |
| Review store listing | Metadata, ASO and App Store review tools | Character budgets and findings; no invented market data |
| Prepare a release | `generate_release_report` | Gate verdict, uninspected items, separate runtime checklist |
| Ship a build | `/apple-native-distribute`: `plan_distribution` | Preflight findings, ExportOptions, approved commands and their results |
| Diagnose setup | `check_environment` | Missing runtimes, Xcode and credentials; never print secret values |

## Evidence hierarchy

1. Apple documentation: declaration, platform availability, URL and fetched timestamp.
2. Static analysis: tool, input, finding code, severity and file/line. Heuristics can have false positives.
3. Compilation and tests: exact command, SDK, result and log. Do not infer a build from a lint pass.
4. Runtime and visual review: actual device/simulator, OS, appearance, locale and accessibility settings.
5. Commercial evidence: measured customer outcomes with consent. Fixture checks cannot establish revenue or time saved.

Apple's primary design reference is [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/). Retrieve task-specific pages through the documentation tools rather than treating a bundled guide as live documentation.

## Integration boundaries

Local stdio is the default for customer source code. Python auditors execute on the MCP server's filesystem: an HTTP endpoint does not gain access to a user's laptop project by receiving its local path. A hosted product needs an explicit workspace ingestion and isolation design.

External Figma, simulator, image and source-control tools belong to their respective clients/providers. Use them when present; their subscriptions and permissions are separate. Apple Native Engineer is independent and is not affiliated with Apple.
