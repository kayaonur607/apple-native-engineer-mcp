# `/apple-native-code` — Swift 6, SwiftUI Architecture & Clean Code

Modernizes application state management, ensures data-race safety, and optimizes view composition.

---

## Agent Execution Steps

1. **State Management**:
   - Migrate legacy `ObservableObject` classes with `@Published` properties to the Swift 5.9/6 `@Observable` macro.
   - Replace `@StateObject` with standard `@State` in views.

2. **Thread Concurrency**:
   - Isolate all ViewModels and UI mutations to `@MainActor`.
   - Audit asynchronous tasks to eliminate unstructured detached tasks and retain cycles (`[weak self]`).

3. **View Composition**:
   - Extract heavy sub-views from monolithic parent `body` properties into dedicated structs with their own state identity.
   - Eliminate heavy computations and formatters from `var body`.

4. **Testing**:
   - Implement unit test suites using the modern Swift Testing framework (`import Testing`, `@Test`, `#expect`).
