# Community Resources & Open-Source Research

This document cites and evaluates the high-quality open-source repositories, design engineering frameworks, and community research studied during the development of this skill.

---

## 1. Studied Open-Source Repositories

### A. Apple HIG & Design Agent Skills

| Repository | Author / Org | URL | License | Influence on This Skill |
| :--- | :--- | :--- | :--- | :--- |
| **apple-hig-skills** | Raintree Technology | [github.com/raintree-technology/apple-hig-skills](https://github.com/raintree-technology/apple-hig-skills) | MIT | Validated modular decomposition of HIG across platforms, inputs, and components for agent prompt efficiency. |
| **apple-hig-skill** | ykswang | [github.com/ykswang/apple-hig-skill](https://github.com/ykswang/apple-hig-skill) | MIT | Provided patterns for cross-platform UI review and auditing workflows for Flutter/React Native ports. |
| **apple-design-skill** | tzzs | [github.com/tzzs/apple-design-skill](https://github.com/tzzs/apple-design-skill) | MIT | Explored encoding Apple aesthetic tokens, glass materials, and typography into structured agent rules. |
| **apple-hig** | ebuntario | [github.com/ebuntario/apple-hig](https://github.com/ebuntario/apple-hig) | MIT | Evaluated approaches to structuring Apple HIG summaries for prompt injection. |

### B. Design Engineering & Animation

| Project | Organization / Author | Source URL | License | What Was Learned & Influence |
| :--- | :--- | :--- | :--- | :--- |
| **emilkowalski/skills** | Emil Kowalski | [github.com/emilkowalski/skills](https://github.com/emilkowalski/skills) | MIT | Masterclass design engineering principles: avoiding `scale(0)` pops, physics-based springs, animation review filters, interruptibility, and micro-haptic pairing. Translated from web/Expo to pure SwiftUI. |
| **glisse** | 0kzh | [github.com/0kzh/glisse](https://github.com/0kzh/glisse) | MIT | Optical parameters and light reflection simulation for Liquid Glass interfaces (refraction, specular rim lighting, customizable sheen). Translated into native SwiftUI Metal-backed shaders and modifiers. |

### C. SwiftUI Architecture & Code Quality

| Repository | Author / Org | URL | License | Influence on This Skill |
| :--- | :--- | :--- | :--- | :--- |
| **clean-architecture-swiftui** | Alexey Naumov | [github.com/nalexn/clean-architecture-swiftui](https://github.com/nalexn/clean-architecture-swiftui) | MIT | Informed approaches to dependency injection, testable application state, and repository patterns in SwiftUI. |
| **swift-composable-architecture (TCA)** | Point-Free (Brandon Williams, Stephen Celis) | [github.com/pointfreeco/swift-composable-architecture](https://github.com/pointfreeco/swift-composable-architecture) | Apache 2.0 | Studied for state management rigor, navigation tree modeling, and side-effect testing; informed architectural neutrality guidelines. |
| **SwiftLint** | Realm | [github.com/realm/SwiftLint](https://github.com/realm/SwiftLint) | MIT | Informs code quality rules, identifier naming, line limits, and formatting consistency across Swift code examples. |

### D. Standards & Package Management

| Resource | Author / Org | URL | License | Influence on This Skill |
| :--- | :--- | :--- | :--- | :--- |
| **Agent Skills Standard** | Agent Skills Org | [agentskills.io](https://agentskills.io/) | Open Standard | Established canonical `SKILL.md` frontmatter rules (`name`, `description`, character limits, metadata map). |
| **Vercel Skills CLI** | Vercel Labs | [github.com/vercel-labs/skills](https://github.com/vercel-labs/skills) | Apache 2.0 | Formatted repository layout for seamless discovery via `npx skills add`. |

---

## 2. Synthesis & Intellectual Property Notice

All instructions, checklists, SwiftUI examples, and design tokens contained in this project are original works authored specifically for this skill. While informed and inspired by the open-source research listed above, no code or proprietary text has been copied verbatim. 

This repository respects all original authors and their respective MIT and Apache 2.0 licenses.
