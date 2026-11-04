# Animation & Motion Design Engineering

Great motion is not decorative; it provides continuity, clarifies spatial relationships, and imparts physical weight and delight to software. This guide adapts the elite design engineering motion principles pioneered by **Emil Kowalski** (author of *Animations on the Web*, creator of Sonner and Vaul) and translates them natively into SwiftUI and Apple Human Interface Guidelines.

---

## 1. Core Principles of Apple Motion Engineering

1. **Physical Plausibility**: Real-world objects have mass, friction, and momentum. They do not start or stop instantaneously.
2. **Springs Over Bezier Easing**: Never use linear or generic bezier curves for spatial motion. Use physics-based springs that react to user gesture velocity and maintain momentum.
3. **No `scale(0)` Pops**: Elements appearing on screen must not scale up from zero. Scaling from zero looks cartoonish and ungrounded. Instead, scale subtly from `0.88`–`0.92` to `1.0` combined with an opacity crossfade.
4. **Interruptibility**: Animations must never lock the interface. If a user interrupts a sheet or card mid-transition, the animation must immediately respond to the new vector without jarring jump-cuts.
5. **Purposeful Feedback**: Micro-interactions should pair motion with subtle tactile feedback (`.sensoryFeedback`).

---

## 2. Modern SwiftUI Spring Palette (iOS 17+)

In iOS 17+, Apple introduced first-class spring presets that map directly to design intent:

| Spring Preset | Characteristics | Best Use Cases |
| :--- | :--- | :--- |
| `.spring(.snappy)` | High response, zero perceived overshoot. Crisp and immediate. | Toggles, segmented controls, small icon badge changes, tab switches. |
| `.spring(.bouncy)` | Controlled playful overshoot with quick settling. | Favorite heart pops, completion badges, celebratory notifications. |
| `.spring(.smooth)` | Fluid, gentle deceleration with no bounce. | Expanding bottom sheets, card accordion expansion, modal reveals. |
| Custom `.spring(response:dampingRatio:)` | Finely tuned response (frequency) and damping ratio. | Drag gestures, physics card dismissals, custom carousels. |

```swift
// Example: Interactive Spring Toggle
Button {
    withAnimation(.spring(.snappy(duration: 0.28, extraBounce: 0.05))) {
        isOn.toggle()
    }
} label: {
    Image(systemName: isOn ? "checkmark.circle.fill" : "circle")
        .foregroundStyle(isOn ? .green : .secondary)
        .symbolEffect(.bounce, value: isOn) // Native SF Symbol bounce!
}
.sensoryFeedback(.selection, trigger: isOn)
```

---

## 3. The Emil Kowalski Anti-Pattern Guide

### Anti-Pattern 1: The "Scale-From-Zero" Pop
```swift
// ❌ ANTI-PATTERN: Pops abruptly from nothing like a 1990s flash banner
.scaleEffect(isVisible ? 1.0 : 0.0)
.animation(.easeInOut(duration: 0.3), value: isVisible)

// ✅ CORRECT: Grounded subtle entrance from 0.92 with opacity fade
.scaleEffect(isVisible ? 1.0 : 0.92)
.opacity(isVisible ? 1.0 : 0.0)
.animation(.spring(response: 0.32, dampingRatio: 0.82), value: isVisible)
```

### Anti-Pattern 2: Linear Spatial Animation
```swift
// ❌ ANTI-PATTERN: Robotic, unnatural linear motion
withAnimation(.linear(duration: 0.4)) {
    sheetOffset = 0
}

// ✅ CORRECT: Decelerating spring preserving natural inertia
withAnimation(.spring(response: 0.38, dampingRatio: 0.78)) {
    sheetOffset = 0
}
```

### Anti-Pattern 3: Animating Layout Frames Instead of GPU Properties
Animating `.frame(width:height:)` forces SwiftUI to re-calculate layout passes for every frame, triggering 120Hz frame drops on complex views.
```swift
// ❌ SLOW: Forces full layout recalculation on every frame
.frame(width: isExpanded ? 300 : 100)
.animation(.spring(), value: isExpanded)

// ✅ FAST: GPU-accelerated transform matrix without layout invalidation
.scaleEffect(isExpanded ? 1.5 : 1.0)
.animation(.spring(.smooth), value: isExpanded)
```

---

## 4. Sensory Haptics & Feedback

Haptics must reinforce visual feedback, not compete with it:

```swift
struct BookmarkButton: View {
    @State private var isBookmarked: Bool = false
    
    var body: some View {
        Button {
            withAnimation(.spring(.bouncy(duration: 0.3, extraBounce: 0.15))) {
                isBookmarked.toggle()
            }
        } label: {
            Image(systemName: isBookmarked ? "bookmark.fill" : "bookmark")
                .font(.title2)
                .foregroundStyle(isBookmarked ? .indigo : .secondary)
                .symbolEffect(.bounce, value: isBookmarked)
        }
        // Micro-haptic triggered exactly upon state toggle
        .sensoryFeedback(.impact(weight: .light, intensity: 0.8), trigger: isBookmarked)
    }
}
```

---

## 5. Reduced Motion Compliance

Always respect user preferences for reduced motion:

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion

var transition: AnyTransition {
    if reduceMotion {
        return .opacity
    } else {
        return .asymmetric(
            insertion: .scale(scale: 0.92).combined(with: .opacity),
            removal: .scale(scale: 0.96).combined(with: .opacity)
        )
    }
}
```
