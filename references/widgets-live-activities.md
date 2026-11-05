# Widgets & Live Activities (WidgetKit & ActivityKit)

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple HIG — Widgets](https://developer.apple.com/design/human-interface-guidelines/widgets), [Live Activities HIG](https://developer.apple.com/design/human-interface-guidelines/live-activities), [WWDC23: Bring widgets to new places](https://developer.apple.com/videos/play/wwdc2023/10027/), [WWDC24: Design with interactive widgets](https://developer.apple.com/videos/play/wwdc2024/10148/)

A widget is not a mini-app. It is an Archivable SwiftUI view the system renders at timestamps you compute, in
a separate process, with no shared memory and no guarantee your app is running. A Live Activity is the same
pipeline aimed at an event with a start and an end.

---

## 1. The protocols, exactly

| Declaration | Framework | Since | What it is |
| :--- | :--- | :--- | :--- |
| `Widget` | SwiftUI | iOS 14 | `init()` + `var body: some WidgetConfiguration` |
| `WidgetBundle` | SwiftUI | iOS 14 | `@main` entry point; `body` is `some Widget` |
| `WidgetConfiguration` | SwiftUI | iOS 14 | The DSL — `.supportedFamilies`, `.configurationDisplayName` |
| `TimelineProvider` | WidgetKit | iOS 14 | Completion-based: `placeholder`, `getSnapshot`, `getTimeline` |
| `AppIntentTimelineProvider` | WidgetKit | iOS 17 | Async provider + `WidgetConfigurationIntent` |
| `ControlWidget` | SwiftUI | iOS 18 | Control Center, Lock Screen control, Action Button — not a Home Screen widget |
| `ActivityConfiguration` | WidgetKit | iOS 16.1 | Live Activity Lock Screen presentation plus Dynamic Island |

`WidgetConfiguration.Body` is itself a `WidgetConfiguration`. That is why configuration modifiers return
`some WidgetConfiguration`, and why a trailing `.padding()` on a configuration does not compile.

---

## 2. A provider worth shipping

`TimelineProvider` is correct when the widget has no options. Once the user can choose what it shows,
`AppIntentConfiguration` + `AppIntentTimelineProvider` is the answer; `IntentConfiguration` is the pre-iOS-17
form.

```swift
import AppIntents
import SwiftUI
import WidgetKit

struct HabitEntry: TimelineEntry {
    let date: Date
    let completed: Int
    let total: Int
}

struct HabitWidgetIntent: WidgetConfigurationIntent {
    static var title: LocalizedStringResource = "Habit Board"

    @Parameter(title: "List")
    var listName: String?
}

struct HabitProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> HabitEntry {
        HabitEntry(date: .now, completed: 3, total: 5)
    }

    func snapshot(for configuration: HabitWidgetIntent, in context: Context) async -> HabitEntry {
        HabitEntry(date: .now, completed: 3, total: 5)
    }

    func timeline(for configuration: HabitWidgetIntent, in context: Context) async -> Timeline<HabitEntry> {
        let refresh = Calendar.current.date(byAdding: .hour, value: 1, to: .now) ?? .now
        return Timeline(entries: [HabitEntry(date: .now, completed: 3, total: 5)], policy: .after(refresh))
    }
}

struct HabitWidget: Widget {
    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: "HabitWidget", intent: HabitWidgetIntent.self, provider: HabitProvider()) { entry in
            HabitWidgetView(entry: entry)
                .containerBackground(for: .widget) { Color(uiColor: .systemBackground) }
        }
        .configurationDisplayName("Habits")
        .description("Today's completion at a glance.")
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryRectangular])
    }
}
```

`containerBackground(for: .widget)` is required since iOS 17: the system draws the platter and pads your
content, and a widget without one shows as an empty tile. `Timeline` takes `.atEnd`, `.after(_:)` or `.never`;
a provider that returns `.never` without a `WidgetCenter` reload is frozen until the user removes the widget.

---

## 3. Families

| Family | Platform | Layout budget |
| :--- | :--- | :--- |
| `.systemSmall` | iPhone, iPad, Mac | One number, one glyph |
| `.systemMedium` | iPhone, iPad, Mac | Two or three rows |
| `.systemLarge` | iPhone, iPad, Mac | A list, chart or short timeline |
| `.systemExtraLarge` | iPad, Mac | Dashboard width; never assume it exists |
| `.accessoryCircular` | Lock Screen, watchOS | A gauge or glyph on `AccessoryWidgetBackground()` |
| `.accessoryRectangular` | Lock Screen, watchOS | Two lines of text or a sparkline |
| `.accessoryInline` | Lock Screen, watchOS | One line, image plus text, no interaction |

Declare only the families you draw for. WidgetKit does not scale `.systemSmall` content into `.systemLarge`; it
renders your view in a bigger box and the layout falls apart.

---

## 4. Interactive widgets (iOS 17+)

`Button(intent:)` and `Toggle(intent:)` run an `AppIntent` in the widget process without launching the app. The
intent must be fast, local and idempotent — WidgetKit gives it a short window and may retry.

```swift
import AppIntents
import SwiftUI
import WidgetKit

struct ToggleHabitIntent: AppIntent {
    static var title: LocalizedStringResource = "Toggle Habit"
    static var isDiscoverable: Bool = false

    @Parameter(title: "Habit ID")
    var habitID: String

    init() {}

    init(habitID: String) {
        self.habitID = habitID
    }

    func perform() async throws -> some IntentResult {
        try await HabitStore.shared.toggle(id: habitID)
        return .result()
    }
}

struct HabitRow: View {
    let habit: Habit

    var body: some View {
        Button(intent: ToggleHabitIntent(habitID: habit.id)) {
            Label(habit.name, systemImage: habit.isDone ? "checkmark.circle.fill" : "circle")
        }
        .buttonStyle(.plain)
        .accessibilityLabel(habit.isDone ? "\(habit.name), done" : "\(habit.name), not done")
    }
}
```

Use `Toggle(isOn:intent:)` for a real switch; it animates the state change. Anything needing a network round
trip, a permission prompt or a sheet belongs in the app — `Button(intent:)` cannot present UI.

---

## 5. Control Center controls (iOS 18+)

`ControlWidget` uses the `ControlWidgetConfiguration` DSL and is a different surface from `Widget`.
`StaticControlConfiguration` for a fixed control, `AppIntentControlConfiguration` when the intent carries
configuration; the templates are `ControlWidgetToggle` and `ControlWidgetButton`.

```swift
import AppIntents
import SwiftUI
import WidgetKit

struct ToggleFocusIntent: SetValueIntent {
    static var title: LocalizedStringResource = "Set Focus"

    @Parameter(title: "State")
    var value: Bool

    func perform() async throws -> some IntentResult {
        await FocusStore.shared.setActive(value)
        return .result()
    }
}

struct FocusControl: ControlWidget {
    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: "FocusControl") {
            ControlWidgetToggle("Focus", isOn: FocusStore.shared.isActive, action: ToggleFocusIntent()) { isOn in
                Label(isOn ? "Focus on" : "Focus off", systemImage: isOn ? "moon.fill" : "moon")
            }
        }
        .displayName("Focus")
        .description("Start or end a focus session.")
    }
}
```

Controls have no timeline and no provider. When the app changes state in the background, request
`ControlCenter.shared.reloadControls(ofKind: "FocusControl")`.

---

## 6. Live Activities

`ActivityAttributes` is the static half (order number, courier); its nested `ContentState` is the mutable half.
Both must be `Codable`, `ContentState` also `Hashable`. Every update replaces the whole state, so keep it small.

```swift
import ActivityKit
import SwiftUI
import WidgetKit

struct DeliveryAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var stage: String
        var eta: Date
    }

    var orderNumber: String
    var courier: String
}

struct DeliveryLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: DeliveryAttributes.self) { context in
            HStack {
                Text("Order \(context.attributes.orderNumber)")
                Spacer()
                Text(context.state.eta, style: .time)
            }
            .padding()
            .activityBackgroundTint(.black.opacity(0.4))
            .activitySystemActionForegroundColor(.white)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Label(context.attributes.courier, systemImage: "bicycle")
                }
                DynamicIslandExpandedRegion(.center) {
                    Text(context.state.stage).font(.headline)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text(context.state.eta, style: .time)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    ProgressView(value: 0.6)
                }
            } compactLeading: {
                Image(systemName: "bicycle")
            } compactTrailing: {
                Text(context.state.eta, style: .time).font(.caption2)
            } minimal: {
                Image(systemName: "bicycle")
            }
            .keylineTint(.orange)
        }
    }
}
```

The expanded positions are `.leading`, `.trailing`, `.center`, `.bottom`. `compactLeading`, `compactTrailing`
and `minimal` are not optional decoration — leave one empty and the activity looks broken on device. On iOS 27,
`@Environment(\.isDynamicIslandLimitedInWidth)` reports when the system is squeezing the island.

### Lifecycle

```swift
import ActivityKit

@MainActor
func startDelivery(order: String, courier: String) throws {
    let attributes = DeliveryAttributes(orderNumber: order, courier: courier)
    let content = ActivityContent(
        state: DeliveryAttributes.ContentState(stage: "Preparing", eta: .now.addingTimeInterval(1800)),
        staleDate: .now.addingTimeInterval(1800)
    )
    // `content:` is current; `contentState:` was deprecated in iOS 16.2.
    _ = try Activity.request(attributes: attributes, content: content, pushType: .token)
}

@MainActor
func finishDelivery() async {
    let final = DeliveryAttributes.ContentState(stage: "Delivered", eta: .now)
    for activity in Activity<DeliveryAttributes>.activities {
        await activity.end(
            ActivityContent(state: final, staleDate: nil),
            dismissalPolicy: .after(.now.addingTimeInterval(300))
        )
    }
}
```

Updates arrive from `await activity.update(_:)`, from APNs when you pass `pushType: .token`, and from
`Activity.activityUpdates`. Observe `activity.pushTokenUpdates` and re-register the token with your server —
tokens rotate. `ActivityAuthorizationInfo().areActivitiesEnabled` tells you whether the user disabled Live
Activities; `Activity.request` throws rather than failing silently.

`NSSupportsLiveActivities` must be `true` in Info.plist or `Activity.request` fails at runtime. Add
`NSSupportsLiveActivitiesFrequentUpdates` only if you genuinely push more than a few times an hour.

---

## 7. Limits that come from the system

| Limit | Reality |
| :--- | :--- |
| Live Activity lifetime | 8 hours active, then up to 4 hours on the Lock Screen |
| Update rate | Throttled; once per second is a ceiling, not a target |
| Widget timeline | A budget, not a contract — reloads are coalesced across apps |
| Widget memory | Tens of MB; one large decoded image is enough to be killed |
| Dynamic Island compact width | Roughly 50pt per side; two words maximum |
| Advertising in a Live Activity | Forbidden by App Store Review Guideline 4.5.4 |

---

## 8. What the validator catches

`tools/widget-validator/validate_widget.py` encodes the failures that only appear on a user's Home Screen.

| Code | Severity | Trigger |
| :--- | :--- | :--- |
| `WID001` | info | No `import WidgetKit` / `import ActivityKit` source |
| `WID010` | error | `Activity.request` without `NSSupportsLiveActivities` |
| `WID011` | error | `Activity.request` with no `ActivityAttributes` type |
| `WID013` | info | No push token handling; process-only updates |
| `WID020` | warn | `DynamicIsland` missing compact, minimal or expanded content |
| `WID021` | info | Default margins may clip edge-to-edge compact content |
| `WID022` | warn | `ActivityAttributes` with no `DynamicIsland` presentation |
| `WID030` | info | No `accessoryRectangular` family — no Lock Screen presence |
| `WID031` | warn | No `.supportedFamilies(_:)` |
| `WID032` | error | No `TimelineProvider`, `AppIntentTimelineProvider` or `WidgetBundle` |
| `WID033` | info | Widget not configurable — `AppIntentConfiguration` is the iOS 17+ fix |
| `WID034` | info | No App Group identifier, so the widget cannot read app data |
| `WID035` | info | Widget sources declare no availability, hiding iOS 17+ API use |

```bash
python3 tools/widget-validator/validate_widget.py path/to/Project
```
