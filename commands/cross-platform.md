---
description: "Bring any cross-platform app (Flutter, React Native, Expo, Capacitor, .NET MAUI, Kotlin/Compose Multiplatform) to Apple-native quality and ship it."
---

# Cross-platform app — Apple-native quality

Apple reviews the app, not the framework. Treat the project as framework code plus a native host, and hold both to
the same standard as a Swift app.

## 1. Identify

1. `audit_cross_platform` — which framework, where the iOS host lives, what blocks quality or review.
2. Route: Flutter → `/apple-native-flutter`; React Native or Expo → `/apple-native-react-native`; Capacitor,
   .NET MAUI and KMP continue here.
3. Read `apple-native://references/cross-platform-apple`.

## 2. Apply

- Capacitor: bundle web assets (no remote `server.url`, `CPC001`), honour safe areas, use native plugins for share,
  haptics and status bar; test feel on a device, not only the browser.
- .NET MAUI: `SemanticProperties`, `AppThemeBinding`, font auto-scaling on; Info.plist and privacy manifest in
  `Platforms/iOS`.
- KMP / Compose Multiplatform: keep iOS chrome (navigation, tab bars, sheets) in SwiftUI where it matters; share
  logic in Kotlin.
- For all: run `audit_privacy_manifest` and `plan_distribution` on the host; Apple-only features are Swift targets.

## Verify like a native team

1. `audit_cross_platform` again — no errors; every remaining warning fixed or justified.
2. Build for the Simulator and report the command and result.
3. `capture_screenshots` with the plan's `-screen` launch arguments: light, dark, a right-to-left locale and the
   largest Dynamic Type size; look at the images and fix what you see.
4. `plan_distribution` before release; account-changing steps only with approval.

## Report

Answer in the user's language with: outcome · files changed · checks actually run (tool + finding codes, build
command and result, simulator runs) · Apple and framework sources with URLs · what remains unverified · next action.
Static findings are not a build; a build is not a runtime check; neither is App Review approval.
