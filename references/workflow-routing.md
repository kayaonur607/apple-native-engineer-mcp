# Apple developer and designer workflows

This guide routes intent to the server's existing capabilities. Discover the current tool inventory: modules may be disabled.

| User goal | First action | Evidence to collect |
| --- | --- | --- |
| Understand an existing app | `inspect_apple_project`, then `audit_project` | Targets, deployment floors, attributed finding codes |
| Design a native screen | `find_apple_guidelines`, read design references | HIG source URLs, screen states, semantic type/colour decisions |
| Implement or fix SwiftUI | Inspect project, research API availability | Actual build result, `review_diff`, runtime observations where available |
| Choose SF Symbols | `validate_sf_symbols` | Symbol existence and platform availability |
| Create a design system | `forge_design_tokens` | Generated SwiftUI and asset files; validate the resulting app |
| Prepare App Store assets | Icon tools, screenshot composition | Validated dimensions; label compositions and preserve real captures |
| Review store listing | Metadata, ASO and App Store review tools | Character budgets and findings; no invented market data |
| Prepare a release | `generate_release_report` | Gate verdict, uninspected items, separate runtime checklist |
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
