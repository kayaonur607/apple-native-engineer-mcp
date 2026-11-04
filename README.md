<p align="center">
  <img src="assets/hero.svg" alt="Apple Native Engineer MCP Banner" width="100%">
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
  <a href="https://modelcontextprotocol.io"><img src="https://img.shields.io/badge/MCP-JSON--RPC%202.0-8A2BE2.svg?style=flat-square" alt="MCP Protocol"></a>
  <a href="https://agentskills.io"><img src="https://img.shields.io/badge/Standard-Agent%20Skills-4A154B.svg?style=flat-square" alt="Agent Skills Standard"></a>
  <a href="#supported-apple-platforms--hardware"><img src="https://img.shields.io/badge/Ecosystem-Apple%20Platforms-0A84FF.svg?style=flat-square" alt="Apple Platforms"></a>
  <a href="#validation--test-suite"><img src="https://img.shields.io/badge/Tests-18%20Passed-30D158.svg?style=flat-square" alt="Tests Passed"></a>
</p>

<p align="center">
  <strong>The Full-Lifecycle Apple Development Standard, Executable Toolkit &amp; Model Context Protocol (MCP) Server.</strong><br>
  <em>Design natively. Engineer cleanly. Audit privacy. Automate App Store Connect. Ship first-party quality software.</em>
</p>

> [!NOTE]
> **Independent Developer Notice**: This project is developed and maintained by independent open-source developers. It is **not** an official Apple product, and is **not** affiliated with, authorized by, sponsored by, or endorsed by Apple Inc. All Apple platform names, hardware models, and guidelines are referenced strictly for identification and interoperability under nominative fair use.

---

## The Central Promise

> **"Transform your AI coding assistant into a research-driven Apple platform design engineer, software architect, privacy auditor, and App Store Connect specialist."**

AI assistants frequently generate generic "AI slop" when asked for Apple code: flat web-like cards, hardcoded hex colors that break in Dark Mode, rigid containers that truncate under Dynamic Type, and missing Privacy Manifests that cause immediate App Store rejections.

**`apple-native-engineer-mcp`** solves this by providing a unified, framework-independent standard across three complementary layers:
1. **Layer 1: AI Engineering Standard**: Comprehensive Human Interface Guidelines (HIG), Kowalski physics springs, Glisse optical materials, Swift concurrency, and MVVM architecture.
2. **Layer 2: Executable CLI Toolkit (`tools/`)**: 8 standalone command-line tools for project inspection, icon validation, screenshot generation, metadata checks, privacy audits, localization, and release scoring.
3. **Layer 3: Model Context Protocol (MCP) Server (`integrations/mcp-server/`)**: A standard stdio JSON-RPC 2.0 server connecting Claude Desktop, Cursor, OpenAI Codex, and Gemini directly to your Apple development tools and the App Store Connect REST API.

---

## Supported Apple Platforms & Hardware

Designed for the modern Apple ecosystem across all primary device classes:

| Platform | Hardware Ecosystem | Target Capabilities & Form Factors |
| :--- | :--- | :--- |
| 📱 **iOS** | **iPhone 16 / Pro / Max**, **iPhone 15 Series**, **iPhone 14 / 13 / 12 / SE** | Dynamic Island, StandBy mode, Action Button, Control Center widgets, Live Activities, ProMotion 120Hz. |
| 📱 **iPadOS** | **iPad Pro (M4 / M2)**, **iPad Air (M2)**, **iPad mini**, **iPad (10th Gen)** | Multi-column `NavigationSplitView`, sidebar morphing, Stage Manager resizing, pointer hover, Apple Pencil. |
| 💻 **macOS** | **MacBook Pro**, **MacBook Air**, **Mac Studio**, **Mac mini**, **Mac Pro** | Unified window toolbars, Menu Bar extras, native Settings scenes, keyboard command shortcuts. |
| 🥽 **visionOS** | **Apple Vision Pro** | Shared Space windows, 3D volumetric containers, Immersive Spaces (`.mixed`, `.progressive`, `.full`), ornaments, gaze-pinch input. |
| ⌚ **watchOS** | **Apple Watch Ultra 2**, **Apple Watch Series 10 / 9**, **Apple Watch SE** | Smart Stack widgets, vertical pagination, Digital Crown haptic interaction, Double Tap gesture, Always-On display. |

---

## 3-Layer System Architecture

```
┌────────────────────────────────────────────────────────────────────────┐
│               LAYER 1: CANONICAL AGENT SKILL (SKILL.md)                │
│  • HIG Design Foundations    • Kowalski Physics Springs  • Swift MVVM  │
│  • Glisse Optical Materials  • Privacy Manifest Auditing • Checklists  │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ triggers / guides
┌───────────────────────────────────▼────────────────────────────────────┐
│                    LAYER 2: EXECUTABLE CLI TOOLS                       │
│  tools/project-inspector/     tools/asset-validator/                   │
│  tools/privacy-auditor/       tools/metadata-validator/               │
│  tools/localization-checker/  tools/widget-validator/                 │
│  tools/screenshot-studio/     tools/release-readiness/                 │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ exposes via stdio
┌───────────────────────────────────▼────────────────────────────────────┐
│          LAYER 3: MODEL CONTEXT PROTOCOL (MCP) & ASC CLIENT            │
│  • JSON-RPC 2.0 Server (Claude Desktop, Cursor, Copilot, Codex)        │
│  • Official App Store Connect REST API (JWT ES256 authentication)      │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Model Context Protocol (MCP) Quickstart

Connect your favorite AI coding environment directly to Apple native development tools.

### 1. Claude Desktop Configuration
Add the server configuration to your `claude_desktop_config.json` (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": [
        "/Users/YOUR_USERNAME/Desktop/apple-native-engineer-mcp/integrations/mcp-server/src/index.js"
      ],
      "env": {
        "ASC_KEY_ID": "YOUR_KEY_ID",
        "ASC_ISSUER_ID": "YOUR_ISSUER_ID",
        "ASC_PRIVATE_KEY_PATH": "/path/to/AuthKey_XYZ.p8"
      }
    }
  }
}
```

### 2. Cursor Configuration
Add to your project's `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["./integrations/mcp-server/src/index.js"]
    }
  }
}
```

### 3. Verification via Terminal
Test the MCP server over stdio:

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/list"}' | node integrations/mcp-server/src/index.js
```

---

## Executable CLI Tools & Terminal Previews

All tools are located in `tools/` and run without third-party Python dependencies (Python 3 standard library only).

### 1. Project Inspector
Analyzes Xcode project structure, Swift package manifests, frameworks, and deployment targets:

```bash
python3 tools/project-inspector/inspect_project.py .
```

```text
============================================================
📱 Apple Native Engineer — Project Inspection Report
============================================================
Project Root:        /Users/developer/MyNativeApp
Project Type:        Xcode Workspace (.xcworkspace)
Swift Version:       Swift 6
Platforms:           iOS (17.0+), iPadOS (17.0+), macOS (14.0+)
UI Framework:        SwiftUI (Native)
Architecture:        Clean MVVM + Observation (@Observable)
Concurrency:         Strict Concurrency Checking Enabled
============================================================
```

### 2. Privacy Manifest & Required-Reason Auditor
Scans Swift sources for Apple's Required-Reason APIs and verifies declarations in `PrivacyInfo.xcprivacy`:

```bash
python3 tools/privacy-auditor/audit_privacy.py .
```

```text
============================================================
🔒 Apple Native Engineer — Privacy & Security Audit
============================================================
Manifest Status:     FOUND (PrivacyInfo.xcprivacy)
Scanned Source Files: 42 Swift files
------------------------------------------------------------
[PASS] NSPrivacyAccessedAPICategoryFileTimestamp
       Declared reasons: ["C617.1"]
[PASS] NSPrivacyAccessedAPICategoryUserDefaults
       Declared reasons: ["CA92.1"]
------------------------------------------------------------
Result: 0 Critical Errors, 0 Missing Reason Declarations
Status: PASS (Ready for App Store Review)
============================================================
```

### 3. App Store Icon & Asset Validator
Ensures App Store marketing icons strictly meet Apple's non-negotiable requirements (1024×1024, zero alpha transparency):

```bash
python3 tools/asset-validator/validate_assets.py --icon AppIcon-1024.png
```

```text
============================================================
🎨 Apple Native Engineer — App Icon & Asset Validator
============================================================
Target:      AppIcon-1024.png
Dimensions:  1024 × 1024 px [PASS]
Format:      PNG Signature [PASS]
Alpha:       No Transparency Channels [PASS]
Status:      VALID (App Store Submission Ready)
============================================================
```

### 4. Localization & Right-to-Left (RTL) Checker
Scans SwiftUI views for hardcoded text, non-adaptive directional padding (`.left`/`.right`), and String Catalog (`.xcstrings`) completeness:

```bash
python3 tools/localization-checker/check_localization.py --project-dir .
```

### 5. WidgetKit & Dynamic Island Validator
Audits WidgetKit bundles and Live Activities for missing Dynamic Island presentation states (`compactLeading`, `compactTrailing`, `minimal`) and verifies `NSSupportsLiveActivities` in `Info.plist`:

```bash
python3 tools/widget-validator/validate_widget.py --project-dir .
```

### 6. Automated Pre-Flight Release Readiness Report
Generates an App Store readiness audit scoring code, privacy, assets, and metadata:

```bash
python3 tools/release-readiness/generate_report.py . --output RELEASE_REPORT.md
```

---

## Executable Slash Commands & Workflows

Compatible AI assistants can execute specialized workflows using these commands:

| Command | Target Domain | Core Responsibility & Tool Invocation |
| :--- | :--- | :--- |
| **`/apple-native`** | Master Inspection | End-to-end audit: evaluates architecture, HIG, privacy, and generates action plan. |
| **`/apple-native-design`** | HIG & Visuals | 8pt grid, SF Symbols, Liquid Glass shaders, squircle corners, and color semantics. |
| **`/apple-native-code`** | Swift Architecture | Modernizes state with `@Observable`, enforces `@MainActor`, and modularizes views. |
| **`/apple-native-review`** | App Store Review | Pre-submission audit across Guidelines 1–5 (Safety, Performance, Business, Design, Legal). |
| **`/apple-native-privacy`** | Privacy Manifests | Audits `PrivacyInfo.xcprivacy` using `tools/privacy-auditor/audit_privacy.py`. |
| **`/apple-native-icon`** | App Icon Check | Validates 1024×1024 PNG with `tools/asset-validator/validate_assets.py`. |
| **`/apple-native-screenshots`** | Screenshot Studio | Validates App Store screenshot resolutions and prepares multi-device frames. |
| **`/apple-native-connect`** | ASC Automation | Interacts with the App Store Connect REST API (apps, versions, builds, testers). |
| **`/apple-native-metadata`** | App Store Metadata | Validates character counts, keywords, and URLs with `tools/metadata-validator/`. |
| **`/apple-native-widgets`** | Widgets & Island | Audits WidgetKit timelines and Dynamic Island states with `tools/widget-validator/`. |
| **`/apple-native-localization`** | i18n & RTL | Audits String Catalogs and RTL mirroring with `tools/localization-checker/`. |
| **`/apple-native-release`** | Release Gate | Generates pre-submission release report with `tools/release-readiness/`. |

---

## Comprehensive Knowledge Base

The repository includes 29 specialized engineering reference guides, 12 audit checklists, and 9 production-grade examples:

### Reference Guides (`references/`)
- [`apple-hig-foundations.md`](file:///references/apple-hig-foundations.md): Clarity, deference, depth, and mental models.
- [`typography-and-color.md`](file:///references/typography-and-color.md): SF Pro family, Dynamic Type scales, and semantic materials.
- [`liquid-glass.md`](file:///references/liquid-glass.md): Native materials, specular edge highlights, and Glisse-inspired parameter engine.
- [`native-components.md`](file:///references/native-components.md): Buttons, lists, forms, menus, sheets, pickers, and search bars.
- [`navigation-patterns.md`](file:///references/navigation-patterns.md): `NavigationStack`, `NavigationSplitView`, `TabView`, and detents.
- [`iphone-design.md`](file:///references/iphone-design.md): Compact width, thumb reach, safe areas, and keyboard avoidance.
- [`ipad-design.md`](file:///references/ipad-design.md): Multi-column layouts, sidebars, Stage Manager, pointer hover, and shortcuts.
- [`macos-design.md`](file:///references/macos-design.md): Mac unified toolbars, window styles, settings scenes, and menu bar commands.
- [`visionos-spatial-design.md`](file:///references/visionos-spatial-design.md): 3D windows, volumes, immersive spaces, ornaments, and gaze-pinch input.
- [`watchos-design.md`](file:///references/watchos-design.md): Smart Stack, vertical pagination, Digital Crown haptics, and Double Tap gesture.
- [`widgets-live-activities.md`](file:///references/widgets-live-activities.md): WidgetKit, ActivityKit, Dynamic Island presentations, and Lock Screen widgets.
- [`app-intents-siri-shortcuts.md`](file:///references/app-intents-siri-shortcuts.md): App Intents framework, AppShortcutsProvider, Siri, and iOS 18 Control Center widgets.
- [`architecture-and-clean-code.md`](file:///references/architecture-and-clean-code.md): Clean architecture, MVVM, `@Observable`, dependency injection, and Swift Testing.
- [`swiftui-engineering.md`](file:///references/swiftui-engineering.md): SwiftUI state lifecycle, custom view modifiers, and view tree optimization.
- [`storekit-monetization.md`](file:///references/storekit-monetization.md): StoreKit 2 paywalls, auto-renewing subscriptions, promotional offers, and Xcode testing.
- [`cloudkit-sync-data.md`](file:///references/cloudkit-sync-data.md): SwiftData `@Model` entities, schema migrations, and private CloudKit database synchronization.
- [`metal-shaders-visual-effects.md`](file:///references/metal-shaders-visual-effects.md): Metal stitchable shaders, iOS 18 MeshGradient, and sensory haptic feedback.
- [`internationalization-localization.md`](file:///references/internationalization-localization.md): String Catalogs (`.xcstrings`), pluralization, and Right-to-Left (RTL) mirroring.
- [`offline-caching-networking.md`](file:///references/offline-caching-networking.md): Resilient `URLSession` concurrency, NWPathMonitor reachability, and background transfers.
- [`privacy-and-security.md`](file:///references/privacy-and-security.md): Privacy Manifests (`PrivacyInfo.xcprivacy`), Required-Reason APIs, Keychain, and ATT.
- [`app-store-readiness.md`](file:///references/app-store-readiness.md): App Store Review Guidelines (Sections 1–5), StoreKit 2 paywalls, and Sign in with Apple.
- [`app-store-connect-api.md`](file:///references/app-store-connect-api.md): Official App Store Connect REST API, JWT auth, endpoints, and error handling.
- [`accessibility.md`](file:///references/accessibility.md): VoiceOver semantics, Dynamic Type AX, contrast, and 44pt touch targets.
- [`performance-optimization.md`](file:///references/performance-optimization.md): 120Hz ProMotion, GPU transforms, view invalidation, and retain cycles.
- [`animation-principles.md`](file:///references/animation-principles.md): Kowalski motion design, physics springs, and sensory feedback.
- [`design-systems.md`](file:///references/design-systems.md): Token systems for spacing, radius, typography, and elevation.
- [`visual-quality.md`](file:///references/visual-quality.md): Visual verification protocols, Xcode Previews matrix, and Simulator testing.
- [`official-resources.md`](file:///references/official-resources.md): Official Apple HIG, Developer Documentation, and WWDC citations.
- [`community-resources.md`](file:///references/community-resources.md): Open-source inspirations and attributions.

### Review Checklists (`checklists/`)
- [`apple-hig-audit.md`](file:///checklists/apple-hig-audit.md): Complete 10-step Apple HIG audit template and severity guide.
- [`app-store-guidelines-review.md`](file:///checklists/app-store-guidelines-review.md): Full App Store Review Guidelines compliance checklist (Sections 1–5).
- [`privacy-security-review.md`](file:///checklists/privacy-security-review.md): Privacy manifests, permissions, Keychain, and ATT checklist.
- [`performance-review.md`](file:///checklists/performance-review.md): SwiftUI rendering, 120Hz smoothness, and concurrency safety checklist.
- [`iphone-review.md`](file:///checklists/iphone-review.md): iPhone layout, thumb reach, and modal ergonomics review.
- [`ipad-review.md`](file:///checklists/ipad-review.md): iPad multi-column, sidebar, Stage Manager, and pointer review.
- [`accessibility-review.md`](file:///checklists/accessibility-review.md): Dynamic Type AX, VoiceOver tree, contrast, and touch target checklist.
- [`visual-design-review.md`](file:///checklists/visual-design-review.md): Visual polish, 8pt spacing grid, materials, and hierarchy review.
- [`release-review.md`](file:///checklists/release-review.md): Pre-submission release checklist.
- [`widget-dynamic-island-review.md`](file:///checklists/widget-dynamic-island-review.md): WidgetKit, Dynamic Island, and Smart Stack review.
- [`localization-review.md`](file:///checklists/localization-review.md): String Catalogs, RTL mirroring, and formatting checklist.
- [`swiftdata-persistence-review.md`](file:///checklists/swiftdata-persistence-review.md): SwiftData model safety, migrations, and CloudKit sync review.

### Production Examples (`examples/`)
- [`navigation-examples.md`](file:///examples/navigation-examples.md): Adaptive iPhone/iPad navigation architectures.
- [`adaptive-layout-examples.md`](file:///examples/adaptive-layout-examples.md): Size-class switching and `ViewThatFits` implementations.
- [`native-components.md`](file:///examples/native-components.md): Production forms, buttons, pickers, and sheets with correct vs incorrect patterns.
- [`animation-examples.md`](file:///examples/animation-examples.md): Fluid springs, expandable cards, bookmark toggles, and reduced motion fallbacks.
- [`design-system-example.md`](file:///examples/design-system-example.md): Modular SwiftUI design token implementation.
- [`live-activities-example.md`](file:///examples/live-activities-example.md): Dynamic Island & Live Activity full implementation.
- [`swiftdata-cloudkit-example.md`](file:///examples/swiftdata-cloudkit-example.md): SwiftData model container with CloudKit sync and queries.
- [`mesh-gradients-shaders.md`](file:///examples/mesh-gradients-shaders.md): iOS 18 `MeshGradient` and Metal shader effects.
- [`storekit-paywall-example.md`](file:///examples/storekit-paywall-example.md): StoreKit 2 custom subscription store with offer codes.

---

## Validation & Test Suite

Verify all repository tools, frontmatter specifications, and link integrity:

```bash
# 1. Run Python unit tests for all CLI tools (18 unit tests)
python3 -m unittest discover -s tests

# 2. Run Agent Skills standard validation and link verification
./scripts/validate-skill.sh

# 3. Run all tools in pipeline against local project
./scripts/run-all-tools.sh .
```

---

## Disclaimers & Independent Developer Notice

- **Independent Project**: This repository is created, maintained, and operated by independent developers and the open-source community. It has no affiliation, connection, association, sponsorship, authorization, or endorsement from Apple Inc.
- **Trademark Disclaimers**: Apple, iPhone, iPad, iPadOS, Mac, macOS, Apple Watch, watchOS, Apple Vision Pro, visionOS, Swift, SwiftUI, AppKit, UIKit, Dynamic Island, Action Button, SF Symbols, and Dynamic Type are trademarks or registered trademarks of Apple Inc. in the United States and other jurisdictions. Their mention in this repository is strictly for descriptive identification, educational instruction, and platform interoperability under nominative fair use.
- **No Guarantee of Approval**: All audit checklists, risk ratings, and guidelines represent independent developer interpretations of publicly available Apple documentation. They do not constitute formal legal counsel and cannot guarantee App Store approval, which remains solely at the discretion of Apple Inc.

---

## License

This project is licensed under the [MIT License](LICENSE).
