# In-App Purchases & StoreKit 2 Monetization

> **Authority**: [Apple Human Interface Guidelines — In-App Purchase](https://developer.apple.com/design/human-interface-guidelines/in-app-purchase), [StoreKit Documentation](https://developer.apple.com/documentation/storekit), [App Store Review Guidelines 3.1](https://developer.apple.com/app-store/review/guidelines/#business)  
> **Status**: Official Apple Requirements & Architectural Best Practices

StoreKit 2 provides a modern, Swift-concurrency-native API for processing in-app purchases, auto-renewing subscriptions, non-consumables, and promotional offers.

---

## 1. Product Types

| Type | Examples | Restorable | Server Verification |
| :--- | :--- | :--- | :--- |
| **Consumable** | Coins, game lives, AI query credits | No (lost on reinstall unless synced to app backend) | Recommended |
| **Non-Consumable** | Pro Unlock, Lifetime License, filter pack | Yes (must have Restore button) | Supported |
| **Auto-Renewing Sub** | Monthly / Annual subscriptions | Yes (managed in App Store settings) | JWS App Store Server API |
| **Non-Renewing Sub** | 1-season sports pass, 6-month trial | Yes | App server or iCloud |

---

## 2. StoreKit 2 SwiftUI Views (iOS 17+)

Apple provides first-party SwiftUI views that handle styling, legal disclosures, terms of service, and purchase flows automatically.

```swift
import SwiftUI
import StoreKit

struct PaywallView: View {
    let subscriptionGroupID = "21405928"

    var body: some View {
        SubscriptionStoreView(groupID: subscriptionGroupID) {
            // Custom Header Banner
            VStack(spacing: 8) {
                Image(systemName: "sparkles")
                    .font(.system(size: 48))
                    .foregroundStyle(.tint)
                Text("Unlock Studio Pro")
                    .font(.title2.bold())
                Text("Access unlimited exports, spatial filters, and 4K rendering.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding(.vertical)
        }
        .subscriptionStoreControlStyle(.picker)
        .storeButton(.visible, for: .restorePurchases)
        .storeButton(.visible, for: .policies)
    }
}
```

---

## 3. Transaction Monitoring & Swift Concurrency

Always listen to transaction updates on app launch to capture background renewals, family sharing grants, and external revocations.

```swift
import StoreKit

@Observable
final class SubscriptionManager {
    static let shared = SubscriptionManager()
    
    var isProUser = false
    private var updatesTask: Task<Void, Never>?

    init() {
        updatesTask = listenForTransactions()
        Task {
            await updatePurchasedStatus()
        }
    }

    deinit {
        updatesTask?.cancel()
    }

    private func listenForTransactions() -> Task<Void, Never> {
        Task.detached(priority: .background) {
            for await result in Transaction.updates {
                do {
                    let transaction = try self.checkVerified(result)
                    await self.updatePurchasedStatus()
                    await transaction.finish()
                } catch {
                    print("Transaction verification failed: \(error)")
                }
            }
        }
    }

    @MainActor
    func updatePurchasedStatus() async {
        var purchasedIDs = Set<String>()

        for await result in Transaction.currentEntitlements {
            if case .verified(let transaction) = result {
                if transaction.revocationDate == nil {
                    purchasedIDs.insert(transaction.productID)
                }
            }
        }

        self.isProUser = purchasedIDs.contains("com.example.pro.annual") ||
                         purchasedIDs.contains("com.example.pro.monthly")
    }

    private func checkVerified<T>(_ result: VerificationResult<T>) throws -> T {
        switch result {
        case .unverified(_, let error):
            throw error
        case .verified(let safe):
            return safe
        }
    }
}
```

---

## 4. App Store Review Guidelines Compliance (Section 3.1)

Apps frequently get rejected for paywall violations. Ensure the following rules are strictly satisfied:

1. **Explicit Pricing and Terms**:
   - Must clearly show subscription length (e.g. "$4.99 / month" or "$39.99 / year").
   - Free trial duration must be prominently displayed (e.g. "3-day free trial, then $39.99/year").
2. **Restore Purchases**:
   - Must provide a clear "Restore Purchases" button on every screen where purchases are offered.
3. **Legal Links**:
   - Direct, clickable links to your **Terms of Use (EULA)** and **Privacy Policy** must be present on the paywall screen itself.
4. **No Misleading Claims**:
   - Do not claim a purchase is "Free" if it automatically converts into a paid recurring subscription.
5. **Xcode Local Testing**:
   - Use an `.storekit` configuration file in Xcode Schemes to test expired cards, renewals, upgrades, downgrades, and refunds without connecting to sandbox servers.
