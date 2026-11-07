# Flutter on Apple Platforms

> **Authority**: [Flutter — Automatic platform adaptations](https://docs.flutter.dev/ui/adaptive-responsive/platform-adaptations),
> [Internationalizing Flutter apps](https://docs.flutter.dev/ui/internationalization),
> [Build and release an iOS app](https://docs.flutter.dev/deployment/ios),
> [Dart and Flutter MCP server](https://docs.flutter.dev/ai/mcp-server),
> Apple [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/).
> Verified 2026-11-07 with Flutter 3.44.8 / Dart 3.12.2, Xcode 27.2 and the iOS 27.2 Simulator
> ([recorded run](../assets/evidence/flutter-run.json)).

Flutter renders every pixel itself. That is its strength across platforms and the reason an iPhone build does not
become iOS-native by default: system Liquid Glass, native tab bars, SF Symbols, Dynamic Type metrics and
VoiceOver semantics only appear when the app asks for them. Everything Apple reviews — Info.plist, entitlements,
privacy manifest, icons, signing — lives in the native host `ios/Runner`.

---

## 1. Checks `audit_cross_platform` runs

| Code | Rule | Fix |
| :--- | :--- | :--- |
| `FLT001` | Text scaling disabled (`TextScaler.noScaling`, `textScaleFactor: 1`) | Remove; clamp one widget with `textScaler.clamp(maxScaleFactor: …)` if a layout cannot grow |
| `FLT002` | `Switch`, `Slider`, `CircularProgressIndicator`, `Checkbox`, `Radio`, `AlertDialog`, `RefreshIndicator` without `.adaptive()` | Use the adaptive constructor so iOS gets the Cupertino control |
| `FLT003` | Material bottom navigation on iOS | `CupertinoTabBar` on iOS, `NavigationBar` elsewhere (branch on `Platform.isIOS`) |
| `FLT004` | `IconButton` without `tooltip` | The tooltip becomes the VoiceOver label |
| `FLT005` | `GestureDetector` around an `Icon` | `IconButton`, or `Semantics(button: true, label: …)` |
| `FLT006` | Images without `semanticLabel` / `excludeFromSemantics` | Describe meaningful images, hide decorative ones |
| `FLT007` | `MaterialApp` without `darkTheme` | Provide `darkTheme`; keep `themeMode: ThemeMode.system` |
| `FLT008` | `EdgeInsets.only(left:)`, `Alignment.centerLeft`, `TextAlign.left` | `EdgeInsetsDirectional`, `AlignmentDirectional`, `TextAlign.start` |
| `FLT009` | ARB / `supportedLocales` languages missing from Xcode `knownRegions` | Runner › Info › Localizations › `+` (Flutter's documented step) |
| `XPL010` | Permission plugin without its Info.plist usage description (`camera` → camera *and* microphone, `geolocator`, `image_picker`, `local_auth` …) | Add the key with the specific purpose; iOS terminates the app without it |
| `XPL012` | No `PrivacyInfo.xcprivacy` in `ios/Runner` | Plugins ship their own; the app still declares its own required-reason API use |
| `XPL020` | iOS deployment target below the installed Xcode's minimum | Raise `IPHONEOS_DEPLOYMENT_TARGET` (and the Podfile platform) |

**Recorded finding:** a fresh `flutter create` project on Flutter 3.44.8 sets `IPHONEOS_DEPLOYMENT_TARGET = 13.0`;
Xcode 27.2 supports 15.0–27.2 and `flutter build ios --simulator` fails until it is raised. `XPL020` reads the
minimum from the installed SDK's `SDKSettings.json`, so it stays correct as Xcode moves.

---

## 2. What Flutter adapts on iOS by itself

Push transitions with parallax, edge-swipe back, bouncing scroll physics with momentum, status-bar tap to scroll to
top, San Francisco typography, iOS text selection and toolbar, adapted Material icons (`Icons.adaptive`), light
haptics on pickers. Text fields are **not** restyled automatically.

## 3. Making it feel native

- **Controls:** `.adaptive()` constructors; Cupertino widgets (`CupertinoNavigationBar`, `CupertinoSliverNavigationBar`,
  `CupertinoActionSheet`, `CupertinoContextMenu`, `CupertinoPicker`) where the iOS idiom is expected.
- **Navigation:** iOS tab bar at the bottom (`CupertinoTabBar`), large titles (`CupertinoSliverNavigationBar`), modal
  sheets with `fullscreenDialog` / `showCupertinoModalPopup`.
- **Type:** keep Dynamic Type; test at the largest accessibility size; avoid fixed-height text containers.
- **Accessibility:** `Semantics` for custom controls, `MergeSemantics` for rows, `ExcludeSemantics` for decoration;
  verify in the Simulator's Accessibility Inspector.
- **Glass and materials:** Flutter cannot draw system Liquid Glass. Shader packages imitate it and will not track
  system changes. Prefer honest Cupertino/Material styling, or embed native UIKit/SwiftUI with `UiKitView` platform
  views where a system component matters.
- **Native features** (widgets, Live Activities, App Intents, App Clips, share extensions) are Swift targets added
  to `ios/Runner.xcodeproj`, sharing data through App Groups.

## 4. Screenshots

`capture_screenshots` works with `build/ios/iphonesimulator/Runner.app` from `flutter build ios --simulator`.

Route to each screen with the same launch argument the Swift and React Native examples use. Verified in the
Simulator:

| Route | Result on iOS |
| :--- | :--- |
| `-screen insights` → `SharedPreferencesAsync().getString('screen')` | **Works** — iOS puts launch arguments in the NSUserDefaults argument domain |
| `SIMCTL_CHILD_SCREEN=insights` → `Platform.environment['SCREEN']` | Does not work: `Platform.environment` is empty for Flutter apps on iOS |
| `simctl openurl habits://…` with `FlutterDeepLinkingEnabled` | Works, but iOS first shows “Open in …?”, which lands in the screenshot |

Locale comes from `-AppleLanguages`/`-AppleLocale` like any iOS app; it is honoured only for languages in
`supportedLocales` **and** `knownRegions`. Example: [`examples/flutter-pipeline`](../examples/flutter-pipeline/README.md).

## 5. Release

`plan_distribution` detects Flutter and plans:

```bash
flutter pub get
flutter build ipa --release --export-options-plist=build/ExportOptions-app-store.plist   # build/ios/archive, build/ios/ipa
xcrun altool --validate-app build/ios/ipa/*.ipa --api-key "$ASC_KEY_ID" --api-issuer "$ASC_ISSUER_ID"
xcrun altool --upload-package build/ios/ipa/*.ipa --api-key "$ASC_KEY_ID" --api-issuer "$ASC_ISSUER_ID" --wait
```

Version and build come from `pubspec.yaml` (`version: 1.4.0+12` → `CFBundleShortVersionString` 1.4.0,
`CFBundleVersion` 12); override with `--build-name`/`--build-number`. Consider `--obfuscate --split-debug-info`.

## 6. Pair with

- **Dart and Flutter MCP server** (`dart mcp-server`, Dart 3.9+/Flutter 3.35+, experimental): analysis, pub.dev
  search, tests and runtime errors. This server adds the Apple side.
- **[flutter/agent-plugins](https://github.com/flutter/agent-plugins)**: official skills for localization setup,
  responsive layout, routing, tests and architecture.
