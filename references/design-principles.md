# Design Principles & Authority Classification

When architecting, reviewing, or refactoring native Apple applications, precision regarding **why** a decision is made is paramount. AI agents often conflate personal aesthetic tastes with mandatory platform requirements, eroding developer trust. 

This document defines the 5-tiered authority taxonomy used throughout this skill.

---

## 1. The 5-Tiered Authority Taxonomy

```
┌───────────────────────────────────────────────────────────┐
│ Level 1: Official Apple Requirement                       │  Mandatory (App Store / System Contract)
├───────────────────────────────────────────────────────────┤
│ Level 2: Official Apple Recommendation                    │  HIG Standard (Strong Architectural Guidance)
├───────────────────────────────────────────────────────────┤
│ Level 3: Platform Convention                              │  User Expectation (Native Platform Idiom)
├───────────────────────────────────────────────────────────┤
│ Level 4: Community Best Practice                          │  Industry Consensus (Swift / SwiftUI Engineering)
├───────────────────────────────────────────────────────────┤
│ Level 5: Design Engineering Recommendation                 │  Taste & Polish (Kowalski Motion, Micro-Delight)
└───────────────────────────────────────────────────────────┘
```

---

## 2. Detailed Breakdown & Concrete Examples

### Level 1: Official Apple Requirement
Enforced directly by App Store Review Guidelines, Apple Platform Human Interface Guidelines strict minimums, or runtime crash-prevention contracts.

- **Examples**:
  - **Touch Target Size**: Minimum 44×44pt tappable area for all interactive elements (except inline text links in body copy).
  - **Safe Area Insets**: Interactive controls must not overlap the Home Indicator, Dynamic Island, or status bar.
  - **Main Thread Execution**: All UI updates and view modifications must execute on the `@MainActor`.
  - **Privacy Strings**: `Info.plist` usage descriptions for Camera, Location, Photos, etc., must explicitly explain why the app needs the capability.
  - **App Icon Alpha**: App icon assets must not contain transparency / alpha channels.

```swift
// ❌ FAILS LEVEL 1 (Touch target is only 24x24pt)
Button {
    dismiss()
} label: {
    Image(systemName: "xmark")
        .frame(width: 24, height: 24)
}

// ✅ COMPLIES WITH LEVEL 1 (Visual glyph is 16pt, but hit-testing target is 44x44pt)
Button {
    dismiss()
} label: {
    Image(systemName: "xmark")
        .font(.system(size: 16, weight: .semibold))
        .foregroundStyle(.secondary)
        .frame(width: 44, height: 44) // Explicit minimum hit area
        .contentShape(Rectangle())    // Ensures clear hit-testing
}
```

---

### Level 2: Official Apple Recommendation
Documented directly in the Apple Human Interface Guidelines as the official, intended way to build native experiences.

- **Examples**:
  - Use `NavigationSplitView` instead of custom multi-column hacks for iPadOS and macOS.
  - Use semantic colors (`Color(uiColor: .systemBackground)`, `.secondaryLabel`, `.tint`) rather than hardcoded hex values.
  - Use standard typography text styles (`.title`, `.headline`, `.body`) to ensure automatic Dynamic Type support.
  - Avoid custom tab bars that recreate system tab bars poorly; use SwiftUI `TabView`.

```swift
// ❌ FAILS LEVEL 2 (Hardcoded hex values break in Dark Mode and ignore High Contrast)
Text("Account Settings")
    .foregroundColor(Color(hex: "#1A1A1A"))
    .background(Color(hex: "#F5F5F7"))

// ✅ COMPLIES WITH LEVEL 2 (Semantic styles automatically adapt to Light, Dark, and Contrast modes)
Text("Account Settings")
    .foregroundStyle(.primary)
    .background(Color(uiColor: .systemGroupedBackground))
```

---

### Level 3: Platform Convention
Unwritten or conventional rules that users have internalized over years of using Apple devices. Violating these makes the app feel "foreign" or like a lazy web port.

- **Examples**:
  - **Pull-to-refresh**: Available on chronological or feed-like lists, but not on static forms.
  - **Back navigation gesture**: Interactive edge-swipe from the leading edge to pop a navigation stack. Never disable this gesture unless handling conflicting canvas drawing gestures.
  - **Destructive Actions**: Placed at the bottom of action sheets on iPhone, colored `.red` (`role: .destructive`), and requiring confirmation if data loss is permanent.
  - **Form Alignment**: Section titles in grouped lists should be concise, uppercase/capitalized consistently, and aligned with standard section headers.

```swift
// ❌ FAILS LEVEL 3 (Disables interactive pop gesture and replaces standard navigation back)
.navigationBarBackButtonHidden(true) // Forcing custom button often breaks edge-swipe gesture!

// ✅ COMPLIES WITH LEVEL 3 (Native toolbar items preserving system gestures)
.toolbar {
    ToolbarItem(placement: .topBarLeading) {
        // Standard back or dismiss button
    }
}
```

---

### Level 4: Community Best Practice
Architecture, state management, and code organization patterns validated across the professional Swift and iOS engineering ecosystem.

- **Examples**:
  - Prefer the **Observation framework** (`@Observable`) over `ObservableObject` and `@Published` in iOS 17+.
  - Modularize view hierarchies into small, reusable structs rather than massive monolithic views with deep closures.
  - Encapsulate design tokens into type-safe namespaces (e.g., `DesignSystem.Spacing.medium`).
  - Write testable domain logic using Swift Testing (`@Test`, `#expect`) or XCTest without coupling views directly to network singletons.

```swift
// ❌ FAILS LEVEL 4 (Monolithic view with embedded networking, impossible to test or preview)
struct UserProfileView: View {
    @State private var userData: [String: Any] = [:]
    
    var body: some View {
        VStack {
            // 200 lines of inline UI logic and URLSession calls
        }
    }
}

// ✅ COMPLIES WITH LEVEL 4 (Modern Observation, dependency-injected model, testable and previewable)
@Observable
@MainActor
final class ProfileViewModel {
    private(set) var user: User?
    private let userService: UserServiceProtocol
    
    init(userService: UserServiceProtocol) {
        self.userService = userService
    }
    
    func load() async {
        user = try? await userService.fetchCurrentUser()
    }
}
```

---

### Level 5: Design Engineering Recommendation
Advanced craftsmanship principles (advocated by design engineers like Emil Kowalski, Apple Design Award winners, and motion specialists) that elevate a functional app into an extraordinary, tactile experience.

- **Examples**:
  - **Spring Physics**: Use `.spring(.snappy)` or `.spring(.bouncy)` over linear or basic easing.
  - **No `scale(0)` pops**: Animate scale from `0.85` or `0.9` to `1.0` combined with opacity fade for grounded entry transitions.
  - **Haptic Tactility**: Trigger `.sensoryFeedback(.selection, trigger:)` when a picker snaps into place or a tab switches.
  - **Micro-interactivity**: Interactive card presses that scale down subtly (`0.98`) with spring recovery when depressed.

```swift
// ❌ FAILS LEVEL 5 (Linear animation and scale(0) feels abrupt, robotic, and unpolished)
withAnimation(.linear(duration: 0.3)) {
    isPresented.toggle()
}
// with: .scaleEffect(isPresented ? 1.0 : 0.0)

// ✅ COMPLIES WITH LEVEL 5 (Subtle, physical spring with realistic scale entry and haptic feedback)
withAnimation(.spring(response: 0.32, dampingFraction: 0.82)) {
    isPresented.toggle()
}
// with:
.scaleEffect(isPresented ? 1.0 : 0.92)
.opacity(isPresented ? 1.0 : 0.0)
.sensoryFeedback(.impact(weight: .light), trigger: isPresented)
```

---

## 3. Decision Matrix for AI Agents

When advising a developer or proposing code changes:

| Level | Classification | Language to Use | Enforcement |
| :--- | :--- | :--- | :--- |
| **Level 1** | Requirement | *"Must", "Required by App Store / HIG / Runtime"* | Strict rejection if violated |
| **Level 2** | Recommendation | *"Apple HIG recommends", "The standard pattern is"* | Highly encouraged, explain exceptions |
| **Level 3** | Convention | *"Apple platform convention expects", "iOS users anticipate"* | Recommend unless custom branding requires departure |
| **Level 4** | Best Practice | *"Architectural best practice suggests", "Modern Swift pattern"* | Adapt to existing codebase architecture |
| **Level 5** | Design Engineering | *"To elevate polish and tactile feel", "Recommended motion refinement"* | Polish enhancement; make optional |
