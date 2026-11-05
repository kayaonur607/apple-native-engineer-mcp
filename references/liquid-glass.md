# Liquid Glass

Liquid Glass is the system material language introduced with **iOS 26, iPadOS 26, macOS 26 (Tahoe), watchOS 26
and tvOS 26**. It is a real optical material — it refracts and reflects the content behind it, reacts to device
motion, and merges with neighbouring glass — not a blur you can approximate with stacked `.ultraThinMaterial`
views.

> **Availability verified against the iOS 27.2 SDK** (`SwiftUICore.swiftinterface`). Everything below is checked
> by `tools/liquid-glass-auditor/audit_liquid_glass.py` on every CI run.

---

## 1. The API, exactly

| Declaration | Availability | Notes |
| :--- | :--- | :--- |
| `.glassEffect(_ glass: Glass = .regular, in shape: some Shape = DefaultGlassEffectShape())` | iOS 26.0+, macOS 26.0+ | **unavailable on visionOS** |
| `.glassEffectID(_:in:)` | iOS 26.0+ | Stable identity for morph animations inside a container |
| `.glassEffectUnion(id:namespace:)` | iOS 26.0+ | Merge adjacent glass into one optical surface |
| `.glassEffectTransition(_:)` | iOS 26.0+ | `.materialize`, `.matchedGeometry` |
| `GlassEffectContainer { }` | iOS 26.0+ | Required for merging/morphing sibling glass |
| `Glass.regular` / `.clear` / `.identity` | iOS 26.0+ | `.clear` is for media-rich backdrops; `.identity` is a no-op used for symmetric animation |
| `.tint(_ color: Color?)` | iOS 26.0+ | Tints the glass, not the content |
| `.interactive(_ isEnabled: Bool = true)` | iOS 26.0+ | Adds the pointer/press reaction to *custom* interactive glass |
| `.buttonStyle(.glass)` / `.buttonStyle(.glassProminent)` | iOS 26.0+ | System glass buttons — do not hand-build these |
| `.scrollEdgeEffectStyle(_:for:)` / `.scrollEdgeEffectHidden()` | iOS 26.0+ | The soft edge fade under bars |

`Glass` is a value type: `Glass.regular.tint(.accentColor).interactive()` composes.

---

## 2. The one pattern you need

```swift
struct GlassSurface<Content: View>: View {
    @ViewBuilder var content: Content

    var body: some View {
        if #available(iOS 26.0, macOS 26.0, *) {
            content
                .padding(16)
                .glassEffect(.regular, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        } else {
            content
                .padding(16)
                .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
        }
    }
}
```

The `#available` branch is not optional if your deployment target is below 26. Shipping the call unguarded is a
compile error on older SDKs and a runtime crash on older OS versions — `LG001` catches it.

### Merging glass

Two glass surfaces that overlap should merge rather than stack. Use a container and stable IDs:

```swift
if #available(iOS 26.0, *) {
    GlassEffectContainer(spacing: 12) {
        HStack(spacing: 12) {
            ControlA().glassEffect(.regular).glassEffectID("a", in: namespace)
            ControlB().glassEffect(.regular).glassEffectID("b", in: namespace)
        }
    }
}
```

Without the container, each surface samples the backdrop independently: double the GPU cost and a visible seam.

### Buttons and bars

Do not build glass buttons by hand. The system has them:

```swift
Button("Continue") { submit() }
    .buttonStyle(.glassProminent)   // primary action
Button("Cancel") { dismiss() }
    .buttonStyle(.glass)            // secondary
```

---

## 3. What *not* to do

```swift
// ✗ Imitation: three independent backdrop samples, wrong optics, three offscreen passes
content
    .background(.ultraThinMaterial)
    .blur(radius: 12)
    .overlay(LinearGradient(colors: [.white.opacity(0.3), .clear],
                            startPoint: .top, endPoint: .bottom))
    .shadow(color: .black.opacity(0.2), radius: 24)
```

- **Don't stack materials.** One material surface, or one glass effect. Nested `.ultraThinMaterial` layers each
  sample the backdrop.
- **Don't blur content that already has a material.** `.blur` behind a material is redundant work.
- **Don't fake the specular rim with a linear gradient.** Real glass highlights follow the shape's curvature and
  the light source.
- **Don't apply glass to text-heavy surfaces.** Legibility wins; use a plain background with
  `.foregroundStyle(.primary)`.
- **Don't use `.clear` glass over busy content.** Use it over video or photos where the content *is* the point,
  and add a `.tint` for contrast.

---

## 4. Performance

| Rule | Why |
| :--- | :--- |
| One container per cluster of glass | Each surface is a separate backdrop sample |
| Prefer `.glass` button styles over custom glass on tap targets | System implementation is already optimised and state-aware |
| Avoid glass in `List` rows | Hundreds of live backdrops is the fastest way to drop frames |
| Keep glass off the scrolling axis when possible | Backdrop sampling during scroll is the expensive case |
| Profile with the Animation Hitches instrument | Glass regressions show up as hitches, not CPU spikes |

---

## 5. Accessibility

- **Reduce Transparency** (`UIAccessibility.isReduceTransparencyEnabled`): glass becomes opaque. Never encode
  meaning in the translucency alone — a label on glass must still meet 4.5:1 against the *worst* backdrop.
- **Increase Contrast** increases material opacity automatically; custom gradients do not get that treatment.
- **Reduce Motion** disables the interactive reaction; don't rely on it for feedback.
- VoiceOver ignores visual layering: every glass control still needs a label.

---

## 6. Review checklist

- [ ] Every glass API call is inside an availability guard matching the deployment target
- [ ] Sibling glass elements live in a `GlassEffectContainer` with `.glassEffectID`
- [ ] No `.ultraThinMaterial` + `.blur` + gradient shadow stacks remain
- [ ] Glass buttons use `.buttonStyle(.glass)` / `.glassProminent`
- [ ] Text on glass passes contrast against the busiest backdrop you ship
- [ ] Verified with Reduce Transparency and Increase Contrast enabled
- [ ] `tools/liquid-glass-auditor/audit_liquid_glass.py` reports zero `LG001` / `LG010`

---

## 7. Sources

- Apple, *Liquid Glass* technology overview — <https://developer.apple.com/documentation/technologyoverviews/liquid-glass>
- Apple, *Adopting Liquid Glass* — <https://developer.apple.com/documentation/technologyoverviews/adopting-liquid-glass>
- `SwiftUICore` SDK interface (verified locally against iOS 27.2)
