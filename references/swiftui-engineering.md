# SwiftUI Architecture & Engineering

Modern SwiftUI (iOS 17+, Swift 5.9 / Swift 6) represents a mature, declarative UI framework with fine-grained reactivity, robust concurrency, and high-performance rendering. Writing production-quality SwiftUI requires adhering to modern state modeling patterns and avoiding architectural anti-patterns from the early SwiftUI eras.

---

## 1. Modern State Management: The Observation Framework

Starting in iOS 17 (macOS 14), Apple introduced the **Observation framework** (`@Observable`), which replaces `ObservableObject`, `@Published`, and `@StateObject`.

### Advantages of `@Observable`:
1. **Property-Level Tracking**: SwiftUI only re-renders views that access specific mutated properties, completely eliminating cascade re-renders.
2. **Simplified Property Wrappers**: Use standard `@State` in views rather than `@StateObject`.
3. **No `@Published` Ceremony**: Regular Swift properties are observed automatically.

```swift
// ✅ Modern iOS 17+ State Model
import SwiftUI
import Observation

@Observable
@MainActor
final class OrderViewModel {
    var items: [OrderItem] = []
    var isProcessing: Bool = false
    var errorMessage: String?
    
    private let orderService: OrderServiceProtocol
    
    init(orderService: OrderServiceProtocol = OrderService()) {
        self.orderService = orderService
    }
    
    func placeOrder() async {
        isProcessing = true
        errorMessage = nil
        do {
            try await orderService.submit(items: items)
            items.removeAll()
        } catch {
            errorMessage = error.localizedDescription
        }
        isProcessing = false
    }
}

struct OrderSummaryView: View {
    // In iOS 17+, @State manages an @Observable class instance lifecycle!
    @State private var viewModel = OrderViewModel()
    
    var body: some View {
        List {
            ForEach(viewModel.items) { item in
                Text(item.name)
            }
        }
        .overlay {
            if viewModel.isProcessing {
                ProgressView("Placing order...")
            }
        }
    }
}
```

---

## 2. Swift 6 Concurrency & `@MainActor` Isolation

Swift 6 enforces strict data-race safety. All view models powering SwiftUI views must be explicitly isolated to `@MainActor` to prevent background thread mutations from causing UI glitches or crashes:

```swift
// ❌ WRONG: Background closure mutating state without actor isolation
class LegacyModel: ObservableObject {
    @Published var count = 0
    func increment() {
        DispatchQueue.global().async {
            self.count += 1 // Thread sanitizer crash in Swift 6!
        }
    }
}

// ✅ CORRECT: Explicit @MainActor isolation with async/await
@Observable
@MainActor
final class SecureModel {
    var count = 0
    
    func increment() async {
        let result = await performBackgroundCalculation()
        self.count = result // Safe: Guaranteed execution on MainActor
    }
}
```

---

## 3. View Composition & Invalidation Optimization

SwiftUI's declarative nature means the `body` property is called whenever observed state changes. To keep the interface buttery smooth at 120Hz ProMotion:

1. **Extract Sub-views into Dedicated Structs**: Separate structs have their own identity and only invalidate when their inputs change. Computed `var` properties inside the parent view re-run every time the parent invalidates.
2. **Never Perform Heavy Computation in `body`**: Move filtering, formatting, and sorting into view models or cache them.
3. **Use `.task(id:)` for Data Loading**: Automatically cancels in-flight tasks when the view disappears or the identifier changes.

```swift
struct FeedView: View {
    @State private var viewModel = FeedViewModel()
    
    var body: some View {
        List(viewModel.posts) { post in
            // Dedicated struct preserves identity and avoids parent re-render cascades
            PostRowView(post: post)
        }
        .task(id: viewModel.selectedFilter) {
            await viewModel.loadPosts()
        }
    }
}
```

---

## 4. Modern Unit Testing with Swift Testing

In Xcode 16 / Swift 6, Apple introduced the modern **Swift Testing** framework (`import Testing`), replacing XCTest for idiomatic testing:

```swift
import Testing
@testable import MyApp

@Suite("Order Processing Suite")
struct OrderViewModelTests {
    
    @Test("Submitting order clears cart on success")
    @MainActor
    func testOrderSuccess() async {
        let mockService = MockOrderService()
        let vm = OrderViewModel(orderService: mockService)
        vm.items = [OrderItem(id: UUID(), name: "MacBook Pro")]
        
        await vm.placeOrder()
        
        #expect(vm.items.isEmpty)
        #expect(vm.errorMessage == nil)
    }
}
```

---

## 5. Architectural Neutrality

Do not dogmatically force third-party architectures (such as The Composable Architecture or heavy coordinator patterns) into small-to-medium Apple apps. 

- For **new or focused apps**: Native SwiftUI view composition + `@Observable` models + `NavigationStack` provides the highest velocity and lowest complexity.
- For **existing apps with TCA or Clean Architecture**: Respect the existing architecture, ensure state mutations are isolated to `@MainActor`, and follow established codebase conventions.
