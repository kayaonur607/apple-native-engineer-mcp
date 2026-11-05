# App Intents, Siri & Shortcuts

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Human Interface Guidelines — App Shortcuts](https://developer.apple.com/design/human-interface-guidelines/app-shortcuts), [Apple Developer Documentation — App Intents](https://developer.apple.com/documentation/appintents), [WWDC24: Bring your app to Siri](https://developer.apple.com/videos/play/wwdc2024/10133/)

An intent is not a URL scheme with metadata. It is a struct the system discovers, resolves, schedules and
runs in your process — sometimes with your app closed. Siri, Shortcuts, Spotlight, the Action Button,
widgets and Control Center all read the same definitions.

---

## 1. The types that matter

| Type | Since | Role |
| :--- | :--- | :--- |
| `AppIntent` | iOS 16 | One action: `perform() async throws -> some IntentResult` |
| `AppEntity` | iOS 16 | A thing the user can name: identifier, display representation, query |
| `EntityQuery` | iOS 16 | Resolves entities by identifier and supplies suggestions |
| `AppShortcutsProvider` | iOS 16 | Phrases that are installed with the app, no user setup |
| `IndexedEntity` | iOS 18 | An entity Spotlight can index without a Shortcuts donation |
| `SetValueIntent` | iOS 18 | A toggle-shaped intent for `ControlWidgetToggle` |

`AppIntent` requires `static var title` and `init()`. Everything else has a default. An intent is a value
type on purpose: the system may construct it, encode it, and run it without any state you set up in the app.

---

## 2. An intent that compiles

```swift
import AppIntents

struct LogWaterIntent: AppIntent {
    static var title: LocalizedStringResource = "Log Water"
    static var description = IntentDescription("Adds a glass of water to today's total.")

    @Parameter(title: "Millilitres")
    var millilitres: Int

    func perform() async throws -> some IntentResult & ProvidesDialog {
        try await HydrationStore.shared.add(millilitres)
        return .result(dialog: "Logged \(millilitres) ml.")
    }
}
```

`.result(dialog:)` returns an `IntentResultContainer` whose dialog is an `IntentDialog`; that is why the
return type must include `ProvidesDialog`. Throwing from `perform()` surfaces your error to Siri, so throw a
`LocalizedError` with a real sentence rather than a generic failure.

An intent may present a snippet view without launching the app:

```swift
import AppIntents
import SwiftUI

struct WaterSnippet: View {
    let total: Int

    var body: some View {
        Text("\(total) ml today")
            .font(.title3)
    }
}

struct ShowWaterIntent: AppIntent {
    static var title: LocalizedStringResource = "Show Water Total"

    func perform() async throws -> some IntentResult & ProvidesDialog & ShowsSnippetView {
        let total = await HydrationStore.shared.todayTotal
        return .result(dialog: "You are at \(total) ml.", view: WaterSnippet(total: total))
    }
}
```

---

## 3. Entities and queries

```swift
import AppIntents
import Foundation

struct RecipeEntity: AppEntity {
    static var typeDisplayRepresentation: TypeDisplayRepresentation = "Recipe"
    static var defaultQuery = RecipeQuery()

    var id: UUID
    var title: String
    var cuisine: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(
            title: "\(title)",
            subtitle: "\(cuisine)",
            image: .init(systemName: "fork.knife")
        )
    }
}

struct RecipeQuery: EntityQuery {
    func entities(for identifiers: [UUID]) async throws -> [RecipeEntity] {
        try await RecipeStore.shared.recipes(withIDs: identifiers)
    }

    func suggestedEntities() async throws -> [RecipeEntity] {
        try await RecipeStore.shared.recent(limit: 6)
    }
}
```

`entities(for:)` must return exactly the identifiers it was asked for — a missing result makes Siri drop
the parameter. `suggestedEntities()` fills the picker before the user types; return recent or favourite
items, not the whole database.

---

## 4. App Shortcuts

```swift
import AppIntents

struct WaterShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: LogWaterIntent(),
            phrases: [
                "Log water in \(.applicationName)",
                "Add a glass of water in \(.applicationName)"
            ],
            shortTitle: "Log Water",
            systemImageName: "drop.fill"
        )
    }
}
```

Two rules are enforced at install time: every phrase must contain `\(.applicationName)`, and the phrase must
be sayable. A shortcut that never mentions the app name cannot be routed. When your parameter options change,
call `WaterShortcuts.updateAppShortcutParameters()` from the app so Siri re-reads the entity list.

---

## 5. Foreground or background

By default an intent runs without bringing the app forward. `openAppWhenRun` is how you change that, and
**iOS 26 deprecates it** in favour of `supportedModes`:

```swift
import AppIntents

struct OpenBoardIntent: AppIntent {
    static var title: LocalizedStringResource = "Open Board"

    // iOS 26 deprecates this property. `supportedModes` is the replacement, but
    // `IntentModes` itself is iOS 26+, so an iOS 17 floor keeps this form.
    static var openAppWhenRun: Bool = true

    func perform() async throws -> some IntentResult {
        .result()
    }
}
```

On an iOS 26-only target write `static var supportedModes: IntentModes = .foreground` instead. Do not put
`supportedModes` in a struct with a lower deployment floor and expect it to compile — `IntentModes` is
declared `@available(anyAppleOS 26.0, *)`.

---

## 6. Siri tips and the Shortcuts link

```swift
import AppIntents
import SwiftUI

struct HabitToolbar: View {
    @State private var showSiriTip = true

    var body: some View {
        VStack {
            SiriTipView(intent: LogWaterIntent(), isVisible: $showSiriTip)
                .siriTipViewStyle(.automatic)
            ShortcutsLink()
                .shortcutsLinkStyle(.automaticOutline)
        }
    }
}
```

`SiriTipView` is unavailable on macOS — ship it in an iOS-only view. Both views are iOS 16+, so they need no
guard at an iOS 17 floor. Pass a binding to `isVisible` when the user can dismiss the tip; without one the
system decides.

---

## 7. Spotlight indexing (iOS 18+)

```swift
import AppIntents
import CoreSpotlight

@available(iOS 18.0, macOS 15.0, *)
extension RecipeEntity: IndexedEntity {
    var attributeSet: CSSearchableItemAttributeSet {
        let attributes = defaultAttributeSet
        attributes.title = title
        attributes.contentDescription = cuisine
        return attributes
    }
}
```

`defaultAttributeSet` fills the boilerplate fields. Only adopt `IndexedEntity` for content the user would
search for by name; indexing every row floods Spotlight and slows the donation pass.

---

## 8. Limits the system enforces

| Limit | Reality |
| :--- | :--- |
| Execution time | Seconds, not minutes. Long work belongs in a background task you start and return from |
| UI | A snippet view or a dialog. No sheets, no navigation, no permission prompts |
| Network | Allowed, but a timeout is a failed intent; cache the answer you usually need |
| Parameters | Resolved before `perform()` runs; an unresolvable entity aborts the intent |
| App Shortcuts | Installed per phrase; a phrase missing `\(.applicationName)` never appears |

---

## 9. Review checklist

- [ ] Every intent has a `title` and a meaningful error thrown from `perform()`
- [ ] Entity queries return exactly the requested IDs and a short suggestion list
- [ ] Every App Shortcut phrase contains `\(.applicationName)`
- [ ] `openAppWhenRun` is intentional; `supportedModes` is only used behind an iOS 26 guard
- [ ] Snippet views are small, static, and do not fetch on appear
- [ ] Widget configuration uses `AppIntentConfiguration` — `WID033` flags a widget with no configurable intent
- [ ] Availability is declared where intents call iOS 17+ API — `WID035` flags widget sources without it

```bash
python3 tools/widget-validator/validate_widget.py path/to/Project
```
