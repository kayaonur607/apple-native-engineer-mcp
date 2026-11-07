# React Native and Expo on Apple Platforms

> **Authority**: [React Native — Accessibility](https://reactnative.dev/docs/accessibility),
> [SafeAreaView (deprecated)](https://reactnative.dev/docs/safeareaview),
> [Expo app config reference](https://docs.expo.dev/versions/latest/config/app/),
> [expo/skills](https://github.com/expo/skills) (`expo-ui`, `expo-native-ui`, `eas-app-stores`),
> [callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills),
> [FormidableLabs/eslint-plugin-react-native-a11y](https://github.com/FormidableLabs/eslint-plugin-react-native-a11y).
> Reviewed 2026-11-07.

React Native renders real UIKit views, so an RN app is closer to native than a self-drawn UI — but only for the
components it uses. Expo now goes further: **`@expo/ui` renders real SwiftUI**, `expo-glass-effect` gives system
Liquid Glass and `expo-symbols` renders SF Symbols.

---

## 1. Checks `audit_cross_platform` runs

| Code | Rule | Fix |
| :--- | :--- | :--- |
| `RNA001` | `allowFontScaling={false}` / `maxFontSizeMultiplier={1}` | Keep scaling; cap only where layout cannot grow (`maxFontSizeMultiplier` ≥ 1.5) |
| `RNA002` | `Pressable`/`Touchable*` with only an icon or image and no `accessibilityLabel` | `accessibilityLabel="…"` and `accessibilityRole="button"` |
| `RNA003` | `SafeAreaView` from `react-native` (deprecated) | `react-native-safe-area-context`, or `ScrollView contentInsetAdjustmentBehavior="automatic"` |
| `RNA004` | `Dimensions.get()` | `useWindowDimensions()` — iPad multitasking, Stage Manager and iPhone Duo resize windows |
| `RNA005` | Hard-coded colours and no `useColorScheme`/`PlatformColor` | Dynamic colours: `PlatformColor('label')`, `DynamicColorIOS`, expo-router `Color` |
| `RNA006` | `marginLeft`/`paddingLeft`/`textAlign: 'left'` | `marginStart`/`paddingStart`, `textAlign: 'auto'` |
| `RNA007` | `<Image>` without a label | `accessibilityLabel`/`alt`, or hide decorative images |
| `RNA020` | Expo app without `@expo/ui`, `expo-glass-effect`, `expo-symbols` | Native SwiftUI controls, Liquid Glass, SF Symbols |
| `EXP001` | No `ios.bundleIdentifier` | Required for builds and submission |
| `EXP002` | No `ios.config.usesNonExemptEncryption` | `false` when only exempt encryption is used; avoids a manual answer per build |
| `EXP003` | `userInterfaceStyle` missing or `light` | **Expo defaults to `light`** — set `"automatic"` for Dark Mode |
| `EXP004` | No `ios.privacyManifests` | Declare `NSPrivacyAccessedAPITypes` |
| `EXP005` | No `ios.buildNumber` and no EAS `autoIncrement` | Each upload needs a higher `CFBundleVersion` |
| `EXP006` | `supportsTablet: true` | iPad 13″ screenshots become required |
| `EXP007`/`EXP008` | No icon / single-image icon | `ios.icon` accepts an Icon Composer `.icon` or `{light, dark, tinted}` |
| `XPL010`/`XPL011` | Permission package without a usage string / with the plugin's generic default | Plugin permission option or `ios.infoPlist.<key>` with the specific purpose (Guideline 5.1.1) |

## 2. Native building blocks (Expo SDK 56+)

| Need | Use | Why |
| :--- | :--- | :--- |
| Sheets, pickers, sliders, toggles, menus, grouped settings rows | `@expo/ui` (`Host`, `BottomSheet`, `Picker`, `Switch`, `List`) | Real SwiftUI on iOS; `List` is not virtualized — use `FlatList`/`FlashList` for feeds |
| Liquid Glass | `expo-glass-effect` | System material, not a blur imitation |
| SF Symbols | `expo-symbols` `SymbolView` | Real symbols with weights and animations; vector icon fonts are not SF Symbols |
| Semantic colours | `Color` from `expo-router` | Adapts to light/dark and Increase Contrast |
| Safe areas | `contentInsetAdjustmentBehavior="automatic"` | System inset behaviour under large titles and bars |
| Tabs and stacks | Expo Router native tabs/stack | UIKit navigation, large titles, native transitions |

Bare React Native: `react-native-screens` native stacks, `PlatformColor`, `DynamicColorIOS`, native modules for
anything SwiftUI-only (widgets, Live Activities, App Intents live in Swift targets).

## 3. Screenshots

Build for the Simulator (`npx expo run:ios --configuration Release`, or `xcodebuild` on `ios/<App>.xcworkspace`
with `-sdk iphonesimulator`), then `capture_screenshots`. Route screens with launch arguments: iOS places
`-screen insights` in the NSUserDefaults argument domain, and React Native's iOS-only `Settings.get('screen')`
reads NSUserDefaults. (The Swift and Flutter routes are exercised in this repository's recorded runs; the React
Native route is not yet — confirm it once in your app, or read the value in a small native module.)

## 4. Release

`plan_distribution` detects the setup:

- **Expo without `ios/` (managed):** `npx eas-cli@latest build -p ios --profile production`, then
  `npx eas-cli@latest submit -p ios --latest` (requires approval; EAS cloud plans have limits — `--local` builds on
  your Mac). Preflight runs on `app.json`.
- **Expo with `ios/` or bare React Native:** dependencies → `pod install` → `xcodebuild archive` on the workspace →
  export/upload. With Continuous Native Generation, `npx expo prebuild` regenerates `ios/`: keep native changes in
  config plugins.

## 5. Pair with

- **Expo MCP server** (`https://mcp.expo.dev/mcp`, preview, Expo account): docs, `npx expo install` compatible
  versions, EAS.
- **[expo/skills](https://github.com/expo/skills)** and **[callstackincubator/agent-skills](https://github.com/callstackincubator/agent-skills)**
  (performance, upgrades, React Navigation, tvOS).
- **eslint-plugin-react-native-a11y** in CI for exhaustive accessibility linting; `audit_cross_platform` covers
  the Apple-specific subset and the app config.
