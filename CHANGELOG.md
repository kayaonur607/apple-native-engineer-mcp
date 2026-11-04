# Changelog

All notable changes to the `apple-native-engineer` skill are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.0.0] - 2026-11-04

### Added
- **Canonical Skill Definition (`SKILL.md`)**: Full compliance with the [Agent Skills open standard](https://agentskills.io/).
- **Foundational Architecture**:
  - 5-tier Hierarchy of Authority (`references/design-principles.md`).
  - Core Apple Human Interface Guidelines synthesis (`references/apple-hig-foundations.md`).
  - Typography and Semantic Color token systems (`references/typography-and-color.md`).
  - Native materials, translucency, and Liquid Glass (`references/liquid-glass.md`).
- **Platform Idioms & Ergonomics**:
  - iPhone handheld ergonomics, thumb zone mapping, and safe areas (`references/iphone-design.md`).
  - iPadOS multi-column `NavigationSplitView`, Stage Manager, hover effects, and keyboard shortcuts (`references/ipad-design.md`).
  - macOS unified toolbars, window styles, and settings scenes (`references/macos-design.md`).
- **Engineering & Polish**:
  - Accessibility standards, VoiceOver semantics, and Dynamic Type scaling (`references/accessibility.md`).
  - Modern SwiftUI architecture: `@Observable`, Swift 6 Concurrency, and Swift Testing (`references/swiftui-engineering.md`).
  - Emil Kowalski design engineering motion principles adapted to SwiftUI springs (`references/animation-principles.md`).
  - Modular project design token system (`references/design-systems.md`).
  - Visual verification and simulator testing protocols (`references/visual-quality.md`).
- **Audit & Review Checklists**:
  - Systematic Apple HIG compliance audit template with severity grading (`checklists/apple-hig-audit.md`).
  - Specialized checklists for iPhone, iPadOS, Accessibility, Visual Design, and Pre-Release.
- **Production Examples**:
  - NavigationStack and NavigationSplitView architectures (`examples/navigation-examples.md`).
  - Adaptive layout with `ViewThatFits` and size classes (`examples/adaptive-layout-examples.md`).
  - Native forms, pickers, search experiences, and detented sheets (`examples/native-components.md`).
  - Emil Kowalski micro-interactions, haptic feedback, and fluid transitions (`examples/animation-examples.md`).
  - Drop-in production design tokens package (`examples/design-system-example.md`).
- **Cross-Agent Integrations**:
  - Integration guides and configurations for Claude Code, OpenAI Codex, Cursor, GitHub Copilot, Gemini CLI, OpenCode, and Vercel Skills CLI (`npx skills`).
- **Tooling & CI**:
  - Automated validation script (`scripts/validate-skill.sh`).
  - Link integrity verification (`scripts/check-references.sh`).
  - Cross-agent installer (`scripts/install-skill.sh`).
  - GitHub Actions automated validation workflow (`.github/workflows/validate.yml`).
