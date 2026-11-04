# macOS & AppKit/SwiftUI Design Fundamentals

Designing for the Mac requires shifting from touch-first heuristics to precision pointer, persistent windowing, menu bar hierarchies, and keyboard navigation. A Mac app ported directly from iOS without adaptation feels foreign and clumsy.

---

## 1. Key macOS Design Heuristics

1. **Information Density & Windowing**: Mac users expect multiple resizable windows, tabs, and dense data tables. Controls are more compact (default control size is typically 20–28pt vs. 44pt touch targets on iOS).
2. **The System Menu Bar**: The menu bar (`⌘-N`, `⌘-O`, `⌘-P`, `⌘-,`) is the primary discovery mechanism for commands. Every major action must have a menu bar item.
3. **Unified Window Toolbars**: macOS windows feature integrated toolbars with search, segmented view switches, and window titles blending seamlessly into the title bar.
4. **Context Menus & Secondary Clicks**: Right-click context menus are ubiquitous on macOS and provide contextual shortcuts.

---

## 2. Window Architecture & Unified Toolbars

In modern SwiftUI macOS apps, configure windows to use unified styling:

```swift
@main
struct MacApp: App {
    var body: some Scene {
        WindowGroup {
            MacMainView()
        }
        .windowStyle(.hiddenTitleBar)
        .windowToolbarStyle(.unified(showsTitle: true))
        
        // Native Mac Settings Scene (⌘,)
        Settings {
            MacSettingsView()
        }
        
        // Native Menu Bar Commands
        .commands {
            SidebarCommands()
            ToolbarCommands()
            CommandMenu("Project") {
                Button("Run Diagnostics") {
                    runDiagnostics()
                }
                .keyboardShortcut("r", modifiers: [.command, .shift])
            }
        }
    }
}
```

---

## 3. Native macOS Settings Window

Mac settings are organized into a tabbed toolbar window:

```swift
struct MacSettingsView: View {
    private enum Tabs: Hashable {
        case general, appearance, sync, advanced
    }
    
    var body: some View {
        TabView {
            GeneralSettingsView()
                .tabItem {
                    Label("General", systemImage: "gearshape")
                }
                .tag(Tabs.general)
            
            AppearanceSettingsView()
                .tabItem {
                    Label("Appearance", systemImage: "paintbrush")
                }
                .tag(Tabs.appearance)
            
            SyncSettingsView()
                .tabItem {
                    Label("Sync", systemImage: "arrow.triangle.2.circlepath")
                }
                .tag(Tabs.sync)
        }
        .padding(20)
        .frame(width: 480, height: 320)
    }
}
```

---

## 4. Mac Table Views & Density

Mac data presentation uses `Table` instead of `List` when displaying multi-column structured records:

```swift
Table(projects, selection: $selectedProjectId, sortOrder: $sortOrder) {
    TableColumn("Name", value: \.name) { project in
        HStack {
            Image(systemName: project.icon)
            Text(project.name)
        }
    }
    TableColumn("Status", value: \.status) { project in
        StatusBadge(status: project.status)
    }
    TableColumn("Last Modified", value: \.modifiedDate) { project in
        Text(project.modifiedDate.formatted(date: .abbreviated, time: .shortened))
            .foregroundStyle(.secondary)
    }
}
```

---

## 5. Official HIG References
- [Apple HIG - Designing for macOS](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG - Windows](https://developer.apple.com/design/human-interface-guidelines/windows)
- [Apple HIG - Menu Bars](https://developer.apple.com/design/human-interface-guidelines/the-menu-bar)
