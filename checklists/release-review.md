# Pre-Release & App Store Readiness Review Checklist

Use this checklist prior to submitting an iOS, iPadOS, or macOS application for App Store review or production distribution.

---

## 1. App Store Review Guidelines - Design (Section 4)
- [ ] **Native Experience**: The app provides a high-quality native experience and does not merely wrap a responsive website inside a WebView (Guideline 4.2).
- [ ] **No Placeholder Content**: All sample text ("Lorem ipsum"), mock test data, and placeholder icons are removed.
- [ ] **Broken Links & Navigation**: All navigation routes, deep links, and external Safari links are functional and lead to valid destinations.
- [ ] **Sign in with Apple**: If third-party or social login providers (Google, Facebook) are supported, **Sign in with Apple** is offered with equal prominence.

---

## 2. App Icons & Launch Screen
- [ ] **App Icon Resolution**: App icon provided at 1024×1024pt in sRGB or Display P3 color space.
- [ ] **No Alpha Channel**: App icon contains zero transparency / alpha channels (App Store will reject icons with alpha).
- [ ] **No Pre-Rounded Corners**: App icon is submitted as a full square; Apple's system squircle mask is applied dynamically by the OS.
- [ ] **Native Launch Screen**: Launch screen matches initial application canvas background and layout to prevent visual flash on startup.

---

## 3. Privacy Manifests & Permission Descriptions
- [ ] **Privacy Manifest (`PrivacyInfo.xcprivacy`)**: Required reason APIs (e.g. file timestamps, user defaults, system boot time) are declared accurately in the privacy manifest.
- [ ] **Clear Permission Strings**: `Info.plist` usage descriptions (`NSCameraUsageDescription`, `NSLocationWhenInUseUsageDescription`, etc.) clearly explain *why* the user should grant access.
- [ ] **Just-In-Time Permissions**: Permissions are requested in context when the user attempts a related action, never immediately on initial app launch.

---

## 4. Runtime Stability & Performance
- [ ] **MainActor Strict Safety**: Code compiled under Swift 6 strict concurrency with zero data-race warnings or main thread UI violations.
- [ ] **Memory Leaks**: Instruments Leaks and Allocations profiles show no retain cycles in navigation closures or view models.
- [ ] **Offline Resilience**: When airplane mode is enabled, the app displays a clear `ContentUnavailableView` or cached state without crashing or freezing.
- [ ] **Fast Launch Time**: App becomes interactive within 400ms of launch on supported devices.
