# iPhone Duo Design & Engineering

> **Authority**: [Human Interface Guidelines — Designing for iPhone Duo](https://developer.apple.com/design/human-interface-guidelines/designing-for-iphone-duo),
> [Preparing your app for iPhone Duo](https://developer.apple.com/documentation/technologyoverviews/preparing-your-app-for-iphone-duo),
> [Screenshot specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications).
> Retrieved 2026-11-07. This is a new form factor: re-read the live pages with `find_apple_guidelines
> page="designing-for-iphone-duo"` and verify every API with `inspect_apple_api_availability` before using it.

iPhone Duo has an **outer display** (used closed) and an **inner display** (used open), each with its own
front camera, joined by a center **hinge**. It is still an iPhone: everything in [iPhone design](iphone-design.md)
applies. What changes is that one app now runs at many sizes and poses.

---

## 1. Build to resize — the whole strategy

- Use **size classes**: compact width on the outer display, regular width on the inner display. Those two layouts
  cover every pose (book, flat, standing on an edge). Do not design one layout per pose.
- Lay out with layout margins and safe-area insets. **No fixed widths, no display-specific checks.**
- Keep functionality and state identical across displays and poses. Show one *extra* level of hierarchy on the
  inner display when it helps (Mail: list *or* message closed; list *and* message open).
- Games: lock to one orientation if needed, but fill the screen in every pose; prefer changing aspect ratio over
  letterboxing; if you must letterbox, put artwork in the padding.
- Preview poses in Xcode's **Device Hub**, and run the **iPhone Duo** simulator (`xcrun simctl list devicetypes`).

---

## 2. Vertical controls

On the outer display (and the inner display in landscape) the system moves the **status bar, Dynamic Island,
toolbar and tab bar to the side**, preserving vertical space. The inner display in portrait keeps horizontal bars.
Standard components do this automatically.

| Guidance | Detail |
| :--- | :--- |
| Don't override default bar placement | Side controls are a core platform pattern |
| Account for asymmetry | Content area is uneven; rely on safe areas, including controls on the opposite edge in Split View |
| Placement order | Top of the vertical axis: Back/Close, then prominent actions (Done); keep remaining groups intact |
| Prioritize items | Items overflow bottom-to-top; set visibility priority (`ToolbarItemVisibilityPriority` / `UIBarButtonItemVisibilityPriority`) |
| Title **and** symbol | Give every non-text toolbar item both; the system chooses per context and uses titles in overflow |
| Few text buttons | Text labels stay in horizontal bars; prefer symbols |
| Group, don't space | `ToolbarItemGroup` / `UIBarButtonItemGroup` adapt spacing; never add fixed spacers |
| Keep controls near content | Controls for a leading pane stay with that pane |
| Compression | Navigation apps keep the tab bar and overflow toolbar items; task apps minimize the tab bar (`ToolbarVerticalCompressionBehavior`) |
| One overflow menu | Move custom overflow into the system menu (`ToolbarOverflowMenu` / `additionalOverflowItems`); ellipsis means overflow only |
| RTL | Vertical controls stay on the same hardware side in right-to-left languages |

Full-width layouts without bars (Calculator) are fine when nothing collides with the Dynamic Island or status bar.

---

## 3. Reserved regions and the fold

Content avoids **reserved regions**:

1. the outer front camera (always present; expands into the Dynamic Island for Live Activities),
2. the inner front camera (only while the camera is active),
3. the **folding region** (when partially open, it splits the inner display into usable regions).

Alerts, context menus and sheets move automatically; split views rebalance columns around the fold. For custom
layouts use **`ReservedRegion`** (SwiftUI) or **`UIView.ReservedRegion`** (UIKit). Prefer an even number of grid
columns so content divides cleanly; make small adjustments rather than rearranging the screen as it folds.

---

## 4. Containers

- **Split views** (`NavigationSplitView`, `UISplitViewController`) expand on the inner display and collapse to one
  pane on the outer display, exactly like regular ↔ compact elsewhere.
- **Arrangement views** (`ArrangementView`, `UIArrangementViewController`) hold a primary and secondary view and
  organize them by size, orientation and reserved regions. *Split* arrangements divide space (horizontal when
  wide, vertical when tall); *overlay* arrangements stack the views and move them to each side when folded.
  Use one where you already have an `HStack`/`VStack` pair (split) or a `ZStack` (overlay). Keep navigation
  containers **outside** arrangement views.

---

## 5. App Store

| Set | Size (portrait / landscape) | Requirement |
| :--- | :--- | :--- |
| iPhone Duo outer display | 1398×2034 / 2034×1398 | Required from **April 2027** for apps built with the **iOS 27.1 SDK or later** |
| iPhone Duo inner display | 2007×2853 / 2853×2007 | Same |

Capture both with `capture_screenshots` on the `iPhone Duo` simulator (`devices: ["iphone-duo-outer"]` resolves
to it); `audit_screenshots platforms=["iOS"]` reports the future requirement as `SHOT024`.

---

## 6. Review checklist

- [ ] No fixed widths; layouts driven by size classes, margins and safe areas
- [ ] Same features and state on outer and inner displays and in every pose
- [ ] Standard bars used; no custom top/bottom bars that fight vertical placement
- [ ] Toolbar items have titles and symbols, grouped, with visibility priorities for key actions
- [ ] Custom content clears reserved regions and the fold; grids use even column counts
- [ ] Split View multitasking tested (controls on each app's outer edge)
- [ ] RTL tested; vertical controls remain on the hardware side
- [ ] Outer and inner App Store screenshots captured (or scheduled before April 2027)

Runtime pose behaviour is **not verified** by static tools. State which poses were exercised in Device Hub, the
simulator or on hardware.
