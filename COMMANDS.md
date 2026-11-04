# Agent Slash-Commands & Workflow Reference

This document defines the specialized command workflows of `apple-native-engineer`. Compatible AI coding assistants (such as Claude Code, Cursor, Codex, Copilot, or Gemini CLI) can be invoked using these slash-commands or equivalent natural-language prompts.

---

## 1. Quick Command Overview

| Command | Workflow Description | Target Domain |
| :--- | :--- | :--- |
| **`/apple-native-install`** | Automatically detects project environment and safely installs/links the skill. | Setup & Discovery |
| **`/apple-native`** | Master inspection: evaluates existing app, diagnoses flaws, proposes prioritized plan, and implements fixes. | Full Lifecycle |
| **`/apple-native-design`** | Native UI/UX audit: layout, spacing, typography, materials, squircle corners, and HIG compliance. | Design & HIG |
| **`/apple-native-code`** | Swift 6, SwiftUI architecture, Observation (`@Observable`), MainActor, and clean code review. | Architecture |
| **`/apple-native-review`** | App Store Review readiness audit across Safety, Performance, Business, Design, and Legal. | App Store Pre-Flight |
| **`/apple-native-privacy`** | Privacy Manifests (`PrivacyInfo.xcprivacy`), Required-Reason APIs, Permissions, and Keychain audit. | Privacy & Security |
| **`/apple-native-ipad`** | iPadOS adaptation: `NavigationSplitView`, sidebars, Stage Manager, pointer hover, and keyboard shortcuts. | iPadOS & macOS |
| **`/apple-native-accessibility`** | Comprehensive accessibility audit: Dynamic Type (AX1–AX5), VoiceOver tree, contrast, and touch targets. | Accessibility (a11y) |
| **`/apple-native-performance`** | 120Hz ProMotion smoothness, SwiftUI view invalidation, memory leaks, and concurrency audit. | Performance & Metal |
| **`/apple-native-release`** | Pre-submission release checklist: App icons, launch screens, metadata, and final verification gates. | App Store Release |

---

## 2. Detailed Command Workflows

### A. `/apple-native-install`
**Purpose**: Effortlessly add the skill to an existing Xcode or Swift project.

**Agent Execution Steps**:
1. Inspect the workspace root for existing project files (`.xcodeproj`, `Package.swift`, `Podfile`).
2. Detect the active AI assistant (Claude Code, Cursor, Codex, Copilot, Gemini).
3. Safely symlink or copy the skill directory into the target agent's discovery directory (e.g., `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`).
4. Preserve existing user configuration files and custom instructions.
5. Verify that `SKILL.md` is discoverable by the assistant.
6. Print a confirmation summary explaining how to invoke the master command `/apple-native`.

---

### B. `/apple-native` (Master Workflow)
**Purpose**: Complete, end-to-end inspection, prioritization, and improvement of an application.

**Agent Execution Steps**:
1. **Understand Current State**: Read project configuration, deployment targets, architecture pattern (MVVM, Clean, TCA), and design conventions.
2. **Multi-Domain Inspection**:
   - Check HIG compliance, typography, and touch target sizes.
   - Audit state management, `@MainActor` thread safety, and view composition.
   - Audit `PrivacyInfo.xcprivacy` and permission usage strings.
   - Evaluate iPad adaptation and Dynamic Type responsiveness.
3. **Formulate Prioritized Plan**: Categorize findings by severity (Critical, High, Medium, Low, Suggestion).
4. **Interactive Alignment**: Present the findings and request user confirmation before modifying critical files.
5. **Implementation & Verification**: Apply the approved native refactoring and run available validation checks.

---

### C. `/apple-native-design`
**Purpose**: Elevate visual polish and interface adherence to Apple Human Interface Guidelines.

**Agent Execution Steps**:
- Audit typography against SF Pro and Dynamic Type standards.
- Replace hardcoded hex colors with semantic colors (`Color(uiColor: .systemGroupedBackground)`).
- Ensure continuous squircle curvature on all rounded cards (`style: .continuous`).
- Apply authentic Apple materials (`.ultraThinMaterial`, `.regularMaterial`) with subtle specular highlights.
- Implement Emil Kowalski motion principles: physics springs, no `scale(0)` pops, and sensory haptic pairing.

---

### D. `/apple-native-code`
**Purpose**: Modernize Swift code quality, state modeling, and architecture.

**Agent Execution Steps**:
- Migrate legacy `ObservableObject` and `@Published` classes to the modern `@Observable` macro (iOS 17+).
- Enforce strict `@MainActor` isolation on all UI models and view state mutations.
- Extract complex view closures into modular, high-performance sub-view structs.
- Inject dependencies via SwiftUI's Environment values for effortless previewing and testing.
- Introduce unit test suites using the modern Swift Testing framework (`import Testing`).

---

### E. `/apple-native-review`
**Purpose**: Pre-flight review for App Store Review Guidelines.

**Agent Execution Steps**:
- Verify compliance with Guidelines 2.1 (Completeness, no placeholders, crash-free), 3.1.1 (StoreKit 2 IAP), 4.2 (Minimum functionality, avoid raw WebViews), 4.8 (Sign in with Apple), and 5.1 (Privacy).
- Format all findings using the 7-part standard report: Affected File, Apple Guideline URL, Why It Matters, Severity, Recommended Fix, Code Example, Verification Method.

---

### F. `/apple-native-privacy`
**Purpose**: Audit privacy manifests, required-reason APIs, and secure storage.

**Agent Execution Steps**:
- Verify the presence of `PrivacyInfo.xcprivacy` in the main bundle.
- Cross-reference codebase API calls against Apple's Required-Reason categories (User Defaults, File Timestamps, Boot Time, Disk Space).
- Inspect `Info.plist` usage description strings for clarity, detail, and user benefit.
- Confirm authentication credentials are saved in Keychain Services, never in `UserDefaults`.

---

### G. `/apple-native-ipad`
**Purpose**: Optimize the app for iPadOS ergonomics, multi-windowing, and desktop inputs.

**Agent Execution Steps**:
- Replace stretched full-screen iPhone views with `NavigationSplitView` (2 or 3 columns).
- Add right-side `.inspector(isPresented:)` panels for contextual metadata.
- Implement native pointer hover effects (`.hoverEffect(.highlight)`) on interactive controls.
- Add hardware keyboard shortcuts (`⌘-N`, `⌘-S`, `⌘-F`) for power users.
- Support fluid window resizing under Stage Manager.

---

### H. `/apple-native-accessibility`
**Purpose**: Ensure the application is completely accessible to all users.

**Agent Execution Steps**:
- Audit text containers for Dynamic Type resilience up to Accessibility Sizes (AX1–AX5).
- Combine fragmented VoiceOver elements using `.accessibilityElement(children: .combine)`.
- Verify all interactive controls satisfy the minimum 44×44pt touch target requirement.
- Verify color contrast meets WCAG AA standards (4.5:1 body, 3:1 large text).
- Respect `@Environment(\.accessibilityReduceMotion)` by substituting bouncy springs with crossfades.

---

### I. `/apple-native-performance`
**Purpose**: Diagnose render hitches, frame drops, and concurrency bottlenecks.

**Agent Execution Steps**:
- Eliminate object allocations (`DateFormatter`, heavy filters) from `var body`.
- Convert CPU-bound `.frame` animations to GPU-accelerated `.scaleEffect()` and `.opacity()`.
- Audit closures and async tasks for retain cycles (`[weak self]`).
- Ensure all asynchronous UI operations execute on `@MainActor`.

---

### J. `/apple-native-release`
**Purpose**: Final pre-flight checklist before submitting to App Store Connect or TestFlight.

**Agent Execution Steps**:
- Verify app icon resolution (1024×1024pt, zero alpha, no pre-rounded corners).
- Ensure native launch screen matches initial view canvas.
- Confirm working demo credentials are prepared for App Store Review notes.
- Verify that all privacy manifests and required capabilities are bundled.

---

## 3. Invocation Across Different AI Agents

If your AI coding assistant does not support custom slash commands directly, use these equivalent prompt invocations:

### Claude Code
```text
> /apple-native-review
# Or in natural language:
> Run an apple-native review on our checkout and subscription paywall.
```

### Cursor Composer
```text
@apple-native-engineer /apple-native-code
# Or in natural language:
> @apple-native-engineer Audit this SwiftUI view for HIG compliance and touch targets.
```

### OpenAI Codex / CLI
```bash
codex "/apple-native-privacy: audit our app target for PrivacyInfo.xcprivacy and required reason APIs."
```

### GitHub Copilot
```text
@workspace /apple-native-ipad Refactor our root navigation into an adaptive NavigationSplitView.
```
