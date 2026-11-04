# iPhone Design & Ergonomics Review Checklist

Use this checklist to systematically review an iPhone application or screen for adherence to Apple native handheld ergonomics and technical requirements.

---

## 1. Ergonomics & Reachability
- [ ] **Thumb Reach Zone**: Primary calls-to-action (e.g. "Continue", "Buy", "Submit") are located within the bottom 40% of the screen.
- [ ] **Interactive Pop Gesture**: The system edge-swipe back navigation gesture is fully functional and not disabled by custom navigation bar overlays.
- [ ] **One-Handed Usability**: Destructive or critical confirmation buttons can be tapped with one thumb without awkward hand repositioning.
- [ ] **Search Positioning**: Search bars are positioned at the top of scrollable lists and reveal/collapse naturally during scroll via `.searchable()`.

---

## 2. Safe Area Insets & Hardware Boundaries
- [ ] **Home Indicator Clearance**: Bottom action buttons, tab bars, and sticky footers have adequate bottom padding and do not collide with the Home Indicator.
- [ ] **Dynamic Island & Sensor Housing**: Headers, floating status chips, and custom toolbars maintain clearance below the status bar and Dynamic Island.
- [ ] **Background Bleed**: Background materials and canvas colors bleed into the safe area (`.ignoresSafeArea()`), while all interactive text and controls remain strictly within safe boundaries.
- [ ] **Landscape Mode**: If landscape orientation is supported, side margins account for the sensor notch cutout and home indicator repositioning.

---

## 3. Touch Targets & Hit Boundaries
- [ ] **44×44pt Minimum**: Every button, icon toggle, close cross, and interactive cell has a hit-testing frame of at least 44×44pt.
- [ ] **Hit Testing Precision**: Small icons (e.g. 18pt SF Symbols) use `.contentShape(Rectangle())` to ensure the entire 44pt bounding box responds to touch.
- [ ] **Spacing Between Interactive Elements**: Adjacent buttons maintain at least 8pt to 12pt separation to prevent accidental erroneous taps.

---

## 4. Modal Ergonomics & Sheets
- [ ] **Presentation Detents**: Secondary workflows (filters, comments, options) present as bottom sheets with `.presentationDetents([.medium, .large])` rather than blocking full-screen covers.
- [ ] **Drag Indicator**: Sheets with multiple detents display a visible drag handle (`.presentationDragIndicator(.visible)`).
- [ ] **Dismiss Affordance**: Modals offer both a dedicated "Done" / "Cancel" toolbar button and interactive pull-down-to-dismiss behavior.

---

## 5. Keyboard & Input Handling
- [ ] **Scroll Dismissal**: Scroll views use `.scrollDismissesKeyboard(.interactively)`.
- [ ] **Input Visibility**: When the virtual software keyboard appears, the active text field smoothly animates into view without being obscured.
- [ ] **Numeric Keypad Toolbars**: Text fields using `.numberPad` or `.phonePad` include a toolbar accessory with a "Done" button to dismiss the keyboard.
