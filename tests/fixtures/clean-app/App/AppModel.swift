import Foundation
import Observation

struct Item: Identifiable, Hashable {
    let id: UUID
    let title: String
    let symbol: String
}

/// `@Observable` state: SwiftUI tracks exactly the properties each view reads,
/// so changing `refreshInterval` never invalidates the list.
@Observable
final class AppModel {
    var items: [Item] = [
        Item(id: UUID(), title: "Design review", symbol: "square.and.pencil"),
        Item(id: UUID(), title: "Ship build 42", symbol: "shippingbox")
    ]
    var syncEnabled: Bool {
        didSet { defaults.set(syncEnabled, forKey: "syncEnabled") }
    }
    var refreshInterval: Int = 15

    private let defaults: UserDefaults

    init(defaults: UserDefaults = .standard) {
        self.defaults = defaults
        self.syncEnabled = defaults.object(forKey: "syncEnabled") as? Bool ?? true
    }

    @MainActor
    func refresh() async throws {
        try await Task.sleep(for: .milliseconds(200))
        items = items.map { item in
            Item(id: item.id, title: item.title, symbol: item.symbol)
        }
    }

    static let preview: AppModel = {
        let model = AppModel(defaults: UserDefaults(suiteName: "group.com.example.cleanapp") ?? .standard)
        return model
    }()
}
