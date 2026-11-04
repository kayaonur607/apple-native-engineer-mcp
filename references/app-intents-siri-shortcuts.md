# App Intents, Siri & System Controls

> **Authority**: [Apple Human Interface Guidelines — App Shortcuts](https://developer.apple.com/design/human-interface-guidelines/app-shortcuts), [Apple Developer Documentation — App Intents](https://developer.apple.com/documentation/appintents), [WWDC24: Bring your app to Siri](https://developer.apple.com/videos/play/wwdc2024/10133/)  
> **Status**: Official Apple Recommendations & Specifications

The **App Intents** framework provides a unified way to expose app features to the system: Siri, the Shortcuts app, Spotlight search, interactive widgets, the Action Button, and iOS 18 Control Center widgets.

---

## 1. Defining an App Intent

An `AppIntent` is a Swift struct with metadata, parameters, and an asynchronous `perform()` execution body.

```swift
import AppIntents
import Foundation

struct StartVoiceRecordingIntent: AppIntent {
    static var title: LocalizedStringResource = "Start Voice Recording"
    static var description = IntentDescription("Begins audio capture in the active note session.")
    
    // Controls whether the main app launches into foreground
    static var openAppWhenRun: Bool = false

    @Parameter(title: "Project Name", default: "Quick Note")
    var projectName: String

    func perform() async throws -> some ProvidesDialog & ShowsSnippetView {
        let recordingID = try await AudioService.shared.startRecording(project: projectName)
        
        return .result(
            dialog: IntentDialog("Recording started for \(projectName)."),
            view: RecordingSnippetView(recordingID: recordingID)
        )
    }
}
```

---

## 2. App Shortcuts Provider

`AppShortcutsProvider` registers predefined shortcuts automatically upon app installation without requiring the user to configure anything in the Shortcuts app.

```swift
struct AppShortcuts: AppShortcutsProvider {
    static var appShortcuts: [AppShortcut] {
        AppShortcut(
            intent: StartVoiceRecordingIntent(),
            phrases: [
                "Start a recording in \(.applicationName)",
                "Begin \(.applicationName) audio note",
                "Record note with \(.applicationName)"
            ],
            shortTitle: "Record Note",
            systemImageName: "mic.fill"
        )
    }
}
```

---

## 3. iOS 18 Control Center Widgets (`ControlWidget`)

Starting in iOS 18, third-party developers can place actionable controls inside the Control Center, Lock Screen quick actions, and Action Button.

```swift
import WidgetKit
import SwiftUI
import AppIntents

struct FlashlightControlWidget: ControlWidget {
    var body: some ControlWidgetConfiguration {
        StaticControlConfiguration(kind: "com.example.app.flashlight") {
            ControlWidgetToggle(
                "Studio Light",
                isOn: LightService.shared.isOn,
                action: ToggleStudioLightIntent()
            ) { isOn in
                Label(isOn ? "Light On" : "Light Off", systemImage: isOn ? "lightbulb.fill" : "lightbulb")
            }
        }
        .displayName("Studio Light")
        .description("Quickly toggle the connected studio fill light.")
    }
}

struct ToggleStudioLightIntent: SetValueIntent {
    static var title: LocalizedStringResource = "Toggle Studio Light"

    @Parameter(title: "Target State")
    var value: Bool

    func perform() async throws -> some IntentResult {
        await LightService.shared.setLight(state: value)
        return .result()
    }
}
```

---

## 4. Siri & Spotlight Indexing

Expose app entities via `AppEntity` so users can search within Spotlight and ask Siri contextual questions about items inside the app.

```swift
struct RecipeEntity: AppEntity {
    static var defaultQuery = RecipeQuery()
    static var typeDisplayRepresentation: TypeDisplayRepresentation = "Recipe"

    var id: UUID
    var title: String
    var cuisine: String

    var displayRepresentation: DisplayRepresentation {
        DisplayRepresentation(
            title: "\(title)",
            subtitle: "\(cuisine) Cuisine",
            image: .init(systemName: "fork.knife")
        )
    }
}

struct RecipeQuery: EntityQuery {
    func entities(for identifiers: [UUID]) async throws -> [RecipeEntity] {
        return await Database.shared.fetchRecipes(ids: identifiers)
    }

    func suggestedEntities() async throws -> [RecipeEntity] {
        return await Database.shared.fetchRecentRecipes()
    }
}
```

---

## 5. System Integration Review Rules

1. **Keep Phrases Natural**: Voice phrases in `AppShortcutsProvider` must incorporate the `\(.applicationName)` token and read like authentic colloquial speech.
2. **Perform Intent Quickly**: Intents that run in background must finish within a few seconds, or system watchdog will terminate them.
3. **Handle Errors with Informative Dialogs**: Throwing generic errors in `perform()` leads to Siri reporting "Something went wrong." Provide descriptive dialogs via `IntentDialog`.
