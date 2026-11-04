# Performance & Concurrency Review Checklist

Use this checklist to audit render performance, 120Hz ProMotion smoothness, memory safety, and thread concurrency.

---

## 1. SwiftUI Rendering & Body Evaluation
- [ ] **No Object Allocations in `var body`**: Heavy formatters (`DateFormatter`, `NumberFormatter`), network calls, or database queries are strictly kept out of `body`.
- [ ] **Sub-View Struct Decomposition**: Monolithic views with large closure bodies are decomposed into dedicated sub-view structs with their own state identity.
- [ ] **No Collection Filtering in `body`**: Sorting and filtering logic resides in ViewModels or memoized caches.
- [ ] **GPU-Accelerated Transforms**: Spatial animations animate `.scaleEffect()`, `.opacity()`, and `.offset()` rather than re-measuring `.frame(width:height:)`.

---

## 2. Concurrency & `@MainActor` Safety (Swift 6)
- [ ] **MainActor ViewModels**: All classes providing observable state to SwiftUI views are explicitly annotated with `@MainActor`.
- [ ] **No Data Races**: Code compiles under Swift 6 strict concurrency with zero compiler warnings regarding mutable shared state.
- [ ] **Structured Tasks**: Asynchronous tasks are initiated via `.task(id:)` or structured task groups rather than loose detached tasks.

---

## 3. Memory Safety & Retain Cycles
- [ ] **No Retain Cycles in Closures**: Escaping closures capturing view model instances use `[weak self]` where appropriate.
- [ ] **Notification & Stream Cancellation**: `AsyncStream` and Combine subscriptions are properly cancelled when parent views dismiss.
- [ ] **Image Downsampling**: Large high-resolution images are downsampled to display dimensions before rendering in `List` or `LazyVGrid`.
