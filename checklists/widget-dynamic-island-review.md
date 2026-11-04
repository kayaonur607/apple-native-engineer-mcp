# WidgetKit & Dynamic Island Review Checklist

Use this checklist to audit WidgetKit extensions, ActivityKit Live Activities, and Dynamic Island presentations against Apple Human Interface Guidelines and App Store Review standards.

---

## 1. Widget Design & Glanceability
- [ ] **Focused Purpose**: Each widget displays a single, focused piece of actionable information rather than trying to replicate the full app.
- [ ] **Adaptive Sizes**: Supported widget sizes (`systemSmall`, `systemMedium`, `systemLarge`) adapt their layout intelligently without clipped labels or overlapping components.
- [ ] **Accurate Previews**: All widgets provide placeholder previews (`TimelineProvider.placeholder()`) that render cleanly before remote data loads.
- [ ] **Deep Links**: Tapping the widget opens the specific item or screen in the main app via `.widgetURL()` or `Link`.
- [ ] **Interactive Widgets (iOS 17+)**: Any interactive buttons or toggles use `AppIntent` and provide instant visual feedback without launching the app into foreground.

---

## 2. Dynamic Island & Live Activities (ActivityKit)
- [ ] **Compact State Elegance**: `compactLeading` and `compactTrailing` are concise and legible in the approx 50x20pt space.
- [ ] **Minimal State Resilience**: When multiple activities are running, the `minimal` circle displays a clear identifiable icon or progress ring.
- [ ] **Expanded Presentation Ergonomics**: The expanded long-press view fits comfortably without content overflowing past the screen edges.
- [ ] **No Unsolicited Advertising**: Complies strictly with App Store Review Guideline 4.5.4—no marketing, promotional offers, or unsolicited spam in Live Activities.
- [ ] **Stale Date Management**: Live Activities define a reasonable `staleDate` so expired events do not display outdated states indefinitely.
- [ ] **End Activity Properly**: Completed tasks call `activity.end(dismissalPolicy:)` rather than lingering on the Lock Screen indefinitely.

---

## 3. StandBy & Lock Screen
- [ ] **StandBy Mode Optimization**: Tested with device horizontally placed on charger; high-contrast elements adapt cleanly to StandBy night mode.
- [ ] **Accessory Families**: If supporting Lock Screen widgets (`accessoryCircular`, `accessoryRectangular`, `accessoryInline`), content looks sharp in monochrome/tinted rendering.
- [ ] **Data Redaction**: Sensitive personal info is masked when the device is locked using `.privacySensitive()`.
