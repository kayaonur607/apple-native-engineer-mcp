# Typography & Colour

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Type and colour are the two systems that carry every other decision. Both have a semantic API that already
handles Dark Mode, Increase Contrast, Bold Text and the accessibility type sizes. Using it is less work than
replacing it.

---

## 1. The typeface family, and what `Font.Design` can actually reach

Apple ships two families: **San Francisco** (SF Pro, SF Compact, SF Mono, plus Rounded and the non-Latin
variants) and **New York** (serif). `Font.Design` exposes four cases and no more:

| Design case | Typeface | Use |
| :--- | :--- | :--- |
| `.default` | SF Pro | Everything, unless you have a reason |
| `.rounded` | SF Pro Rounded | Friendly, playful, health and fitness, numeric readouts |
| `.serif` | New York | Editorial, long-form reading, brand voice |
| `.monospaced` | SF Mono | Code, tabular numbers, fixed-width identifiers |

```swift
Text("Balance")
    .font(.system(.largeTitle, design: .rounded, weight: .bold))
```

There is **no `.compact` case**. SF Compact is chosen by the system on watchOS and is not selectable through
`Font.Design` on iOS. Reaching for `.custom("SFCompactText-Regular", …)` is wrong twice: it embeds a system font
the HIG tells you not to embed, and it loses Dynamic Type. Use `.default` and let the platform pick.

**Optical size is automatic.** The HIG's *Typography* page describes the system fonts as variable fonts with
"dynamic optical sizes… a single, continuous design", so there is no Text/Display switch to make. Do not
approximate it with `.fontWidth(_:)` — width is a different axis.

### The width axis

`.fontWidth(_:)` (iOS 16+) takes a `Font.Width`: `.compressed`, `.condensed`, `.standard`, `.expanded`, or
`Font.Width(0.8)` for a custom value.

```swift
// Tabular figures that still fit a narrow column at AX5
Text(amount, format: .number.precision(.fractionLength(2)))
    .font(.body.monospacedDigit().width(.condensed))
```

`Font.width(_:)` and the view modifier `.fontWidth(_:)` are the same axis. Use `.expanded` for a display word,
never for body text: at AX5 you need the horizontal room for the glyphs, not extra tracking.

---

## 2. Text styles, with the real numbers

Sizes are from the HIG *Typography* page, "iOS, iPadOS Dynamic Type sizes". The AX5 column is what makes the
fixed-size argument for you.

| Style | Large (default) | AX5 | Growth |
| :--- | :--- | :--- | :--- |
| `.largeTitle` | 34pt / 41 leading | 60pt / 70 | 1.76× |
| `.title` | 28 / 34 | 58 / 68 | 2.07× |
| `.title2` | 22 / 28 | 56 / 66 | 2.55× |
| `.title3` | 20 / 25 | 55 / 65 | 2.75× |
| `.headline` | 17 / 22 semibold | 53 / 62 | 3.12× |
| `.body` | 17 / 22 | 53 / 62 | 3.12× |
| `.callout` | 16 / 21 | 51 / 60 | 3.19× |
| `.subheadline` | 15 / 20 | 49 / 58 | 3.27× |
| `.footnote` | 13 / 18 | 44 / 52 | 3.38× |
| `.caption` | 12 / 16 | 43 / 51 | 3.58× |
| `.caption2` | 11 / 13 | 40 / 48 | 3.64× |

The smaller the style, the *more* it grows, because legibility has a floor. `caption2` nearly quadruples.

---

## 3. Why a fixed point size is not "just smaller text"

`.font(.system(size: 17))` looks identical to `.body` at the default setting. It is not the same text.

At Large, `.body` is 17pt. At AX5 it is 53pt — 3.12×. A 14-character label such as "Payment method" measures
roughly 116pt at 17pt, so at 53pt it needs roughly 362pt. The usable width inside a 393pt-wide iPhone with 16pt
margins is 361pt. One label now consumes the entire row, and anything sharing it either truncates or pushes off
screen.

A fixed 17pt label stays 17pt and silently becomes the smallest, least readable text on a screen where the user
asked for larger text. That is the failure: not ugliness, unusability.

```swift
// ❌ SWU012, A11Y010: frozen at 17pt while everything around it scales
Text("Payment method").font(.system(size: 17))

// ✅ Scales with the user's setting, and keeps the platform's weight and leading
Text("Payment method").font(.body)

// ✅ A brand face that still scales, relative to a text style
Text("Payment method").font(.custom("Avenir-Medium", size: 17, relativeTo: .body))
```

`.custom(_:size:fixedSize:)` exists and is the wrong tool for UI text — it opts out of Dynamic Type on purpose.

**Never constrain text with `.frame(width:)`** (`SWU005`). Use `maxWidth`, `lineLimit` plus
`minimumScaleFactor`, or let the container decide:

```swift
Text(item.title)
    .fixedSize(horizontal: false, vertical: true)   // grow taller, never truncate sideways
```

---

## 4. Tracking and kerning are not the same axis

| Modifier | Applies | Carries a trailing gap | Use for |
| :--- | :--- | :--- | :--- |
| `.tracking(_:)` | After every character, including the last | Yes | All-caps labels; mockups |
| `.kerning(_:)` | Between character pairs only | No | Any label that must align to an edge |

The system already sets tracking per point size. The HIG publishes the values: at 17pt SF Pro carries
**−0.43pt** of tracking; at 12pt, **0.0**; below 12pt it goes positive (+0.24pt at 6pt) to keep tiny text
legible.

```swift
// ❌ Double-tracked: the system already applies −0.43pt at 17pt
Text("Total").font(.body).tracking(0.4)

// ✅ Tracking for a spaced-out caption; nothing for body copy
Text("AVAILABLE NOW").font(.caption2).tracking(1.2)
```

Because `.tracking` adds a gap after the final glyph, a trailing-aligned label measured with tracking is
visually inset by that gap. Use `.kerning` when the edge matters.

---

## 5. Sizes that are not text

Icons, gaps and glyph boxes need to scale too, or a symbol stays 16pt next to 53pt text. `@ScaledMetric` scales
an arbitrary value against a text style:

```swift
struct StatusRow: View {
    @ScaledMetric(relativeTo: .body) private var glyphSize: CGFloat = 20
    @Environment(\.dynamicTypeSize) private var typeSize

    var body: some View {
        let layout = typeSize.isAccessibilitySize
            ? AnyLayout(VStackLayout(alignment: .leading, spacing: 8))
            : AnyLayout(HStackLayout(spacing: 12))

        layout {
            Image(systemName: "checkmark.seal.fill")
                .font(.body)
                .frame(width: glyphSize, height: glyphSize)
            Text("Verified").font(.body)
        }
    }
}
```

Clamp only chrome, with a range: `.dynamicTypeSize(...DynamicTypeSize.accessibility3)`. Never clamp body content.

---

## 6. Colour: semantic first, asset second, literal never

Three tiers, in order of preference:

1. **Semantic**: `.primary`, `.secondary`, `.background`, `Color(uiColor: .systemGroupedBackground)`.
2. **Asset colour** with Any / Dark / High Contrast appearances.
3. **Literal.** Only for a colour that carries no meaning (a brand mark, a chart series already differentiated
   by shape).

The HIG's *Color* page is explicit about tier 2: "If you define a custom color, make sure to supply light and dark
variants, and an increased contrast option for each variant." That is three slots per colour in the asset
catalog, not one. A single-slot colour is a Dark Mode bug waiting for its first reviewer.

```swift
// ✅ One tint drives buttons, toggles, links and the caret
ContentView().tint(.indigo)

// ✅ A subtle surface derived from the accent instead of another literal, iOS 18+
if #available(iOS 18.0, *) {
    row.background(Color.accentColor.mix(with: Color(uiColor: .systemBackground), by: 0.88))
}
```

`Color.mix(with:by:in:)` is iOS 18+. The fraction is the distance *toward* the second colour, so `by: 0.88`
is 12% accent over the system background. It is the correct way to derive a tinted surface — `.opacity(_:)`
instead reduces alpha, which lets the backdrop through and breaks contrast unpredictably.

**Never encode status in hue alone.** Read the setting instead of assuming:

```swift
@Environment(\.accessibilityDifferentiateWithoutColor) private var noColour

Label("Paid", systemImage: "checkmark.circle.fill")
    .foregroundStyle(noColour ? AnyShapeStyle(.primary) : AnyShapeStyle(Color.green))
```

The glyph carries the meaning; colour is the acceleration. `AnyShapeStyle` is what lets the two branches — a
hierarchical style and a concrete colour — share one modifier.

---

## 7. WCAG maths, with worked numbers

Contrast ratio = `(L1 + 0.05) / (L2 + 0.05)`, where `L` is WCAG relative luminance. Thresholds: **4.5:1** for
body text, **3:1** for large text (≥18pt, or ≥14pt bold). `tools/lib/apple_native/colors.py` implements exactly
this, and `audit_accessibility` reports `A11Y001` / `A11Y002` with the numbers below.

Measured against the system palette, light appearance, white background:

| Colour | Ratio on `#FFFFFF` | Verdict |
| :--- | :--- | :--- |
| `label` `#000000` | 21.00 | Passes everything |
| `secondaryLabel` (60% `#3C3C43` composited) → `#8A8A8E` | **3.44** | Fails 4.5 body; passes 3.0 large |
| `tertiaryLabel` (30% composited) → `#C4C4C7` | **1.74** | Decorative only |
| `systemGray` `#8E8E93` | **3.26** | Fails body text |
| `systemBlue` `#007AFF` | 4.02 | Fails 4.5 as body text |
| `systemIndigo` `#5856D6` | 5.65 | Passes |
| `systemTeal` `#30B0C7` | 2.57 | Icons at 3:1 only if larger than a glyph |
| `systemOrange` `#FF9500` | 2.20 | Never as text on white |
| `systemGreen` `#34C759` | 2.22 | Never as text on white |

In the dark appearance, against `#1C1C1E`: `secondaryLabel` reaches 5.94 and `systemGray` 5.22. The same token
that fails in Light passes in Dark, which is why both must be measured.

Three consequences worth internalising:

- **`.secondary` is de-emphasis, not information.** At body size it measures 3.44:1 in Light. Fine for "Last
  updated 2 min ago"; not fine for the only place a value appears.
- **A tinted accent is not automatically readable text.** `#007AFF` on white is 4.02:1. Coloured body text needs
  a darker variant or a non-text carrier.
- **A coloured dot is not a status.** Pair it with a label or a glyph — and measure the glyph, not the dot.

These are measurements of the light-mode palette at the time of writing. The HIG warns that "actual color values
may fluctuate from release to release", so re-run the auditor rather than trusting the table.

---

## 8. Checklist

- [ ] Zero `.font(.system(size:))` in UI text — text styles or `.custom(_:size:relativeTo:)` only
- [ ] No `.fixedSize` on a font; no `.frame(width:)` on a text-bearing view
- [ ] Every custom colour has Any / Dark / High Contrast slots
- [ ] No colour carries meaning on its own — `accessibilityDifferentiateWithoutColor` respected
- [ ] Contrast measured against the *rendered* background, both appearances
- [ ] `.tracking()` only where a trailing gap is harmless
- [ ] Layout intact at `.accessibility5`, verified in a render
- [ ] `audit_accessibility` clean: no `A11Y001`, `A11Y002`, `A11Y010`, `A11Y011`

---

## 9. Sources

- Apple HIG, *Typography* — <https://developer.apple.com/design/human-interface-guidelines/typography>
- Apple HIG, *Color* — <https://developer.apple.com/design/human-interface-guidelines/color>
- Apple HIG, *Dark Mode* — <https://developer.apple.com/design/human-interface-guidelines/dark-mode>
- `SwiftUICore` iOS 27.2 — `Font.Design`, `Font.Width`, `.fontWidth(_:)`, `ScaledMetric`, `Color.mix(with:by:in:)`
- WCAG 2.2, *Contrast (Minimum)* 1.4.3 — <https://www.w3.org/TR/WCAG22/#contrast-minimum>
