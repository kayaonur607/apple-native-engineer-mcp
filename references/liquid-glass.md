# Liquid Glass & Native Materials

Apple's design language has evolved towards a sophisticated interplay of optical refraction, background materials, and physical depth—culminating in the visionOS spatial aesthetic and iOS 18 / macOS Sequoia translucent "Liquid Glass" interfaces.

This document details how to implement native Apple materials and avoid fake, un-native "glassmorphism" web tropes, featuring an advanced configurable parameter engine inspired by research into optical glass simulation (such as `0kzh/glisse`).

---

## 1. Native SwiftUI Material Hierarchy

SwiftUI provides native materials that leverage hardware-accelerated Metal shaders. These automatically sample the backdrop, calculate real-time optical blur, and inject Apple's proprietary vibrancy filter into foreground elements.

| Material | Blur Intensity | Translucency | Recommended Use Cases |
| :--- | :--- | :--- | :--- |
| `.ultraThinMaterial` | Minimal | Highest | Floating controls, HUD overlays, translucent player controls over video |
| `.thinMaterial` | Light | High | Toolbars, segmented controls, contextual cards |
| `.regularMaterial` | Moderate | Balanced | Standard modal sheets, popovers, floating dock-style navigation bars |
| `.thickMaterial` | Heavy | Low | Content panels requiring high text legibility over busy photo backdrops |
| `.ultraThickMaterial` | Maximum | Minimal | Large sidebars, background sheets, persistent utility panels |

---

## 2. Implementing Native Liquid Glass in SwiftUI

### The Anatomy of Authentic Apple Glass
Authentic Apple glass is **not** just a semi-transparent box. It consists of three synchronized layers:
1. **The Material Backdrop**: Real-time Gaussian blur with luminance adjustment.
2. **The Specular Rim (Edge Highlight)**: A microscopic 0.5pt to 1pt stroke along the perimeter simulating light catching the edge of chamfered glass.
3. **Vibrant Foreground Content**: Using `.foregroundStyle(.primary | .secondary)` so text and SF Symbols pull luminance through the glass.

```swift
// ✅ Authentic Apple Native Liquid Glass Card
struct LiquidGlassCard<Content: View>: View {
    @Environment(\.colorScheme) private var colorScheme
    @ViewBuilder var content: Content
    
    var body: some View {
        content
            .padding(16)
            .background {
                RoundedRectangle(cornerRadius: 20, style: .continuous)
                    .fill(.regularMaterial)
                    .overlay {
                        // Specular lighting edge
                        RoundedRectangle(cornerRadius: 20, style: .continuous)
                            .strokeBorder(
                                LinearGradient(
                                    colors: colorScheme == .dark
                                        ? [Color.white.opacity(0.25), Color.white.opacity(0.05)]
                                        : [Color.white.opacity(0.65), Color.black.opacity(0.05)],
                                    startPoint: .topLeading,
                                    endPoint: .bottomTrailing
                                ),
                                lineWidth: 0.5
                            )
                    }
                    // Soft, ambient shadow (never harsh black)
                    .shadow(
                        color: colorScheme == .dark ? Color.black.opacity(0.3) : Color.black.opacity(0.06),
                        radius: 12,
                        x: 0,
                        y: 4
                    )
            }
    }
}
```

---

## 3. Web-Slop "Glassmorphism" vs. Apple Native Materials

Many AI coding assistants generate brittle CSS-like glass that fails on native Apple platforms. Avoid these common anti-patterns:

| Aspect | ❌ Web-Slop Anti-Pattern | ✅ Apple Native Standard |
| :--- | :--- | :--- |
| **Backdrop Blur** | Stacking arbitrary opacity colors: `Color.white.opacity(0.1)` with no material filter. | Using SwiftUI `.regularMaterial` or `.ultraThinMaterial`. |
| **Borders** | Thick solid 2pt or 3pt borders with high opacity (`Color.white.opacity(0.5)`). | Hairline (0.5pt) subtle gradient stroke simulating light refraction. |
| **Shadows** | Huge muddy black shadows (`.shadow(color: .black, radius: 30)`). | Subtle, multi-tiered ambient shadows with very low opacity (5% - 15%). |
| **Foreground Text** | Hardcoded white or black text that becomes invisible when backdrop changes. | Semantic foreground styles (`.foregroundStyle(.primary)`) which automatically adopt system vibrancy. |
| **Corner Radius** | Circular or geometric corners (`CornerRadius(16)` without continuous curve). | Continuous squircle corners (`style: .continuous`). |

---

## 4. Accessibility: Handling `Reduce Transparency`

Users with vision impairments or sensory sensitivity often turn on **Reduce Transparency** in iOS/iPadOS/macOS Settings (`Settings → Accessibility → Display & Text Size → Reduce Transparency`).

When this is enabled, transparent materials must automatically collapse into solid, high-contrast opaque surfaces.

```swift
struct AdaptiveGlassSurface: View {
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    @Environment(\.colorScheme) private var colorScheme
    
    var body: some View {
        VStack {
            Text("Native Glass")
                .font(.headline)
                .foregroundStyle(.primary)
        }
        .padding()
        .background {
            if reduceTransparency {
                // Fallback to fully opaque semantic system background
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(Color(uiColor: .secondarySystemGroupedBackground))
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .stroke(Color(uiColor: .separator), lineWidth: 0.5)
                    )
            } else {
                // Liquid native material
                RoundedRectangle(cornerRadius: 16, style: .continuous)
                    .fill(.ultraThinMaterial)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16, style: .continuous)
                            .strokeBorder(.white.opacity(colorScheme == .dark ? 0.2 : 0.5), lineWidth: 0.5)
                    )
            }
        }
    }
}
```

---

## 5. Advanced Configurable Liquid Glass Engine (Inspired by Glisse)

Drawing insights from web-based optical liquid glass implementations (such as `0kzh/glisse`) and translating them into hardware-accelerated native SwiftUI, developers can fine-tune refraction, specular intensity, ambient tints, and continuous squircle curvature through a single parameter struct:

```swift
import SwiftUI

// MARK: - Liquid Glass Configuration Parameters
public struct LiquidGlassConfiguration: Sendable {
    public var material: Material
    public var cornerRadius: CGFloat
    public var specularIntensity: Double
    public var specularAngle: Angle
    public var surfaceTint: Color?
    public var tintOpacity: Double
    public var shadowRadius: CGFloat
    public var shadowOpacity: Double
    
    public init(
        material: Material = .regularMaterial,
        cornerRadius: CGFloat = 16,
        specularIntensity: Double = 0.5,
        specularAngle: Angle = .degrees(45),
        surfaceTint: Color? = nil,
        tintOpacity: Double = 0.08,
        shadowRadius: CGFloat = 12,
        shadowOpacity: Double = 0.08
    ) {
        self.material = material
        self.cornerRadius = cornerRadius
        self.specularIntensity = specularIntensity
        self.specularAngle = specularAngle
        self.surfaceTint = surfaceTint
        self.tintOpacity = tintOpacity
        self.shadowRadius = shadowRadius
        self.shadowOpacity = shadowOpacity
    }
    
    // Standard Presets
    public static let standard = LiquidGlassConfiguration()
    
    public static let hud = LiquidGlassConfiguration(
        material: .ultraThinMaterial,
        cornerRadius: 24,
        specularIntensity: 0.7,
        shadowRadius: 16,
        shadowOpacity: 0.12
    )
    
    public static let floatingDock = LiquidGlassConfiguration(
        material: .thinMaterial,
        cornerRadius: 32,
        specularIntensity: 0.6,
        surfaceTint: .white,
        tintOpacity: 0.05,
        shadowRadius: 20,
        shadowOpacity: 0.15
    )
}

// MARK: - Configurable Liquid Glass ViewModifier
public struct ConfigurableLiquidGlassModifier: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme
    @Environment(\.accessibilityReduceTransparency) private var reduceTransparency
    
    public let config: LiquidGlassConfiguration
    
    public func body(content: Content) -> some View {
        content
            .background {
                if reduceTransparency {
                    // Accessibility high-contrast opaque fallback
                    RoundedRectangle(cornerRadius: config.cornerRadius, style: .continuous)
                        .fill(Color(uiColor: .secondarySystemGroupedBackground))
                        .overlay {
                            RoundedRectangle(cornerRadius: config.cornerRadius, style: .continuous)
                                .stroke(Color(uiColor: .separator), lineWidth: 0.5)
                        }
                } else {
                    // Optical Liquid Glass with Specular Gradient & Vibrancy
                    RoundedRectangle(cornerRadius: config.cornerRadius, style: .continuous)
                        .fill(config.material)
                        .overlay {
                            if let tint = config.surfaceTint {
                                RoundedRectangle(cornerRadius: config.cornerRadius, style: .continuous)
                                    .fill(tint.opacity(config.tintOpacity))
                            }
                        }
                        .overlay {
                            // Specular Edge Lighting
                            let specularColor = colorScheme == .dark ? Color.white : Color.white
                            let baseOpacity = colorScheme == .dark ? 0.3 : 0.6
                            let highlightOpacity = baseOpacity * config.specularIntensity
                            
                            RoundedRectangle(cornerRadius: config.cornerRadius, style: .continuous)
                                .strokeBorder(
                                    LinearGradient(
                                        colors: [
                                            specularColor.opacity(highlightOpacity),
                                            specularColor.opacity(highlightOpacity * 0.2),
                                            Color.clear
                                        ],
                                        startPoint: .topLeading,
                                        endPoint: .bottomTrailing
                                    ),
                                    lineWidth: 0.5
                                )
                        }
                        .shadow(
                            color: Color.black.opacity(colorScheme == .dark ? config.shadowOpacity * 2.2 : config.shadowOpacity),
                            radius: config.shadowRadius,
                            x: 0,
                            y: 4
                        )
                }
            }
    }
}

// MARK: - View Extension
public extension View {
    func liquidGlass(
        _ config: LiquidGlassConfiguration = .standard
    ) -> some View {
        modifier(ConfigurableLiquidGlassModifier(config: config))
    }
    
    func liquidGlass(
        material: Material = .regularMaterial,
        cornerRadius: CGFloat = 16,
        tint: Color? = nil,
        specularIntensity: Double = 0.5
    ) -> some View {
        let config = LiquidGlassConfiguration(
            material: material,
            cornerRadius: cornerRadius,
            specularIntensity: specularIntensity,
            surfaceTint: tint
        )
        return modifier(ConfigurableLiquidGlassModifier(config: config))
    }
}
```

---

## 6. Official HIG References
- [Apple HIG - Materials](https://developer.apple.com/design/human-interface-guidelines/materials)
- [Apple HIG - Color & Vibrancy](https://developer.apple.com/design/human-interface-guidelines/color)
- [Apple HIG - Spatial Layout and Glass (visionOS)](https://developer.apple.com/design/human-interface-guidelines/spatial-layout)
