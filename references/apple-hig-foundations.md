# Apple HIG Foundations

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

The Human Interface Guidelines are a specification, not a mood board. Almost every rule in them already has a
SwiftUI default that implements it; the job is to stop overriding that default. This page is the map from HIG
chapter to the API that satisfies it.

---

## 1. How the HIG is organised in 2026

| Section | Pages | What it settles |
| :--- | :--- | :--- |
| Design fundamentals | *Design principles*, *Getting started*, *Designing for macOS*, *Designing for iPhone Duo* | The intent behind every rule |
| Foundations | *Accessibility*, *App icons*, *Color*, *Layout*, *Materials*, *Typography* | Cross-platform rules for the raw materials |
| Components | *Content*, *Menus and actions*, *Navigation and search*, *Presentation*, *Selection and input*, *Status*, *System experiences* | Which control, and why that one |
| Patterns | *Loading*, *Searching*, *Modality*, *Settings*, *Onboarding*, *Feedback*, *Undo and redo* | Multi-screen behaviour |
| Inputs, Technologies | *Gestures*, *Pointing devices*, *Widgets*, *Live Activities* | Platform capability |

There is no *Motion* page in Foundations any more. Motion guidance lives in *Feedback* and in the Liquid Glass
material guidance. Quote the page you actually read.

---

## 2. The eight principles, and what they cost in code

The HIG's current *Design principles* page lists eight. Each one rules out a specific habit.

| Principle | HIG wording | The habit it rules out |
| :--- | :--- | :--- |
| Purpose | "Make something meaningful." | Feature parity with a competitor nobody asked for |
| Agency | "Let people do things their own way." | Onboarding that traps the user in a wizard |
| Responsibility | "Act in people's best interest." | Permission prompts with no rationale string |
| Familiarity | "Build on what people know." | A bespoke tab bar that behaves almost-but-not-quite like `TabView` |
| Flexibility | "Adapt to diverse contexts and needs." | A layout that only survives one size class |
| Simplicity | "Be clear and direct." | Three equally-weighted buttons in one toolbar |
| Craft | "Care about every detail." | A 0.5pt stroke in one card and 1pt in the next |
| Delight | "Make it human." | Motion on every tap, including the 40th item in a list |

Clarity, deference and depth were the iOS 7 framing. They are not on the current page. Use the eight.

---

## 3. Hierarchy comes from type and space, not from boxes

This is the rule that separates native from web-port. Before adding a card, border or shadow, ask what the
grouping looks like with 8 more points of space and a `.secondary` label.

```swift
// ✅ Grouping from type and space
VStack(alignment: .leading, spacing: 8) {
    Text("Balance")
        .font(.footnote)
        .foregroundStyle(.secondary)
    Text(balance, format: .currency(code: "USD"))
        .font(.largeTitle.bold())
        .contentTransition(.numericText())
}

// ❌ Grouping from a box: three decorations to say what spacing already says
VStack(alignment: .leading, spacing: 8) {
    Text("Balance").font(.footnote).foregroundStyle(.secondary)
    Text(balance, format: .currency(code: "USD")).font(.largeTitle.bold())
}
.padding(16)
.background(Color(uiColor: .secondarySystemBackground))
.clipShape(RoundedRectangle(cornerRadius: 12))
.overlay(RoundedRectangle(cornerRadius: 12).stroke(.quaternary))
.shadow(radius: 8)   // SWU020
```

The HIG's *Layout* page says it directly: "you might use negative space, container shapes, or separator lines to
show which elements are related". Negative space is listed first. Reach for it first.

**When a container is correct:** a row that must be distinguishable while scrolling (a message bubble, a photo
tile), or content that sits on a photographic/video backdrop. Not for two lines of text that already share a
`VStack`.

---

## 4. The spacing rhythm

The HIG does not publish a grid. What it does publish is a default text size (17pt on iOS) and margins that you
inherit for free. In practice the system's own paddings land on multiples of 4, so a 4/8pt scale inherits the
platform rhythm instead of fighting it.

| Value | Use |
| :--- | :--- |
| 2pt | Hairline offsets, optical nudges |
| 4pt | Icon-to-label gap, glyph padding inside a 44pt target |
| 8pt | Default element spacing inside a group |
| 16pt | Screen margin, list row inset |
| 24–32pt | Section separation |

`8.5`, `11`, `13` are the tell. A layout built on arbitrary values reads as a resized web page because nothing
lines up with the system chrome beside it.

**Optical alignment beats mathematical alignment.** A glyph with a rounded leading edge looks inset when aligned
to a square text stem. Nudge the glyph, not the whole row.

---

## 5. Corner geometry

`RoundedRectangle` uses a continuous (squircle) corner by default in the iOS 27.2 SDK:

```text
@frozen public struct RoundedRectangle : Shape {
    public init(cornerRadius: CGFloat, style: RoundedCornerStyle = .continuous)
}
```

So `.rect(cornerRadius: 12)` and `RoundedRectangle(cornerRadius: 12)` are already continuous. What is *not*
continuous is the old `.cornerRadius(_:)` modifier and any `UIBezierPath(roundedRect:cornerRadius:)` you bring
from UIKit. If you still ship `.cornerRadius`, replace it:

```swift
// ❌ Circular corners: the transition from straight edge to arc is abrupt
card.cornerRadius(12)

// ✅ Continuous corners: the same curve system chrome uses
card.clipShape(.rect(cornerRadius: 12))
```

Match radius to size, not to taste: 10–12pt for a control, 16–20pt for a card, and never more than two distinct
radii on one screen.

---

## 6. Materials, depth, and Liquid Glass

*Materials* is a Foundations page and, since iOS 26, Liquid Glass is what the system uses for every control
layer. The HIG's *Layout* page says controls should be differentiated by the material and a scroll edge effect,
"instead of applying a solid or semi-opaque background color beneath controls".

That means:

- Toolbars, tab bars, sidebars and floating controls are glass by default. Do not paint a background under them.
- A card in the content layer is **not** glass. Glass is for the layer above content.
- Below iOS 26, one material surface. Never a material plus a blur plus a white gradient.

Full API, guards and anti-patterns live in [liquid-glass.md](liquid-glass.md). Do not re-derive them here.

---

## 7. HIG page → the API that already implements it

| HIG page | Rule | API |
| :--- | :--- | :--- |
| *Typography* | Use text styles, not point sizes | `.font(.body)`, `.font(.system(.title2, design: .rounded))` |
| *Layout* | Adapt by size class, not device | `@Environment(\.horizontalSizeClass)`, `ViewThatFits` |
| *Layout* | Respect safe areas and margins | `.safeAreaPadding(_:)`, `.contentMargins(_:_:for:)` |
| *Color* | Supply light, dark and increased-contrast variants | Asset catalog appearances; `.foregroundStyle(.primary)` |
| *Materials* | Controls float above content | `.glassEffect(_:in:)` (iOS 26+), `.scrollEdgeEffectStyle(_:for:)` (iOS 26+) |
| *Lists and tables* | Use the list, not a scroll view of stacks | `List`, `.listStyle(.insetGrouped)` |
| *Tab bars* | One system tab bar, not a custom bar | `TabView`, `Tab` (iOS 18+) |
| *Search fields* | Search belongs in the navigation bar | `.searchable(text:placement:prompt:)` |
| *Loading* | Never a blank screen | `ProgressView`, `.redacted(reason: .placeholder)` |
| *Feedback* | Confirm with the platform's own feedback | `.sensoryFeedback(_:trigger:)` |

Every row above is verified against the installed SDK; the type-and-colour rows are detailed in
[typography-and-color.md](typography-and-color.md), the component rows in [native-components.md](native-components.md).

---

## 8. Review checklist

- [ ] No container where 8pt of space and a `.secondary` label would group the content
- [ ] Every padding and gap on the 4/8 scale; no 8.5, 11, 13
- [ ] At most two corner radii on the screen, both continuous
- [ ] No background painted under a toolbar, tab bar or sidebar
- [ ] Glass used only in the control layer, never behind body text
- [ ] Each screen rendered in Light, Dark, AX5 and RTL before it is called done
- [ ] `lint_swiftui` reports zero `SWU001`, `SWU002`, `SWU012`, `SWU013`, `SWU020`

---

## 9. Sources

- Apple HIG, *Design principles* — <https://developer.apple.com/design/human-interface-guidelines/design-principles>
- Apple HIG, *Layout* — <https://developer.apple.com/design/human-interface-guidelines/layout>
- Apple HIG, *Typography* — <https://developer.apple.com/design/human-interface-guidelines/typography>
- Apple HIG, *Color* — <https://developer.apple.com/design/human-interface-guidelines/color>
- Apple HIG, *Materials* — <https://developer.apple.com/design/human-interface-guidelines/materials>
- Apple HIG, *Lists and tables* — <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables>
- `SwiftUICore` SDK interface, iOS 27.2 (`RoundedRectangle.init(cornerRadius:style:)`, `Shape.rect(cornerRadius:style:)`)
