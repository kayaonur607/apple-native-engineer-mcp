# Community Resources & Open-Source Research

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

This index lists the community work studied while building this skill. It is deliberately short. Inclusion requires three things: a license file that permits reuse, activity within the last year, and something specific this repository learned from it.

**Verification method.** License identifiers below are read from the repository's `LICENSE` file via the GitHub API (`license.spdx_id`), not from a README badge. Last-push dates are from the same call, checked 5 November 2026. A repository with no license file is **not** MIT by assumption — under copyright law it is all rights reserved, so it is not listed.

---

## 1. How a project gets on this list

| Test | Why it matters |
| :--- | :--- |
| A `LICENSE` file, not a README badge | Without a license the work is all rights reserved, whatever the badge says |
| Activity within the last year | A dead dependency is a migration you inherit |
| Something specific learned | "Popular" is not a contribution |
| No vendored Apple headers, fonts or assets | Those are Apple's, and redistributing them is not a licence question |
| Readable source, not just a demo | Ideas transfer; unreadable code does not |
| Tagged releases | Branch-only projects make version pinning impossible |

Re-verifying the table takes one loop — this is how the license and date columns were produced:

```bash
for repo in pointfreeco/swift-composable-architecture realm/SwiftLint; do
  curl -sL "https://api.github.com/repos/$repo" | python3 -c 'import json,sys
d = json.load(sys.stdin)
print(d["full_name"], (d.get("license") or {}).get("spdx_id"), d["pushed_at"])'
done
```

Before a project becomes a dependency rather than an influence, ask five questions: does it pin to a Swift version you support; does it build with strict concurrency checks on; does it have tests you can run; what does its binary size cost; and what is the exit plan if it is abandoned next quarter. A project that fails the last question is a prototype dependency.

---

## 2. Design and motion research

| Repository | License | Last push | What it contributed |
| :--- | :--- | :--- | :--- |
| [emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | 2026-11 | Design-engineering vocabulary: why `scale(0)` pops, spring vs. curve on interruption, an animation review checklist. Translated to SwiftUI springs and `PhaseAnimator`. |
| [0kzh/glisse](https://github.com/0kzh/glisse) | MIT | 2026-10 | Optical parameters for glass: refraction, specular rim, sheen. Informed the numbers discussed in [liquid-glass.md](liquid-glass.md) — the shipping API is still `.glassEffect(_:in:)`. |
| [raintree-technology/hig-doctor](https://github.com/raintree-technology/hig-doctor) | MIT | 2026-11 | Modular HIG decomposition (foundations, platforms, components, inputs) sized for agent context. Formerly published as `apple-hig-skills`. |
| [ebuntario/apple-hig](https://github.com/ebuntario/apple-hig) | MIT | 2026-04 | An alternative structuring of HIG summaries for prompt injection; useful as a cross-check on what a component page must contain. |

None of these are dependencies. They are inputs to prose, and where their claims disagreed with the SDK, the SDK won.

---

## 3. SwiftUI architecture and code quality

| Repository | License | Last push | What it contributed |
| :--- | :--- | :--- | :--- |
| [pointfreeco/swift-composable-architecture](https://github.com/pointfreeco/swift-composable-architecture) | MIT | 2026-11 | Rigorous state modelling, navigation as data, exhaustive effect testing. Studied to keep this repository architecturally neutral rather than TCA-shaped. |
| [nalexn/clean-architecture-swiftui](https://github.com/nalexn/clean-architecture-swiftui) | MIT | 2025-07 | A worked dependency-injection and repository example. Reference reading, not a dependency — it has not been updated recently. |
| [realm/SwiftLint](https://github.com/realm/SwiftLint) | MIT | 2026-11 | The rule set behind the line-length, naming and complexity limits used in the examples here. |
| [SimplyDanny/SwiftLintPlugins](https://github.com/SimplyDanny/SwiftLintPlugins) | MIT | 2026-08 | Swift Package build-tool plugins for SwiftLint, so linting runs without a run-script phase. |

The licensing correction worth recording: TCA was Apache-2.0 for years and is now **MIT**. A licensing table copied from memory is wrong within a year — re-read the file.

---

## 4. Testing and tooling

| Repository | License | Last push | What it contributed |
| :--- | :--- | :--- | :--- |
| [swiftlang/swift-testing](https://github.com/swiftlang/swift-testing) | Apache-2.0 | 2026-11 | `@Test`, `#expect`, `#require`, traits, parameterised cases. The default for new tests in this repository. |
| [pointfreeco/swift-snapshot-testing](https://github.com/pointfreeco/swift-snapshot-testing) | MIT | 2026-10 | Snapshot strategy for view regression, including the trap of recording on the wrong device size. |
| [swiftlang/swift-format](https://github.com/swiftlang/swift-format) | Apache-2.0 | 2026-11 | Formatting rules that keep snippets in this repository copy-pasteable. |
| [apple/swift-openapi-generator](https://github.com/apple/swift-openapi-generator) | Apache-2.0 | 2026-11 | Typed clients from an OpenAPI document, as an alternative to hand-written `Codable` DTOs. |
| [apple/swift-argument-parser](https://github.com/apple/swift-argument-parser) | Apache-2.0 | 2026-10 | The command-line pattern used by the Swift tools shipped alongside the Python auditors. |
| [apple/swift-collections](https://github.com/apple/swift-collections) | Apache-2.0 | 2026-11 | `Deque`, `OrderedDictionary` — the right answer when an array's `removeFirst()` is the bottleneck. |
| [pointfreeco/swift-dependencies](https://github.com/pointfreeco/swift-dependencies) | MIT | 2026-10 | Dependency injection as an explicit, test-overridable value instead of a singleton; informed the DI discussion in [architecture-and-clean-code.md](architecture-and-clean-code.md). |
| [apple/swift-log](https://github.com/apple/swift-log) | Apache-2.0 | 2026-11 | The `Logger` façade used in the logging examples, so a backend can be swapped without touching call sites. |
| [Alamofire/Alamofire](https://github.com/Alamofire/Alamofire) | MIT | 2026-11 | Request retry, adaptation and pinned-session patterns; used as a comparison point in [offline-caching-networking.md](offline-caching-networking.md), not as a recommendation to add a dependency. |
| [onevcat/Kingfisher](https://github.com/onevcat/Kingfisher) | MIT | 2026-11 | The reference for image cache layering (memory → disk → network) before rolling your own. |
| [kean/Pulse](https://github.com/kean/Pulse) | MIT | 2026-10 | On-device network logging that survives release builds; useful when a bug only reproduces on a tester's device. |

---

## 5. Standards and packaging

| Resource | License | Last push | What it contributed |
| :--- | :--- | :--- | :--- |
| [agentskills.io](https://agentskills.io/) | Open specification | — | `SKILL.md` frontmatter contract: `name`, `description`, character limits, metadata map. |
| [vercel-labs/skills](https://github.com/vercel-labs/skills) | MIT | 2026-11 | Repository layout that lets `npx skills add` discover the skill without a manifest. |

---

## 6. Removed from a previous revision

Recorded here because a deleted row is evidence, not an omission:

| Repository | Why removed |
| :--- | :--- |
| `ykswang/apple-hig-skill` | No `LICENSE` file. Without a license the content is all rights reserved, so it cannot be described as MIT or reused. |
| `tzzs/apple-design-skill` | GitHub reports `NOASSERTION` — a custom or unclear license. Not safe to attribute as MIT. |
| `raintree-technology/apple-hig-skills` | Renamed; the canonical URL now redirects to `raintree-technology/hig-doctor`, which is listed above. |

If you maintain one of these and add a license, open an issue and the row comes back with the real identifier.

---

## 7. Synthesis and intellectual property

All instructions, checklists, Swift examples and design tokens in this repository are original work written for this skill. The projects above informed the ideas; no code and no proprietary text is copied verbatim.

Where a community source and Apple's documentation disagree, the Apple documentation and the installed SDK win, and the disagreement is worth reporting upstream. A well-maintained project treats that as a bug report, not an insult.

---

## 8. How this list is maintained

- Reviewed before each release, in the same pass as `python3 scripts/check_api_claims.py`.
- Removed when a repository is archived, changes license, goes twelve months without a push, or makes a claim the SDK contradicts.
- Added only after the work was actually used and its license was read.
- "Last push" is GitHub's `pushed_at` value, not a release date — a project can be active for a year without tagging a version.
- No stars, no rankings. Popularity is not evidence, and a table sorted by stars ages worse than one sorted by usefulness.
