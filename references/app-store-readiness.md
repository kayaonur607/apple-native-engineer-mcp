# App Store Review & Submission Readiness

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.
> **Authority**: [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/), [App Store Connect Help — App information](https://developer.apple.com/help/app-store-connect/reference/app-information/app-information), [App Privacy Details](https://developer.apple.com/app-store/app-privacy-details/)

Rejections are mechanical, not aesthetic. A reviewer works through a short list — does the build crash, is the metadata accurate, is the paywall legal, is the manifest present — and one failure stops the submission. This guide covers the checks that stop builds, and the local tool that predicts each one before upload.

---

## 1. The clauses that reject builds

| Clause | What the reviewer checks | The failure it catches |
| :--- | :--- | :--- |
| **2.1 App Completeness** | Final build, no placeholder text or empty URLs, working demo account, every configured in-app purchase visible and purchasable. | "We will reject incomplete app bundles and binaries that crash or exhibit obvious technical problems." |
| **2.5.1 Software Requirements** | Public APIs only; the app runs on the currently shipping OS; deprecated frameworks are phased out. | Private selectors, `dlopen` of system frameworks, binaries that only launch on an old OS. |
| **3.1.1 In-App Purchase** | Features, subscriptions, premium content and currencies are unlocked through IAP — not license keys, QR codes or crypto wallets. | A "restore licence" field or a web checkout for a digital unlock. |
| **3.1.1(a) Link to Other Purchase Methods** | Outside the **United States** storefront, a button or link to an outside purchase destination needs a StoreKit External Purchase Link entitlement. In the US storefront that prohibition does not apply. | Steering copy in metadata or UI that is legal in one storefront and not another. |
| **3.1.2 Subscriptions** | Ongoing value, a period of at least seven days, availability across the user's devices. | A 3-day "subscription" or a subscription that unlocks nothing new. |
| **4.2 Minimum Functionality** | Features, content and UI beyond a repackaged website. | A `WKWebView` shell with a share button. |
| **4.3 Spam** | One bundle ID per app; no variants indistinguishable from what is already on the store. | A separate app per city, team or university; another flashlight or timer. |
| **4.8 Login Services** | If a third-party or social login sets up the user's primary account, an equivalent option is required that limits data collection to name and email, lets users keep the email private, and does not use interactions for ads without consent. | Google-only sign-in with no equivalent, or an "equivalent" that harvests contacts. |
| **5.1.1 Privacy** | Privacy policy link in App Store Connect metadata **and** in the app; in-app account deletion when accounts can be created. | A policy URL that 404s, or "email us to delete your account". |
| **5.1.2 Data Use and Sharing** | Explicit permission before sharing personal data with third parties — including third-party AI — and ATT consent before tracking. | An analytics SDK that ships data before the ATT prompt. |

Two clauses changed recently and catch otherwise-compliant apps: 5.1.2 now names **third-party AI** as a disclosure, and 3.1.1(a) is no longer uniform across storefronts. Read the clause, not last year's blog post.

---

## 2. Metadata limits

App Store Connect counts characters, not bytes, and blocks the field — not the submission — when you exceed the limit.

| Field | Limit | Validator code |
| :--- | ---: | :--- |
| Name | 30 | `META001`, `META002` (whitespace), `META003` (empty) |
| Subtitle | 30 | `META001`, `META002` |
| Keywords | 100 | `META001`, `META007` (duplicates), `META008` (single characters) |
| Promotional text | 170 | `META001` |
| Description | 4 000 | `META001`, `META003` (empty), `META010` (`http://`), `META011` (wall of text) |
| What's New | 4 000 | `META001` |
| Support URL, Privacy URL | required, `https://` | `META004` (missing), `META005` (not https) |
| Marketing URL | optional, `https://` | `META006` |
| Screenshots | 10 maximum per size | `META012` (fewer than 3), `META013` (more than 10) |

Apple's hard requirement is **at least one** screenshot per required device size; the validator warns below three because three is the conversion minimum, not the review minimum.

```json
{
  "name": "Northwind Ledger",
  "subtitle": "Receipts, reconciled daily",
  "keywords": "receipt,expense,ledger,invoice,scan",
  "description": "Photograph a receipt and Northwind files it against the right account.",
  "support_url": "https://example.com/support",
  "privacy_url": "https://example.com/privacy",
  "screenshots": ["01.png", "02.png", "03.png"]
}
```

```bash
python3 tools/metadata-validator/validate_metadata.py metadata.json
```

The validator also accepts `localizations` keyed by locale and the camelCase field names the App Store Connect API uses (`privacyPolicyUrl`, `promotionalText`), so one file serves both the human and the API path. It warns `META014` when no `en-US` localisation exists, because `en-US` is the fallback listing.

---

## 3. Icon and screenshot rules

App Store Connect rejects at upload time, silently, and the reason is rarely in the email.

| Rule | Value | Validator code |
| :--- | :--- | :--- |
| Marketing icon size | exactly 1024×1024 | `ASSET003` |
| Format | PNG | `ASSET002` |
| Alpha channel | none — flatten onto an opaque background | `ASSET004` |
| Bit depth | 8 bits per channel, sRGB | `ASSET005` |
| Corners | square; iOS applies the mask | — |
| `Contents.json` slots | every referenced file exists, every size matches | `ASSET013`, `ASSET014`, `ASSET015` |

Screenshots are accepted only at known device slots. The 6.9″ iPhone slots are the ones you must supply:

| Device | Portrait | Landscape |
| :--- | :--- | :--- |
| iPhone 6.9″ (Dynamic Island) | 1320×2868, 1290×2796 | 2868×1320, 2796×1290 |
| iPhone 6.5″ (Face ID) | 1242×2688, 1284×2778 | 2688×1242, 2778×1284 |
| iPad 13″ | 2064×2752, 2048×2732 | 2752×2064, 2732×2048 |

Apple requires the iPhone Dynamic Island (medium) size, and the iPad 13″ size when the app runs on iPad. An image that matches no slot is `ASSET022`, and the validator prints the closest accepted size, which is usually the fastest fix.

```bash
python3 tools/asset-validator/validate_assets.py --icon AppIcon-1024.png
python3 tools/asset-validator/validate_assets.py --screenshots ./fastlane/screenshots
python3 tools/asset-validator/validate_assets.py .          # walks .appiconset folders
```

> Dated requirement: App Store Connect states that from **April 2027** screenshots are required for any app built with the iOS 27.1 SDK or later. iPhone Duo screenshots are accepted separately, and supplying them adds a "made for iPhone Duo" badge to the product page. Budget for it in the release plan that crosses that date.

---

## 4. Privacy labels, age ratings, accessibility labels

Three questionnaires sit beside the binary, and all three are manual. None has an App Store Connect API endpoint, so treat the answers as source that needs review like any other.

- **App Privacy ("nutrition label")** — what you collect, whether it is linked to identity, whether it is used for tracking. It must match `PrivacyInfo.xcprivacy` and what the SDKs actually do. See [privacy-and-security.md](privacy-and-security.md).
- **Age rating** — a questionnaire over content descriptors, in-app controls and capabilities. On iOS 26, iPadOS 26, macOS 26, tvOS 26, visionOS 26 and watchOS 26 the categories are **4+, 9+, 13+, 16+, 18+**; earlier OS versions display legacy values. Answer for the worst content in the app, not the average.
- **Accessibility Nutrition Labels** — opt-in declarations for VoiceOver, Voice Control, Larger Text, Dark Interface, Differentiate Without Color Alone, Sufficient Contrast, Reduced Motion, Captions and Audio Descriptions. Claim only what you have tested; these are surfaced on the product page.

---

## 5. A paywall that survives 3.1.2

`SubscriptionStoreView` renders Apple's own disclosure, restore and policy controls, which is the shortest path to a compliant paywall.

```swift
import SwiftUI
import StoreKit

struct PaywallView: View {
    private let productIDs = ["com.example.pro.monthly", "com.example.pro.yearly"]

    var body: some View {
        SubscriptionStoreView(productIDs: productIDs) {
            VStack(spacing: 8) {
                Image(systemName: "crown.fill")
                    .font(.largeTitle)
                    .foregroundStyle(.tint)
                    .accessibilityHidden(true)
                Text("Pro")
                    .font(.largeTitle.bold())
                Text("Unlimited sync, exports, and priority support.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding()
        }
        .subscriptionStorePolicyDestination(
            url: URL(string: "https://example.com/privacy")!,
            for: .privacyPolicy
        )
        .subscriptionStorePolicyDestination(
            url: URL(string: "https://example.com/terms")!,
            for: .termsOfService
        )
        .storeButton(.visible, for: .restorePurchases)
    }
}
```

When you build the purchase path yourself instead, restore must still be reachable and functional:

```swift
import StoreKit

func restorePurchases() async throws -> [StoreKit.Transaction] {
    try await AppStore.sync()                       // shows the Apple ID sign-in prompt
    var restored: [StoreKit.Transaction] = []
    for await result in StoreKit.Transaction.currentEntitlements {
        if case .verified(let transaction) = result {
            restored.append(transaction)
        }
    }
    return restored
}
```

The anti-pattern to delete: a paywall that states a price in a `Text` literal instead of reading `product.displayPrice`. Localised prices and Apple's disclosure will disagree with your hard-coded string.

---

## 6. Login services (4.8)

If a social login establishes the primary account, guideline 4.8 requires an equivalent option that limits data to name and email, allows a private email address, and does not use interactions for advertising without consent. Sign in with Apple satisfies all three, which is why it is the usual answer.

```swift
import SwiftUI
import AuthenticationServices

struct AccountView: View {
    var onCredential: (ASAuthorizationAppleIDCredential) -> Void
    var onFailure: (Error) -> Void

    var body: some View {
        VStack(spacing: 12) {
            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.fullName, .email]
            } onCompletion: { result in
                switch result {
                case .success(let authorization):
                    if let credential = authorization.credential as? ASAuthorizationAppleIDCredential {
                        onCredential(credential)
                    }
                case .failure(let error):
                    onFailure(error)
                }
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .clipShape(.rect(cornerRadius: 12))

            Button("Continue with Google") {}
                .buttonStyle(.bordered)
        }
        .padding(.horizontal, 24)
    }
}
```

4.8 is about equivalence, not just presence: the alternative button needs the same height, the same width and no more friction than the social login it sits beside.

---

## 7. Before you upload

| Check | How |
| :--- | :--- |
| Metadata within every limit | `validate_metadata.py metadata.json` |
| Icon 1024×1024, PNG, no alpha | `validate_assets.py --icon AppIcon-1024.png` |
| Screenshots match a real slot | `validate_assets.py --screenshots ./screenshots` |
| Privacy manifest declares what the code touches | `audit_privacy.py .` |
| Every reachable API is public and current | `2.5.1`: grep for `NSClassFromString`, `dlopen`, `perform(Selector(` |
| Demo account in review notes | App Store Connect ▸ App Review Information |
| Account deletion reachable in-app | `5.1.1(v)` |
| Paywall shows price, duration, restore, terms | `3.1.2` — run the paywall in Sandbox |

## 8. Evidence

One line: `python3 tools/metadata-validator/validate_metadata.py metadata.json && python3 tools/asset-validator/validate_assets.py --icon AppIcon-1024.png --screenshots ./screenshots && python3 tools/privacy-auditor/audit_privacy.py .` — each tool names the rule it enforces (`META*`, `ASSET*`, `PRIV*`), so a failure is already a fix instruction. Live submission state: `python3 tools/app-store-connect/cli.py verify` — see [app-store-connect-api.md](app-store-connect-api.md).

Full documentation index: [official-resources.md](official-resources.md). Clause text: [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/).
