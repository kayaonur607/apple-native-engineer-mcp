# Offline Caching & Resilient Networking

> **Authority**: [Apple Developer Documentation — URLSession](https://developer.apple.com/documentation/foundation/urlsession), [Network Framework](https://developer.apple.com/documentation/network), [WWDC23: Support low-data and offline experiences](https://developer.apple.com/videos/play/wwdc2023/10156/)  
> **Status**: Official Apple Engineering Standards

Apple native applications must provide dependable offline behavior, graceful network degradation, responsive local caching, and low-power background synchronization.

---

## 1. Modern Structured Concurrency Networking

Use `URLSession.shared.data(from:)` with Swift concurrency, strong typing, and cancellation support.

```swift
import Foundation

actor NetworkClient {
    private let session: URLSession

    init(session: URLSession = .shared) {
        let configuration = URLSessionConfiguration.default
        // 50MB memory cache, 200MB disk cache
        configuration.urlCache = URLCache(
            memoryCapacity: 50 * 1024 * 1024,
            diskCapacity: 200 * 1024 * 1024,
            diskPath: "AppURLCache"
        )
        configuration.requestCachePolicy = .useProtocolCachePolicy
        configuration.waitsForConnectivity = true // Wait for network rather than failing instantly
        configuration.timeoutIntervalForResource = 60
        self.session = URLSession(configuration: configuration)
    }

    func fetch<T: Decodable>(_ type: T.Type, from url: URL) async throws -> T {
        var request = URLRequest(url: url)
        request.setValue("application/json", forHTTPHeaderField: "Accept")
        
        let (data, response) = try await session.data(for: request)
        
        guard let httpResponse = response as? HTTPURLResponse,
              (200...299).contains(httpResponse.statusCode) else {
            throw URLError(.badServerResponse)
        }

        let decoder = JSONDecoder()
        decoder.dateDecodingStrategy = .iso8601
        return try decoder.decode(T.self, from: data)
    }
}
```

---

## 2. Network Reachability Monitoring (`NWPathMonitor`)

Never block the UI while waiting for network. Monitor network paths reactively and inform the user without obstructing offline features.

```swift
import Network
import Observation

@Observable
final class NetworkMonitor {
    static let shared = NetworkMonitor()

    private let monitor = NWPathMonitor()
    private let queue = DispatchQueue(label: "com.example.networkmonitor")

    var isConnected: Bool = true
    var isExpensive: Bool = false // Cellular hotspot or metered Wi-Fi
    var isConstrained: Bool = false // Low Data Mode enabled

    private init() {
        monitor.pathUpdateHandler = { [weak self] path in
            DispatchQueue.main.async {
                self?.isConnected = (path.status == .satisfied)
                self?.isExpensive = path.isExpensive
                self?.isConstrained = path.isConstrained
            }
        }
        monitor.start(queue: queue)
    }

    deinit {
        monitor.cancel()
    }
}
```

---

## 3. Offline UI Banner & Graceful Degradation

```swift
struct OfflineStatusBanner: View {
    @State private var network = NetworkMonitor.shared

    var body: some View {
        if !network.isConnected {
            HStack(spacing: 8) {
                Image(systemName: "wifi.slash")
                Text("Working Offline — Changes will sync when reconnected.")
                    .font(.caption.bold())
            }
            .foregroundStyle(.white)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .frame(maxWidth: .infinity)
            .background(Color.orange)
            .transition(.move(edge: .top).combined(with: .opacity))
        }
    }
}
```

---

## 4. Background Uploads & Downloads

For long-running file transfers, use background `URLSession` sessions so tasks continue even if the user swipes away to another app or the system suspends the process.

```swift
let backgroundConfig = URLSessionConfiguration.background(withIdentifier: "com.example.mediaUploads")
backgroundConfig.isDiscretionary = true // Let system schedule during off-peak power/Wi-Fi
backgroundConfig.sessionSendsLaunchEvents = true
let uploadSession = URLSession(configuration: backgroundConfig, delegate: self, delegateQueue: nil)
```

---

## 5. Offline Engineering Principles

1. **Optimistic Local Updates**: When a user creates a new record, insert it into local SwiftData storage immediately and queue an async network synchronization task.
2. **Exponential Backoff**: If an API endpoint fails with HTTP 500 or network timeout, retry with jittered exponential backoff (1s, 2s, 4s, 8s, max 32s).
3. **Respect Low Data Mode (`isConstrained`)**: When active, avoid auto-playing videos, downloading high-resolution assets, or prefetching large payloads.
