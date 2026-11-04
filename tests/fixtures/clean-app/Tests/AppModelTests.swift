import Testing
@testable import CleanApp

@Suite("App model")
struct AppModelTests {
    @Test("defaults to background sync enabled")
    func defaultsToSync() {
        let suite = UserDefaults(suiteName: "test.cleanapp")!
        let model = AppModel(defaults: suite)
        #expect(model.syncEnabled == true)
    }

    @Test("refresh preserves identity")
    @MainActor
    func refreshPreservesIdentity() async throws {
        let model = AppModel(defaults: .standard)
        let before = model.items.map(\.id)
        try await model.refresh()
        #expect(model.items.map(\.id) == before)
    }
}
