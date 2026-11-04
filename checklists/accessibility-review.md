# Accessibility (a11y) Review Checklist

Every application deployed to the App Store must be accessible to all users, including those who rely on assistive technologies such as VoiceOver, Dynamic Type, Switch Control, and Voice Control.

---

## 1. Dynamic Type Scaling & Layout Resilience
- [ ] **Standard Text Styles**: All text utilizes standard semantic fonts (`.largeTitle`, `.headline`, `.body`, `.caption`) or custom fonts scaled via `.custom(..., relativeTo:)`.
- [ ] **Accessibility Sizes Testing (AX1–AX5)**: Layout tested at the largest accessibility size without text clipping, truncation into `...`, or horizontal overflowing.
- [ ] **No Rigid Heights**: Containers displaying text do not use hardcoded `.frame(height: N)`. Containers use `.frame(minHeight: N)` and flexible vertical padding.
- [ ] **Adaptive Directionality**: Multi-column or horizontal cards reflow automatically into vertical stacks when Dynamic Type reaches accessibility sizes (`dynamicTypeSize.isAccessibilitySize`).

---

## 2. VoiceOver Navigation & Semantics
- [ ] **Semantic Grouping**: Multi-part information cards combine fragmented child labels into a single unified accessibility element (`.accessibilityElement(children: .combine)`).
- [ ] **Descriptive Labels**: Custom buttons and icon glyphs have clear `.accessibilityLabel()` strings explaining their function.
- [ ] **Accessibility Values**: Steppers, sliders, and toggles report their current state via `.accessibilityValue()`.
- [ ] **Accessibility Hints**: Non-obvious custom interactions provide brief `.accessibilityHint()` guidance.
- [ ] **Accessibility Traits**: Elements carry appropriate traits (`.isButton`, `.isHeader`, `.isSelected`, `.isModal`).
- [ ] **Decorative Elements Hidden**: Purely decorative illustrations, gradient backdrops, and spacer icons are explicitly hidden (`.accessibilityHidden(true)`).

---

## 3. Color Contrast & Visual Accessibility
- [ ] **Body Text Contrast**: Contrast ratio between body text (< 18pt regular) and background meets or exceeds **4.5:1** in both Light and Dark Mode.
- [ ] **Large Text Contrast**: Contrast ratio for large text (≥ 18pt regular or ≥ 14pt bold) meets or exceeds **3:1**.
- [ ] **Differentiate Without Color**: Information communicated by color (e.g. green for success, red for error) is simultaneously reinforced with an icon or clear text label.
- [ ] **High Contrast Mode**: The UI respects `@Environment(\.colorSchemeContrast)` and increases border definitions or background contrast when set to `.increased`.

---

## 4. Motion & Sensory Preferences
- [ ] **Reduce Motion Respected**: All bouncy spring animations and spatial transitions switch to subtle crossfades when `@Environment(\.accessibilityReduceMotion)` is enabled.
- [ ] **No Flashing Content**: No screen elements flash or flicker more than three times per second.
- [ ] **Reduce Transparency Respected**: Translucent materials (`.ultraThinMaterial`) gracefully fall back to high-contrast opaque fills when `@Environment(\.accessibilityReduceTransparency)` is enabled.

---

## 5. Motor & Input Accessibility
- [ ] **44×44pt Touch Boundaries**: Every clickable or tappable component provides at least a 44×44pt hit target.
- [ ] **Full Keyboard Access (FKA)**: When navigated with a hardware keyboard, focused elements display clear system focus rings (`.focused()` / `.focusable()`).
