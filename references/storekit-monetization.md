# StoreKit 2 & Monetization

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Human Interface Guidelines — In-App Purchase](https://developer.apple.com/design/human-interface-guidelines/in-app-purchase), [StoreKit Documentation](https://developer.apple.com/documentation/storekit), [App Store Review Guidelines 3.1](https://developer.apple.com/app-store/review/guidelines/#business)

StoreKit 2 is the async/await API: `Product`, `Transaction`, `VerificationResult`, and system paywall views
that draw the price, the trial and the legal links for you. The old `SKProduct` / `SKPaymentQueue` surface
still exists; do not start new code on it.

---

## 1. What you may sell

| Product type | Example | Restorable | Notes |
| :--- | :--- | :--- | :--- |
| Consumable | Credits, coins, AI queries | No | Grant on the server; a reinstall loses local state |
| Non-consumable | Pro unlock, lifetime licence | Yes | Needs a visible Restore action |
| Auto-renewable subscription | Monthly / annual plan | Yes | Managed by the user in App Store settings |
| Non-renewing subscription | Season pass | Yes | You track expiry yourself |

App Store Review Guideline 3.1.1 requires in-app purchase for digital content, features and subscriptions
consumed inside the app. Physical goods, real-world services and person-to-person services use Apple Pay
instead. Reader apps and the region-specific external purchase link entitlement are the narrow exceptions;
both are review-configurable, not something you switch on in code.

---

## 2. Load products

```swift
import StoreKit

func loadProducts() async throws -> [Product] {
    let identifiers = ["com.example.pro.monthly", "com.example.pro.annual"]
    let products = try await Product.products(for: identifiers)
    // Order is not guaranteed; sort by price so the UI is stable.
    return products.sorted { $0.price < $1.price }
}
```

`Product.products(for:)` returns only products that are approved and available in the current storefront.
An empty array usually means a missing App Store Connect metadata row, not a code bug.

---

## 3. A paywall built from system views (iOS 17+)

```swift
import StoreKit
import SwiftUI

struct PaywallView: View {
    let groupID = "21405928"

    var body: some View {
        SubscriptionStoreView(groupID: groupID) {
            VStack(spacing: 8) {
                Image(systemName: "sparkles")
                    .font(.largeTitle)
                    .foregroundStyle(.tint)
                Text("Unlock Studio Pro")
                    .font(.title2.bold())
                Text("Unlimited exports and 4K rendering.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
            }
            .padding(.vertical)
        }
        .subscriptionStoreControlStyle(.picker)
        .storeButton(.visible, for: .restorePurchases, .policies)
    }
}
```

`SubscriptionStoreView` handles price localisation, the trial badge, renewal terms and the manage-subscription
link. The marketing content closure is the only part you design. For a single product use `ProductView(id:)`;
for a mixed set use `StoreView(ids:)` — both draw the price and purchase button themselves.

`.storeButton(.visible, for:)` takes `StoreButtonKind` values: `.restorePurchases`, `.policies`, `.signIn`,
`.redeemCode`, `.cancellation`. Restore and policies should be visible on every purchase surface.

---

## 4. Purchase, verify, finish

```swift
import StoreKit

enum PurchaseError: Error {
    case unverified
}

@MainActor
func buy(_ product: Product) async throws -> Bool {
    switch try await product.purchase() {
    case .success(let verification):
        guard case .verified(let transaction) = verification else {
            throw PurchaseError.unverified
        }
        await grantEntitlement(for: transaction.productID)
        await transaction.finish()
        return true
    case .userCancelled, .pending:
        return false
    @unknown default:
        return false
    }
}
```

`purchase()` returns `.success(VerificationResult<Transaction>)`, `.userCancelled` or `.pending`. `.pending`
means Ask to Buy or a deferred payment — do not show an error. Verify before granting, grant before
`finish()`: a crash between the two replays the transaction, which is the failure mode you want.

### Listen for transactions at launch

```swift
import StoreKit

@MainActor
final class Entitlements {
    static let shared = Entitlements()
    private(set) var owned: Set<String> = []
    private var updates: Task<Void, Never>?

    private init() {
        updates = Task { [weak self] in
            for await result in Transaction.updates {
                guard case .verified(let transaction) = result else { continue }
                await self?.refresh()
                await transaction.finish()
            }
        }
    }

    func refresh() async {
        var ownedIDs = Set<String>()
        for await result in Transaction.currentEntitlements {
            guard case .verified(let transaction) = result,
                  transaction.revocationDate == nil else { continue }
            ownedIDs.insert(transaction.productID)
        }
        owned = ownedIDs
    }
}
```

`Transaction.currentEntitlements` is the right source of truth and is **not** deprecated — only the
per-product `currentEntitlement(for:)` was. `Transaction.updates` delivers renewals, refunds, Family Sharing
grants and purchases made on another device while your app was closed.

---

## 5. Subscription status, in a view

```swift
import StoreKit
import SwiftUI

struct ProGate<Content: View>: View {
    let groupID = "21405928"
    @State private var isPro = false
    @ViewBuilder var content: Content

    var body: some View {
        content
            .subscriptionStatusTask(for: groupID) { state in
                switch state {
                case .loading:
                    break
                case .failure:
                    isPro = false
                case .success(let statuses):
                    isPro = statuses.contains {
                        $0.state == .subscribed || $0.state == .inGracePeriod
                    }
                }
            }
    }
}
```

`EntitlementTaskState` is `.loading`, `.failure` or `.success`, with `.value` for the non-optional result.
`RenewalState` is `.subscribed`, `.expired`, `.inBillingRetryPeriod`, `.inGracePeriod` or `.revoked`. Treat
grace period as entitled and billing retry as entitled-but-warn; the user has paid and Apple is retrying.

---

## 6. Offers

| Offer | Configured in | API |
| :--- | :--- | :--- |
| Introductory (free trial, pay-as-you-go) | App Store Connect | Automatic eligibility; `Product.SubscriptionOffer.OfferType.introductory` |
| Promotional | Your server signs the offer | `Product.PurchaseOption.promotionalOffer(...)` |
| Offer code | App Store Connect | `offerCodeRedemption(...)` sheet |
| Win-back | App Store Connect, iOS 18+ | `Product.PurchaseOption.winBackOffer(_:)` |

```swift
import StoreKit
import SwiftUI

struct RedeemScreen: View {
    @State private var showRedeem = false

    var body: some View {
        VStack {
            Button("Redeem Code") { showRedeem = true }
            if #available(iOS 27.0, macOS 27.0, *) {
                StoreView(ids: ["com.example.pro.annual"])
                    .offerCodeRedemption(options: [], isPresented: $showRedeem) { _ in }
            } else {
                StoreView(ids: ["com.example.pro.annual"])
                    .offerCodeRedemption(isPresented: $showRedeem) { _ in }
            }
        }
    }
}
```

iOS 27 deprecates `offerCodeRedemption(isPresented:onCompletion:)` in favour of the `options:` form. The old
call still compiles, so the guard is about warnings and future removal, not a hard break.

---

## 7. Review checklist

- [ ] Digital content uses in-app purchase; physical goods use Apple Pay — Guideline 3.1.1
- [ ] Price, period and trial length are visible before the purchase button
- [ ] Restore Purchases and Terms/Privacy links are on the paywall, not buried in Settings
- [ ] `.storekit` configuration file used to test expiry, renewal, upgrade and refund paths
- [ ] Every transaction is verified before entitlement is granted and finished afterwards
- [ ] `Transaction.updates` listener starts at launch and survives background renewals
- [ ] Subscription UI handles grace period, billing retry and revocation
- [ ] App Store Server Notifications configured if entitlement is enforced by a backend

See `app-store-readiness.md` for the submission side, and `whats-new-ios-27.md` for the iOS 27 subscription
bundle product types.
