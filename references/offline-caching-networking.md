# Offline Caching & Resilient Networking

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.
> **Authority**: [URLSession](https://developer.apple.com/documentation/foundation/urlsession), [Network framework](https://developer.apple.com/documentation/network), [WWDC23: Support low-data and offline experiences](https://developer.apple.com/videos/play/wwdc2023/10156/)

Offline behaviour is a data-model decision before a networking one: a request that cannot complete still has to
produce a correct screen. This covers transport, cache contract, persistence and background handoff.

---

## 1. One client, one cache policy

```swift
import Foundation

actor API {
    private let session: URLSession

    init() {
        let configuration = URLSessionConfiguration.default
        configuration.urlCache = URLCache(
            memoryCapacity: 32 * 1024 * 1024,
            diskCapacity: 256 * 1024 * 1024,
            directory: URL.cachesDirectory.appending(path: "API")
        )
        configuration.requestCachePolicy = .useProtocolCachePolicy
        configuration.waitsForConnectivity = true
        configuration.timeoutIntervalForResource = 60
        session = URLSession(configuration: configuration)
    }

    func data(for request: URLRequest) async throws -> Data {
        var attempt = 0
        while true {
            do {
                let (data, response) = try await session.data(for: request)
                guard let http = response as? HTTPURLResponse else { throw URLError(.badServerResponse) }
                if (200..<300).contains(http.statusCode) { return data }
                if http.statusCode >= 500, attempt < 4 { attempt += 1 } else { throw URLError(.badServerResponse) }
            } catch let error as URLError where error.code == .cancelled {
                throw error                                   // cancellation is not a failure to retry
            } catch where attempt < 4 {
                attempt += 1
            }
            let seconds = pow(2, Double(attempt))             // 2, 4, 8, 16
            try await Task.sleep(for: .seconds(seconds))
        }
    }
}
```

`URLCache(memoryCapacity:diskCapacity:directory:)` is current; `diskPath:` is deprecated. `waitsForConnectivity`
turns "no network yet" into a bounded wait — pair it with a request timeout.

---

## 2. Let HTTP do the caching you already paid for

`URLCache` obeys the response headers. Configure the server, not the client:

| Server header | Client behaviour |
| :--- | :--- |
| `Cache-Control: max-age=300` | Serves from cache for five minutes, no network call. |
| `ETag: "abc123"` | Sends `If-None-Match` on revalidation. |
| `Last-Modified` | Sends `If-Modified-Since` when no `ETag` exists. |
| `Cache-Control: no-store` | Never caches — use for account and payment screens. |
| `Cache-Control: private` | Caches per device; never in a shared proxy. |
| 304 Not Modified | URLSession returns the cached body as a 200; you see nothing. |
| `stale-if-error` | Not implemented by `URLCache`; handle stale fallback in your client. |

If you implement conditional requests yourself (custom store, not `URLCache`), a `304` arrives with an empty
body: read the stored payload, never `data`.

For a response you must never serve stale, set `.reloadIgnoringLocalCacheData` on that one request; for a screen
that must open fast and update after, use `.returnCacheDataElseLoad` and refresh in the background.

---

## 3. Reachability is a UI signal, not a gate

```swift
import Network
import SwiftUI

@Observable
@MainActor
final class NetworkMonitor {
    private(set) var isConnected = true
    private(set) var isExpensive = false
    private(set) var isConstrained = false

    private let monitor = NWPathMonitor()

    init() {
        Task { [monitor] in
            for await path in monitor {
                isConnected = path.status == .satisfied
                isExpensive = path.isExpensive
                isConstrained = path.isConstrained
            }
        }
    }
}
```

`NWPathMonitor` is an `AsyncSequence` on iOS 17+, so the `for await` loop replaces the `pathUpdateHandler`
closure and its `DispatchQueue.main.async` hop. Never gate a request on `isConnected`: the path can change
between the check and the call. Attempt the request; use the monitor to decide *presentation* — an offline
banner, a "retry when online" affordance, or pausing prefetch.

`isConstrained` is Low Data Mode. When it is true, skip video autoplay, high-resolution image prefetch, and
background sync over cellular.

---

## 4. The persistence boundary is an actor

Writes belong to a `@ModelActor`, reads for the UI belong to the main context. Crossing the boundary carries
DTOs, never model objects — a `@Model` class is not `Sendable`.

```swift
import SwiftData

struct NoteDTO: Sendable, Codable, Identifiable { var id: UUID; var title: String; var updatedAt: Date }

@Model
final class Note {
    @Attribute(.unique) var id: UUID
    var title: String
    var updatedAt: Date

    init(id: UUID, title: String, updatedAt: Date) {
        self.id = id
        self.title = title
        self.updatedAt = updatedAt
    }
}

@ModelActor
actor NoteWriter {
    /// Upsert by server id, so a replay after reconnect cannot duplicate rows.
    func merge(_ incoming: [NoteDTO]) throws {
        for dto in incoming {
            let id = dto.id
            let matches = try modelContext.fetch(
                FetchDescriptor<Note>(predicate: #Predicate { $0.id == id })
            )
            if let note = matches.first {
                note.title = dto.title
                note.updatedAt = dto.updatedAt
            } else {
                modelContext.insert(Note(id: dto.id, title: dto.title, updatedAt: dto.updatedAt))
            }
        }
        try modelContext.save()
    }
}
```

`@ModelActor` gives the actor its own `ModelContext` and executor; `modelContext` is the generated handle.
The `.unique` attribute on `id` makes the upsert idempotent, which is what makes retries safe.

---

## 5. Conflict resolution: pick a rule, write it down

| Rule | Implementation | Use when |
| :--- | :--- | :--- |
| Server wins | Overwrite local with the response, keep a local draft | Documents, prices, inventory |
| Client wins with a base version | Send `If-Match: <etag>`; a `412` means someone else changed it | Collaborative editing |
| Last write wins by timestamp | Compare `updatedAt`, keep the newer | Low-stakes preferences |
| Merge fields | Field-level timestamps or a CRDT | Offline-first notes |

Whatever the rule, make the write idempotent (client-generated `UUID` or an `Idempotency-Key` header) so a retry
after a timeout does not create a second row.

---

## 6. Background transfers

```swift
final class DownloadClient: NSObject, URLSessionDownloadDelegate {
    private lazy var session: URLSession = {
        let configuration = URLSessionConfiguration.background(withIdentifier: "com.example.downloads")
        configuration.isDiscretionary = true          // let the system pick the moment
        configuration.sessionSendsLaunchEvents = true
        return URLSession(configuration: configuration, delegate: self, delegateQueue: nil)
    }()

    func urlSession(_ session: URLSession, downloadTask: URLSessionDownloadTask,
                    didFinishDownloadingTo location: URL) {
        // Move the file synchronously: this URL is deleted when the method returns.
    }

    func urlSessionDidFinishEvents(forBackgroundURLSession session: URLSession) {
        // Call the completion handler captured in
        // application(_:handleEventsForBackgroundURLSession:completionHandler:).
    }
}
```

Background sessions hand control back to the system, so the file at `location` is temporary — copy it inside the
delegate method. Store the completion handler from the app delegate and call it from
`urlSessionDidFinishEvents(forBackgroundURLSession:)`, or the system will keep throttling relaunches.

---

## 7. Offline checklist

- [ ] Every screen renders from local data when the network fails; the error is a message, not an empty view.
- [ ] Retries are bounded, jittered, and cancelled when the view goes away (`SWU017`).
- [ ] `URLError.cancelled` is rethrown, never retried.
- [ ] Writes are idempotent and carry a client-generated identifier.
- [ ] `isConstrained` suppresses large downloads and autoplay.
- [ ] Background session completion handlers are stored and invoked exactly once.

Related: [architecture-and-clean-code.md](architecture-and-clean-code.md),
[cloudkit-sync-data.md](cloudkit-sync-data.md),
[performance-optimization.md](performance-optimization.md).
