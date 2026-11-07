# Cross-Platform Apps, Apple-Native Results

> **Scope**: Flutter, React Native, Expo, Capacitor/Ionic, .NET MAUI and Kotlin/Compose Multiplatform shipping to
> iPhone, iPad and Mac. Framework details: [Flutter](flutter-apple-native.md) ·
> [React Native and Expo](react-native-expo-apple-native.md). Reviewed 2026-11-07.

Apple does not review frameworks; it reviews the app. VoiceOver, Dynamic Type, Dark Mode, privacy manifests,
usage descriptions, screenshots and signing apply identically. This server therefore treats every app as
**framework code + a native host project** and runs the Apple-side tools on the host.

---

## 1. How the tools see each framework

| Framework | Detected by | iOS host | How UI is drawn | Native ceiling |
| :--- | :--- | :--- | :--- | :--- |
| Flutter | `pubspec.yaml` with `sdk: flutter` | `ios/Runner.xcodeproj` | Own engine (Impeller) | Cupertino widgets, adaptive constructors, platform views |
| React Native | `react-native` in `package.json` | `ios/<App>.xcworkspace` | UIKit views | Native modules, `react-native-screens`, `PlatformColor` |
| Expo | `expo` in `package.json` | `ios/` after prebuild, or none (EAS) | UIKit + **SwiftUI via `@expo/ui`** | Real SwiftUI, Liquid Glass, SF Symbols |
| Capacitor / Ionic | `@capacitor/core` or `capacitor.config.*` | `ios/App` | WKWebView | Native plugins; web layer decides the feel |
| .NET MAUI | `.csproj` with `UseMaui` / `net*-ios` | `Platforms/iOS` | UIKit handlers | Platform-specific code in `Platforms/iOS` |
| Kotlin / Compose Multiplatform | Gradle + `iosApp/` | `iosApp/iosApp.xcodeproj` | Compose draws its own UI; SwiftUI screens are native | Mix SwiftUI screens with shared Kotlin logic |

`inspect_apple_project`, `audit_privacy_manifest`, `plan_distribution` and `capture_screenshots` find the host in
`ios/`, `macos/`, `ios/App` or `iosApp/` automatically. `audit_cross_platform` checks the framework layer;
`audit_project` runs both.

## 2. The Apple-native checklist for any framework

- [ ] Text follows Dynamic Type up to the largest accessibility size (no scaling overrides)
- [ ] Every control has a VoiceOver label and role; decorative images are hidden
- [ ] Dark Mode follows the system (Expo's default is **light**)
- [ ] iOS navigation idioms: tab bar at the bottom, back swipe, sheets, large titles
- [ ] Windows resize (iPad multitasking, Stage Manager, iPhone Duo) — no fixed screen sizes
- [ ] Right-to-left layouts mirror (start/end, not left/right)
- [ ] Every permission plugin has a specific usage description
- [ ] Every language the app ships is registered in the iOS project (Flutter: `knownRegions`)
- [ ] `PrivacyInfo.xcprivacy` in the host, besides the plugins' own manifests
- [ ] Deployment target within the installed Xcode's supported range
- [ ] App icon with dark and tinted appearances (Icon Composer `.icon` where the framework supports it)

## 3. Where a framework stops

System Liquid Glass, widgets, Live Activities, App Intents, App Clips, Siri and share extensions are Apple
frameworks used from Swift. Every framework above reaches them through a **native Swift target** in the host
project (communicating via App Groups or native modules). Plan those as Swift work and review them with the Swift
auditors (`lint_swiftui`, `validate_widgets`).

## 4. Screenshots and release

| Framework | Simulator build for `capture_screenshots` | Release (`plan_distribution`) |
| :--- | :--- | :--- |
| Flutter | `flutter build ios --simulator` → `build/ios/iphonesimulator/Runner.app` | `flutter build ipa --export-options-plist=…` → altool |
| React Native | `xcodebuild -workspace ios/<App>.xcworkspace -scheme <App> -sdk iphonesimulator -configuration Release -derivedDataPath build` | `pod install` → archive → export/upload |
| Expo | `npx expo run:ios --configuration Release` | EAS build + submit, or prebuild + Xcode |
| Capacitor | `npx cap sync ios`, then `xcodebuild` on `ios/App/App.xcworkspace` | sync → archive → export/upload |
| .NET MAUI | `dotnet build -f net10.0-ios -p:RuntimeIdentifier=iossimulator-arm64` | `dotnet publish -f net10.0-ios -c Release -p:ArchiveOnBuild=true` |
| KMP | `xcodebuild` on `iosApp/iosApp.xcodeproj` (Gradle runs in a build phase) | archive → export/upload |

Screen routing: pass `-screen <name>` as a launch argument and read it from the NSUserDefaults argument domain —
`UserDefaults` (Swift), `Settings.get` (React Native), `SharedPreferencesAsync` (Flutter),
`NSUserDefaults.StandardUserDefaults` (MAUI), `NSUserDefaults.standardUserDefaults` (Kotlin/Native). Swift and
Flutter are verified in the recorded runs; the others use the same NSUserDefaults lookup but have not been
recorded here. Avoid custom-scheme deep links for captures: iOS asks for confirmation first, and
`Platform.environment` is empty for Flutter on iOS.

## 5. Ecosystem (reviewed on GitHub, 2026-11-07)

| Source | Use |
| :--- | :--- |
| [Dart and Flutter MCP server](https://docs.flutter.dev/ai/mcp-server) — [dart-lang/ai](https://github.com/dart-lang/ai) | Dart analysis, pub.dev, tests, runtime errors |
| [flutter/agent-plugins](https://github.com/flutter/agent-plugins) | Official Flutter/Dart agent skills |
| [Expo MCP server](https://docs.expo.dev/mcp/) and [expo/skills](https://github.com/expo/skills) | Expo docs, compatible installs, EAS, `@expo/ui`, App Store deployment |
| [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills) | React Native performance, upgrades, navigation, tvOS |
| [margelo/react-native-skills](https://github.com/margelo/react-native-skills) | Nitro modules, Swift/C++ native modules, VisionCamera |
| [FormidableLabs/eslint-plugin-react-native-a11y](https://github.com/FormidableLabs/eslint-plugin-react-native-a11y) | Exhaustive React Native accessibility linting |
| [ionic-team/capacitor](https://github.com/ionic-team/capacitor), [dotnet/maui](https://github.com/dotnet/maui), [JetBrains/compose-multiplatform](https://github.com/JetBrains/compose-multiplatform) | Framework sources for their iOS hosts |

Those servers and skills know their framework; this server knows Apple's side — HIG, App Store specifications,
privacy, Simulator captures and distribution. Use them together.
