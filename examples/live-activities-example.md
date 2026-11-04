# Live Activities & Dynamic Island Example

This production-ready example demonstrates a complete ActivityKit implementation for an order delivery tracking experience on iOS 16.1+ / 17+ / 18+.

```swift
import ActivityKit
import WidgetKit
import SwiftUI

// MARK: - 1. Activity Attributes & State Model
public struct OrderDeliveryAttributes: ActivityAttributes {
    public struct ContentState: Codable, Hashable {
        public var statusText: String
        public var estimatedDeliveryTime: Date
        public var progressPercent: Double // 0.0 to 1.0
        public var driverName: String
        
        public init(statusText: String, estimatedDeliveryTime: Date, progressPercent: Double, driverName: String) {
            self.statusText = statusText
            self.estimatedDeliveryTime = estimatedDeliveryTime
            self.progressPercent = progressPercent
            self.driverName = driverName
        }
    }

    public var orderNumber: String
    public var restaurantName: String

    public init(orderNumber: String, restaurantName: String) {
        self.orderNumber = orderNumber
        self.restaurantName = restaurantName
    }
}

// MARK: - 2. Dynamic Island & Lock Screen Widget
public struct OrderDeliveryActivityWidget: Widget {
    public init() {}

    public var body: some WidgetConfiguration {
        ActivityConfiguration(for: OrderDeliveryAttributes.self) { context in
            // Lock Screen & StandBy Banner
            VStack(alignment: .leading, spacing: 12) {
                HStack {
                    VStack(alignment: .leading, spacing: 2) {
                        Text(context.attributes.restaurantName)
                            .font(.headline)
                        Text("Order #\(context.attributes.orderNumber)")
                            .font(.caption)
                            .foregroundStyle(.secondary)
                    }
                    Spacer()
                    VStack(alignment: .trailing, spacing: 2) {
                        Text(context.state.statusText)
                            .font(.subheadline.bold())
                            .foregroundStyle(.green)
                        Text(context.state.estimatedDeliveryTime, style: .timer)
                            .font(.caption.monospacedDigit())
                    }
                }

                ProgressView(value: context.state.progressPercent)
                    .tint(.green)

                HStack {
                    Label(context.state.driverName, systemImage: "bicycle")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                    Spacer()
                    Text("Arriving Soon")
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
            }
            .padding(16)
            .activityBackgroundTint(Color.black.opacity(0.85))

        } dynamicIsland: { context in
            DynamicIsland {
                // Expanded View (Long Press on Island)
                DynamicIslandExpandedRegion(.leading) {
                    VStack(alignment: .leading) {
                        Image(systemName: "bag.fill")
                            .foregroundStyle(.green)
                        Text(context.attributes.restaurantName)
                            .font(.subheadline.bold())
                    }
                }
                DynamicIslandExpandedRegion(.trailing) {
                    VStack(alignment: .trailing) {
                        Text(context.state.statusText)
                            .font(.caption.bold())
                            .foregroundStyle(.green)
                        Text(context.state.estimatedDeliveryTime, style: .timer)
                            .font(.subheadline.monospacedDigit())
                    }
                }
                DynamicIslandExpandedRegion(.bottom) {
                    VStack(spacing: 8) {
                        ProgressView(value: context.state.progressPercent)
                            .tint(.green)
                        HStack {
                            Text("Driver: \(context.state.driverName)")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                            Spacer()
                            Text("Order #\(context.attributes.orderNumber)")
                                .font(.caption2)
                                .foregroundStyle(.secondary)
                        }
                    }
                    .padding(.top, 4)
                }
            } compactLeading: {
                Image(systemName: "bicycle")
                    .foregroundStyle(.green)
            } compactTrailing: {
                Text(context.state.statusText)
                    .font(.caption2.bold())
                    .foregroundStyle(.green)
            } minimal: {
                Image(systemName: "bag.fill")
                    .foregroundStyle(.green)
            }
        }
    }
}

// MARK: - 3. App Client Lifecycle Controller
public final class DeliveryActivityManager {
    public static let shared = DeliveryActivityManager()
    private var activeActivity: Activity<OrderDeliveryAttributes>?

    public func startDelivery(orderNumber: String, restaurant: String) {
        guard ActivityAuthorizationInfo().areActivitiesEnabled else { return }

        let attributes = OrderDeliveryAttributes(orderNumber: orderNumber, restaurantName: restaurant)
        let initialContentState = OrderDeliveryAttributes.ContentState(
            statusText: "Preparing",
            estimatedDeliveryTime: Date().addingTimeInterval(1800),
            progressPercent: 0.25,
            driverName: "Alex"
        )

        do {
            let activity = try Activity.request(
                attributes: attributes,
                content: .init(state: initialContentState, staleDate: nil),
                pushType: nil
            )
            self.activeActivity = activity
        } catch {
            print("Failed to start Live Activity: \(error)")
        }
    }

    public func updateProgress(status: String, progress: Double) async {
        guard let activity = activeActivity else { return }
        let updatedState = OrderDeliveryAttributes.ContentState(
            statusText: status,
            estimatedDeliveryTime: Date().addingTimeInterval(900),
            progressPercent: progress,
            driverName: "Alex"
        )
        await activity.update(.init(state: updatedState, staleDate: nil))
    }

    public func finishDelivery() async {
        guard let activity = activeActivity else { return }
        let finalState = OrderDeliveryAttributes.ContentState(
            statusText: "Delivered",
            estimatedDeliveryTime: Date(),
            progressPercent: 1.0,
            driverName: "Alex"
        )
        await activity.end(.init(state: finalState, staleDate: nil), dismissalPolicy: .immediate)
        self.activeActivity = nil
    }
}
```
