# Performance & Rendering Optimization

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

SwiftUI performance is two numbers: how many view bodies run per state change, and how many bytes the GPU
touches per frame. Everything below moves one of those numbers, and nothing below is worth doing before you have
measured it.

---

## 1. Measure first, on hardware, in Release

| Instrument | Answers | Use when |
| :--- | :--- | :--- |
| SwiftUI | Which views evaluate `body`, which properties invalidate them, which identities churn | Scrolling stutters or a tap redraws half the screen |
| Time Profiler | Where CPU time goes on the main thread | A hitch has no obvious SwiftUI cause |
| Animation Hitches | Frames missed, and in which commit/render phase | Motion feels uneven at 120 Hz |
| Hangs | Main-thread stalls over the threshold | The app freezes, not just drops frames |
| Allocations + Leaks | Heap growth, abandoned memory, retain cycles | Memory climbs across navigation |

Profile the **Release** configuration on a device. Debug builds skip optimisations and add runtime checks, so
their timings are not evidence of anything.

---

## 2. `body` is a function; treat it like one

`body` runs whenever a dependency of that view changes, and SwiftUI may evaluate it more than once per frame.
Work inside it is therefore per-frame work.

| Inside `body` | Cost | Fix |
| :--- | :--- | :--- |
| `DateFormatter()`, `NumberFormatter()` | Allocation per evaluation | `date.formatted(…)` or a cached formatter in the model |
| Sorting/filtering an array | O(n log n) per evaluation | Do it in the model when the data changes |
| `AnyView` wrapping | Type erasure defeats diffing (`SWU015`) | Return the concrete type or use `@ViewBuilder` |
| A computed `var` returning a view | Rebuilt with the parent | Move it into a child `View` struct with its own dependencies |

```swift
struct Post: Identifiable, Sendable {
    let id: UUID
    var title: String
    var publishedAt: Date
}

struct PostRow: View {
    let post: Post

    var body: some View {
        VStack(alignment: .leading, spacing: 4) {
            Text(post.title).font(.headline)
            Text(post.publishedAt.formatted(date: .abbreviated, time: .shortened))
                .font(.subheadline)
                .foregroundStyle(.secondary)
        }
    }
}
```

`PostRow` is a dependency scope of its own: a parent whose list changes does not re-evaluate rows whose `post`
did not change. That is the whole reason to extract rows into structs.

---

## 3. Observation reads are per property, not per object

`@Observable` registers the stored properties a body actually reads. A view that reads `model.profile.name`
does not invalidate when `model.settings` changes; a view that reads the whole `model` in one expression does.

| Read | Invalidates when |
| :--- | :--- |
| `model.profile.name` | `profile` is assigned |
| `model.items.count` | `items` is assigned (insert, remove, replace) |
| `model.items[0].title` | `items` or that element's `title` changes |
| `model` passed whole to a child | Anything the *child* reads — not the parent |

The practical rule: split a screen so each subview reads the smallest slice it needs. A settings panel that
reads `model.settings` must not sit in the same view as a feed that reads `model.items`.

---

## 4. Lazy containers: pick by collection lifetime

| Container | Builds | Recycles | Use for |
| :--- | :--- | :--- | :--- |
| `List` | Rows on demand | Yes | Unbounded or long collections, swipe actions, sections |
| `LazyVStack` / `LazyHStack` | Children on demand | No — created children stay alive | Bounded feeds inside a custom `ScrollView` |
| `LazyVGrid` | Cells on demand | No | Grids of a known, moderate size |
| `ScrollView { VStack { … } }` | Everything immediately | No | Never, for unbounded content |

Identity is what makes laziness correct. `ForEach(items)` over `Identifiable` matches rows by data; a range
(`SWU018`) matches by offset, so inserting at the top re-renders every row; a fresh `.id(UUID())` (`SWU016`)
throws away state and animations on every evaluation.

```swift
struct FeedList: View {
    let posts: [Post]

    var body: some View {
        List(posts) { post in
            PostRow(post: post)
        }
        .listStyle(.plain)
    }
}
```

`List` recycles its rows, so a 10 000-row feed costs roughly one screen of views. `LazyVStack` keeps every row it
has ever built — fine for 200 items, fatal for a timeline that grows forever.

---

## 5. Images: downsample before you decode

A decoded image costs `width × height × 4` bytes. A 4000 × 3000 photo is **48 MB** in memory before it is drawn,
whatever its file size on disk. Ten of them in a scrolling list is a memory-pressure kill.

Downsample to the pixel size you will actually draw, off the main actor:

```swift
import ImageIO
import UIKit

@concurrent
func downsample(_ url: URL, maxPixelSize: Int) async -> UIImage? {
    let sourceOptions = [kCGImageSourceShouldCache: false] as CFDictionary
    guard let source = CGImageSourceCreateWithURL(url as CFURL, sourceOptions) else { return nil }
    let options = [
        kCGImageSourceCreateThumbnailFromImageAlways: true,
        kCGImageSourceCreateThumbnailWithTransform: true,
        kCGImageSourceShouldCacheImmediately: true,
        kCGImageSourceThumbnailMaxPixelSize: maxPixelSize,
    ] as CFDictionary
    guard let cgImage = CGImageSourceCreateThumbnailAtIndex(source, 0, options) else { return nil }
    return UIImage(cgImage: cgImage)
}
```

`kCGImageSourceShouldCacheImmediately` forces the decode at thumbnail time instead of on first draw — that is the
difference between a hitch while scrolling and no hitch.

---

## 6. GPU: group effects, do not stack them

| Modifier | What it does | Cost |
| :--- | :--- | :--- |
| `.drawingGroup()` | Flattens a subtree into one Metal-rendered layer | One offscreen pass; wins when the subtree has many overlapping shapes or blurs |
| `.compositingGroup()` | Groups opacity/blend without rasterising | Cheap; use before animating opacity of a stack |
| `.colorEffect(_:)` | Per-pixel colour transform shader | Pixels × 1 pass |
| `.distortionEffect(_:maxSampleOffset:)` | Per-pixel position warp | Pixels + offscreen texture sized by the sample offset |
| `.layerEffect(_:maxSampleOffset:)` | Samples neighbouring pixels | Pixels × kernel + offscreen texture |

```swift
struct GlassCard: View {
    var body: some View {
        RoundedRectangle(cornerRadius: 20, style: .continuous)
            .fill(.regularMaterial)
            .overlay(alignment: .topLeading) { Text("Total").padding() }
            .drawingGroup()   // one layer instead of material + overlay + shadow passes
    }
}
```

Rules that keep the frame budget:

1. `.drawingGroup()` on a subtree that changes every frame is a regression, not an optimisation — it rasterises
   and re-rasterises.
2. A shader's `maxSampleOffset` must be the smallest value that covers the effect. It sizes an offscreen texture.
3. Never animate a shader from `body`. Drive it with `TimelineView(.animation)` or a state change.
4. Check the thermal and power budget before starting continuous motion:

```swift
var allowsContinuousMotion: Bool {
    !ProcessInfo.processInfo.isLowPowerModeEnabled
        && ProcessInfo.processInfo.thermalState == .nominal
}
```

`ProcessInfo.thermalStateDidChangeNotification` tells you when to re-check. On Low Power Mode or a hot device,
fall back to a static gradient — the system may throttle your frames anyway.

---

## 7. Quick wins

| Symptom | First fix | Code |
| :--- | :--- | :--- |
| Tap re-renders the screen | Split reading scopes into child views | — |
| List scroll hitches | Downsample images; check `AnyView` in rows | `SWU015` |
| Row state resets | Stable `ForEach` identity, no `.id(UUID())` | `SWU016`, `SWU018` |
| Formatter churn | `formatted(…)` or a cached formatter | — |
| Blur-heavy card drops frames | One `drawingGroup()` on the static subtree | — |
| Animation stutters under load | Respect Reduce Motion and thermal state | — |

Related: [swiftui-engineering.md](swiftui-engineering.md),
[metal-shaders-visual-effects.md](metal-shaders-visual-effects.md),
[design-systems.md](design-systems.md).
