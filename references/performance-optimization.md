# Performance & Rendering Optimization

Apple devices feature 120Hz ProMotion displays, high-density Retina screens, and energy-efficient Apple Silicon. A buttery-smooth, battery-conscious user experience requires understanding how SwiftUI calculates view invalidation, schedules drawing passes, and manages memory.

---

## 1. SwiftUI View Identity & Invalidation Mechanics

SwiftUI creates and tears down view structs constantly. The `body` property is cheap to instantiate, but evaluating complex logic inside `body` wastes CPU and battery.

### Structural vs. Explicit Identity
- **Structural Identity**: Determined by the view's position within the view hierarchy (e.g. `if / else` branches).
- **Explicit Identity**: Assigned via `.id(uniqueIdentifier)`.

### Common Invalidation Mistakes:
1. **Instantiating Objects inside `var body`**:
   ```swift
   // ❌ SLOW: Creates a new DateFormatter on every single scroll frame
   var body: some View {
       let formatter = DateFormatter() // Massive allocation churn!
       Text(formatter.string(from: date))
   }
   
   // ✅ FAST: Pre-instantiated or using formatted() API
   var body: some View {
       Text(date.formatted(date: .abbreviated, time: .shortened))
   }
   ```
2. **Filtering Collections in `body`**:
   Move all sorting, filtering, and mapping operations to your ViewModel.

---

## 2. 120Hz ProMotion Animation Optimization

To maintain 120 frames per second without frame drops, animations must leverage GPU-accelerated render trees rather than triggering CPU layout passes.

| Animation Property | Performance Level | Execution Pipeline |
| :--- | :--- | :--- |
| `.opacity()` | **GPU Accelerated** (Ultra Fast) | Alpha blend pass in Metal render tree. |
| `.scaleEffect()` | **GPU Accelerated** (Ultra Fast) | Hardware 2D matrix transformation. |
| `.offset()` | **GPU Accelerated** (Ultra Fast) | Translation matrix transformation. |
| `.frame(width:height:)` | **CPU Bound** (Slow) | Invalidates layout tree, triggers remeasurement of all sibling and parent views. |

```swift
// ❌ SLOW: Re-measures layout every frame (triggers hitching)
.frame(width: isExpanded ? 320 : 120)
.animation(.spring(), value: isExpanded)

// ✅ FAST: GPU-accelerated scaling
.scaleEffect(isExpanded ? 1.4 : 1.0)
.animation(.spring(.snappy), value: isExpanded)
```

---

## 3. Memory Management & Retain Cycles in Concurrency

With Swift structured concurrency, retain cycles can still occur when long-lived tasks capture references to class instances:

```swift
@Observable
@MainActor
final class ChatSessionManager {
    var messages: [String] = []
    
    func startStreaming() {
        Task { [weak self] in
            for await message in messageStream {
                guard let self else { return }
                self.messages.append(message)
            }
        }
    }
}
```

---

## 4. Profiling with Xcode Instruments

Never guess where performance bottlenecks lie. Use Xcode Instruments:

1. **SwiftUI View Body Tool**:
   - Xcode → Product → Profile → SwiftUI Instrument.
   - Highlights view types that re-evaluate excessively during scroll or interaction.
2. **Time Profiler**:
   - Identifies CPU spikes and heavy computations running on the main thread.
3. **Leaks & Allocations**:
   - Detects abandoned memory and cyclic references in ViewModels or network caches.
