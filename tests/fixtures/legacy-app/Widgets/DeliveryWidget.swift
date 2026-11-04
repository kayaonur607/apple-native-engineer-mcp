import ActivityKit
import SwiftUI
import WidgetKit

// Deliberately incomplete: the Dynamic Island only declares compactLeading, the
// widget has no supportedFamilies, and Info.plist is missing the Live Activities
// flag. Every one of these ships a broken widget experience.

struct DeliveryAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        var status: String
        var eta: Int
    }
    var orderID: String
}

struct DeliveryLiveActivity: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: DeliveryAttributes.self) { _ in
            Text("Delivering")
        } dynamicIsland: { _ in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) {
                    Text("ETA")
                }
            } compactLeading: {
                Image(systemName: "box.truck")
            } compactTrailing: {
                Text("5m")
            } minimal: {
                Image(systemName: "box.truck")
            }
        }
    }
}
