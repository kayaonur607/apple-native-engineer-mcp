# Design System Engineering in SwiftUI

A production-grade Apple design system establishes visual consistency, accelerates developer velocity, and guarantees compliance with Apple Human Interface Guidelines. Unlike web design systems built on CSS classes, a native SwiftUI design system leverages Swift's strong type system, SwiftUI view modifiers, custom environment keys, and continuous corner geometry.

---

## 1. Token Architecture

Organize design tokens into strongly-typed, immutable namespaces:

```swift
public enum AppTheme {
    
    // MARK: - Spacing Scale (8pt Grid)
    public enum Spacing {
        public static let xxxSmall: CGFloat = 2
        public static let xxSmall: CGFloat  = 4
        public static let xSmall: CGFloat   = 8
        public static let small: CGFloat    = 12
        public static let medium: CGFloat   = 16
        public static let large: CGFloat    = 24
        public static let xLarge: CGFloat   = 32
        public static let xxLarge: CGFloat  = 48
    }
    
    // MARK: - Corner Radius (Continuous Squircles)
    public enum Radius {
        public static let small: CGFloat    = 8
        public static let medium: CGFloat   = 12
        public static let large: CGFloat    = 16
        public static let xLarge: CGFloat   = 24
        public static let pill: CGFloat     = 999
    }
    
    // MARK: - Motion Tokens
    public enum Motion {
        public static let snappy  = Animation.spring(response: 0.26, dampingFraction: 0.8)
        public static let bouncy  = Animation.spring(response: 0.34, dampingFraction: 0.65)
        public static let gentle  = Animation.spring(response: 0.42, dampingFraction: 0.88)
    }
}
```

---

## 2. Semantic Color Tokens

Avoid raw color literals in UI code. Define tokens that bind to semantic system colors or asset catalog colors with Light/Dark mode variants:

```swift
extension ShapeStyle where Self == Color {
    public static var brandPrimary: Color { Color.accentColor }
    public static var brandSecondary: Color { Color.indigo }
    
    public static var surfacePrimary: Color { Color(uiColor: .systemBackground) }
    public static var surfaceGrouped: Color { Color(uiColor: .systemGroupedBackground) }
    public static var surfaceElevated: Color { Color(uiColor: .secondarySystemGroupedBackground) }
    
    public static var borderSubtle: Color { Color(uiColor: .separator) }
}
```

---

## 3. Elevation & Ambient Shadows

Apple's depth model avoids dark, muddy drop shadows. Elevation is achieved through subtle, multi-stage ambient shadows:

```swift
public struct ElevationModifier: ViewModifier {
    @Environment(\.colorScheme) private var colorScheme
    public let level: Level
    
    public enum Level {
        case low, medium, high
    }
    
    public func body(content: Content) -> some View {
        switch level {
        case .low:
            content.shadow(
                color: Color.black.opacity(colorScheme == .dark ? 0.25 : 0.04),
                radius: 4, x: 0, y: 2
            )
        case .medium:
            content.shadow(
                color: Color.black.opacity(colorScheme == .dark ? 0.35 : 0.08),
                radius: 12, x: 0, y: 6
            )
        case .high:
            content
                .shadow(
                    color: Color.black.opacity(colorScheme == .dark ? 0.4 : 0.06),
                    radius: 8, x: 0, y: 4
                )
                .shadow(
                    color: Color.black.opacity(colorScheme == .dark ? 0.3 : 0.12),
                    radius: 24, x: 0, y: 12
                )
        }
    }
}

public extension View {
    func elevation(_ level: ElevationModifier.Level) -> some View {
        modifier(ElevationModifier(level: level))
    }
}
```

---

## 4. Custom SwiftUI ViewModifiers & Styles

Expose design system components through native SwiftUI styling protocols (such as `ButtonStyle`, `ToggleStyle`, `LabelStyle`) rather than monolithic wrapper views:

```swift
// ✅ Custom ButtonStyle integrating design tokens
public struct PrimaryActionButtonStyle: ButtonStyle {
    @Environment(\.isEnabled) private var isEnabled
    
    public func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .font(.headline)
            .foregroundStyle(.white)
            .padding(.horizontal, AppTheme.Spacing.large)
            .padding(.vertical, AppTheme.Spacing.medium)
            .frame(maxWidth: .infinity, minHeight: 48)
            .background {
                RoundedRectangle(cornerRadius: AppTheme.Radius.medium, style: .continuous)
                    .fill(Color.accentColor.opacity(isEnabled ? 1.0 : 0.5))
            }
            .scaleEffect(configuration.isPressed ? 0.98 : 1.0)
            .animation(AppTheme.Motion.snappy, value: configuration.isPressed)
    }
}

public extension ButtonStyle where Self == PrimaryActionButtonStyle {
    static var primaryAction: PrimaryActionButtonStyle { PrimaryActionButtonStyle() }
}
```
