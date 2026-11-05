# Metal Shaders & Modern SwiftUI Visual Effects

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.
> **Authority**: [SwiftUI — Shader](https://developer.apple.com/documentation/swiftui/shader), [WWDC23: Explore SwiftUI animation and effects](https://developer.apple.com/videos/play/wwdc2023/10158/), [WWDC24: Enhance your app with MeshGradient](https://developer.apple.com/videos/play/wwdc2024/10149/)

SwiftUI gives you three GPU hooks — `colorEffect`, `distortionEffect` and `layerEffect` — that run a Metal
function over the view you attach them to. Reach for them when the effect is genuinely per-pixel; everything
else is a material, a gradient, or a shape.

---

## 1. The three effect modifiers

| Effect | Modifier | Metal signature | Use for |
| :--- | :--- | :--- | :--- |
| Colour | `.colorEffect(_:isEnabled:)` | `half4 f(float2 position, half4 color, …)` | Tint, duotone, thermal map, subtle sheen |
| Distortion | `.distortionEffect(_:maxSampleOffset:isEnabled:)` | `float2 f(float2 position, …)` | Ripple, lens, liquid hover |
| Layer | `.layerEffect(_:maxSampleOffset:isEnabled:)` | `half4 f(float2 position, SwiftUI::Layer layer, …)` | Blur, bloom, edge detection — anything that reads neighbours |

All three are iOS 17 / macOS 14 and **unavailable on watchOS**. The first two parameters are supplied by the
system; every argument after them is yours and must be passed from Swift in declaration order.

---

## 2. The Metal side

Functions are marked `[[stitchable]]` and compiled into the app's default Metal library. Include
`SwiftUI/SwiftUI_Metal.h` only when you need `SwiftUI::Layer`.

```metal
#include <metal_stdlib>
#include <SwiftUI/SwiftUI_Metal.h>
using namespace metal;

// colourEffect: position and the current pixel arrive first.
[[stitchable]] half4 tintSheen(float2 position, half4 color, float time, half4 tint) {
    float wave = sin(position.y * 0.04 + time * 2.0) * 0.5 + 0.5;
    return mix(color, tint, half(wave * 0.25));
}

// distortionEffect: return the coordinate to sample instead of the incoming one.
[[stitchable]] float2 ripple(float2 position, float2 origin, float progress, float amplitude) {
    float2 delta = position - origin;
    float distance = length(delta);
    if (distance == 0.0) return position;
    float falloff = exp(-distance * 0.02);
    float wave = sin(progress * 12.0) * falloff * amplitude;
    return position + normalize(delta) * wave;
}

// layerEffect: sample the whole layer, not just the current pixel.
[[stitchable]] half4 softBlur(float2 position, SwiftUI::Layer layer, float radius) {
    half4 sum = 0;
    for (int i = -2; i <= 2; ++i) {
        sum += layer.sample(position + float2(float(i) * radius * 0.5, 0.0));
    }
    return sum / 5.0h;
}
```

`SwiftUI::Layer.sample(_:)` returns premultiplied RGBA in the layer's working colour space, with linear
interpolation between pixels. That is why the blur averages samples rather than reading a texture directly.

---

## 3. The SwiftUI side

Arguments are passed as `Shader.Argument` values: `.float(_:)`, `.float2(_:)`, `.color(_:)`, `.size`,
`.boundingRect`. `ShaderLibrary` resolves function names dynamically, so a typo fails at render time — compile
the shader once at launch to catch it early.

```swift
import SwiftUI

struct LiveBadge: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var start = Date.now

    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 30.0, paused: reduceMotion)) { context in
            let time = context.date.timeIntervalSince(start)
            Text("LIVE")
                .font(.caption.weight(.semibold))
                .padding(.horizontal, 10)
                .padding(.vertical, 4)
                .colorEffect(ShaderLibrary.tintSheen(.float(time), .color(.accentColor)))
        }
    }
}

struct RippleSurface: View {
    @State private var origin: CGPoint = .zero
    @State private var progress: Double = 0

    var body: some View {
        Color.clear
            .frame(width: 240, height: 160)
            .distortionEffect(
                ShaderLibrary.ripple(.float2(origin), .float(progress), .float(12)),
                maxSampleOffset: CGSize(width: 16, height: 16)   // ≥ the largest displacement
            )
            .onTapGesture(coordinateSpace: .local) { location in
                origin = location
                progress = 0
                withAnimation(.easeOut(duration: 0.6)) { progress = 1 }
            }
    }
}
```

Two rules the compiler cannot check:

1. **Argument order is the contract.** Swift and Metal must agree on every parameter after the implicit ones.
2. **`maxSampleOffset` is a promise.** If the shader can displace a pixel further than the offset, the edge of
   the view shows the unwarped backdrop.

---

## 4. Precompile, then fall back

`Shader.compile(as:)` (iOS 18+) loads the Metal function ahead of first draw. Without it, the first frame that
uses the effect pays the library load — visible as a one-frame hitch on the first scroll.

```swift
@MainActor
func warmUpShaders() async {
    let shader = ShaderLibrary.tintSheen(.float(0), .color(.accentColor))
    if #available(iOS 18.0, macOS 15.0, *) {
        try? await shader.compile(as: .colorEffect)
    }
}
```

Below the effect's deployment floor, degrade to a material or a gradient — never to a `CABasicAnimation` copy of
the same effect:

```swift
struct Backdrop: View {
    @State private var mid: Float = 0.5

    var body: some View {
        if #available(iOS 18.0, macOS 15.0, *) {
            MeshGradient(
                width: 3, height: 3,
                points: [
                    [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
                    [0.0, 0.5], [mid, 0.5], [1.0, 0.5],
                    [0.0, 1.0], [0.5, 1.0], [1.0, 1.0],
                ],
                colors: [.blue, .indigo, .purple, .cyan, .teal, .blue, .blue, .indigo, .purple]
            )
            .ignoresSafeArea()
            .onAppear {
                withAnimation(.easeInOut(duration: 4).repeatForever(autoreverses: true)) { mid = 0.7 }
            }
        } else {
            LinearGradient(colors: [.indigo, .blue], startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()
        }
    }
}
```

`MeshGradient` (iOS 18+) is the cheap answer for organic colour fields: one pass, no shader file, and it
animates through its control points.

---

## 5. Cost control

| Knob | Effect | Set it when |
| :--- | :--- | :--- |
| `maxSampleOffset` | Sizes the offscreen texture | Always: the smallest value the effect needs |
| `.animation(minimumInterval:)` | Caps shader updates per second | Always: 30 Hz is invisible for ambient motion |
| `.animation(paused:)` | Freezes the timeline | Reduce Motion, Low Power Mode, background |
| `.drawingGroup()` | Merges the subtree into one layer | Many overlapping shapes above the shader |
| `Shader.dithersColor` | Controls dithering of shader output | Banding appears in a gradient |

```swift
var allowsContinuousMotion: Bool {
    !ProcessInfo.processInfo.isLowPowerModeEnabled
        && ProcessInfo.processInfo.thermalState == .nominal
}
```

Three anti-patterns that show up in review:

1. Stacking `.ultraThinMaterial` + `.blur` + a shader to imitate glass. On iOS 26 use `.glassEffect(_:in:)`
   inside `#available`; below it, one material surface.
2. Driving a shader from a `@State` timer instead of `TimelineView`. The timer wakes the CPU; the timeline is
   tied to the display.
3. Applying a shader to a whole screen when the effect is a 120pt badge. Cost scales with pixels.

---

## 6. Checklist

- [ ] Effect sits behind the correct availability guard; watchOS is excluded.
- [ ] Argument order matches the Metal signature; `maxSampleOffset` matches the maximum displacement.
- [ ] Motion pauses under Reduce Motion and in Low Power Mode.
- [ ] Shader compiled once at launch on iOS 18+.
- [ ] A static fallback exists for every older OS and for thermal throttling.

Related: [performance-optimization.md](performance-optimization.md),
[liquid-glass.md](liquid-glass.md), [animation-principles.md](animation-principles.md).
