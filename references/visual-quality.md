# Visual Verification & UI Quality Protocol

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

A layout is not verified because the code looks right. It is verified because you looked at four renders and
measured them. This page is the measurement procedure: what to render, how to render it, and what to look at.

---

## 1. The four renders

Every screen ships in four states. Not three.

| Render | Why it breaks layouts |
| :--- | :--- |
| Light | The default; least likely to reveal contrast problems |
| Dark | Materials invert, alpha-based colours lose contrast, elevation disappears |
| Largest accessibility size | 3× type. Horizontal stacks stop fitting. Truncation appears |
| RTL locale (Arabic or Hebrew) | Every `.leading` becomes `.trailing`; asymmetric padding flips; icons point the wrong way |

Add a fifth when the screen is dense: **Increase Contrast**. It is the one that catches decorative greys used as
information.

If you have not looked at all four, the screen is not done. Say so rather than claiming otherwise.

---

## 2. The preview matrix that compiles

```swift
#Preview("Light") {
    ProfileView()
        .preferredColorScheme(.light)
}

#Preview("Dark") {
    ProfileView()
        .preferredColorScheme(.dark)
}

#Preview("AX5") {
    ProfileView()
        .dynamicTypeSize(.accessibility5)
}

#Preview("RTL, Arabic") {
    ProfileView()
        .environment(\.layoutDirection, .rightToLeft)
        .environment(\.locale, Locale(identifier: "ar"))
}

#Preview("Compact width") {
    ProfileView()
        .environment(\.horizontalSizeClass, .compact)
}
```

`.dynamicTypeSize(_:)` also takes a range — `.dynamicTypeSize(...DynamicTypeSize.accessibility3)` clamps a
subtree, which is legitimate for chrome (a tab bar label) and never for body content.

**Increase Contrast cannot be set from a preview.** `EnvironmentValues.colorSchemeContrast` is get-only in the
iOS 27.2 SDK:

```text
public var colorSchemeContrast: ColorSchemeContrast { get }
```

So `.environment(\.colorSchemeContrast, .increased)` does not compile. Read it, never write it:

```swift
@Environment(\.colorSchemeContrast) private var contrast
```

Toggle the real setting in the Simulator (§3) or in Settings → Accessibility → Display & Text Size.

---

## 3. Simulator commands that work

`xcrun simctl ui` takes three options and no others: `appearance`, `increase_contrast`, `content_size`.

```bash
# Appearance
xcrun simctl ui booted appearance dark
xcrun simctl io booted screenshot /tmp/dark.png

# Increase Contrast — the setting previews cannot reach
xcrun simctl ui booted increase_contrast enabled
xcrun simctl io booted screenshot /tmp/contrast.png
xcrun simctl ui booted increase_contrast disabled

# Dynamic Type: the valid names are the content-size categories, not "AX3"
xcrun simctl ui booted content_size accessibility-extra-extra-extra-large
xcrun simctl io booted screenshot /tmp/ax5.png
xcrun simctl ui booted content_size large
```

`xcrun simctl ui booted font-size accessibility-XXXL` is not a command. Run `xcrun simctl ui booted` with no
arguments and the tool prints the accepted values — cheaper than guessing.

RTL: launch with `-AppleLanguages "(ar)"` and `-AppleLocale ar` as launch arguments, because `layoutDirection`
alone flips layout without translating strings, and Arabic text is longer than the English you designed around.

---

## 4. The screenshot review checklist

Apply these to a rendered image, in this order. Each one is measurable, so two reviewers should agree.

| # | Check | Pass | Fail means |
| :--- | :--- | :--- | :--- |
| 1 | **Leading edges** | Every label in a group starts on one vertical line | Two different leading values → nothing aligns, eye has no path |
| 2 | **Spacing rhythm** | Every gap on the 4/8 scale | 8.5, 11, 13 → accidental values, layout was nudged not designed |
| 3 | **Weight ladder** | ≤3 distinct font weights on one screen | Four weights means hierarchy is being shouted |
| 4 | **Radius count** | ≤2 distinct corner radii | Three radii read as three unrelated systems |
| 5 | **Truncation** | No `…` except fixed-format values (IDs, timestamps) | `A11Y011` — a label that truncates at AX5 hides content |
| 6 | **Tap targets** | Every glyph sits inside a 44pt square | `A11Y020` — the visible glyph is not the tappable area |
| 7 | **Greyscale test** | Desaturate the image; every state still distinguishable | Status encoded in hue alone → fails Differentiate Without Colour |
| 8 | **Contrast, sampled** | Sample the *rendered pixel*, run the ratio | The token passed on paper; the material behind it did not |
| 9 | **Baseline** | Symbol and text share a baseline in every row | Hand-built `HStack` instead of `Label` |
| 10 | **Orphans** | No single word on the last line of a heading | Heading wrapped at a size you did not test |

Check 8 is the one that catches what code review cannot. A label on `.regularMaterial` has no fixed background,
so compute the ratio against the worst pixel behind it, not against the average.

---

## 5. Density, optical alignment, restraint

Three judgement calls that the checklist cannot settle. Argue them from the content, not from taste.

**Density follows the task, not the device.** A settings screen has one decision per row. A dashboard has many
values per row. If every element on the screen has the same weight, there is no hierarchy — the reader has to
read everything to find anything. Pick the one thing the screen is for and let it win.

**Optical alignment beats mathematical alignment.** A round glyph aligned to a square text stem looks inset. A
label aligned to a chevron looks off-centre because the chevron is heavier. Correct the glyph, not the row:

```swift
// ✅ The system aligns symbol to text; do not hand-tune the HStack
Label("Library", systemImage: "books.vertical")

// ❌ Hand-built row drifts by a point or two at every Dynamic Type size
HStack(spacing: 6) {
    Image(systemName: "books.vertical")
    Text("Library")
}
```

**Restraint is subtraction.** Before adding a divider, ask whether the 12pt gap already separates the groups. It
usually does. The HIG's *Layout* page lists negative space first, container shapes second, separator lines third —
that order is the guidance.

A screen that survives all ten checks and still feels busy has one element too many. Remove it and look again.

---

## 6. Automating the pass

Snapshot tests — `swift-snapshot-testing`, or a plain `xcrun simctl io booted screenshot` plus an image diff —
catch regressions, not mistakes. A snapshot of a bad layout is a stable bad layout. Run them *after* the manual
pass, not instead of it.

```bash
# A CI loop that captures the four states in one run
for state in "light:light:large" "dark:dark:large" \
             "ax5:light:accessibility-extra-extra-extra-large"; do
  IFS=: read -r name appearance size <<< "$state"
  xcrun simctl ui booted appearance "$appearance"
  xcrun simctl ui booted content_size "$size"
  xcrun simctl io booted screenshot "/tmp/$name.png"
done
```

`tools/screenshot-studio` exists for the App Store asset pass, not for layout review. Keep the two separate: one
produces marketing screenshots, the other produces evidence.

---

## 7. Integrity rule

If you are running headless — no Simulator, no previews, no image tool — you cannot verify a layout. Then:

1. State plainly that the render was not inspected.
2. Hand over the `#Preview` block and the `simctl` commands above so a human can look.
3. Do a static pass and label it as static: `frame`/`padding` values, `lineLimit`, `dynamicTypeSize` usage,
   `.leading` vs `.left`, and the contrast of any literal colour.
4. Do not write "verified", "looks good", or "responsive" about a screen you have not seen.

Claiming visual verification without a render is the single most damaging thing an agent can do to its own
credibility. The checklist above is worth more when you say which items you could not run.

---

## 8. Sources

- Apple HIG, *Layout* — <https://developer.apple.com/design/human-interface-guidelines/layout>
- Apple HIG, *Accessibility* — <https://developer.apple.com/design/human-interface-guidelines/accessibility>
- Apple HIG, *Dark Mode* — <https://developer.apple.com/design/human-interface-guidelines/dark-mode>
- `SwiftUICore` iOS 27.2 — `EnvironmentValues.colorSchemeContrast` (get-only), `.dynamicTypeSize(_:)`,
  `.preferredColorScheme(_:)`
- `xcrun simctl ui --help` on Xcode 27.2 — three supported options: `appearance`, `increase_contrast`, `content_size`
- Contrast maths: `tools/lib/apple_native/colors.py`
