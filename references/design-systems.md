# Design System Engineering in SwiftUI

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

A SwiftUI design system is not a component library. It is a token graph with one direction of dependency, plus
a handful of styles that consume the semantic tier. The type system does the enforcement; the linter does the
policing.

---

## 1. Three tiers, one direction

| Tier | Example | May reference | Never |
| :--- | :--- | :--- | :--- |
| Primitive | `Palette.blue500`, `Radius.md = 12` | Raw literal | A component, a screen, a role |
| Semantic | `Color.surface`, `Spacing.section` | Primitives | A specific screen |
| Component | `button.background`, `button.padding` | Semantic tokens | A primitive |

The rule that keeps the graph acyclic: **a component may name a semantic token, never a primitive.** Renaming
`blue500` must not require opening a single component file. When you want to bypass a tier, that is the token
that is missing — add it at the semantic level.

---

## 2. Generate the tokens; do not hand-write them

Tokens come from a design tool and arrive as JSON. `tools/design-token-forge` compiles that document into a
Swift namespace and, optionally, into `.xcassets` colour sets — so a designer's change is a regenerate, not a
find-and-replace.

```json
{
  "name": "Acme",
  "colors": {
    "brand":  { "light": "#0A84FF", "dark": "#409CFF" },
    "canvas": { "light": "#FFFFFF", "dark": "#000000" }
  },
  "spacing": { "xs": 4, "sm": 8, "md": 16 },
  "radius":  { "card": 20, "pill": 999 },
  "typography": { "title": { "style": "title", "weight": "bold" } },
  "contrastPairs": [{ "foreground": "brand", "background": "canvas" }]
}
```

```bash
python3 tools/design-token-forge/forge_tokens.py tokens.json \
    --out Sources/DesignSystem/Tokens.swift \
    --xcassets Sources/DesignSystem/Assets.xcassets
```

The generator emits one public namespace with a typed member per token, plus the appearance helper it needs:

```text
public enum Acme {
    public enum Colors {
        public static let brand = Color.token(light: "#0A84FF", dark: "#409CFF")
    }
    public enum Spacing { public static let md: CGFloat = 16 }
    public enum Radius  { public static let card: CGFloat = 20 }
    public enum Typography {
        public static let title = Font.system(.title, design: .default, weight: .bold)
    }
}
```

`--xcassets` writes one `<token>.colorset` per colour with a light and a dark entry, which is what Xcode's asset
catalog expects. Prefer that output when the app must also build for macOS: the inline `Color.token` helper is
built on `UIColor` and is iOS-only.

Two things to check in the generated file before you commit it:

| Check | Why |
| :--- | :--- |
| `Font.system` order is `style, design:, weight:` | The current generator emits `weight:` before `design:`, which does not compile (`missing argument label 'size:'`). Reorder or fix the template. |
| `TOK011` is clean | A token pair under 4.5:1 fails WCAG AA in one appearance. |

---

## 3. Colour is semantic, or it is a bug

| Need | Use | Code if you hardcode |
| :--- | :--- | :--- |
| Body and secondary text | `.primary`, `.secondary`, `.tertiary` | — |
| Screen and grouped surfaces | `.background`, asset `canvas` | `SWU013` |
| Separators | `.separator` | `SWU001` |
| Brand accent | `.tint` or the `brand` token | `SWU001` |
| System-defined colour | `Color(uiColor: .systemBackground)` | `SWU019` |

Hex literals belong in the token source, not in view code (`SWU001`). `Color.white` as a background breaks Dark
Mode (`SWU013`); `UIColor.red` and friends ignore Increase Contrast (`SWU019`).

```swift
struct CardSurface: ViewModifier {
    func body(content: Content) -> some View {
        content
            .padding(Acme.Spacing.md)
            .background(.background, in: RoundedRectangle(cornerRadius: Acme.Radius.card, style: .continuous))
            .overlay {
                RoundedRectangle(cornerRadius: Acme.Radius.card, style: .continuous)
                    .strokeBorder(.separator, lineWidth: 0.5)   // specular edge, not a drop shadow
            }
    }
}
```

---

## 4. Type scales; fixed sizes do not

Text styles carry Dynamic Type, Bold Text and accessibility sizes for free. `@ScaledMetric` does the same for
custom numbers — icon sizes, control heights, custom padding — but only if you give it the text style it should
track.

```swift
struct ActivityCard: View {
    @ScaledMetric(relativeTo: .body) private var iconSize: CGFloat = 22
    @ScaledMetric(relativeTo: .body) private var cardPadding: CGFloat = 16

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: "flame.fill")
                .font(.system(size: iconSize))          // scaled, not fixed
            VStack(alignment: .leading) {
                Text("Move").font(.headline)
                Text(320, format: .number)
                    .font(.title3)
                    .monospacedDigit()                  // digits stop jittering as values change
            }
        }
        .padding(cardPadding)
    }
}
```

`.font(.system(size: 22))` is a linter finding (`SWU012`) because it ignores Dynamic Type entirely.
`.fontDesign(.rounded)` restyles a whole hierarchy without replacing the text style.

Audit at the largest accessibility size before shipping: the layout must reflow, not clip.

---

## 5. Corners: continuous by default, concentric when nested

`RoundedRectangle(cornerRadius:style:)` with `.continuous` produces the squircle optics Apple's own chrome uses.
A plain corner next to system UI reads as a rectangle with the corners filed off.

```swift
extension View {
    @ViewBuilder
    func cardShape(radius: CGFloat = 16) -> some View {
        if #available(iOS 26.0, macOS 26.0, *) {
            clipShape(ConcentricRectangle(corners: .concentric, isUniform: true))
        } else {
            clipShape(RoundedRectangle(cornerRadius: radius, style: .continuous))
        }
    }
}
```

`ConcentricRectangle` (iOS 26+) derives its radius from the enclosing container, so a card inside a sheet keeps
the same optical curve as the sheet. Below iOS 26, a `.continuous` rounded rectangle is the correct fallback —
never `.circular`.

---

## 6. Components are styles, not wrapper views

A `ButtonStyle` keeps `Button`'s semantics — hit target, VoiceOver traits, keyboard activation, disabled state —
and still lets the design system own the pixels.

```swift
struct PrimaryActionButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled

    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .padding(.horizontal, Acme.Spacing.md)
            .padding(.vertical, Acme.Spacing.sm)
            .frame(maxWidth: .infinity, minHeight: 48)      // 44pt target + optical balance
            .foregroundStyle(.white)                        // component token: onBrand
            .background(
                Acme.Colors.brand,
                in: RoundedRectangle(cornerRadius: Acme.Radius.card, style: .continuous)
            )
            .opacity(isEnabled ? 1 : 0.4)
            .scaleEffect(configuration.isPressed ? 0.98 : 1)
            .animation(.snappy, value: configuration.isPressed)
    }
}

extension ButtonStyle where Self == PrimaryActionButtonStyle {
    static var primary: PrimaryActionButtonStyle { PrimaryActionButtonStyle() }
}
```

The same pattern covers `ToggleStyle`, `LabelStyle`, `ProgressViewStyle` and `ShapeStyle`. A wrapper view that
contains a `Button` loses the trait plumbing and breaks `buttonStyle` composition.

---

## 7. The audit loop

| Finding | Meaning | Fix |
| :--- | :--- | :--- |
| `TOK011` | Token pair below 4.5:1 in one appearance | Change the token, not the call site |
| `TOK003`, `TOK007` | Invalid hex, unknown `Font.TextStyle` | Fix the token source, regenerate |
| `SWU001` | Hex or literal colour in view code | Move it to the token source |
| `SWU012` | Fixed point size | Text style, or `@ScaledMetric` |
| `SWU013` | `Color.white` / `Color.black` background | Semantic background or asset colour |
| `SWU019` | Static `UIColor.red` and friends | Semantic colour |
| `SWU020` | Shadow radius over 8pt | Material surface plus a 0.5pt stroke |

Related: [typography-and-color.md](typography-and-color.md),
[performance-optimization.md](performance-optimization.md),
[swiftui-engineering.md](swiftui-engineering.md).
