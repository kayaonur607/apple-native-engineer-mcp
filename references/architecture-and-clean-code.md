# Software Architecture & Clean Code in Modern Swift

Writing maintainable, scalable Apple platform software requires pragmatic architectural patterns, strict thread safety, loose coupling via dependency injection, and clean separation of concerns. This guide outlines standard patterns for modern Swift 6 and SwiftUI.

---

## 1. Architectural Neutrality & Codebase Respect

Never dogmatically impose an architecture on an existing codebase:
- If a project uses **Clean Architecture with Repositories/Use Cases**, align with that structure.
- If a project uses **The Composable Architecture (TCA)**, follow its reducer and environment conventions.
- If a project uses **MVVM**, optimize it using Swift 5.9/6 `@Observable` classes isolated to `@MainActor`.
- For **new or lightweight projects**, prefer idiomatic SwiftUI: modular views, focused `@Observable` models, and type-safe `NavigationStack`.

---

## 2. Modern MVVM with the Observation Framework

In iOS 17+, the `@Observable` macro completely replaces legacy `ObservableObject`, `@Published`, and `@StateObject`:

```swift
import SwiftUI
import Observation
import OSLog

private let logger = Logger(subsystem: "com.app.domain", category: "Transactions")

// MARK: - Protocol Definition (Dependency Inversion)
public protocol TransactionServiceProtocol: Sendable {
    func fetchTransactions() async throws -> [Transaction]
    func submit(payment: PaymentRequest) async throws -> TransactionResult
}

// MARK: - View Model (Isolated to MainActor)
@Observable
@MainActor
public final class TransactionListViewModel {
    public private(set) var transactions: [Transaction] = []
    public private(set) var isLoading: Bool = false
    public var errorMessage: String?
    
    private let service: TransactionServiceProtocol
    
    public init(service: TransactionServiceProtocol) {
        self.service = service
    }
    
    public func loadTransactions() async {
        isLoading = true
        errorMessage = nil
        do {
            transactions = try await service.fetchTransactions()
            logger.info("Successfully fetched \(self.transactions.count) transactions.")
        } catch {
            errorMessage = error.localizedDescription
            logger.error("Failed to load transactions: \(error.localizedDescription)")
        }
        isLoading = false
    }
}

// MARK: - View Composition
public struct TransactionListView: View {
    @State private var viewModel: TransactionListViewModel
    
    public init(service: TransactionServiceProtocol) {
        _viewModel = State(initialValue: TransactionListViewModel(service: service))
    }
    
    public var body: some View {
        List(viewModel.transactions) { tx in
            TransactionRowView(transaction: tx)
        }
        .overlay {
            if viewModel.isLoading && viewModel.transactions.isEmpty {
                ProgressView("Loading transactions...")
            } else if viewModel.transactions.isEmpty {
                ContentUnavailableView("No Transactions", systemImage: "creditcard")
            }
        }
        .task {
            await viewModel.loadTransactions()
        }
    }
}
```

---

## 3. Dependency Injection via SwiftUI Environment

Inject services and repositories through SwiftUI's environment to enable effortless mocking in `#Preview` and unit testing:

```swift
// MARK: - Custom Environment Key
private struct TransactionServiceKey: EnvironmentKey {
    static let defaultValue: TransactionServiceProtocol = LiveTransactionService()
}

public extension EnvironmentValues {
    var transactionService: TransactionServiceProtocol {
        get { self[TransactionServiceKey.self] }
        set { self[TransactionServiceKey.self] = newValue }
    }
}

// Usage in Root View
WindowGroup {
    ContentView()
        .environment(\.transactionService, LiveTransactionService())
}

// Usage in Previews with Mock
#Preview {
    ContentView()
        .environment(\.transactionService, MockTransactionService())
}
```

---

## 4. Swift 6 Concurrency & Data-Race Prevention

Swift 6 enables complete compiler-checked thread safety. Adhere to these three rules:

1. **All UI code runs on `@MainActor`**: ViewModels, Views, and UI notification observers must be tagged with `@MainActor`.
2. **Domain Models are `Sendable`**: Value types (`struct`, `enum`) containing immutable or sendable properties can safely cross concurrency domains.
3. **Avoid Unstructured Detached Tasks**: Avoid `Task.detached`. Use structured concurrency (`async let`, `withTaskGroup`, `.task(id:)`) to tie task lifecycles to their view or parent task.

```swift
// Structured concurrent data fetching
func loadDashboardData() async throws -> DashboardData {
    async let profileTask = userService.fetchProfile()
    async let statsTask = analyticsService.fetchWeeklyStats()
    async let notificationsTask = notificationService.fetchPending()
    
    // Concurrently awaits all three requests
    let (profile, stats, notifications) = try await (profileTask, statsTask, notificationsTask)
    return DashboardData(profile: profile, stats: stats, notifications: notifications)
}
```

---

## 5. Modern Unit Testing with Swift Testing

Xcode 16 / Swift 6 introduces the modern **Swift Testing** framework (`import Testing`), which replaces XCTest:

```swift
import Testing
@testable import MyApp

@Suite("Transaction List Tests")
struct TransactionListTests {
    
    @Test("Loading transactions populates list on success")
    @MainActor
    func testLoadSuccess() async {
        let mockService = MockTransactionService()
        mockService.stubbedTransactions = [
            Transaction(id: UUID(), title: "Coffee", amount: 4.50)
        ]
        
        let vm = TransactionListViewModel(service: mockService)
        await vm.loadTransactions()
        
        #expect(vm.transactions.count == 1)
        #expect(vm.errorMessage == nil)
        #expect(!vm.isLoading)
    }
}
```
