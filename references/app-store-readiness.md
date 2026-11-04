# App Store Review & Submission Readiness

Preparing an application for App Store Review requires comprehensive auditing across Apple's five official Review Guideline pillars: **Safety**, **Performance**, **Business**, **Design**, and **Legal**. 

> **Important Notice**: This review protocol provides a technical risk assessment based on published App Store Review Guidelines and App Store precedent. It does **not** guarantee App Store approval, as final review decisions are made exclusively by Apple's App Review team.

---

## 1. The 5 App Store Review Guideline Pillars

### Pillar 1: Safety (Section 1)
- **User-Generated Content (UGC) (Guideline 1.2)**: Apps featuring user-generated text, photos, or audio **must** include:
  1. A mechanism to report offensive content.
  2. A mechanism to block abusive users.
  3. Terms of Service / EULA specifying zero tolerance for objectionable content.
  4. Active moderation response within 24 hours.

### Pillar 2: Performance (Section 2)
- **App Completeness (Guideline 2.1)**:
  - Apps with crashes, non-functional buttons, broken URLs, or placeholder text ("Lorem Ipsum", "Test Product") are rejected immediately.
  - Test accounts with active demo data must be supplied in App Store Connect review notes.
- **Accurate Metadata (Guideline 2.3)**:
  - Screenshots must reflect the actual running app on device displays (not misleading mockups or non-existent hardware).
  - Search keywords and descriptions must accurately represent app functionality.

### Pillar 3: Business (Section 3)
- **In-App Purchases (Guideline 3.1.1)**:
  - Digital content, subscriptions, features, or game currencies unlocked within the app **must** use Apple's In-App Purchase (StoreKit 2).
  - External web checkout links for digital goods are strictly prohibited unless authorized under regional regulatory exemptions (e.g. EU Alternative Terms).
- **Auto-Renewing Subscriptions (Guideline 3.1.2)**:
  - Paywalls must clearly disclose: Subscription title, duration (e.g., 1 month), pricing, billing terms, and instructions on how to cancel in Apple ID settings.
  - Must provide functional "Restore Purchases" and "Terms of Use (EULA)" buttons.

### Pillar 4: Design (Section 4)
- **Minimum Functionality (Guideline 4.2)**:
  - Apps that merely repackage a website inside a `WKWebView` without native iOS capabilities (push notifications, widgets, native controls, offline mode) will be rejected.
- **Sign in with Apple (Guideline 4.8)**:
  - If your app supports third-party or social login (Google, Facebook, X, GitHub), you **must** also offer **Sign in with Apple** with equal or greater prominence.

### Pillar 5: Legal & Privacy (Section 5)
- **Data Collection & Storage (Guideline 5.1.1)**:
  - Apps must present a clear Privacy Policy URL.
  - In-app account deletion must be supported if users can register an account (Guideline 5.1.1(v)).

---

## 2. In-App Purchase & Subscription Paywall Compliance (StoreKit 2)

Modern paywalls built with StoreKit 2 should utilize native subscription views to guarantee immediate guideline compliance:

```swift
import SwiftUI
import StoreKit

struct NativeSubscriptionPaywall: View {
    @Environment(\.dismiss) private var dismiss
    let productIDs = ["com.app.pro.monthly", "com.app.pro.yearly"]
    
    var body: some View {
        SubscriptionStoreView(productIDs: productIDs) {
            VStack(spacing: 12) {
                Image(systemName: "crown.fill")
                    .font(.system(size: 56))
                    .foregroundStyle(.yellow)
                    .symbolEffect(.bounce, options: .repeating)
                
                Text("Unlock Pro Membership")
                    .font(.largeTitle)
                    .fontWeight(.bold)
                
                Text("Unlimited sync, advanced export, and priority customer support.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
            }
            .padding()
        }
        .subscriptionStorePolicyDestination(url: URL(string: "https://example.com/privacy")!, for: .privacyPolicy)
        .subscriptionStorePolicyDestination(url: URL(string: "https://example.com/terms")!, for: .termsOfService)
        // Native StoreKit 2 restore and cancellation disclosures are automatically embedded
    }
}
```

---

## 3. Mandatory Sign in with Apple Implementation (Guideline 4.8)

When offering social sign-in, embed the native `SignInWithAppleButton`:

```swift
import SwiftUI
import AuthenticationServices

struct SocialLoginOptionsView: View {
    @State private var authViewModel = AuthenticationViewModel()
    
    var body: some View {
        VStack(spacing: 16) {
            // Mandatory Sign in with Apple
            SignInWithAppleButton(.signIn) { request in
                request.requestedScopes = [.fullName, .email]
            } onCompletion: { result in
                switch result {
                case .success(let authorization):
                    authViewModel.handleAppleAuth(authorization)
                case .failure(let error):
                    authViewModel.handleAuthError(error)
                }
            }
            .signInWithAppleButtonStyle(.black)
            .frame(height: 50)
            .cornerRadius(12)
            
            // Secondary third-party login
            Button {
                authViewModel.loginWithGoogle()
            } label: {
                HStack {
                    Image("google_icon")
                    Text("Continue with Google")
                }
                .frame(maxWidth: .infinity, minHeight: 50)
                .background(Color(uiColor: .secondarySystemBackground), in: RoundedRectangle(cornerRadius: 12))
            }
        }
        .padding(.horizontal, 24)
    }
}
```

---

## 4. Standard App Store Review Finding Report Format

When auditing an application or code module, format each finding strictly as follows:

```markdown
### [CRITICAL | HIGH | MEDIUM | LOW] Issue Title

1. **Affected File / Screen / Configuration**:
   - `file:///path/to/SettingsView.swift#L45`
2. **Relevant Apple Guideline / Documentation**:
   - [App Store Review Guideline 5.1.1(v) - Account Deletion](https://developer.apple.com/app-store/review/guidelines/#data-collection-and-storage)
3. **Why the Issue Matters**:
   - Apps allowing account registration that do not provide an immediate, in-app path for users to initiate account deletion are rejected under Guideline 5.1.1(v).
4. **Severity**:
   - **Critical**: Guaranteed App Store rejection upon review submission.
5. **Recommended Fix**:
   - Add a visible "Delete Account" button in account settings with a confirmation dialog triggering user data deletion on your backend.
6. **Implementation Example**:
   \`\`\`swift
   // See references/privacy-and-security.md Section 5 for the complete code.
   \`\`\`
7. **Verification Method**:
   - Run the app, navigate to Settings → Account, tap Delete Account, verify confirmation dialog appears, and confirm the test account data is wiped.
```

---

## 5. Official Guidelines Reference
- [Apple App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/)
- [StoreKit 2 Documentation](https://developer.apple.com/documentation/storekit)
- [Sign in with Apple Documentation](https://developer.apple.com/sign-in-with-apple/)
