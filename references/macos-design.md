# macOS & AppKit/SwiftUI Design Fundamentals

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

The Mac is a pointer-and-keyboard machine with persistent windows and a menu bar that belongs to the
system, not to your app. A Mac app ported straight from iOS feels foreign in the first ten seconds,
usually because the menu bar is empty and every control is twice the size it should be.

---

## 1. What makes an app a Mac citizen

| Expectation | What it means in code |
| :--- | :--- |
| Every command exists in the menu bar | `.commands` + `CommandGroup` / `CommandMenu` |
| Every command has a shortcut | `.keyboardShortcut(_:modifiers:)` |
| Settings open with `⌘,` | A `Settings` scene, not a custom modal |
| Windows are resizable and restore their frame | `WindowGroup` + `.defaultSize` + scene state |
| Density is higher than iOS | `.controlSize(.small)` where the context is compact |
| Right-click always does something | `.contextMenu` on rows, canvases, and toolbars |
| Buttons are compact and legible | Default control metrics — no 44pt iOS targets |
| The pointer is a first-class input | `.onHover`, `.hoverEffect`, drag and drop |

If a reviewer cannot find a feature by opening the menu bar, the feature is hidden.

---

## 2. Scenes, windows, and sizing

```swift
@main
struct StudioApp: App {
    var body: some Scene {
        WindowGroup {
            StudioWindow()
        }
        .defaultSize(width: 1180, height: 760)
        .windowResizability(.contentMinSize)
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: true))

        Window("Inspector", id: "inspector") {
            InspectorView()
        }
        .defaultSize(width: 320, height: 680)

        Settings {
            SettingsView()
        }
    }
}
```

| API | Use for | Note |
| :--- | :--- | :--- |
| `WindowGroup` | Document or primary content | Multiple windows, one scene definition |
| `Window` | A singleton utility window (inspector, activity log) | One per app; open it with `openWindow(id:)` |
| `.defaultSize(width:height:)` | First-launch size | A hint, not a constraint — the user owns the frame afterwards |
| `.windowResizability(.contentMinSize)` | Prevent collapse below usable content | `.contentSize` locks the window to the content's ideal size |
| `.windowStyle(.hiddenTitleBar)` | Content that draws its own header | Never hide the title bar without keeping the traffic lights reachable |
| `.windowToolbarStyle(.unified(showsTitle:))` | One-row toolbar with the title | The default Mac look since Big Sur |

`.defaultSize` replaces `.frame(width:height:)` on the root view. A fixed frame on the root turns a
resizable Mac window into a canvas with dead space around it.

Multi-window and per-window state use the same APIs as iPad — see [iPad Design](ipad-design.md) for
`WindowGroup(id:for:)`, `openWindow`, `dismissWindow`, and `@SceneStorage`.

---

## 3. The menu bar is the API

```swift
.commands {
    SidebarCommands()
    ToolbarCommands()

    CommandGroup(after: .newItem) {
        Button("Import…") { importFiles() }
            .keyboardShortcut("i", modifiers: [.command, .shift])
    }

    CommandMenu("Project") {
        Button("Run Diagnostics") { runDiagnostics() }
            .keyboardShortcut("r", modifiers: [.command, .shift])
        Divider()
        Toggle("Show Warnings", isOn: $showWarnings)
    }
}
```

| Placement | Purpose |
| :--- | :--- |
| `CommandGroup(after: .newItem)` | Add to an existing menu without replacing it |
| `CommandGroup(replacing: .help)` | Replace a standard menu when you have a better one |
| `CommandMenu("Project")` | A top-level menu for your domain |
| `SidebarCommands()` / `ToolbarCommands()` | The standard View menu items users expect |
| `.keyboardShortcut(.defaultAction)` | Return triggers the confirming button |

Rules:

- **Do not replace system groups you have no replacement for.** Users know where Undo, Close, and Help
  live; moving them costs more than it buys.
- **Menus trump custom chrome.** A command that exists only as an in-window button is invisible to
  keyboard users and to macOS automation.
- **`.help("…")` on dense controls.** Tooltips are how a Mac user learns an unfamiliar icon without
  leaving the window.
- **`Settings` creates `⌘,` for you.** Do not hand-roll a preferences sheet.

---

## 4. MenuBarExtra

For a utility that should not own a Dock icon, use a menu bar scene:

```swift
MenuBarExtra("Sync", systemImage: "arrow.triangle.2.circlepath") {
    Button("Sync Now") { sync() }
    Divider()
    SettingsLink { Text("Settings…") }
    Divider()
    Button("Quit") { NSApp.terminate(nil) }
}
.menuBarExtraStyle(.window)
```

- `.menuBarExtraStyle(.menu)` gives a plain menu; `.window` gives a floating SwiftUI panel for richer
  controls. Choose `.menu` unless you genuinely need custom layout.
- `SettingsLink` opens the `Settings` scene without reaching for AppKit.
- A menu-bar-only app still needs a main menu for `⌘Q` and Edit commands; `NSApp` requires
  `import AppKit`.

---

## 5. Tables, not lists, for columnar data

`Table` gives resizable columns, click-to-sort headers, multi-selection, and keyboard navigation. A
`List` with `HStack` rows gives none of that.

```swift
struct Project: Identifiable, Hashable {
    let id: UUID
    var name: String
    var owner: String
    var modified: Date
}

struct ProjectTable: View {
    @State private var projects: [Project] = []
    @State private var selection: Project.ID?
    @State private var sortOrder = [KeyPathComparator(\Project.name)]

    var body: some View {
        Table(projects, selection: $selection, sortOrder: $sortOrder) {
            TableColumn("Name", value: \.name)
            TableColumn("Owner", value: \.owner)
            TableColumn("Modified", value: \.modified) { project in
                Text(project.modified, format: .dateTime)
            }
        }
        .onChange(of: sortOrder) { _, newOrder in
            projects.sort(using: newOrder)
        }
    }
}
```

- `value:` only works for `Comparable` columns. Use the trailing closure form for badges, icons, and
  custom cells.
- Sort in `onChange(of: sortOrder)`, not inside `body`. Sorting is a side effect.
- Row height follows content; do not force 60pt rows. Mac density expects 24–32pt.

---

## 6. Focus and the key view loop

The Mac key loop is a contract: Tab moves between controls, the arrow keys move inside the focused
control, and the focused control is visibly focused.

```swift
struct SearchPane: View {
    enum Field: Hashable { case query, results }

    @State private var query = ""
    @FocusState private var focused: Field?

    var body: some View {
        VStack(spacing: 8) {
            TextField("Search", text: $query)
                .textFieldStyle(.roundedBorder)
                .focused($focused, equals: .query)

            ResultList()
                .focusable()
                .focused($focused, equals: .results)
        }
        .focusSection()
        .defaultFocus($focused, .query)
        .onKeyPress(.escape) {
            focused = nil
            return .handled
        }
    }
}
```

- `@FocusState` is the source of truth. Reading focus from AppKit's `firstResponder` in SwiftUI code
  drifts the moment a sheet appears.
- `.focusSection()` groups a pane so Tab stays inside it before moving on.
- `.defaultFocus(_:_:)` sets the initial key view; without it, focus starts wherever AppKit decides.
- `.onKeyPress` handles non-Command keys. Command shortcuts belong on menus, not on views, or they stop
  being discoverable.

---

## 7. Settings that look like settings

```swift
struct SettingsView: View {
    @AppStorage("syncEnabled") private var syncEnabled = true

    var body: some View {
        Form {
            Toggle("Sync in background", isOn: $syncEnabled)
            Picker("Update channel", selection: $channel) {
                Text("Stable").tag(Channel.stable)
                Text("Beta").tag(Channel.beta)
            }
        }
        .formStyle(.grouped)
        .frame(width: 420)
        .fixedSize(horizontal: false, vertical: true)
    }
}
```

`Settings` presents as one window with a toolbar of panes. For multiple panes, wrap the content in a
`TabView`; on macOS 15+ prefer `Tab(_:systemImage:)`, and on macOS 14 use `.tabItem`. Keep each pane's
width modest — a settings window that is 900pt wide reads as a document editor.

---

## 8. Review checklist

- [ ] `Settings` scene exists and `⌘,` opens it
- [ ] Every major action is reachable from the menu bar with a shortcut
- [ ] `⌘Q`, `⌘W`, `⌘N`, `⌘F` are not shadowed by custom shortcuts
- [ ] `.defaultSize` used instead of a fixed frame on the root view
- [ ] Window restores position and size across launches
- [ ] Columnar data uses `Table`, not `List` rows of `HStack`
- [ ] `.contextMenu` on every row and canvas
- [ ] Focus is driven by `@FocusState`; Escape and Return are handled
- [ ] Controls use default Mac metrics; no 44pt iOS-sized buttons
- [ ] Menu-bar extras offer Quit and Settings

---

## 9. Official HIG references

- [Apple HIG — Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-macos)
- [Apple HIG — Windows](https://developer.apple.com/design/human-interface-guidelines/windows)
- [Apple HIG — The menu bar](https://developer.apple.com/design/human-interface-guidelines/the-menu-bar)
- [Apple HIG — Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)
