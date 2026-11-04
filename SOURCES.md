# Research Strategy & Source Attribution (SOURCES)

This document provides a comprehensive record of the research, official documentation, and open-source projects that ground the standards, architectures, and review protocols of `apple-native-engineer`.

---

## 1. Research Strategy & Philosophy

`apple-native-engineer` was built by conducting rigorous, multi-layered research across two primary domains:

1. **Official Apple Platform Authority**: Apple's official documentation, WWDC engineering sessions, Human Interface Guidelines, and App Store Review Guidelines represent the supreme authority.
2. **Elite Open-Source & Community Research**: Evaluated top-tier Swift, SwiftUI, and design engineering projects to identify industry best practices, battle-tested architectural patterns, and tactile interaction design.

### Non-Duplication & Synthesis Principle
This project does not copy third-party repositories, scrape proprietary materials, or enforce arbitrary personal taste. Instead, it synthesizes proven ideas into an **original, unified Apple development standard** that balances design refinement, architectural rigor, user privacy, and App Store compliance.

---

## 2. Primary Authority: Official Apple Documentation

All platform requirements and recommendations in this repository are verified against official Apple documentation:

| Document / Portal | URL | Authority Scope | Date Verified |
| :--- | :--- | :--- | :--- |
| **Apple Human Interface Guidelines (HIG)** | [developer.apple.com/design/human-interface-guidelines](https://developer.apple.com/design/human-interface-guidelines/) | UI foundations, typography, materials, layouts, components, inputs, and cross-platform idioms (iOS, iPadOS, macOS, visionOS, watchOS). | November 2026 |
| **App Store Review Guidelines** | [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) | Mandatory compliance rules covering Safety (Section 1), Performance (Section 2), Business (Section 3), Design (Section 4), and Legal/Privacy (Section 5). | November 2026 |
| **SwiftUI Documentation** | [developer.apple.com/documentation/swiftui](https://developer.apple.com/documentation/swiftui/) | Declarative views, layouts, observation, gestures, and animations. | November 2026 |
| **Swift Concurrency & Language Guide** | [swift.org/documentation](https://www.swift.org/documentation/) | Structured concurrency (`async`/`await`), actors (`@MainActor`), Sendable checks, and the `@Observable` macro mechanics. | November 2026 |
| **Apple Developer Privacy Documentation** | [developer.apple.com/app-store/app-privacy-details](https://developer.apple.com/app-store/app-privacy-details/) | Privacy Nutrition Labels, `PrivacyInfo.xcprivacy` manifests, Required-Reason APIs, and App Tracking Transparency (ATT). | November 2026 |
| **SF Symbols Specification** | [developer.apple.com/sf-symbols](https://developer.apple.com/sf-symbols/) | System iconography, variable color, symbol effects (bounce, pulse, replace, breathe), and optical alignment. | November 2026 |
| **Apple Accessibility Guidelines** | [developer.apple.com/accessibility](https://developer.apple.com/accessibility/) | VoiceOver semantics, Dynamic Type scales (AX1–AX5), Switch Control, and AssistiveTouch support. | November 2026 |
| **Apple Design Resources** | [developer.apple.com/design/resources](https://developer.apple.com/design/resources/) | Official design kits, typography specifications, and hardware bezel templates. | November 2026 |

---

## 3. Key WWDC Sessions Referenced

The standards in this skill directly integrate design and engineering insights from landmark Apple Worldwide Developers Conferences:

- **WWDC24**:
  - *Explore the new Tab View on iPadOS and iOS 18* (Floating tab bars and dynamic sidebar morphing)
  - *Create custom visual effects with SwiftUI shaders and materials* (Translucent glass and specular reflections)
  - *Migrate your app to Swift 6 strict concurrency* (Eliminating data races and ensuring `@MainActor` safety)
  - *Meet Swift Testing* (Modern `@Test` and `#expect` macros replacing legacy XCTest)
- **WWDC23**:
  - *Discover Observation in SwiftUI* (`@Observable` macro mechanics and property-level invalidation tracking)
  - *Animate with springs* (Standardizing physics spring presets: `.snappy`, `.bouncy`, `.smooth`)
  - *Get started with privacy manifests* (`PrivacyInfo.xcprivacy` and required-reason API declarations)
  - *Design with spatial UI components* (Translucent materials, depth, and elevation)
- **WWDC22**:
  - *The SwiftUI cookbook for navigation* (Type-safe `NavigationStack` and `NavigationSplitView`)
  - *Compose custom layouts with SwiftUI* (`Layout` protocol and `ViewThatFits` adaptive scaling)
- **WWDC21**:
  - *Demystify SwiftUI view evaluation and performance* (View identity, dependency tracking, body evaluation)
  - *Craft search experiences in SwiftUI* (`.searchable`, `.searchSuggestions`, and search scopes)

---

## 4. Community Open-Source Research

The following open-source projects were evaluated for their design engineering, architectural patterns, and quality standards:

### A. Apple HIG & Design Agent Skills

| Project | Organization / Author | Source URL | License | What Was Learned & Influence |
| :--- | :--- | :--- | :--- | :--- |
| **apple-hig-skills** | Raintree Technology | [github.com/raintree-technology/apple-hig-skills](https://github.com/raintree-technology/apple-hig-skills) | MIT | Validated modular decomposition of HIG across platforms, inputs, and components for agent prompt efficiency. |
| **apple-hig-skill** | ykswang | [github.com/ykswang/apple-hig-skill](https://github.com/ykswang/apple-hig-skill) | MIT | Provided patterns for cross-platform UI review and auditing workflows for Flutter/React Native ports. |
| **apple-design-skill** | tzzs | [github.com/tzzs/apple-design-skill](https://github.com/tzzs/apple-design-skill) | MIT | Explored encoding Apple aesthetic tokens, glass materials, and typography into structured agent rules. |
| **apple-hig** | ebuntario | [github.com/ebuntario/apple-hig](https://github.com/ebuntario/apple-hig) | MIT | Evaluated approaches to structuring Apple HIG summaries for prompt injection. |

### B. Design Engineering & Animation

| Project | Organization / Author | Source URL | License | What Was Learned & Influence |
| :--- | :--- | :--- | :--- | :--- |
| **skills** | Emil Kowalski | [github.com/emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | Masterclass in micro-interaction design: avoiding `scale(0)` pops, physics-based springs over linear easing, interruptibility, and tactile haptic pairing. Adapted directly into native SwiftUI. |
| **glisse** | 0kzh | [github.com/0kzh/glisse](https://github.com/0kzh/glisse) | MIT | Optical parameters, refraction, specular rim lighting, and sheen simulation for Liquid Glass interfaces. Adapted into hardware-accelerated native SwiftUI modifiers. |

### C. Architecture, Quality & Tooling

| Project | Organization / Author | Source URL | License | What Was Learned & Influence |
| :--- | :--- | :--- | :--- | :--- |
| **clean-architecture-swiftui** | Alexey Naumov | [github.com/nalexn/clean-architecture-swiftui](https://github.com/nalexn/clean-architecture-swiftui) | MIT | Informs clean separation of concerns, dependency injection, and testable application state without third-party frameworks. |
| **swift-composable-architecture (TCA)** | Point-Free | [github.com/pointfreeco/swift-composable-architecture](https://github.com/pointfreeco/swift-composable-architecture) | Apache 2.0 | Studied for state management rigor, navigation tree modeling, and side-effect testing; informed architectural neutrality guidelines. |
| **SwiftLint** | Realm | [github.com/realm/SwiftLint](https://github.com/realm/SwiftLint) | MIT | Informs code quality rules, identifier naming, line limits, and formatting consistency across Swift code examples. |
| **skills (CLI)** | Vercel Labs | [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills) | Apache 2.0 | Formatted repository layout for seamless discovery via `npx skills add`. |
| **Agent Skills Standard** | Agent Skills Org | [agentskills.io](https://agentskills.io/) | Open Standard | Canonical `SKILL.md` frontmatter rules, field length constraints, and discovery specs. |

---

## 5. Authority Separation Matrix

To ensure users and AI agents always understand the weight of any guidance, recommendations are classified into five distinct authority tiers:

| Authority Tier | Origin & Source | Enforcement Level | Example |
| :--- | :--- | :--- | :--- |
| **Level 1: Official Apple Requirement** | App Store Review Guidelines, Apple Developer contracts, privacy laws, and runtime crash constraints. | **Strictly Mandatory** (Blocks approval or crashes app) | Minimum 44×44pt touch target; Privacy Manifests; `@MainActor` UI isolation; In-app account deletion. |
| **Level 2: Official Apple Recommendation** | Apple Human Interface Guidelines and Developer Documentation. | **Strongly Recommended** (Standard platform experience) | Using `NavigationSplitView` on iPad; semantic colors (`Color(uiColor: .systemBackground)`); standard Dynamic Type text styles. |
| **Level 3: Platform Convention** | Established Apple ecosystem user expectations and platform idioms. | **Expected Convention** (Prevents "un-native web port" feel) | Interactive edge-swipe pop gesture; pull-down search in lists; bottom action sheets on iPhone vs popovers on iPad. |
| **Level 4: Community Best Practice** | Consensus among senior Apple platform engineers and architects. | **Architectural Standard** (Maintainability & testability) | `@Observable` state models; view modularization; strongly-typed design token packages; dependency injection. |
| **Level 5: Design Engineering Recommendation** | Elite craftsmanship principles (Kowalski motion, micro-delight). | **Optional Polish** (Elevates good software to great) | Subtle scale-from-0.92 transitions; `.sensoryFeedback` haptics; continuous squircle corners; `.spring(.snappy)`. |

---

## 6. Independent Developer Notice & Disclaimers

- **Independent Open-Source Work**: This research and standard was created and synthesized by an independent developer and open-source contributors. It is **not** affiliated with, sponsored by, authorized by, or endorsed by Apple Inc.
- **Nominative Trademark Usage**: *Apple, iPhone, iPad, iPadOS, macOS, watchOS, visionOS, Swift, SwiftUI, AppKit, UIKit, SF Symbols, and Dynamic Type are trademarks or registered trademarks of Apple Inc.* All trademark references are purely nominative to describe developer tool compatibility and platform design guidelines.
- **Independent Interpretation**: The 5-tiered authority taxonomy and review checklists represent an independent technical analysis intended for educational, architectural, and development assistance. No guarantee of App Store approval or regulatory compliance is expressed or implied.
