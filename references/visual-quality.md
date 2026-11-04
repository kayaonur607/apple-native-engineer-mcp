# Visual Verification & UI Quality Protocol

High-fidelity Apple development demands rigorous visual verification across diverse screen sizes, orientations, Dynamic Type settings, and appearance modes. AI coding assistants must adhere to strict verification standards and never claim a layout has been visually validated unless rendered output (Previews, Simulator screenshots, or snapshot tests) was inspected.

---

## 1. The Xcode Previews Testing Matrix

Use Xcode's `#Preview` macro to render views under all environmental variations simultaneously:

```swift
#Preview("Light Mode - iPhone 16") {
    UserProfileView()
        .preferredColorScheme(.light)
}

#Preview("Dark Mode - iPhone 16") {
    UserProfileView()
        .preferredColorScheme(.dark)
}

#Preview("Accessibility Text Size (AX3)") {
    UserProfileView()
        .environment(\.dynamicTypeSize, .accessibility3)
}

#Preview("High Contrast Mode") {
    UserProfileView()
        .environment(\.colorSchemeContrast, .increased)
}

#Preview("iPad Split View") {
    UserProfileView()
        .environment(\.horizontalSizeClass, .regular)
}
```

---

## 2. Systematic Visual Inspection Checklist

When inspecting rendered previews or simulator screenshots, audit for the following flaws:

| Flaw Category | Inspection Criteria |
| :--- | :--- |
| **Typographic Truncation** | Ensure text does not display ellipsis (`...`) unexpectedly when font scales up. |
| **Safe Area Clipping** | Verify buttons do not touch the screen bezel, Home Indicator, or Dynamic Island. |
| **Material Glare** | In Dark Mode, confirm that translucent materials do not cause low-contrast gray wash over text. |
| **Corner Radius Squircing** | Confirm all rounded cards use continuous corners (`style: .continuous`) to avoid harsh curvature transitions. |
| **Alignment Grids** | Verify all left-aligned labels share identical leading padding (standard is 16pt or 20pt). |
| **Touch Boundaries** | Verify that icon buttons have minimum 44×44pt hit bounds even if the glyph is 16pt. |

---

## 3. Simulator Automation & Snapshot Testing

In automated CI/CD pipelines, capture and verify simulator screenshots using `xcrun simctl` or snapshot testing:

```bash
# Capture screenshot from running iOS Simulator
xcrun simctl io booted screenshot /tmp/screen_light.png

# Switch simulator to Dark Mode and capture
xcrun simctl ui booted appearance dark
xcrun simctl io booted screenshot /tmp/screen_dark.png

# Set Accessibility Dynamic Type size
xcrun simctl ui booted font-size accessibility-XXXL
xcrun simctl io booted screenshot /tmp/screen_ax3.png
```

---

## 4. Integrity Rule for AI Assistants

**CRITICAL**: If you are operating in a terminal or headless sandbox without access to a running macOS Simulator, Xcode Previews, or image inspection tools:
1. **Explicitly state that visual screenshot rendering could not be performed directly.**
2. Provide the exact preview code and `xcrun simctl` commands so the developer can verify the layout in Xcode.
3. Perform static structural analysis of the SwiftUI view code (checking frames, paddings, dynamic type bindings, and safe area modifiers).
