---
description: "Make a React Native or Expo app feel made for Apple platforms: native SwiftUI via @expo/ui, Liquid Glass, SF Symbols, accessibility, Dark Mode, app config, captures and EAS or Xcode release."
---

# React Native and Expo — Apple-native quality

React Native renders UIKit; Expo's `@expo/ui` renders real SwiftUI. Use the most native layer available before
reaching for JavaScript re-implementations.

## 1. Establish context

1. `audit_cross_platform` — framework (bare or Expo, managed or prebuilt), findings (`RNA*`, `EXP*`, `XPL*`).
2. `inspect_apple_project` when `ios/` exists.
3. Read `apple-native://references/react-native-expo-apple-native` and the platform reference.
4. `search_apple_guidelines` for each component; cite the live page.
5. If the Expo MCP server or expo/skills are available, use them for Expo APIs and compatible package versions.

## 2. Apply

- Errors first: `RNA001` font scaling, `EXP001` bundle identifier, `XPL010` usage descriptions.
- `app.json`: `userInterfaceStyle: "automatic"`, `ios.config.usesNonExemptEncryption`, `ios.privacyManifests`,
  `ios.buildNumber` or EAS `autoIncrement`, icon as `.icon` or `{light, dark, tinted}`, plugin permission messages
  that state the purpose.
- Native UI: `@expo/ui` for sheets, pickers, toggles, menus and settings rows; `expo-glass-effect` for glass;
  `expo-symbols` for SF Symbols; native tabs/stack from Expo Router; `react-native-screens` in bare apps.
- Accessibility: `accessibilityLabel` + `accessibilityRole` on icon-only touchables; labels on meaningful images.
- Layout: `useWindowDimensions`, `react-native-safe-area-context` or `contentInsetAdjustmentBehavior`, start/end.
- Widgets, Live Activities, App Intents: Swift targets (config plugins in Expo).

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
