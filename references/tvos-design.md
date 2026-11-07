# tvOS Design & Engineering

> **Authority**: [Human Interface Guidelines — Designing for tvOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-tvos),
> [Focus and selection](https://developer.apple.com/design/human-interface-guidelines/focus-and-selection),
> [Remotes](https://developer.apple.com/design/human-interface-guidelines/remotes),
> [Layout › tvOS](https://developer.apple.com/design/human-interface-guidelines/layout),
> [Top Shelf](https://developer.apple.com/design/human-interface-guidelines/top-shelf),
> [App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons).
> Retrieved 2026-11-07 with `find_apple_guidelines`. Re-read the live page before quoting a number.

Apple TV is a ten-foot, shared, lean-back screen driven by a remote. People sit eight feet or more away, use a
clickpad and touch surface instead of a pointer, and often stay in one app for hours. Everything that follows is a
consequence of those three facts.

---

## 1. The non-negotiables

| Rule | Why | How to verify |
| :--- | :--- | :--- |
| Every interactive element is reachable by **focus** | There is no pointer; focus *is* the cursor | Navigate the whole app with the Siri Remote in the Apple TV simulator (arrow keys) |
| Inset primary content **60 pt top/bottom, 80 pt sides** | TV overscan and compatibility settings crop the edges | Inspect the layout at 1920×1080 points |
| Supply artwork for the **focused (larger) size** | Focus scales items up; undersized art blurs | Check image pixel sizes against the focused frame |
| Leave **space around focusable items** | A focused item grows and must not overlap neighbours or text | Focus each row's first and last item |
| **Back/Menu** returns to the parent screen; at the root it exits to the Home Screen | Standard remote behaviour people rely on in every app | Press Back from every screen |
| No ads or prices in **Top Shelf** | People put your app there because they already chose it | Review Top Shelf content |

---

## 2. Focus

Focusable items have up to five visually distinct states: **unfocused, focused, highlighted (being chosen),
selected, unavailable**. Focus elevates, illuminates and gently animates the item; do not draw your own focus ring
on standard controls.

- In SwiftUI, standard `Button`, `NavigationLink`, `Toggle` and card-style buttons are focusable automatically.
  Use `.focusable()` only for custom views that must take focus, and `@FocusState` / `.focused(_:)` to move it.
- Use `.focusSection()` to make a group a single focus target for directional movement, so swiping toward a
  sparse column lands on its nearest item instead of skipping it.
- In a full-screen experience (video, photo), gestures act on the content, not on focus; do not show focus there.
- Do not display a pointer for menus. A pointer is acceptable only inside gameplay that genuinely needs one.

```swift tvOS
struct ShelfRow: View {
    let items: [String]
    var body: some View {
        ScrollView(.horizontal) {
            LazyHStack(spacing: 48) {
                ForEach(items, id: \.self) { item in
                    Button(item) {}
                        .buttonStyle(.card)
                }
            }
            .padding(.horizontal, 80)
        }
        .focusSection()
    }
}
```

(`.buttonStyle(.card)` exists on tvOS only.)

---

## 3. Remote and gestures

- Use standard gestures for standard actions: swipe to move focus, press (click) to choose, Play/Pause for media.
- **Press is intentional; tap is not.** People rest a thumb on the touch surface, pick the remote up and hand it
  over. Ignore stray taps during live video playback.
- Positional taps (up/down/left/right on the touch surface) are fine when they are discoverable and contextual.
- Custom gestures belong in games. Elsewhere they are something people must discover and remember.
- Also support game controllers where gameplay exists, and Siri where search or playback benefit.

---

## 4. Layout, type and colour

- Design at 1920×1080 points (rendered 4K on Apple TV 4K). Content outside the 60/80 pt safe area may be cropped.
- Grids: keep column spacing consistent; add vertical space for titled rows so a focused item never collides with
  the next title; keep partially visible offscreen content symmetrical on both sides.
- **SF Pro** is the system font; **New York** is available. Use text styles — tvOS sizes are already tuned for
  viewing distance; do not shrink them for density.
- Prefer dark, content-forward layouts with edge-to-edge artwork. Test light appearance too if the app supports it.
- Liquid Glass applies across Apple platforms; use system components and test focus states on glass surfaces.

---

## 5. System experiences

| Experience | What to do |
| :--- | :--- |
| **Top Shelf** | Provide a Top Shelf extension: carousel actions/details templates with Play and More Info, or sectioned/inset content. Feature new or in-progress content; avoid ads and prices. |
| **TV app integration** | Media apps should integrate with the TV app (Up Next, playback handoff). |
| **Multiuser** | Make sign-in easy and rare, handle shared sign-in, and switch profiles when the viewer changes. |
| **SharePlay** | Watching together is a native expectation for media apps. |
| **Picture in Picture** | Long sessions are common; support PiP for video. |

---

## 6. Icons and App Store assets

| Asset | Specification |
| :--- | :--- |
| App icon | Layered **parallax** image stack, **2–5 layers**, layout size **800×480 px**, rectangular with concentric rounded corners. Keep a safe zone: the system crops edges as the icon scales and sways. Put any text on the top layer. |
| Image stacks | Built in Xcode's asset catalog (not Icon Composer). Preview parallax with Apple's Parallax Previewer. |
| Screenshots | **1920×1080 or 3840×2160 px**, required for Apple TV apps (`get_app_store_specs platforms=["tvOS"]`). |
| App previews | Landscape only, 1920×1080, 15–30 s. |

---

## 7. Review loop with this server

1. `search_apple_guidelines query="tvos"` → read `designing-for-tvos`, `focus-and-selection`, `remotes`, `top-shelf`.
2. `inspect_apple_project` → confirm `TVOS_DEPLOYMENT_TARGET` and the tvOS target exist.
3. Implement with focus in mind; `review_diff` on changed Swift files.
4. Capture: `capture_screenshots` with device `apple-tv` (Apple TV 4K simulator) → `audit_screenshots platforms=["tvOS"]`.
5. `plan_distribution method="app-store" platform="tvOS"` for archive and upload.

Static tools cannot judge focus movement. Report focus navigation as **not verified** unless it was exercised in
the simulator or on a device.
