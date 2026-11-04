# Metal Shaders & Modern SwiftUI Visual Effects

> **Authority**: [SwiftUI Documentation — Shader](https://developer.apple.com/documentation/swiftui/shader), [WWDC23: Explore SwiftUI animation and effects](https://developer.apple.com/videos/play/wwdc2023/10158/), [WWDC24: Enhance your app with iOS 18 MeshGradient](https://developer.apple.com/videos/play/wwdc2024/10149/)  
> **Status**: Official Apple APIs & Engineering Practices

SwiftUI in iOS 17+ and iOS 18 introduces first-class GPU-accelerated shaders, `MeshGradient`, and sensory feedback modifiers that replace heavy custom rendering engines with native, battery-efficient Metal pipelines.

---

## 1. SwiftUI Shaders Overview

SwiftUI supports three types of Metal shader functions via view modifiers:

| Shader Type | Modifier | MSL Function Purpose | Use Case |
| :--- | :--- | :--- | :--- |
| **Color Effect** | `.colorEffect()` | Transforms pixel RGBA values | Grayscale, sepia, tinting, thermal map |
| **Distortion Effect**| `.distortionEffect()` | Warps coordinates (X, Y) | Ripple, wave, glass lens magnification |
| **Layer Effect** | `.layerEffect()` | Samples neighboring pixels | Custom blur, bloom, edge detection |

---

## 2. Implementing a Metal Shader

### Metal Shading Language (`Shaders.metal`)

```metal
#include <metal_stdlib>
#include <SwiftUI/SwiftUI_Metal.h>
using namespace metal;

// 1. Color Effect: Chromatic Aberration / Color Tint
[[stitchable]] half4 tintSheen(float2 position, half4 color, float time, half4 tintColor) {
    float wave = sin(position.y * 0.05 + time * 3.0) * 0.5 + 0.5;
    return mix(color, tintColor, wave * 0.3);
}

// 2. Distortion Effect: Interactive Liquid Ripple
[[stitchable]] float2 waterRipple(float2 position, float2 origin, float progress, float amplitude) {
    float distance = length(position - origin);
    float delay = distance * 0.05;
    float time = max(0.0, progress - delay);
    float ripple = sin(time * 12.0) * exp(-time * 4.0) * amplitude;
    
    if (distance == 0.0) return position;
    return position + (position - origin) / distance * ripple;
}
```

### SwiftUI Integration

```swift
import SwiftUI

struct ShaderGlassCard: View {
    @State private var touchOrigin: CGPoint = .zero
    @State private var rippleProgress: Double = 0.0

    var body: some View {
        VStack(spacing: 12) {
            Image(systemName: "sparkles")
                .font(.system(size: 40))
            Text("Dynamic Optical Surface")
                .font(.headline)
        }
        .frame(width: 320, height: 200)
        .background(.ultraThinMaterial, in: RoundedRectangle(cornerRadius: 24, style: .continuous))
        .distortionEffect(
            ShaderLibrary.waterRipple(
                .float2(touchOrigin),
                .float(rippleProgress),
                .float(15.0)
            ),
            maxSampleOffset: CGSize(width: 20, height: 20)
        )
        .onTapGesture { location in
            touchOrigin = location
            rippleProgress = 0.0
            withAnimation(.easeOut(duration: 0.8)) {
                rippleProgress = 1.0
            }
        }
    }
}
```

---

## 3. iOS 18 `MeshGradient`

iOS 18 introduces `MeshGradient` for organic, multi-point color blending that mimics fluid organic surfaces and Apple-style marketing graphics.

```swift
import SwiftUI

struct NativeMeshBackground: View {
    @State private var animatedPoint: Float = 0.5

    var body: some View {
        MeshGradient(
            width: 3,
            height: 3,
            points: [
                [0.0, 0.0], [0.5, 0.0], [1.0, 0.0],
                [0.0, 0.5], [animatedPoint, 0.5], [1.0, 0.5],
                [0.0, 1.0], [0.5, 1.0], [1.0, 1.0]
            ],
            colors: [
                .blue, .indigo, .purple,
                .cyan, .teal, .blue,
                .blue.opacity(0.8), .indigo, .purple
            ],
            smoothsColors: true
        )
        .ignoresSafeArea()
        .onAppear {
            withAnimation(.easeInOut(duration: 4.0).repeatForever(autoreverses: true)) {
                animatedPoint = 0.7
            }
        }
    }
}
```

---

## 4. Sensory Feedback Integration

Pair visual animations with subtle, tactile haptic sensations:

```swift
Button("Deploy Project") {
    triggerDeploy()
}
.sensoryFeedback(.success, trigger: isDeploySuccess)
.sensoryFeedback(.impact(weight: .light, intensity: 0.7), trigger: buttonTapCount)
```

---

## 5. Performance Guidelines for Shaders

1. **Keep `maxSampleOffset` minimal**: High offsets cause SwiftUI to render larger offscreen textures, increasing memory pressure.
2. **Fallback for Older Platforms**: Always use `#if canImport(SwiftUI)` and `@available(iOS 17.0, macOS 14.0, *)` with graceful fallback backgrounds.
3. **Check Thermal State**: Disable continuous shader animations if `ProcessInfo.processInfo.thermalState == .serious` or `.critical`.
