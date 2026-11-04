# Changelog

All notable changes to the `apple-native-engineer-mcp` project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-11-05

### Added
- **Model Context Protocol (MCP) Server (`integrations/mcp-server/`)**:
  - Full stdio JSON-RPC 2.0 server integration for Claude Desktop, Cursor, OpenAI Codex, and Gemini.
  - 10 exposed tools: project inspection, app icon validation, metadata validation, privacy manifest audit, release readiness generation, localization checker, widget validator, and App Store Connect operations.
- **8 Executable CLI Tools (`tools/`)**:
  - `tools/project-inspector/inspect_project.py`: Project structure, frameworks, and architecture analysis.
  - `tools/asset-validator/validate_assets.py`: Exact 1024x1024 dimensions, PNG signature, and zero alpha transparency.
  - `tools/metadata-validator/validate_metadata.py`: Character lengths, mandatory policies, and keyword checks.
  - `tools/privacy-auditor/audit_privacy.py`: Scans Required-Reason APIs and validates `PrivacyInfo.xcprivacy`.
  - `tools/localization-checker/check_localization.py`: Scans for hardcoded strings, non-RTL padding, and String Catalogs.
  - `tools/widget-validator/validate_widget.py`: Dynamic Island compact/minimal states and `NSSupportsLiveActivities` flags.
  - `tools/app-store-connect/`: Official App Store Connect REST API client with ES256 JWT auth and diagnostic mock mode.
  - `tools/release-readiness/generate_report.py`: Automated release score calculation and Markdown report generator.
- **Extended Platform References & Guides (`references/`)**:
  - `references/visionos-spatial-design.md`: 3D windows, volumes, ornaments, immersion levels, gaze-pinch input.
  - `references/watchos-design.md`: Smart Stack, vertical pagination, Digital Crown haptics, Double Tap.
  - `references/widgets-live-activities.md`: WidgetKit timelines, ActivityKit, Dynamic Island presentations.
  - `references/app-intents-siri-shortcuts.md`: App Intents framework, Siri phrases, iOS 18 Control Center widgets.
  - `references/storekit-monetization.md`: StoreKit 2 paywalls, subscriptions, promotional offers, Xcode testing.
  - `references/cloudkit-sync-data.md`: SwiftData `@Model` persistence, schema migration, CloudKit sync.
  - `references/metal-shaders-visual-effects.md`: Metal stitchable shaders, iOS 18 `MeshGradient`, sensory feedback.
  - `references/internationalization-localization.md`: String Catalogs (`.xcstrings`), pluralization, RTL mirroring.
  - `references/offline-caching-networking.md`: URLSession structured concurrency, NWPathMonitor reachability.
- **New Production Examples (`examples/`)**:
  - `examples/live-activities-example.md`: Dynamic Island and Lock Screen ActivityKit implementation.
  - `examples/swiftdata-cloudkit-example.md`: SwiftData model container with CloudKit sync and queries.
  - `examples/mesh-gradients-shaders.md`: iOS 18 `MeshGradient` and Metal shader effects.
  - `examples/storekit-paywall-example.md`: StoreKit 2 custom subscription store with offer codes.
- **New Checklists (`checklists/`)**:
  - `checklists/widget-dynamic-island-review.md`: WidgetKit, Dynamic Island, and Smart Stack review.
  - `checklists/localization-review.md`: String Catalogs, RTL mirroring, and formatting checklist.
  - `checklists/swiftdata-persistence-review.md`: SwiftData model safety, migrations, and CloudKit sync review.
- **Test Suite**:
  - 18 unit tests in `tests/` covering metadata validation, asset checking, privacy manifests, ASC client, localization, and widgets.

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
