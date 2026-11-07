---
description: "Design and build one new native screen end to end: states, HIG research, SwiftUI implementation, review and captured evidence."
---

# New native screen

Turn a screen idea into shipped-quality SwiftUI. Ask only for what changes the next action: which platform(s),
the user's job on this screen, and the data it shows.

## 1. Define before drawing

- **Job**: one sentence — what the person accomplishes here.
- **Entry and exit**: how they arrive (tab, push, sheet, deep link) and leave.
- **States**: loading, empty, error, partial, success, offline; editing and destructive confirmation if relevant.
- **Content hierarchy**: the one thing that must be seen first; everything else is secondary.

## 2. Research

1. `inspect_apple_project` for platform and deployment floor.
2. `search_apple_guidelines` for the pattern (e.g. "lists", "search", "onboarding", "settings") and every component;
   read them with `find_apple_guidelines`. Match the platform reference (`apple-native://references/iphone-design`,
   `ipad-design`, `macos-design`, `watchos-design`, `tvos-design`, `visionos-spatial-design`, `iphone-duo-design`).
3. Verify APIs with `inspect_apple_api_availability`; check symbols with `validate_sf_symbols`.

## 3. Build with Apple's defaults

- System containers: `NavigationStack`/`NavigationSplitView`, `List`/`Form`, `.toolbar`, `.searchable`, `.sheet`.
- Text styles and semantic colours; spacing from the layout margins; no fixed text frames.
- Liquid Glass from system bars and controls; custom `glassEffect` only for floating controls, behind `#available`.
- Motion: system springs, respect Reduce Motion; haptics via `.sensoryFeedback` for meaningful events.
- Accessibility: labels, values, hints, grouped elements, 44 pt targets (60 pt visionOS), Dynamic Type to AX5.
- Every string localizable; layout mirrors in right-to-left languages.
- `#Preview` for each state with deterministic sample data.

## 4. Verify

`review_diff` → build → capture the screen in light, dark, a large text size and a right-to-left locale with
`capture_screenshots` (add a `-screen` launch argument route) → look at the images and fix what you see.

## Report

Answer in the user's language with: outcome · files changed · checks actually run (tool + finding codes, build
command and result, simulator/device runs) · Apple sources with URLs · what remains unverified · next action.
Static findings are not a build; a build is not a runtime check; neither is App Review approval.
