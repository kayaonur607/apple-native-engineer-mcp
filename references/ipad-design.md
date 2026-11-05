# iPadOS Design & Architecture

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

An iPad app is never a stretched iPhone app. The screen is large enough for two panes, the input can be a
trackpad, a keyboard, or a Pencil, and Stage Manager resizes your window to any ratio it likes. Design for
the window you are given, not for a device name.

---

## 1. What separates an iPad app from a scaled-up iPhone app

| Stretched iPhone | Native iPad |
| :--- | :--- |
| One column, one level at a time | Sidebar + content + detail, visible together |
| Tap targets scaled up, content sparse | Higher information density, not bigger margins |
| Full-screen modal for every task | Sheets, popovers, and an inspector panel |
| No keyboard support | Every command has a `⌘` shortcut, discoverable by holding Command |
| Fixed portrait layout | Adapts from compact to regular width while running |

The test: open the app in a 1/3-width Stage Manager window. If it clips, or still renders three columns at
320pt, the layout is decorative rather than adaptive.

---

## 2. NavigationSplitView, content, and an inspector

```swift
struct StudioView: View {
    @State private var selectedFolderID: Folder.ID?
    @State private var selectedDocumentID: Document.ID?
    @State private var isInspectorPresented = true

    var body: some View {
        NavigationSplitView {
            List(folders, selection: $selectedFolderID) { folder in
                Label(folder.name, systemImage: "folder")
            }
            .navigationTitle("Library")
            .navigationSplitViewColumnWidth(min: 220, ideal: 260, max: 340)
        } detail: {
            if let selectedDocumentID {
                DocumentEditor(documentID: selectedDocumentID)
            } else {
                ContentUnavailableView("No Document", systemImage: "doc.text")
            }
        }
        .inspector(isPresented: $isInspectorPresented) {
            DocumentInspector(documentID: selectedDocumentID)
                .inspectorColumnWidth(min: 240, ideal: 300, max: 360)
        }
    }
}
```

- The inspector (iOS 17+) is the right home for read-only metadata: it overlays the trailing edge instead
  of stealing a permanent third column.
- `navigationSplitViewColumnWidth(min:ideal:max:)` gives the sidebar a range. Do not set a fixed width —
  Stage Manager will hand you 320pt and the sidebar will eat the detail.
- Register `navigationDestination` in the detail column so the collapse to a stack still pushes on iPhone.
- A three-column split view is only worth it when the middle column is a real list. An empty `content`
  column is worse than omitting it.

Tabs and sidebar are the same control on iPad. With iOS 18's `Tab` you can offer both:

```swift
enum TabSelection: Hashable { case library, recents }

struct LibraryTabs: View {
    @State private var selection: TabSelection = .library

    var body: some View {
        if #available(iOS 18.0, *) {
            TabView(selection: $selection) {
                Tab("Library", systemImage: "books.vertical", value: .library) { LibraryView() }
                Tab("Recents", systemImage: "clock", value: .recents) { RecentsView() }
            }
            .tabViewStyle(.sidebarAdaptable)
        } else {
            TabView(selection: $selection) {
                LibraryView()
                    .tabItem { Label("Library", systemImage: "books.vertical") }
                    .tag(TabSelection.library)
                RecentsView()
                    .tabItem { Label("Recents", systemImage: "clock") }
                    .tag(TabSelection.recents)
            }
        }
    }
}
```

`Tab` and `.sidebarAdaptable` are iOS 18+, hence the guard. The tab bar floats at the top in iPadOS 18+,
and `.sidebarAdaptable` lets the user convert it into a sidebar — exactly the affordance an iPad user
expects.

---

## 3. Multi-window and Stage Manager

A document-based iPad app should open a real second window, not a modal imitation of one.

```swift
@main
struct StudioApp: App {
    var body: some Scene {
        WindowGroup {
            StudioView()
        }
        WindowGroup(id: "document", for: Document.ID.self) { $documentID in
            if let documentID {
                DocumentWindow(documentID: documentID)
            }
        }
        .defaultSize(width: 1100, height: 760)
    }
}

struct DocumentActions: View {
    @Environment(\.openWindow) private var openWindow
    @Environment(\.dismissWindow) private var dismissWindow
    let documentID: Document.ID

    var body: some View {
        Button("Open in New Window") { openWindow(id: "document", value: documentID) }
        Button("Close Window") { dismissWindow(id: "document") }
    }
}
```

| Rule | Why |
| :--- | :--- |
| Give each data-driven window an `id` and a value type | The system restores windows independently, including after termination |
| Hold per-window UI state in `@SceneStorage` | Two windows of the same document must not share a cursor position |
| Read `@Environment(\.supportsMultipleWindows)` before offering "New Window" | Split View devices cannot honour it |
| Keep `WindowGroup` state-free | A scene is created and destroyed; models belong in the environment or on disk |
| Use `dismissWindow(id:)`, not `dismiss` | `dismiss` closes a presentation, not a scene |

`.windowResizability(.contentSize)` is the other half: on macOS it pins the window to the content's ideal
size, and on iPad it tells Stage Manager the smallest useful size. `.automatic` is right for most
document apps.

---

## 4. Pointer and trackpad

With a Magic Keyboard attached, the pointer morphs into the control under it. Standard controls get that
for free; add it explicitly only to custom hit areas.

| Effect | Visual | Use for |
| :--- | :--- | :--- |
| `.automatic` | System default for the control | Anything standard |
| `.highlight` | Pointer merges with the shape | Toolbar items, icon buttons, small targets |
| `.lift` | Subtle scale and shadow | Cards, tiles, draggable content |
| `.hoverEffectDisabled()` | No morph | Custom animation you fully control |

```swift
Button { open(document) } label: { DocumentCard(document: document) }
    .buttonStyle(.plain)
    .hoverEffect(.lift)
```

`.hoverEffect` has no effect on iPhone touch. Never encode meaning in hover alone: it does not exist for
touch users, and it disappears under Switch Control.

---

## 5. Hardware keyboard

An iPad with a keyboard is a Mac with a touchscreen. Every command needs a shortcut, and every shortcut
should be discoverable by holding Command.

- `.commands` applies to the whole scene, so it is the right place for menu-style actions that also appear
  on macOS. Put a single-screen action in `.toolbar` instead.
- `.keyboardShortcut(.defaultAction)` binds Return to the confirming button; `.cancelAction` binds Escape.
- `.keyboardShortcut("s", modifiers: .command)` on a toolbar button is enough for the common case.

```swift
.toolbar {
    ToolbarItem(placement: .primaryAction) {
        Button("Save") { save() }
            .keyboardShortcut("s", modifiers: .command)
    }
}
```

Do not invent shortcuts that shadow system ones. `⌘W`, `⌘N`, `⌘F`, and `⌘,` already mean something.

---

## 6. Drag and drop

```swift
import CoreTransferable
import UniformTypeIdentifiers

struct Document: Identifiable, Hashable, Codable, Transferable {
    let id: UUID
    var title: String

    static var transferRepresentation: some TransferRepresentation {
        CodableRepresentation(contentType: .data)
    }
}

DocumentCard(document: document)
    .draggable(document)

FolderRow(folder: folder)
    .dropDestination(for: Document.self) { documents, _ in
        documents.forEach(folder.add)
        return true
    }
```

`draggable`/`dropDestination` are the modern pair; `.onDrag`/`.onDrop` remain for `NSItemProvider`-based
legacy sources. Make the returned `Bool` honest — returning `true` for a drop you ignored leaves the drag
animation lying to the user. The closure receives an array, so support multi-item drops.

---

## 7. Apple Pencil

Two different jobs, two APIs.

**Free-form ink** uses PencilKit. Wrap `PKCanvasView`, set `drawingPolicy`, and keep a `PKToolPicker` alive
across view updates:

```swift
import PencilKit

struct CanvasView: UIViewRepresentable {
    @Binding var drawing: PKDrawing

    func makeUIView(context: Context) -> PKCanvasView {
        let canvas = PKCanvasView()
        canvas.drawingPolicy = .pencilOnly
        canvas.tool = PKInkingTool(.pen, color: .label, width: 4)
        return canvas
    }

    func updateUIView(_ canvas: PKCanvasView, context: Context) {
        if canvas.drawing != drawing { canvas.drawing = drawing }
    }
}
```

Hold the tool picker in `@State` (not in `makeUIView`), call `setVisible(_:forFirstResponder:)`, and make
the canvas first responder. `.pencilOnly` avoids palm marks but blocks finger drawing — offer it as a
setting, not a hard rule.

**Gestures** use SwiftUI. Squeeze the Pencil to open a tool palette; the callback is iOS 17.5+:

```swift
CanvasView(drawing: $drawing)
    .onPencilSqueeze { phase in
        if case .ended = phase { isToolPickerVisible.toggle() }
    }
```

`PencilSqueezeGesturePhase` also carries `.active` and `.failed`, and its value exposes `PencilHoverPose`
for altitude and azimuth. Do not use squeeze for destructive actions, and it is unavailable on older
Pencils.

---

## 8. Review checklist

- [ ] Layout adapts to compact width in a 1/3 Stage Manager window
- [ ] Sidebar + detail visible at regular width; nothing clipped at 320pt
- [ ] Detail and inspector both handle a `nil` selection with `ContentUnavailableView`
- [ ] Document windows use `WindowGroup(id:for:)` + `openWindow` / `dismissWindow`
- [ ] Per-window state lives in `@SceneStorage`
- [ ] Every major command has a `⌘` shortcut
- [ ] Cards and tiles respond to pointer hover; nothing depends on hover to be understood
- [ ] Pencil canvas keeps its tool picker alive across view updates

---

## 9. Official HIG references

- [Apple HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG — Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars)
- [Apple HIG — Split views](https://developer.apple.com/design/human-interface-guidelines/split-views)
- [Apple HIG — Pointers](https://developer.apple.com/design/human-interface-guidelines/pointers)
- [Apple HIG — Apple Pencil and Scribble](https://developer.apple.com/design/human-interface-guidelines/apple-pencil-and-scribble)
