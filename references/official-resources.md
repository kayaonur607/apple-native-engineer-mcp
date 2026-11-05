# Official Apple Documentation & Primary Authority

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Links rot and get restructured. This index is checked before each release: every URL below resolved when it was last verified, and anything that 404s is removed rather than kept "for reference".

---

## 1. Authority hierarchy

When sources disagree, the higher row wins.

| Layer | Source | Use it for |
| :--- | :--- | :--- |
| Runtime truth | The installed SDK (`xcrun --sdk iphoneos --show-sdk-path`) | Does this symbol exist, on which OS, with which parameters |
| Contract | [App Store Review Guidelines](https://developer.apple.com/app-store/review/guidelines/) | What gets a build rejected |
| Design | [Human Interface Guidelines](https://developer.apple.com/design/human-interface-guidelines/) | Layout, materials, controls, platform conventions |
| API | [Apple Developer Documentation](https://developer.apple.com/documentation/) | Signatures, availability, lifecycle rules |
| Practical | [WWDC session videos](https://developer.apple.com/videos/) | Intent and migration guidance behind an API |
| Community | [community-resources.md](community-resources.md) | Ideas and tooling — never a source of truth for behaviour |

A blog post that disagrees with the SDK is wrong. The SDK that disagrees with the HIG is shipping behaviour you have to live with.

---

## 2. Core documentation

| Resource | URL | Scope |
| :--- | :--- | :--- |
| Human Interface Guidelines | [developer.apple.com/design/human-interface-guidelines](https://developer.apple.com/design/human-interface-guidelines/) | Principles, layout, components, materials, input, per-platform guidance |
| App icons | [HIG — App icons](https://developer.apple.com/design/human-interface-guidelines/app-icons) | Icon grid, appearance variants, Liquid Glass layers |
| Apple Design Resources | [developer.apple.com/design/resources](https://developer.apple.com/design/resources/) | Figma and Sketch libraries, device templates, typography metrics |
| Icon Composer | [developer.apple.com/icon-composer](https://developer.apple.com/icon-composer/) | Authoring layered `.icon` files with light, dark and tinted appearances |
| SF Symbols | [developer.apple.com/sf-symbols](https://developer.apple.com/sf-symbols/) | Symbol catalogue, rendering modes, variable colour, effects |
| SwiftUI | [developer.apple.com/documentation/swiftui](https://developer.apple.com/documentation/swiftui/) | Views, modifiers, state, layout, animation |
| Observation | [developer.apple.com/documentation/observation](https://developer.apple.com/documentation/observation/) | `@Observable`, tracking, `withObservationTracking` |
| Swift standard library | [developer.apple.com/documentation/swift](https://developer.apple.com/documentation/swift/) | Language and concurrency surface as shipped |
| UIKit | [developer.apple.com/documentation/uikit](https://developer.apple.com/documentation/uikit/) | View controllers, gestures, bridging |
| AppKit | [developer.apple.com/documentation/appkit](https://developer.apple.com/documentation/appkit/) | Windows, menus, toolbars, pointer handling |
| StoreKit | [developer.apple.com/documentation/storekit](https://developer.apple.com/documentation/storekit) | Products, transactions, subscriptions, refunds |
| App Store Connect API | [developer.apple.com/documentation/appstoreconnectapi](https://developer.apple.com/documentation/appstoreconnectapi) | REST resources, JWT auth, rate limiting |
| Accessibility | [developer.apple.com/accessibility](https://developer.apple.com/accessibility/) | VoiceOver, Dynamic Type, Assistive Access, evaluation criteria |
| Technology overviews | [developer.apple.com/documentation/technologyoverviews](https://developer.apple.com/documentation/technologyoverviews) | Cross-framework maps when you do not know which framework owns a feature |
| Sample code | [developer.apple.com/documentation/samplecode](https://developer.apple.com/documentation/samplecode) | Runnable projects that outrank prose |

---

## 3. Frameworks by task

When you know the task and not the framework, start here rather than searching.

| Task | Framework |
| :--- | :--- |
| State, layout, animation | [SwiftUI](https://developer.apple.com/documentation/swiftui/) |
| Observation and change tracking | [Observation](https://developer.apple.com/documentation/observation/) |
| Local persistence with sync | [SwiftData](https://developer.apple.com/documentation/swiftdata/) |
| Home Screen, Lock Screen, controls | [WidgetKit](https://developer.apple.com/documentation/widgetkit/) |
| Live Activities and Dynamic Island | [ActivityKit](https://developer.apple.com/documentation/activitykit/) |
| Siri, Shortcuts, Spotlight actions | [App Intents](https://developer.apple.com/documentation/appintents/) |
| iCloud records and sync engine | [CloudKit](https://developer.apple.com/documentation/cloudkit/) |
| Purchases and subscriptions | [StoreKit](https://developer.apple.com/documentation/storekit) |
| Tests in Swift 6 | [Swift Testing](https://developer.apple.com/documentation/testing/) |
| Accessibility traits and APIs | [Accessibility](https://developer.apple.com/documentation/accessibility/) |
| App icon variants | [Xcode — Configuring your app icon](https://developer.apple.com/documentation/xcode/configuring-your-app-icon) |

---

## 4. Submission and privacy

| Resource | URL |
| :--- | :--- |
| App Store Review Guidelines | [developer.apple.com/app-store/review/guidelines](https://developer.apple.com/app-store/review/guidelines/) |
| App privacy details (nutrition label) | [developer.apple.com/app-store/app-privacy-details](https://developer.apple.com/app-store/app-privacy-details/) |
| Privacy manifest files | [developer.apple.com/documentation/bundleresources/privacy_manifest_files](https://developer.apple.com/documentation/bundleresources/privacy_manifest_files) |
| Required-reason API | [developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api](https://developer.apple.com/documentation/bundleresources/describing-use-of-required-reason-api) |
| Screenshot specifications | [help/app-store-connect/reference/app-information/screenshot-specifications](https://developer.apple.com/help/app-store-connect/reference/app-information/screenshot-specifications/) |
| Age ratings | [help/app-store-connect/reference/app-information/age-ratings-values-and-definitions](https://developer.apple.com/help/app-store-connect/reference/app-information/age-ratings-values-and-definitions/) |
| App information reference | [help/app-store-connect/reference/app-information/app-information](https://developer.apple.com/help/app-store-connect/reference/app-information/app-information) |
| Upcoming requirements | [developer.apple.com/news/upcoming-requirements](https://developer.apple.com/news/upcoming-requirements/) |

`news/upcoming-requirements` is the page that actually changes deadlines — new SDK build requirements, privacy changes, deprecations. Subscribe to it rather than trusting a guide, including this one.

---

## 5. WWDC sessions worth watching

Session titles, not session numbers: numbers get reused in search results and pasted wrongly. Each link goes to the year index, where the title is authoritative.

| Year | Sessions |
| :--- | :--- |
| [WWDC25](https://developer.apple.com/videos/wwdc2025/) | *What's new in SwiftUI* · *Meet Liquid Glass* · *Build a SwiftUI app with the new design* · *What's new in Swift* |
| [WWDC24](https://developer.apple.com/videos/wwdc2024/) | *What's new in SwiftUI* · *Create custom visual effects with SwiftUI* · *Migrate your app to Swift 6* · *Meet Swift Testing* |
| [WWDC23](https://developer.apple.com/videos/wwdc2023/) | *Discover Observation in SwiftUI* · *Animate with springs* · *Meet SwiftUI for spatial computing* |
| [WWDC22](https://developer.apple.com/videos/wwdc2022/) | *The SwiftUI cookbook for navigation* · *Compose custom layouts with SwiftUI* |
| [WWDC21](https://developer.apple.com/videos/wwdc2021/) | *Demystify SwiftUI* · *Craft search experiences in SwiftUI* |

The design sessions age better than the API sessions. *Demystify SwiftUI* is still the best explanation of view identity, and *Animate with springs* is still the reason `.spring(duration:bounce:)` beats a tuned cubic curve.

---

## 6. Language and tooling

| Resource | URL |
| :--- | :--- |
| Swift language documentation | [swift.org/documentation](https://www.swift.org/documentation/) |
| Swift Evolution proposals | [github.com/swiftlang/swift-evolution](https://github.com/swiftlang/swift-evolution) |
| Xcode documentation | [developer.apple.com/documentation/xcode](https://developer.apple.com/documentation/xcode/) |
| Developer Forums | [developer.apple.com/forums](https://developer.apple.com/forums/) |
| Feedback Assistant | [developer.apple.com/feedback-assistant](https://developer.apple.com/feedback-assistant/) |

An API change is not real until it is in a Swift Evolution proposal or the SDK. "I saw it in a beta screenshot" is neither.

---

## 7. How this repository verifies against them

| Check | Command |
| :--- | :--- |
| Every taught modifier exists in the installed SDK | `python3 scripts/check_api_claims.py` |
| Every Swift block parses and type-checks | `python3 scripts/typecheck_snippets.py` |
| Internal links resolve | `python3 scripts/validate_repo.py` |
| Tools behave as documented | `python3 scripts/run-all-tools.sh` |

A rule that cannot be checked is an opinion. The scripts above are the difference between this guide and a list of links.

---

## 8. Independent project and trademarks

- **Independent project.** This repository is created and maintained by an independent developer and open-source contributors. It has **no affiliation, association, authorization, sponsorship, or endorsement from Apple Inc.**
- **Trademarks.** *Apple, iPhone, iPad, iPadOS, macOS, watchOS, visionOS, Swift, SwiftUI, AppKit, UIKit, SF Symbols, and Dynamic Type* are trademarks or registered trademarks of Apple Inc. Their use here is nominative, to describe software compatibility.
