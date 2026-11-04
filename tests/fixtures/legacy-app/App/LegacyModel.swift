import Combine
import Foundation

struct LegacyItem: Identifiable {
    let id = UUID()
    let title: String
}

// ObservableObject is the legacy Combine pattern: every @Published write
// invalidates every view that observes the object.
final class LegacyModel: ObservableObject {
    @Published var items: [LegacyItem] = [
        LegacyItem(title: "First"),
        LegacyItem(title: "Second")
    ]
    @Published var isLoading = false
    @Published var errorMessage: String?

    func save() throws {
        guard !items.isEmpty else {
            throw NSError(domain: "LegacyModel", code: 1)
        }
        UserDefaults.standard.set(true, forKey: "hasSaved")
        isLoading = false
    }
}
