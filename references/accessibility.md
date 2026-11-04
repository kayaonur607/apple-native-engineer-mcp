# Accessibility (a11y) & Inclusive Design

Accessibility is not an optional feature or late-stage polish in Apple ecosystem development; it is a fundamental pillar of software quality and an official App Store requirement. Apple platforms provide world-class assistive technologies including **VoiceOver**, **Dynamic Type**, **Switch Control**, **Voice Control**, and **AssistiveTouch**.

---

## 1. Dynamic Type Engineering

Dynamic Type empowers users to select their preferred reading size in system settings. At the extreme end, Accessibility Sizes (**AX1 through AX5**) enlarge text drastically.

### Key Rules
1. **Never use fixed heights on text containers**: Avoid `.frame(height: 50)`. Use `.frame(minHeight: 44)` with vertical padding.
2. **Never truncate critical information**: Labels with `lineLimit(1)` without alternative presentation will truncate into `...` when text scales up.
3. **Reflow horizontal stacks to vertical stacks**:

```swift
struct StatCard: View {
    @Environment(\.dynamicTypeSize) private var dynamicTypeSize
    let title: String
    let value: String
    
    var body: some View {
        let isAccessibility = dynamicTypeSize.isAccessibilitySize
        
        Group {
            if isAccessibility {
                VStack(alignment: .leading, spacing: 6) {
                    Text(title).font(.subheadline).foregroundStyle(.secondary)
                    Text(value).font(.title).fontWeight(.bold)
                }
            } else {
                HStack {
                    Text(title).font(.subheadline).foregroundStyle(.secondary)
                    Spacer()
                    Text(value).font(.title3).fontWeight(.semibold)
                }
            }
        }
        .padding(16)
        .background(Color(uiColor: .secondarySystemGroupedBackground), in: RoundedRectangle(cornerRadius: 12))
    }
}
```

---

## 2. VoiceOver Optimization

VoiceOver speaks what is on screen to users who are blind or low-vision. By default, SwiftUI creates an accessibility element for every `Text` and `Image`. Monolithic or noisy views create a frustrating experience.

### A. Combine Redundant Elements
```swift
// ❌ WRONG: VoiceOver stops 3 times, reading fragmented text without context
VStack(alignment: .leading) {
    Text("Battery Level")
    Text("85%")
    Image(systemName: "battery.75")
}

// ✅ CORRECT: Combine into a single coherent semantic element
VStack(alignment: .leading) {
    Text("Battery Level")
    Text("85%")
    Image(systemName: "battery.75")
}
.accessibilityElement(children: .combine)
.accessibilityLabel("Battery Level, 85 percent, charging")
```

### B. Provide Clear Labels, Hints & Values
- **Label**: What the element is (e.g., "Play", "Delete Item").
- **Value**: The current state (e.g., "75%", "Selected", "Page 2 of 5").
- **Hint**: What happens if the user interacts (e.g., "Double tap to delete transaction").

```swift
Button {
    toggleMute()
} label: {
    Image(systemName: isMuted ? "speaker.slash.fill" : "speaker.wave.2.fill")
}
.accessibilityLabel("Mute Audio")
.accessibilityValue(isMuted ? "Muted" : "Unmuted")
.accessibilityHint("Double tap to toggle audio playback")
```

### C. Hide Purely Decorative Elements
Never allow VoiceOver to stumble over meaningless background glyphs or decorative borders:

```swift
Image(systemName: "sparkles")
    .accessibilityHidden(true) // Completely ignored by VoiceOver
```

---

## 3. Motion & Sensory Accessibility

### A. Reduce Motion
Users prone to motion sickness or vestibular disorders enable **Reduce Motion**. When active, eliminate bouncy springs and spatial slides:

```swift
struct FluidAccordion: View {
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    @State private var isExpanded: Bool = false
    
    var body: some View {
        VStack {
            Button("Toggle Details") {
                if reduceMotion {
                    // Instant or crossfade only
                    withAnimation(.easeInOut(duration: 0.15)) {
                        isExpanded.toggle()
                    }
                } else {
                    // Full rich Kowalski spring
                    withAnimation(.spring(response: 0.35, dampingRatio: 0.8)) {
                        isExpanded.toggle()
                    }
                }
            }
            
            if isExpanded {
                DetailContent()
                    .transition(reduceMotion ? .opacity : .move(edge: .top).combined(with: .opacity))
            }
        }
    }
}
```

### B. Differentiate Without Color
Users with color vision deficiency must not rely solely on color (e.g. green vs red) to distinguish status. Always pair color with an icon or explicit text:

```swift
@Environment(\.accessibilityDifferentiateWithoutColor) private var differentiateWithoutColor

HStack {
    Circle()
        .fill(isSuccess ? Color.green : Color.red)
        .frame(width: 10, height: 10)
    
    if differentiateWithoutColor {
        Image(systemName: isSuccess ? "checkmark.circle" : "exclamationmark.circle")
            .foregroundStyle(isSuccess ? .green : .red)
    }
    
    Text(isSuccess ? "Payment Approved" : "Payment Declined")
}
```

---

## 4. Touch Targets (Minimum 44×44pt)

App Store Review Guidelines and HIG mandate a minimum 44×44pt touch target. Use `.contentShape(Rectangle())` with `.frame(minWidth: 44, minHeight: 44)` to guarantee compliance:

```swift
Button {
    action()
} label: {
    Image(systemName: "chevron.right")
        .frame(minWidth: 44, minHeight: 44)
        .contentShape(Rectangle())
}
```

---

## 5. Official HIG References
- [Apple HIG - Accessibility](https://developer.apple.com/design/human-interface-guidelines/accessibility)
- [Apple Developer - Accessibility APIs](https://developer.apple.com/accessibility/)
