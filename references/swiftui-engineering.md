# SwiftUI Engineering

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

SwiftUI is cheap to declare and expensive to evaluate. Every rule below protects one number: how many view
bodies run per state change. State has one owner; concurrency has one boundary; identity is derived from data.

---

## 1. State has one owner

| State | Reach for | Why |
| :--- | :--- | :--- |
| A model this screen owns | `@State private var model = Model(...)` | `@State` ties the object's lifetime to the view's identity. |
| A model an ancestor owns | `.environment(model)` + `@Environment(Model.self)` | Descendants read it without threading initialisers through every view. |
| A two-way control binding | `@Bindable var model: Model` | Produces `Binding`s into an `@Observable` object. |
| Local UI state | `@State` on a value type | No object graph, no lifetime question. |

`ObservableObject`, `@StateObject` and `@Published` are legacy (`SWU011`): one change signal means **any** write
invalidates **every** observing view. `@Observable` invalidates only the bodies that read the property changed.

```swift
import SwiftUI

struct Order: Identifiable, Sendable { let id: UUID; var name: String }

struct OrderService: Sendable {
    var submit: @Sendable ([Order]) async throws -> [Order]
    static let live = OrderService { $0 }
}

@Observable
@MainActor
final class OrderModel {
    var orders: [Order] = []
    var isSubmitting = false
    var submitError: String?
    private let service: OrderService

    init(service: OrderService) { self.service = service }

    func submit() async {
        isSubmitting = true
        defer { isSubmitting = false }
        do {
            orders = try await service.submit(orders)
            submitError = nil
        } catch {
            submitError = error.localizedDescription   // failure is state, not a crash
        }
    }
}

struct CheckoutView: View {
    @State private var model = OrderModel(service: .live)
    var body: some View { CheckoutList().environment(model) }
}

struct CheckoutList: View {
    @Environment(OrderModel.self) private var model

    var body: some View {
        List(model.orders) { order in
            Text(order.name)
        }
        .safeAreaInset(edge: .bottom) {
            Button("Place order") { Task { await model.submit() } }   // iOS 26+: Task.immediate (§2)
                .disabled(model.isSubmitting)
        }
    }
}
```

`@MainActor` is explicit so the snippet compiles anywhere; the default isolation in §2 makes it redundant.

---

## 2. Swift 6.2 concurrency: one boundary, no hop you did not ask for

Swift 6.2 makes the common case the default: UI code is main-actor isolated **without** annotating every type,
and background work is opt-in per function.

```text
// Package.swift — the whole module is main-actor isolated unless it says otherwise.
.target(name: "Feature", swiftSettings: [.defaultIsolation(MainActor.self)])
```

The same setting is `-default-isolation MainActor` in Xcode build settings or `OTHER_SWIFT_FLAGS`.

| You want | Write | Effect |
| :--- | :--- | :--- |
| Stay on the caller's actor | `nonisolated(nonsending) func f() async` | No executor hop even though the function is not isolated. |
| Leave for the global executor | `@concurrent func f() async` | Always runs off the caller's actor; use for CPU or blocking work. |
| Start now, not next tick | `Task.immediate { … }` (iOS 26+) | Begins synchronously on the current actor until the first suspension; on iOS 17–25 use `Task { … }`. |
| Fire and forget from a view | `.task { … }` | Structured to the view; cancelled when the view goes away. |

```swift
struct ThumbnailPipeline: Sendable {
    // @concurrent: decoding never occupies the main actor.
    @concurrent
    func load(_ urls: [URL]) async -> [URL: Data] {
        await withTaskGroup(of: (URL, Data).self) { group in
            for url in urls { group.addTask { (url, (try? Data(contentsOf: url)) ?? Data()) } }
            var result: [URL: Data] = [:]
            for await (url, data) in group { result[url] = data }
            return result
        }
    }
}
```

Three rules prevent most Swift 6 errors:

1. Cross an isolation boundary with `Sendable` **values** — snapshots, not `@Observable` classes. An
   `@Observable` class is never `Sendable`; pass the data it holds.
2. `Task.detached` and `DispatchQueue` are last resorts (`SWU008`). Structured tasks inherit cancellation and
   priority; detached tasks inherit neither.
3. `defer` for the flag that must be reset (`isSubmitting` above). A thrown error must not leave the UI stuck.

---

## 3. Invalidation: identity first, then cost

`body` re-runs when a dependency of *that* view changed. Two consequences decide your file layout:

- A computed property inside the view re-runs on every body evaluation — move derived data into the model, or into a
  child view that depends on less.
- A child `View` struct is a separate dependency scope. Extracting a row into `PostRow` is not cosmetic; it is how
  the parent stops re-evaluating rows it did not change.

| Smell | Code | Why it costs |
| :--- | :--- | :--- |
| `AnyView` inside a row | `SWU015` | Erases the concrete type, so SwiftUI cannot diff the subtree. |
| `.id(UUID())` | `SWU016` | New identity every evaluation: state and animations reset. |
| `ForEach(0..<items.count)` | `SWU018` | Rows are matched by offset, not by data, so content jumps. |
| `onAppear { await … }` | `SWU017` | `onAppear` is synchronous and may fire more than once; the task is unstructured. |
| `.animation(_:)` with no `value:` | `SWU010` | Animates every change in the subtree. |

```swift
struct Post: Identifiable, Sendable { let id: UUID; var title: String }

struct PostRow: View {
    let post: Post
    var body: some View { Text(post.title) }
}

@Observable
@MainActor
final class FeedModel {
    enum Phase { case idle, loading, loaded, failed }
    var posts: [Post] = []
    var phase = Phase.idle

    func search(_ query: String) async {
        phase = .loaded              // replace with the real fetch
    }
}

struct FeedView: View {
    @State private var model = FeedModel()
    @State private var query = ""
    @State private var isShowingError = false

    var body: some View {
        List(model.posts) { post in
            PostRow(post: post)      // own body, own dependencies
        }
        .searchable(text: $query)
        .task(id: query) {           // cancels the previous run when query changes
            try? await Task.sleep(for: .milliseconds(250))
            await model.search(query)
        }
        .onChange(of: model.phase, initial: true) { _, phase in
            isShowingError = phase == .failed
        }
        .alert("Could not load", isPresented: $isShowingError) { Button("OK", role: .cancel) {} }
    }
}
```

`.task(id:)` and `.onChange(of:initial:_:)` replace most `onAppear` + `Task` code. `initial: true` fires once at
mount, so "run on appear and on change" is one modifier instead of two code paths.

---

## 4. Test the model, not the view

Swift Testing (`import Testing`) is the default for new tests: `@Suite` groups, `#expect` reports, `#require`
stops. Mark the suite `@MainActor` when the system under test is main-actor isolated. Test doubles are the
injected `@Sendable` closures from §1 — no mocking framework.

```swift
import Testing
@testable import MyApp

@Suite("Order submission") @MainActor
struct OrderModelTests {
    @Test("Clears the cart on success")
    func clearsOnSuccess() async {
        let model = OrderModel(service: OrderService { _ in [] })
        model.orders = [Order(id: UUID(), name: "MacBook Pro")]
        await model.submit()

        #expect(model.orders.isEmpty)
        #expect(model.submitError == nil)
    }
}
```

---

## 5. Before you open the PR

No `ObservableObject` (`SWU011`), no `DispatchQueue` (`SWU008`), no `AnyView` in a row (`SWU015`), no
`id(UUID())` (`SWU016`), no `ForEach(0..<n)` (`SWU018`), no legacy `onChange` (`SWU004`). Then `lint_swiftui`
reports zero errors and `typecheck_snippets` is clean.

Related: [architecture-and-clean-code.md](architecture-and-clean-code.md),
[performance-optimization.md](performance-optimization.md), [navigation-patterns.md](navigation-patterns.md).
