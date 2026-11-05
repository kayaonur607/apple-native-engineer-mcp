# Accessibility & Inclusive Design

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple HIG — Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility), [Apple Developer — Accessibility](https://developer.apple.com/accessibility/)

Accessibility is not a polish pass. Three failures account for most real-world defects: text that fails
contrast, layouts that break at large Dynamic Type, and controls VoiceOver cannot name. All three are
measurable before release.

---

## 1. Contrast, with the actual numbers

WCAG 2.2 relative luminance linearises each sRGB channel, then weights it:

```
L = 0.2126·R + 0.7152·G + 0.0722·B
ratio = (L_lighter + 0.05) / (L_darker + 0.05)
```

| Content | Minimum ratio | Tool code below it |
| :--- | :--- | :--- |
| Body text under 24pt (under 18.66pt bold) | 4.5:1 | `A11Y002` (warn) |
| Large text ≥24pt, or ≥18.66pt bold | 3:1 | `A11Y001` (error) |
| Icons, borders, focus rings, control outlines | 3:1 | — |

Semantic colours pass because they adapt: `.primary` and `.secondary` are defined against the system
background in both appearances. A hex literal is fixed, so it has to pass against white *and* `#1C1C1E`.

```swift
import SwiftUI

struct StatusBadge: View {
    let isApproved: Bool

    var body: some View {
        Label(
            isApproved ? "Approved" : "Declined",
            systemImage: isApproved ? "checkmark.circle.fill" : "xmark.circle.fill"
        )
        .font(.subheadline.weight(.semibold))
        .foregroundStyle(.primary)
        .padding(.horizontal, 10)
        .padding(.vertical, 6)
        .background(.quaternary, in: Capsule())
    }
}
```

Colour is never the only signal. Pair it with a glyph or words — that is also what
`accessibilityDifferentiateWithoutColor` asks you to do, and it covers colour-vision deficiency without a
second layout.

---

## 2. Dynamic Type

| Rule | Why |
| :--- | :--- |
| Use text styles (`.body`, `.title2`), never `.font(.system(size:))` | Fixed sizes ignore the user's setting — `A11Y010` |
| Allow 2+ lines on body copy | `lineLimit(1)` truncates at accessibility sizes — `A11Y011` |
| Use `@ScaledMetric` for glyph and spacing values | Keeps icons proportional to scaled text |
| Reflow at accessibility sizes | `DynamicTypeSize.isAccessibilitySize` is the switch |
| Never fix the height of a text container | Use padding and `minHeight` instead |

```swift
import SwiftUI

struct StatCard: View {
    @Environment(\.dynamicTypeSize) private var typeSize
    @ScaledMetric(relativeTo: .title) private var glyph: CGFloat = 28

    let title: String
    let value: String

    var body: some View {
        Group {
            if typeSize.isAccessibilitySize {
                VStack(alignment: .leading, spacing: 6) {
                    label
                    reading
                }
            } else {
                HStack {
                    label
                    Spacer()
                    reading
                }
            }
        }
        .padding(16)
        .background(.quaternary, in: RoundedRectangle(cornerRadius: 12))
    }

    private var label: some View {
        Text(title).font(.subheadline).foregroundStyle(.secondary)
    }

    private var reading: some View {
        HStack(spacing: 6) {
            Image(systemName: "chart.line.uptrend.xyaxis")
                .font(.system(size: glyph))
            Text(value).font(.title2.weight(.semibold))
        }
    }
}
```

Test at AX5, not at Large. AX5 plus a German translation is the layout that ships broken.

---

## 3. VoiceOver

| Modifier | What VoiceOver says | Use it for |
| :--- | :--- | :--- |
| `.accessibilityLabel` | What the element is | Icon-only buttons, composite rows |
| `.accessibilityValue` | Current state | Sliders, progress, “2 of 5” |
| `.accessibilityHint` | What activation does | Non-obvious actions, not every button |
| `.accessibilityElement(children: .combine)` | Merges children into one stop | A card whose parts only make sense together |
| `.accessibilityElement(children: .ignore)` | Hides children, keeps the container | A row you label yourself |
| `.accessibilityAction(named:)` | Adds a custom rotor action | Row-level actions without a visible button |

```swift
import SwiftUI

struct BatteryCard: View {
    let level: Double
    let isCharging: Bool

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text("Battery")
                .font(.subheadline)
            Text(level, format: .percent)
                .font(.title2.weight(.semibold))
            Image(systemName: isCharging ? "bolt.fill" : "battery.75")
                .accessibilityHidden(true)
        }
        .accessibilityElement(children: .ignore)
        .accessibilityLabel("Battery")
        .accessibilityValue(Text(level, format: .percent))
        .accessibilityHint(isCharging ? "Charging" : "Not charging")
    }
}
```

`Image` inside a `Label` or next to text is decorative; hide it. A standalone icon-only `Button` is the
opposite — it needs a label or VoiceOver reads the SF Symbol name (`A11Y030`).

### Custom rotors

```swift
import SwiftUI

struct ArticleList: View {
    let articles: [Article]
    @Namespace private var rotorNamespace

    var body: some View {
        List(articles) { article in
            Text(article.title)
                .accessibilityRotorEntry(id: article.id, in: rotorNamespace)
        }
        .accessibilityRotor("Unread") {
            ForEach(articles.filter(\.isUnread)) { article in
                AccessibilityRotorEntry(
                    Text(article.title),
                    id: article.id,
                    in: rotorNamespace
                )
            }
        }
    }
}
```

The rotor entry and the row must share both the identifier and the namespace, or rotating does nothing.
Add a rotor only when the list is long enough that swiping is slow.

---

## 4. Touch targets

44×44pt is the minimum hit area, not the minimum drawn size. Grow the target with padding and
`.contentShape`, and the icon stays small.

```swift
import SwiftUI

struct CloseButton: View {
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            Image(systemName: "xmark")
                .font(.body.weight(.semibold))
                .frame(minWidth: 44, minHeight: 44)
                .contentShape(Rectangle())
        }
        .accessibilityLabel("Close")
    }
}
```

`A11Y020` only fires when a `Button` or `onTapGesture` sits within 240 characters of an undersized frame —
which is exactly the case that matters.

---

## 5. Motion, colour and transparency

```swift
import SwiftUI

struct DisclosurePanel: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isExpanded = false

    var body: some View {
        VStack(alignment: .leading) {
            Button("Details") {
                withAnimation(reduceMotion ? .easeInOut(duration: 0.15) : .spring(response: 0.35, dampingFraction: 0.8)) {
                    isExpanded.toggle()
                }
            }
            if isExpanded {
                Text("Panel content")
                    .transition(reduceMotion ? .opacity : .move(edge: .top).combined(with: .opacity))
            }
        }
    }
}
```

Reduce Motion means “remove spatial movement”, not “remove feedback”. A crossfade keeps the state change
legible. Reduce Transparency and Increase Contrast are applied by the system to materials — custom
gradients and translucent overlays do not get that treatment, so verify text on them against the busiest
backdrop you ship.

---

## 6. What the auditor catches

`tools/accessibility-auditor/audit_accessibility.py` checks contrast, type scaling, tap targets and labels.

| Code | Severity | Trigger |
| :--- | :--- | :--- |
| `A11Y000` | warn | No Swift files found to audit |
| `A11Y001` | error | Text colour below 3:1 in the worse of light/dark |
| `A11Y002` | warn | Text colour between 3:1 and 4.5:1 — large text only |
| `A11Y010` | warn | `.font(.system(size:))` — fixed size ignores Dynamic Type |
| `A11Y011` | info | `lineLimit(1)` truncates at accessibility sizes |
| `A11Y020` | error | Interactive element below the 44pt minimum |
| `A11Y030` | warn | Icon-only `Button` with no `accessibilityLabel` |
| `A11Y031` | error | Interactive element hidden from assistive technology |
| `A11Y032` | info | `Image` with neither a label nor a decorative marking |

```bash
python3 tools/accessibility-auditor/audit_accessibility.py path/to/Project
```

---

## 7. Release checklist

- [ ] Every text colour passes 4.5:1, or 3:1 for large/bold text
- [ ] Status is conveyed by icon or text as well as colour
- [ ] Layout verified at AX5 with the longest supported translation
- [ ] Every control has a label; decorative images are hidden
- [ ] Custom actions exist for row gestures that VoiceOver cannot discover
- [ ] All hit areas are at least 44×44pt
- [ ] Reduce Motion, Reduce Transparency and Increase Contrast each tested
- [ ] VoiceOver swipe order matches visual order; focus is not trapped
- [ ] Switch Control can reach and activate every primary flow
- [ ] Accessibility Inspector reports no contrast or label warnings
