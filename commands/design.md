---
description: "Review and improve an existing screen against Apple's Human Interface Guidelines: hierarchy, typography, colour, materials, motion and accessibility."
---

# `/apple-native-design` — HIG design review and polish

## 1. Ground the review

1. `inspect_apple_project`, then `lint_swiftui`, `audit_accessibility` and `audit_liquid_glass` on the screen's files.
2. `search_apple_guidelines` for the screen's pattern and components; read them with `find_apple_guidelines`.
3. Read `apple-native://references/visual-quality`, `typography-and-color` and the platform reference.

## 2. Review in this order

1. **Hierarchy** — one primary element; secondary content quieter through type and colour, not boxes.
2. **Layout** — system margins and safe areas; consistent spacing rhythm; no fixed text frames; adapts to every
   size class and Dynamic Type size.
3. **Typography** — text styles only (`.largeTitle` … `.caption2`); `@ScaledMetric` for custom metrics.
4. **Colour** — semantic and asset colours, verified in light, dark and Increase Contrast (WCAG AA).
5. **Materials** — on iOS 26+ Liquid Glass comes from system bars and controls and `glassEffect(_:in:)` behind
   `#available`; below that, a single system material. Never imitate glass with blur and white overlays.
6. **Motion** — system springs, interruptible, Reduce Motion alternatives; `.sensoryFeedback` for meaningful events.
7. **Accessibility** — VoiceOver order, labels, values and traits; 44 pt targets; no information by colour alone.
8. **Localization** — no concatenated strings; right-to-left mirroring with leading/trailing.

## 3. Change and prove

Propose changes with the HIG URL behind each one. After editing, `review_diff`, build, and capture the screen in
light, dark, AX large text and a right-to-left locale with `capture_screenshots`.

## Report

Answer in the user's language with: outcome · files changed · checks actually run (tool + finding codes, build
command and result, simulator/device runs) · Apple sources with URLs · what remains unverified · next action.
Static findings are not a build; a build is not a runtime check; neither is App Review approval.
