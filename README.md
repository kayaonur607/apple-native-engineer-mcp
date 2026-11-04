<p align="center">
  <img src="assets/hero.svg" alt="Apple Native Engineer Banner" width="100%">
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License: MIT">
  <img src="https://img.shields.io/badge/Standard-Agent%20Skills-purple.svg" alt="Agent Skills Standard">
  <img src="https://img.shields.io/badge/Swift-5.9%20%7C%206.0-orange.svg" alt="Swift 5.9 / 6.0">
  <img src="https://img.shields.io/badge/iOS-17%2B%20%7C%2018%2B-black.svg" alt="iOS 17+ / 18+">
</p>

<p align="center">
  <strong>One skill. Your entire Apple development workflow.</strong><br>
  <em>Design natively. Engineer cleanly. Protect user privacy. Validate platform compatibility. Prepare for App Store Review.</em>
</p>

> [!NOTE]
> **Independent Developer Notice**: This project is developed and maintained by an independent developer and open-source contributors. It is **not** an official Apple product, and is **not** affiliated with, authorized by, sponsored by, or endorsed by Apple Inc. All Apple platform trademarks, names, and design guidelines are referenced solely for descriptive and interoperability purposes under nominative fair use.

---

## The Central Promise

> **Turn your AI coding assistant into a research-driven Apple platform design engineer, software architect, privacy reviewer, and App Store readiness specialist.**

AI coding assistants frequently generate "AI slop" when generating Apple platform code: generic web-like flat cards, hardcoded hex colors that break in Dark Mode, rigid `.frame(height: 44)` containers that truncate under Dynamic Type, and missing Privacy Manifests that lead to immediate App Store rejection.

**`apple-native-engineer`** is a reusable, framework-independent AI Agent Skill built on the [Agent Skills open standard](https://agentskills.io/). It equips compatible coding assistants (Claude Code, Cursor, OpenAI Codex, GitHub Copilot, Gemini CLI, OpenCode) with the deep engineering standards, review checklists, and architectural workflows needed to build, modernize, and ship first-party quality software across **iOS**, **iPadOS**, **macOS**, and **visionOS**.

---

## 11 Key Questions Answered

### 1. What is this project?
An open-source, cross-agent development standard and executable skill that guides AI coding assistants through the complete lifecycle of Apple platform development: UI/UX design, SwiftUI architecture, Swift 6 concurrency, privacy manifests, accessibility, and App Store Review preparation.

### 2. Who should use it?
- **iOS / macOS Engineers** seeking to elevate existing apps to Apple Design Award standards.
- **Solo Developers & Indie Hackers** preparing applications for App Store submission who need an automated pre-flight review.
- **Engineering Teams** wanting to enforce consistent SwiftUI state modeling, Dynamic Type resilience, and strict privacy standards across their AI assistants.

### 3. What problems does it solve?
- **Prevents "Web-Slop" UI**: Replaces flat CSS-like designs with authentic Apple materials (`.regularMaterial`), continuous squircles (`style: .continuous`), and native components.
- **Eliminates Animation Clumsiness**: Replaces linear transitions and unnatural `scale(0)` pops with Emil Kowalski-inspired physics springs (`.spring(.snappy)`) and sensory feedback.
- **Preempts App Store Rejections**: Flags missing required-reason APIs, missing privacy manifests, un-native web wrappers, and paywall disclosure omissions before submission.
- **Enforces Modern Swift Standards**: Migrates legacy `ObservableObject` code to the Swift 5.9/6 `@Observable` macro and ensures `@MainActor` thread safety.

### 4. How does it transform an existing application?
The skill begins by inspecting your existing repository—respecting your architecture, deployment targets, and brand identity. It then executes a systematic 10-step audit, categorizes findings by severity, proposes an actionable remediation plan, and provides tested SwiftUI implementations.

### 5. What can the AI agent inspect, improve, and validate?
1. **Design & HIG**: Layout, 8pt spacing grid, typography scale, SF Symbols, Liquid Glass materials, and touch targets (minimum 44×44pt).
2. **Architecture & Clean Code**: Observation framework, `@MainActor` isolation, dependency injection, and modular view composition.
3. **Privacy & Security**: `PrivacyInfo.xcprivacy` manifests, Required-Reason APIs, `Info.plist` usage descriptions, Keychain vs UserDefaults, and in-app account deletion.
4. **App Store Readiness**: StoreKit 2 subscriptions, Sign in with Apple compliance, cancellation disclosures, and crash-free completeness.
5. **Platform Adaptability**: Multi-column `NavigationSplitView` on iPad, Stage Manager resizing, pointer hover morphing, and keyboard shortcuts.
6. **Accessibility (a11y)**: Dynamic Type scaling (AX1–AX5), VoiceOver semantic grouping, contrast ratios (4.5:1), and Reduce Motion fallbacks.

### 6. Which Apple platforms and development technologies are supported?
- **Platforms**: iOS 17+, iOS 18+, iPadOS 17/18+, macOS 14/15+ (Sonoma/Sequoia), visionOS 1/2+, and watchOS.
- **Technologies**: Swift 5.9 & Swift 6, SwiftUI, Swift Concurrency, Observation framework, StoreKit 2, Swift Testing, and AppKit/UIKit bridges.

### 7. Which AI agents are supported?
- **Anthropic Claude Code**: Project-level (`.claude/skills/`) and Global (`~/.claude/skills/`).
- **OpenAI Codex**: Project-level (`.agents/skills/`) and Global (`~/.agents/skills/`).
- **Cursor**: Workspace skills (`.cursor/skills/` or `.agents/skills/`) and `.cursorrules`.
- **GitHub Copilot**: Project instructions (`.github/copilot-instructions.md`).
- **Google Gemini CLI / Antigravity**: Workspace (`.gemini/skills/`) and Global profile.
- **OpenCode**: Native Agent Skills standard directory.
- **Vercel Skills CLI**: Automated cross-agent installation via `npx skills add`.

### 8. How can a user install it?
Via one command with the Vercel Skills CLI, or using the included cross-agent installer script (see [Installation](#installation) below).

### 9. How can a user invoke it with slash commands?
Using specialized slash-commands such as `/apple-native`, `/apple-native-design`, `/apple-native-review`, and `/apple-native-privacy` (see [Slash Commands](#slash-commands--workflows) below).

### 10. What are its limitations?
- **No Headless Simulator Rendering**: Terminal-only agents without a running macOS Window Server cannot capture live GUI simulator screenshots. In such environments, the skill conducts deep static structural audits and provides copyable `#Preview` code for Xcode verification.
- **Risk Assessment, Not Guarantees**: Pre-flight audits assess compliance with published guidelines; they cannot guarantee App Store approval, which rests solely with Apple.

### 11. Which official documents and open-source projects influenced it?
Apple Human Interface Guidelines, App Store Review Guidelines, WWDC sessions (WWDC21–WWDC24), Emil Kowalski's design engineering principles, Clean Architecture SwiftUI, Point-Free TCA, and the Agent Skills standard. See [`SOURCES.md`](file:///SOURCES.md) for complete citations.

---

## Slash Commands & Workflows

Compatible assistants recognize these specialized workflows. See [`COMMANDS.md`](file:///COMMANDS.md) for full execution details:

| Command | Workflow | Core Responsibility |
| :--- | :--- | :--- |
| **`/apple-native-install`** | Setup & Discovery | Inspects project stack and installs/links skill safely into target agent directory. |
| **`/apple-native`** | Master Inspection | Full-lifecycle review: evaluates existing app, diagnoses flaws, proposes plan, refactors code. |
| **`/apple-native-design`** | HIG & Polish | Audits typography, 8pt spacing grid, squircle corners, materials, and touch targets. |
| **`/apple-native-code`** | Swift 6 Architecture | Modernizes state with `@Observable`, enforces `@MainActor`, and modularizes views. |
| **`/apple-native-review`** | App Store Pre-Flight | Pre-submission audit across Safety, Performance, Business, Design, and Legal (Sections 1–5). |
| **`/apple-native-privacy`** | Privacy & Security | Audits `PrivacyInfo.xcprivacy`, Required-Reason APIs, permissions, and Keychain storage. |
| **`/apple-native-ipad`** | iPadOS Adaptation | Implements `NavigationSplitView`, sidebars, Stage Manager, pointer hover, and keyboard shortcuts. |
| **`/apple-native-accessibility`**| Accessibility (a11y) | Dynamic Type testing (AX1–AX5), VoiceOver grouping, contrast, and 44pt touch targets. |
| **`/apple-native-performance`**  | Performance & 120Hz | Diagnoses render hitches, GPU transforms, view invalidation, and retain cycles. |
| **`/apple-native-release`**      | Release Readiness   | Final pre-submission checklist: App icons, launch screens, metadata, and testing gates. |

---

## Installation

### Option 1: Via Vercel Skills CLI (`npx skills`)
```bash
# Add to current project (interactive agent selector)
npx skills add kayaonur607/apple-native-engineer

# Add globally to user profile across all projects
npx skills add kayaonur607/apple-native-engineer -g

# Target specific agents directly
npx skills add kayaonur607/apple-native-engineer -a claude-code
npx skills add kayaonur607/apple-native-engineer -a cursor
npx skills add kayaonur607/apple-native-engineer -a codex
```

### Option 2: Via Included Local Installer Script
```bash
git clone https://github.com/kayaonur607/apple-native-engineer.git
cd apple-native-engineer

# Install globally for all supported agents on this Mac
./scripts/install-skill.sh -g -a all

# Or link locally into your current Xcode project
./scripts/install-skill.sh -p -a claude
```

---

## Lifecycle Transformation: Before vs. After

### 1. Design & Touch Ergonomics
```swift
// ❌ BEFORE: Web-slop, un-native, un-ergonomic, breaks in Dark Mode
struct OldProfileCard: View {
    var body: some View {
        VStack {
            Text("User Profile")
                .font(.system(size: 20)) // ❌ Fixed size, never scales with Dynamic Type
                .foregroundColor(Color(hex: "#1A1A1A")) // ❌ Hardcoded hex invisible in Dark Mode
            Button("Edit") { edit() }
                .frame(width: 30, height: 24) // ❌ Violates 44x44pt touch target rule!
                .background(Color.blue)
                .cornerRadius(4) // ❌ Non-continuous circular corner
        }
        .padding(13.5) // ❌ Arbitrary non-grid spacing
    }
}

// ✅ AFTER: Native Apple Design Engineering
struct NativeProfileCard: View {
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text("User Profile")
                .font(.headline) // ✅ Dynamic Type support
                .foregroundStyle(.primary) // ✅ Semantic contrast
            
            Button("Edit Profile") { edit() }
                .buttonStyle(.bordered)
                .controlSize(.regular)
                .frame(minHeight: 44) // ✅ Meets Level 1 touch target requirement
        }
        .padding(16) // ✅ 8pt mathematical spacing grid
        .background(
            Color(uiColor: .secondarySystemGroupedBackground),
            in: RoundedRectangle(cornerRadius: 16, style: .continuous) // ✅ Continuous squircle
        )
    }
}
```

### 2. Architecture & Concurrency (Swift 6)
```swift
// ❌ BEFORE: Thread-unsafe legacy ObservableObject triggering body re-render cascades
class UserViewModel: ObservableObject {
    @Published var users: [User] = []
    func load() {
        DispatchQueue.global().async {
            let data = fetchUsers()
            DispatchQueue.main.async {
                self.users = data // Data-race hazard in Swift 6
            }
        }
    }
}

// ✅ AFTER: Modern Swift 6 Observation isolated to MainActor
@Observable
@MainActor
final class UserViewModel {
    private(set) var users: [User] = []
    private let service: UserServiceProtocol
    
    init(service: UserServiceProtocol) {
        self.service = service
    }
    
    func load() async {
        users = (try? await service.fetchUsers()) ?? [] // Clean structured concurrency
    }
}
```

### 3. Privacy Manifests & Required-Reason APIs
```xml
<!-- ❌ BEFORE: Missing PrivacyInfo.xcprivacy — Triggers App Store Rejection -->

<!-- ✅ AFTER: Declared in PrivacyInfo.xcprivacy -->
<key>NSPrivacyAccessedAPITypes</key>
<array>
    <dict>
        <key>NSPrivacyAccessedAPIType</key>
        <string>NSPrivacyAccessedAPICategoryUserDefaults</string>
        <key>NSPrivacyAccessedAPITypeReasons</key>
        <array>
            <string>CA92.1</string>
        </array>
    </dict>
</array>
```

---

## Repository Architecture

```
apple-native-engineer/
├── SKILL.md                          # Canonical Agent Skills standard specification (agentskills.io)
├── README.md                         # Comprehensive documentation, lifecycle guide, quickstart
├── SOURCES.md                        # Master research bibliography, official & community sources
├── COMMANDS.md                       # Complete slash-command specification & agent workflows
├── LICENSE                           # MIT License
├── CHANGELOG.md                      # Semantic version history (v1.0.0)
├── CONTRIBUTING.md                   # Community contribution guide & PR standards
├── CODE_OF_CONDUCT.md                # Contributor Covenant v2.1
├── SECURITY.md                       # Security & vulnerability reporting policy
│
├── references/                       # Progressive disclosure knowledge base
│   ├── apple-hig-foundations.md      # Clarity, Deference, Depth, direct manipulation & feedback
│   ├── design-principles.md          # 5-Tier Authority Taxonomy (Requirements vs Polish)
│   ├── typography-and-color.md       # SF Pro, Dynamic Type AX1-AX5, Semantic Colors, Contrast
│   ├── liquid-glass.md               # Apple Materials (.regularMaterial), Squircles, Specular Edges
│   ├── native-components.md          # Buttons, Lists, Forms, Pickers, Detents, ContentUnavailableView
│   ├── navigation-patterns.md        # NavigationStack, NavigationSplitView, TabView, Toolbars
│   ├── iphone-design.md              # Compact Width, Thumb Reach Zone, Safe Area, Keyboard
│   ├── ipad-design.md                # Multi-column SplitView, Sidebars, Inspectors, Hover, Shortcuts
│   ├── macos-design.md               # AppKit/SwiftUI density, Menu Bar, Unified Toolbars, Settings
│   ├── architecture-and-clean-code.md# Clean Architecture, MVVM, @Observable, MainActor, Swift Testing
│   ├── privacy-and-security.md       # Privacy Manifests (PrivacyInfo.xcprivacy), Keychain, ATT
│   ├── app-store-readiness.md        # App Store Review Guidelines (Sections 1–5), StoreKit 2
│   ├── accessibility.md              # Dynamic Type, VoiceOver, Touch Targets (44pt), Reduce Motion
│   ├── performance-optimization.md   # 120Hz ProMotion, GPU transforms, view invalidation, retain cycles
│   ├── swiftui-engineering.md        # @Observable macro, Swift 6 @MainActor, Swift Testing
│   ├── animation-principles.md       # Emil Kowalski principles, Springs (.snappy), No scale(0) pops
│   ├── design-systems.md             # Strongly-typed tokens: Spacing, Radius, Motion, Elevation
│   ├── visual-quality.md             # Xcode Previews matrix, Simulator inspection & integrity
│   ├── official-resources.md         # Apple HIG & Developer API citations (exact URLs & WWDC)
│   └── community-resources.md        # Studied open-source repos, licenses, and design attributions
│
├── checklists/                       # Systematic review & audit workflows
│   ├── apple-hig-audit.md            # Complete 10-step audit protocol & severity grading template
│   ├── app-store-guidelines-review.md# Full App Store Review Guidelines compliance checklist (Sec 1-5)
│   ├── privacy-security-review.md    # Privacy manifests, permissions, Keychain, and ATT checklist
│   ├── performance-review.md         # SwiftUI rendering, 120Hz smoothness, and concurrency checklist
│   ├── iphone-review.md              # iPhone ergonomics, safe area, and detent review
│   ├── ipad-review.md                # iPadOS multi-column, Stage Manager, pointer review
│   ├── accessibility-review.md       # Dynamic Type AX, VoiceOver tree, contrast, touch target review
│   ├── visual-design-review.md       # Visual hierarchy, 8pt spacing grid, materials & motion review
│   └── release-review.md             # Pre-App Store submission readiness & privacy manifests
│
├── examples/                         # Production-grade, copy-pasteable SwiftUI code
│   ├── navigation-examples.md        # Type-safe router & universal adaptive NavigationSplitView
│   ├── adaptive-layout-examples.md   # ViewThatFits dynamic type & responsive dashboard grids
│   ├── native-components.md          # Grouped forms, interactive search scopes, and detented sheets
│   ├── animation-examples.md         # Grounded card dialogs, tactile bookmark toggle, sensory haptics
│   └── design-system-example.md      # Drop-in production SwiftUI Design System & tokens package
│
├── integrations/                     # Cross-agent setup and discovery guides
│   ├── claude-code.md                # Anthropic Claude Code (.claude/skills/)
│   ├── codex.md                      # OpenAI Codex & Agent Skills standard (.agents/skills/)
│   ├── cursor.md                     # Cursor Composer & .cursorrules (.cursor/skills/)
│   ├── github-copilot.md             # GitHub Copilot (.github/copilot-instructions.md)
│   ├── gemini-cli.md                 # Google Gemini CLI & Antigravity (.gemini/skills/)
│   ├── opencode.md                   # OpenCode & universal agent runtimes
│   └── vercel-skills.md              # Vercel Skills CLI package management (npx skills)
│
├── scripts/                          # Automated validation & installation tooling
│   ├── validate-skill.sh             # Validates YAML frontmatter, file tree & link integrity
│   ├── check-references.sh           # Scans and validates all internal markdown links
│   └── install-skill.sh              # Cross-agent local & global symlink installer
│
└── .github/                          # GitHub templates & CI automation
    ├── ISSUE_TEMPLATE/
    ├── PULL_REQUEST_TEMPLATE.md
    └── workflows/
        └── validate.yml              # GitHub Actions automated validation workflow
```

---

## Validation & Quality Assurance

Run the automated verification suite to validate frontmatter, file presence, and internal reference links:

```bash
# Full repository validation
./scripts/validate-skill.sh

# Local markdown reference scan
./scripts/check-references.sh
```

---

## Disclaimers & Independent Developer Notice

- **Independent Project**: This repository is created, maintained, and operated by an independent developer and the open-source community. It has **no affiliation, connection, association, sponsorship, authorization, or endorsement from Apple Inc.**
- **Trademark Disclaimers**: *Apple, iPhone, iPad, iPadOS, macOS, watchOS, visionOS, Swift, SwiftUI, AppKit, UIKit, SF Symbols, and Dynamic Type are trademarks or registered trademarks of Apple Inc. in the United States and other jurisdictions.* Their mention in this repository is strictly for descriptive identification, educational instruction, and platform interoperability under nominative fair use.
- **No Guarantee of Approval**: All audit checklists, risk ratings, and guidelines represent independent developer interpretations of publicly available Apple documentation. They do not constitute formal legal counsel and cannot guarantee App Store approval, which remains solely at the discretion of Apple Inc.

---

## License

This project is licensed under the [MIT License](LICENSE).
