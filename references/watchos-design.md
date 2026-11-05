# watchOS Design & Engineering

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Human Interface Guidelines — watchOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-watchos), [WWDC23: Design watchOS 10](https://developer.apple.com/videos/play/wwdc2023/10028/), [WWDC24: Design great watchOS apps](https://developer.apple.com/videos/play/wwdc2024/10150/)

A watch app is a glance, not a destination. The user's wrist is raised for a few seconds, the arm drops,
and the session ends. Every design decision follows from that: less content, larger type, one action.

The same availability-guard rule applies on watchOS — the snippets below target watchOS 10, and anything
newer sits behind `if #available(watchOS 11.0, *)`.

---

## 1. The interaction budget

| Duration | What the user is doing | What you build |
| :--- | :--- | :--- |
| 1–5 s | Checking a number | Complication, Smart Stack widget, single-value view |
| 5–30 s | Logging or toggling something | One screen, one primary button, haptic confirmation |
| 30 s+ | Reading, comparing, typing | Not a watch task — hand off to iPhone |

If the feature needs more than about three screens, it belongs on the phone. A watch app that mirrors an
iPhone navigation tree is a watch app nobody opens twice.

---

## 2. Layout for 38–49 mm cases

Case sizes span roughly 160pt to 215pt of width across 38–49 mm. Treat the smallest supported case as
your design width and let the larger ones gain margin, never extra columns.

| Rule | Why |
| :--- | :--- |
| Use text styles, never `.font(.system(size:))` | Fixed sizes ignore the user's text-size setting and clip on the short 40 mm screen |
| One number, one label per row | At `.title2` a five-digit value plus a unit already fills the width |
| `.minimumScaleFactor(0.7)` + `.lineLimit(1)` on values | A shrinking number beats a truncated one |
| Keep 44pt of vertical room per tappable row | Fingertips on a 40 mm case are wider than the row |
| `@ScaledMetric` for custom spacing, not for type | Spacing should grow with the text, fonts should not be scaled by hand |

```swift
struct MetricTile: View {
    let title: LocalizedStringKey
    let value: Int

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            Text(title)
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(value.formatted())
                .font(.title2)
                .fontDesign(.rounded)
                .fontWeight(.semibold)
                .minimumScaleFactor(0.7)
                .lineLimit(1)
        }
        .accessibilityElement(children: .combine)
    }
}
```

---

## 3. Navigation: a stack over vertical pages

watchOS has no tab bar. The two containers are `NavigationStack` for depth and a vertically paging
`TabView` for peers — the Digital Crown scrubs between pages, which is the watch's native scroll.

```swift
struct WorkoutPager: View {
    @State private var page = 0

    var body: some View {
        NavigationStack {
            TabView(selection: $page) {
                LiveMetricsPage().tag(0)
                HeartRateZonePage().tag(1)
                WorkoutControlsPage().tag(2)
            }
            .tabViewStyle(.verticalPage)
            .navigationTitle("Workout")
            .toolbar {
                ToolbarItem(placement: .topBarTrailing) {
                    Button("End", systemImage: "xmark") { endWorkout() }
                }
            }
            .containerBackground(.black, for: .navigation)
        }
    }
}
```

- `.verticalPage` is the watchOS 10 paging style; `.tabViewStyle(.carousel)` is the pre-10 look and reads
  as dated next to the Smart Stack.
- Three pages is the practical ceiling. Each extra page is another crown turn away from the first one.
- One toolbar item, trailing. A second control belongs on the page, not in the navigation bar.
- `.containerBackground(_:for: .navigation)` gives scrolling content a background that survives the
  navigation transition; a `.background` modifier on the root view does not.

---

## 4. Digital Crown

The crown is the only precise input on the device. Bind it to a value the user is deliberately adjusting,
never to something that should simply scroll.

```swift
struct RestTimerEditor: View {
    @State private var seconds: Double = 90

    var body: some View {
        Text("\(Int(seconds)) s")
            .font(.title2)
            .fontDesign(.rounded)
            .focusable()
            .digitalCrownRotation(
                $seconds,
                from: 15,
                through: 300,
                by: 5,
                sensitivity: .medium,
                isContinuous: false,
                isHapticFeedbackEnabled: true
            )
            .sensoryFeedback(.selection, trigger: seconds)
    }
}
```

| Parameter | Choose |
| :--- | :--- |
| `from` / `through` | Always bounded. An unbounded crown spins forever with no feedback |
| `by` | The detent step: 5 for seconds, 1 for reps, 0.1 for a scale |
| `sensitivity` | `.low` for fine values, `.high` for long ranges |
| `isContinuous` | `false` for anything with a limit, so the user feels the ends |
| `isHapticFeedbackEnabled` | `true` unless the value is visual-only |

`.focusable()` is required on a custom view — without it the crown still scrolls the page instead of
adjusting the value.

---

## 5. Double tap

A double tap performs the primary action without touching the screen. It is watchOS 11+, so guard it.

```swift
Button("Log Set", systemImage: "checkmark") {
    logSet()
}
.buttonStyle(.borderedProminent)
```

Map it explicitly only when the default is ambiguous:

```swift
Button("Log Set", systemImage: "checkmark") {
    logSet()
}
.buttonStyle(.borderedProminent)
.handGestureShortcut(.primaryAction) // watchOS 11+
```

The system already routes double tap to a prominent button, so the modifier is a correction, not a
requirement. Never attach it to a destructive action: the gesture fires while the wrist is down and the
screen is barely in view.

---

## 6. Complications and the Smart Stack

One widget configuration serves the watch face, the Smart Stack, and (with the same code) the iPhone Lock
Screen. Watch complications use the accessory families.

```swift
import SwiftUI
import WidgetKit

struct HydrationEntry: TimelineEntry {
    let date: Date
    let millilitres: Int
}

struct HydrationProvider: TimelineProvider {
    func placeholder(in context: Context) -> HydrationEntry {
        HydrationEntry(date: .now, millilitres: 1250)
    }

    func getSnapshot(in context: Context, completion: @escaping (HydrationEntry) -> Void) {
        completion(placeholder(in: context))
    }

    func getTimeline(in context: Context, completion: @escaping (Timeline<HydrationEntry>) -> Void) {
        let entry = HydrationEntry(date: .now, millilitres: 1250)
        completion(Timeline(entries: [entry], policy: .after(.now.addingTimeInterval(3600))))
    }
}

struct HydrationWidget: Widget {
    var body: some WidgetConfiguration {
        StaticConfiguration(kind: "Hydration", provider: HydrationProvider()) { entry in
            HydrationWidgetView(entry: entry)
                .containerBackground(for: .widget) {
                    AccessoryWidgetBackground()
                }
        }
        .configurationDisplayName("Hydration")
        .description("Water logged today.")
        .supportedFamilies([.accessoryCircular, .accessoryRectangular, .accessoryInline, .accessoryCorner])
    }
}
```

| Family | Content |
| :--- | :--- |
| `.accessoryCircular` | A `Gauge` with `.gaugeStyle(.accessoryCircularCapacity)` |
| `.accessoryRectangular` | Two lines: a `.headline` label and a `.title3` value |
| `.accessoryInline` | A single `Label` — text and one symbol only |
| `.accessoryCorner` | A value with a curved label; Ultra only |

- The system owns colour and tint. `AccessoryWidgetBackground()` supplies the material; hardcoded fills
  are ignored or fight the face.
- `.containerBackground(for: .widget)` is required on watchOS 10+ — a widget without it renders as an
  empty slot.
- `getTimeline` should return a `.after` policy measured in minutes, not a rebuilt entry every second.

---

## 7. Always-On Display

When the wrist drops, the system dims the display and updates roughly once a minute. The view is still
rendered, so anything animated keeps costing power while being invisible.

```swift
struct HeartRateCard: View {
    let bpm: Int
    @Environment(\.isLuminanceReduced) private var isLuminanceReduced

    var body: some View {
        VStack(alignment: .leading, spacing: 2) {
            Text("Heart Rate")
                .font(.caption2)
                .foregroundStyle(.secondary)
            Text(bpm.formatted())
                .font(.title2)
                .fontWeight(.semibold)
                .contentTransition(.numericText())
                .privacySensitive()
                .animation(isLuminanceReduced ? nil : .default, value: bpm)
        }
    }
}
```

| In Always-On | Do |
| :--- | :--- |
| Time-varying data | Freeze it; read `isLuminanceReduced` and stop the update |
| Background | Pure black — an OLED pixel that is off costs nothing |
| Secrets | `.privacySensitive()` redacts balances and health values when the wrist is down |
| Motion | No repeats, no pulses; a 1 Hz redraw cannot show them anyway |

`.privacySensitive()` also redacts the view in the app switcher, so it is worth applying even when the
user never enables Always-On.

---

## 8. Haptics

Haptics are the confirmation channel on a device the user is not looking at. `sensoryFeedback` ties a
pattern to a state change, so the tap fires once per transition instead of once per redraw.

| Feedback | Meaning | Use for |
| :--- | :--- | :--- |
| `.success` | It worked | Set logged, workout saved |
| `.warning` | It worked, but check it | Goal exceeded, low battery |
| `.error` | It failed | Sync failure, invalid entry |
| `.selection` | The value moved | Crown detents, picker changes |
| `.start` / `.stop` | A session changed state | Timer started, workout ended |

```swift
Toggle("Water Lock", isOn: $waterLock)
    .sensoryFeedback(.start, trigger: waterLock)
```

Do not fire a haptic on every crown tick — `.selection` on a `digitalCrownRotation` with haptics enabled
produces a double buzz on each detent.

---

## 9. Review checklist

- [ ] The app answers one question or performs one action in under 30 seconds
- [ ] No `.font(.system(size:))` anywhere; every size is a text style
- [ ] Layout holds at the smallest supported case with the largest text size
- [ ] Vertical paging has three pages or fewer
- [ ] Digital Crown ranges are bounded and step through meaningful detents
- [ ] Double tap maps to a non-destructive primary action
- [ ] Each widget family has its own layout; `.containerBackground(for: .widget)` is present
- [ ] Always-On freezes updates, uses black, and redacts sensitive values
- [ ] Every state change the user cannot see is confirmed with a haptic

---

## 10. Official HIG references

- [Apple HIG — Designing for watchOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-watchos)
- [Apple HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG — Digital Crown](https://developer.apple.com/design/human-interface-guidelines/digital-crown)
- [Apple HIG — Complications](https://developer.apple.com/design/human-interface-guidelines/complications)
- [Apple HIG — Always On](https://developer.apple.com/design/human-interface-guidelines/always-on)
- [Apple HIG — Notifications](https://developer.apple.com/design/human-interface-guidelines/notifications)
