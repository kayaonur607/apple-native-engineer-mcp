# watchOS Design & Engineering

> **Authority**: [Apple Human Interface Guidelines — watchOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-watchos), [WWDC23: Design watchOS 10](https://developer.apple.com/videos/play/wwdc2023/10028/), [WWDC24: Design great watchOS apps](https://developer.apple.com/videos/play/wwdc2024/10150/)  
> **Status**: Official Apple Recommendations & Specifications

watchOS is designed for brief, glanceable interactions on a wrist-worn device. Interactions should take seconds, not minutes.

---

## 1. The watchOS 10/11 Visual Language

Modern watchOS utilizes full-screen vertical pagination, corner navigation indicators, dynamic background colors, and the Smart Stack.

### Core Architecture Patterns

| Element | Interaction | Best Use |
| :--- | :--- | :--- |
| **Smart Stack** | Turn Digital Crown upwards from watch face | Contextual widgets, recent activities, next meeting |
| **Vertical Paging** | Digital Crown scroll through full-screen cards | Weather forecast, workout metrics, stocks |
| **Toolbar Buttons** | Small circular controls anchored in navigation bar | Quick actions, dismiss, filters |

```swift
NavigationStack {
    TabView {
        CurrentMetricsView()
        HeartRateZoneView()
        WorkoutControlsView()
    }
    .tabViewStyle(.verticalPage) // watchOS 10+ vertical pagination
    .navigationTitle("Workout")
    .navigationBarTitleDisplayMode(.inline)
}
```

---

## 2. Digital Crown & Haptic Feedback

The Digital Crown provides physical precision without obscuring the screen with fingers.

```swift
struct TimerAdjustmentView: View {
    @State private var minutes: Double = 15.0

    var body: some View {
        VStack {
            Text("\(Int(minutes)) min")
                .font(.system(size: 40, weight: .bold, design: .rounded))
        }
        .focusable()
        .digitalCrownRotation(
            $minutes,
            from: 1.0,
            through: 60.0,
            by: 1.0,
            sensitivity: .medium,
            isContinuous: false,
            isHapticFeedbackEnabled: true // Standard tactile ticks
        )
    }
}
```

---

## 3. Double Tap Gesture (watchOS 10.1+)

On Apple Watch Series 9 and Ultra 2 (and later), users can perform a primary action by tapping their index finger and thumb together twice.

- **Primary Action**: Maps to the primary button in a view automatically if using standard buttons or `.handGestureShortcut(.primaryAction)`.
- Use for answer/hang up call, stop timer, scroll Smart Stack, or advance audio track.

```swift
Button("Confirm Delivery") {
    confirmDelivery()
}
.buttonStyle(.borderedProminent)
.handGestureShortcut(.primaryAction) // Triggers on Double Tap
```

---

## 4. Always-On Display (AOD) Optimization

When the user lowers their wrist, the display dims to 1Hz refresh rate.

- **Remove High-Frequency Updates**: Stop second counters, pulsing animations, and frequent timer repaints.
- **Luminance Budget**: Reduce bright background fills to pure black (`Color.black`) to save battery.
- **Sensitive Data Redaction**: Automatically obscure confidential metrics (e.g., account balance, heart rate history) using `.privacySensitive()`.

```swift
struct MetricCard: View {
    let heartRate: Int

    var body: some View {
        VStack(alignment: .leading) {
            Text("HEART RATE")
                .font(.caption2)
                .foregroundStyle(.secondary)

            Text("\(heartRate) BPM")
                .font(.title2.bold())
                .privacySensitive() // Redacted on Always-On when locked or lowered
        }
    }
}
```

---

## 5. Glanceability Checklist

1. **Information Density**: Display no more than 3-4 primary data points per screen.
2. **Text Readability**: Minimum font size is 12pt caption; primary labels should be 16pt+.
3. **Contrast**: Use pure black background (`Color.black`) with vibrant primary accent colors (`Color.green`, `Color.orange`, `Color.cyan`).
4. **Touch Target**: Minimum button height is 40pt with 4pt minimum vertical spacing.
