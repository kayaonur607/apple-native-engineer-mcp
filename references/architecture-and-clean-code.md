# Software Architecture & Clean Code in Modern Swift

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Architecture is the set of decisions that are expensive to reverse: where state lives, which layer may call
which, and where isolation boundaries sit. Everything else is style.

---

## 1. Four layers, one direction

| Layer | Owns | Isolation | Substituted in tests |
| :--- | :--- | :--- | :--- |
| View (`struct … : View`) | Layout, navigation, accessibility | Main actor | Never |
| Model (`@Observable`) | Screen state, user intent, derived values | Main actor | Injected service |
| Service (`Sendable` struct or `actor`) | Transport, caching policy, DTO → domain mapping | Whatever it declares | Yes, always |
| Store (`@ModelActor`) | Persistence, migrations, merge rules | Its own executor | Yes, in-memory container |
| Composition root (`App`) | Builds the graph once | Main actor | Swapped wholesale |

Dependencies point one way: View → Model → Service → Store. A service never imports SwiftUI; a model never
constructs a `URLSession`. When a layer needs something from above, the design is inverted. Never impose a new
architecture on an existing codebase; align with what is there, then move one seam at a time toward this table.

---

## 2. The composition root builds the graph once

Dependencies are constructed in one place and descend through the environment: views never reach for `.shared`,
and a preview swaps the graph without touching production code.

```swift
import SwiftUI

@Observable
@MainActor
final class AppContainer {
    let orders: OrderModel
    init(orders: OrderModel) { self.orders = orders }
}

@main
struct ShopApp: App {
    @State private var container = AppContainer(orders: OrderModel(service: .live))
    var body: some Scene {
        WindowGroup { RootView().environment(container) }
    }
}

struct RootView: View {
    @Environment(AppContainer.self) private var container
    var body: some View { CheckoutList().environment(container.orders) }
}
```

`@State` in the `App` struct is the correct owner: one instance per process, created once, never rebuilt when a
scene reconnects. Every `.environment(_:)` below it replaces that object for the subtree — which is how a
preview or a test swaps in a fake.

---

## 3. Seams: closures first, protocols when the shape demands it

| Situation | Reach for | Why |
| :--- | :--- | :--- |
| One operation | `@Sendable` closure in a `Sendable` struct | No protocol file, no conformance boilerplate, trivial to fake. |
| Three or more related operations | `protocol` + struct/actor conformance | The closure bundle becomes unreadable. |
| Wrapping a framework type | `protocol` using domain types only | Insulates the app from `URLSession` and SDK churn. |
| Mutable shared state | `actor` | Serialises access without a lock. |

```swift
import Foundation
struct Order: Identifiable, Sendable, Codable { let id: UUID; var name: String }

protocol OrderServiceProtocol: Sendable {
    func fetch() async throws -> [Order]
    func submit(_ orders: [Order]) async throws -> [Order]
}

struct OrderService: OrderServiceProtocol {
    let baseURL: URL
    let session: URLSession = .shared

    func fetch() async throws -> [Order] {
        let (data, _) = try await session.data(from: baseURL.appending(path: "orders"))
        return try JSONDecoder().decode([Order].self, from: data)
    }

    func submit(_ orders: [Order]) async throws -> [Order] {
        var request = URLRequest(url: baseURL.appending(path: "orders"))
        request.httpMethod = "POST"
        request.httpBody = try JSONEncoder().encode(orders)
        let (data, _) = try await session.data(for: request)
        return try JSONDecoder().decode([Order].self, from: data)
    }
}
```

Keep domain types `Sendable`, `Codable`, and free of framework types: a `struct Order` holding a `UUID` and a
`String` crosses every boundary; one holding a managed object crosses none.

---

## 4. Concurrency belongs to the module, not to every type

Swift 6.2 states the isolation rule once per module instead of annotating every class:
`.target(name: "ShopFeature", swiftSettings: [.defaultIsolation(MainActor.self)])` in `Package.swift`, or
`-default-isolation MainActor` in Xcode. Only exceptions are annotated; the compiler enforces both halves.

```swift
actor ImageCache {
    private var storage: [URL: Data] = [:]
    func data(for url: URL) -> Data? { storage[url] }
    func store(_ data: Data, for url: URL) { storage[url] = data }
}

struct Catalogue {
    let cache: ImageCache
    // Leaves the main actor for the expensive part; no lock, no DispatchQueue.
    @concurrent
    func payloads(for urls: [URL]) async -> [URL: Data] {
        var result: [URL: Data] = [:]
        for url in urls {
            if let cached = await cache.data(for: url) { result[url] = cached }
            else if let data = try? Data(contentsOf: url) {
                await cache.store(data, for: url)
                result[url] = data
            }
        }
        return result
    }
}
```

1. UI-side models are main-actor isolated and never cross to a background task.
2. Anything that crosses is `Sendable`: DTOs, domain values, `Data`. Not `@Observable` classes.
3. A model calls a service with `await` and assigns on its own actor. It never hands out its own reference.
4. Structured concurrency (`async let`, `TaskGroup`, `.task`) outlives no scope it did not create (`SWU008`).

---

## 5. Errors are part of the signature

Typed throws turn "any error" into a contract the model can switch on; render failure as state, not a crash.

```swift
enum APIError: Error, Equatable { case offline, unauthorized; case server(status: Int) }

func fetch() async throws(APIError) -> [Order] { throw .offline }

@Observable
@MainActor
final class OrderListModel {
    var orders: [Order] = []
    var message: String?

    func load() async {
        do { orders = try await fetch() }
        catch .offline { message = String(localized: "You're offline. Showing saved orders.") }
        catch { message = error.localizedDescription }
    }
}
```

`try!` is never the answer (`SWU014`). A failure the UI cannot express is a design bug, not a runtime bug.

---

## 6. File structure and naming

```text
Shop/
  App/ShopApp.swift            // composition root
  Order/{CheckoutView,OrderModel,OrderService}.swift
  DesignSystem/Tokens.swift    // generated, see design-systems.md
  Support/Logging.swift
```

| Rule | Why |
| :--- | :--- |
| Feature folders, not layer folders | A change to checkout touches one folder, not five. |
| One primary type per file, named after it | `git grep OrderModel` lands on the right file. |
| `Logger(subsystem:category:)`, never `print` | Logs are filterable, private-by-default, and survive release builds. |
| `is`/`has` for booleans, verbs for methods | The call site reads as a sentence. |
| No `Manager`, `Helper`, `Util` | A name that describes nothing cannot be reviewed. |

---

## 7. Tests target the seams

```swift
import Testing
@testable import Shop

@Suite("Checkout") @MainActor
struct CheckoutTests {
    @Test("A failed submit keeps the cart and surfaces a message")
    func failedSubmitKeepsCart() async {
        let model = OrderModel(service: .failing(APIError.offline))
        model.orders = [Order(id: UUID(), name: "MacBook Pro")]
        await model.submit()
        #expect(model.orders.count == 1)
        #expect(model.submitError != nil)
    }
}
```

Tests assert on state transitions, not on view snapshots: a snapshot says pixels moved, a model test says why.

---

## 8. Review gates

`SWU011` no `ObservableObject`; `SWU014` no `try!` or force unwrap in view or model code; `SWU008` no
`DispatchQueue.main.asyncAfter` (use `Task.sleep(for:)` with cancellation); `SWU017` no `onAppear { await … }`
(use `.task` so the work is tied to view lifetime).

Related: [swiftui-engineering.md](swiftui-engineering.md),
[offline-caching-networking.md](offline-caching-networking.md),
[performance-optimization.md](performance-optimization.md).
