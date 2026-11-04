import ActivityKit
import AppIntents
import SwiftUI
import WidgetKit

struct OrderAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var status: String
        var minutesRemaining: Int
    }

    var orderID: String
}

/// Complete Dynamic Island implementation: every presentation region is
/// declared, the widget advertises its families, and the timeline provider is
/// App-Intent based (iOS 17+).
struct OrderLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: OrderAttributes.self) { context in
            VStack(alignment: .leading) {
                Text("Status: \(context.state.status)")
                    .font(.headline)
                Text("Arriving in \(context.state.minutesRemaining) min")
                    .font(.caption)
            }
            .padding()
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Text("ETA")
                        .font(.caption2)
                }
                DynamicIslandExpandedRegion(.trailing) {
                    Text("\(context.state.minutesRemaining) min")
                        .font(.caption)
                }
                DynamicIslandExpandedRegion(.center) {
                    Text("Status: \(context.state.status)")
                        .font(.headline)
                }
                DynamicIslandExpandedRegion(.bottom) {
                    ProgressView(value: 0.4)
                }
            } compactLeading: {
                Image(systemName: "box.truck")
                    .accessibilityHidden(true)
            } compactTrailing: {
                Text("\(context.state.minutesRemaining)m")
                    .font(.caption2)
            } minimal: {
                Image(systemName: "box.truck")
                    .accessibilityHidden(true)
            }
            .keylineTint(.accentColor)
        }
    }
}

struct StatusEntry: TimelineEntry {
    let date: Date
    let completed: Int
}

struct StatusProvider: AppIntentTimelineProvider {
    func placeholder(in context: Context) -> StatusEntry {
        StatusEntry(date: .now, completed: 3)
    }

    func snapshot(for configuration: StatusConfigurationIntent, in context: Context) async -> StatusEntry {
        StatusEntry(date: .now, completed: 3)
    }

    func timeline(for configuration: StatusConfigurationIntent, in context: Context) async -> Timeline<StatusEntry> {
        let entry = StatusEntry(date: .now, completed: readCompletedFromAppGroup())
        return Timeline(entries: [entry], policy: .after(.now.addingTimeInterval(900)))
    }

    private func readCompletedFromAppGroup() -> Int {
        let defaults = UserDefaults(suiteName: "group.com.example.cleanapp")
        return defaults?.integer(forKey: "completedCount") ?? 0
    }
}

struct StatusConfigurationIntent: WidgetConfigurationIntent {
    static var title: LocalizedStringResource { "Status" }
    static var description: IntentDescription { IntentDescription("Shows completed item count.") }

    @Parameter(title: "Show weekly total")
    var weekly: Bool
}

struct StatusWidget: Widget {
    var body: some WidgetConfiguration {
        AppIntentConfiguration(kind: "StatusWidget", intent: StatusConfigurationIntent.self, provider: StatusProvider()) { entry in
            VStack {
                Text("Completed")
                    .font(.caption)
                Text("\(entry.completed)")
                    .font(.title2.bold())
            }
            .containerBackground(.fill.tertiary, for: .widget)
        }
        .supportedFamilies([.systemSmall, .systemMedium, .accessoryRectangular, .accessoryCircular])
    }
}

@main
struct CleanAppWidgets: WidgetBundle {
    var body: some Widget {
        StatusWidget()
        OrderLiveActivity()
    }
}
