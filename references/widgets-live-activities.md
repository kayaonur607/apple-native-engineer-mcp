# Widgets & Live Activities (WidgetKit & ActivityKit)

> **Authority**: [Apple Human Interface Guidelines — Widgets](https://developer.apple.com/design/human-interface-guidelines/widgets), [Live Activities HIG](https://developer.apple.com/design/human-interface-guidelines/live-activities), [WWDC23: Bring widgets to new places](https://developer.apple.com/videos/play/wwdc2023/10027/), [WWDC24: Design with interactive widgets](https://developer.apple.com/videos/play/wwdc2024/10148/)  
> **Status**: Official Apple Recommendations & Specifications

Widgets provide timely glanceable info on iOS, iPadOS, macOS, and watchOS. Live Activities display real-time events on the Lock Screen and Dynamic Island.

---

## 1. WidgetKit Architecture

A widget is not a mini-app; it is an archivable SwiftUI view rendered at discrete timestamps computed by a `TimelineProvider`.

### Supported Families

| Family | Platform | Typical Layout |
| :--- | :--- | :--- |
| `.systemSmall` | iOS, iPadOS, macOS | 2x2 grid icon footprint, single focused metric |
| `.systemMedium` | iOS, iPadOS, macOS | 2x4 footprint, list of 2-3 items or summary card |
| `.systemLarge` | iOS, iPadOS, macOS | 4x4 footprint, detailed list or rich chart |
| `.systemExtraLarge` | iPadOS, macOS | Wide canvas for complex dashboards |
| `.accessoryCircular` | iOS Lock Screen, watchOS | Circular gauge, percentage ring, icon |
| `.accessoryRectangular` | iOS Lock Screen, watchOS | 2-line textual status or small horizontal graph |
| `.accessoryInline` | iOS Lock Screen, watchOS | Single line of text with optional icon |

### Interactive Widgets (iOS 17+)

Widgets support buttons and toggles backed by **App Intents** without launching the parent app into the foreground.

```swift
import WidgetKit
import SwiftUI
import AppIntents

struct ToggleItemIntent: AppIntent {
    static var title: LocalizedStringResource = "Toggle Task Status"

    @Parameter(title: "Task ID")
    var taskId: String

    init() {}
    init(taskId: String) { self.taskId = taskId }

    func perform() async throws -> some IntentResult {
        await TaskManager.shared.toggleTask(id: taskId)
        return .result()
    }
}

struct TaskRowView: View {
    let task: TaskItem

    var body: some View {
        HStack {
            Button(intent: ToggleItemIntent(taskId: task.id)) {
                Image(systemName: task.isCompleted ? "checkmark.circle.fill" : "circle")
                    .foregroundStyle(task.isCompleted ? .green : .secondary)
            }
            .buttonStyle(.plain)

            Text(task.title)
                .font(.subheadline)
                .strikethrough(task.isCompleted)
        }
    }
}
```

---

## 2. ActivityKit & Live Activities

Live Activities track time-sensitive tasks (flight status, food delivery, sports scores, workout timer) for up to 8 hours (or 12 hours max on Lock Screen).

### Dynamic Island Presentation Modes

When an iPhone 14 Pro, 15, or 16 is unlocked, the Live Activity presents across four possible Dynamic Island states:

1. **Compact**: Two separate areas (`leading` and `trailing`) flanking the camera pill when one activity is active.
2. **Minimal**: A single circular pill when multiple live activities compete for the Dynamic Island.
3. **Expanded**: Long-press on the island opens a larger banner overlay with detailed metrics and controls.
4. **Lock Screen / StandBy**: Full-width interactive card shown when the device is locked or horizontally charging.

```swift
import ActivityKit
import WidgetKit
import SwiftUI

struct FlightStatusAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var flightStatus: String
        var estimatedArrival: Date
        var baggageClaimCarousel: String?
    }

    var flightNumber: String
    var destinationCode: String
}

struct FlightActivityWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: FlightStatusAttributes.self) { context in
            // Lock Screen / StandBy banner
            FlightLockScreenBanner(context: context)
        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded Presentation
                DynamicIslandExpandedRegion(.leading) {
                    Label(context.attributes.flightNumber, systemImage: "airplane")
                        .font(.headline)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text(context.state.flightStatus)
                        .foregroundStyle(.green)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    HStack {
                        Text("ETA:")
                        Text(context.state.estimatedArrival, style: .time)
                            .bold()
                        Spacer()
                        if let carousel = context.state.baggageClaimCarousel {
                            Text("Baggage: Gate \(carousel)")
                        }
                    }
                }
            } compactLeading: {
                Image(systemName: "airplane")
                    .foregroundStyle(.blue)
            } compactTrailing: {
                Text(context.state.flightStatus)
                    .font(.caption2.bold())
            } minimal: {
                Image(systemName: "airplane")
                    .foregroundStyle(.blue)
            }
        }
    }
}
```

---

## 3. Best Practices & App Store Review Rules

- **Do NOT abuse Live Activities as advertisements**: Guideline 4.5.4 explicitly forbids promotional, marketing, or general news notifications in Live Activities.
- **Update Frequency Budget**: ActivityKit allows updates up to once per second for rapid events, but throttles when bandwidth or battery is constrained.
- **Keep Dynamic Island Minimalist**: The compact area is tiny (approx 50x20pt per side). Do not cram small unreadable text into `compactLeading` or `compactTrailing`.
- **Include StandBy Support**: Test on iPhone horizontal charging mode with large night-adapted typography.
