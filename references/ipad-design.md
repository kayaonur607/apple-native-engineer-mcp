# iPadOS Design & Architecture

The iPad is a versatile, multi-modal modular computer. An iPad application is **never** merely an enlarged iPhone app with stretched buttons and sparse, bloated margins. iPadOS users operate with touch, Apple Pencil, precision trackpads, and external hardware keyboards across multi-window environments like **Stage Manager** and **Split View**.

---

## 1. Key Principles of iPad Design

1. **Information Density**: Leverage the larger display to show primary and contextual detail side-by-side rather than forcing multi-step navigation drill-downs.
2. **Dynamic Window Resizing**: In Stage Manager, users can freely resize app windows to arbitrary aspect ratios. An app can switch between **regular** and **compact** size classes in real-time.
3. **Multi-Column Hierarchy**: Use `NavigationSplitView` with sidebars, list content, and detailed inspectors.
4. **Desktop-Class Inputs**: Support precision pointer hover effects, drag-and-drop, and comprehensive keyboard shortcuts.

---

## 2. Multi-Column Navigation with Sidebar & Inspector

Modern iPad apps use a 3-column architecture (Sidebar, Content, Detail) complemented by an auxiliary **Inspector** panel (iOS 17+):

```swift
struct iPadWorkspaceView: View {
    @State private var selectedFolder: Folder?
    @State private var selectedDocument: Document?
    @State private var showInspector: Bool = true
    
    var body: some View {
        NavigationSplitView {
            // Column 1: Sidebar
            FolderSidebarView(selection: $selectedFolder)
                .navigationTitle("Folders")
        } content: {
            // Column 2: Document List
            DocumentListView(folder: selectedFolder, selection: $selectedDocument)
                .navigationTitle(selectedFolder?.name ?? "Documents")
        } detail: {
            // Column 3: Main Editor
            if let selectedDocument {
                DocumentEditorView(document: selectedDocument)
            } else {
                ContentUnavailableView("Select a Document", systemImage: "doc.text")
            }
        }
        // Auxiliary Right-Side Inspector Panel (iOS 17+)
        .inspector(isPresented: $showInspector) {
            DocumentMetadataInspector(document: selectedDocument)
                .inspectorColumnWidth(min: 240, ideal: 280, max: 320)
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showInspector.toggle()
                } label: {
                    Label("Toggle Inspector", systemImage: "sidebar.trailing")
                }
            }
        }
    }
}
```

---

## 3. Pointer & Trackpad Hover Effects

When an iPad user connects an Apple Magic Keyboard or Bluetooth trackpad, the cursor morphs dynamically to fit interactive controls:

```swift
// ✅ Add native pointer hover highlighting
Button {
    createNewDocument()
} label: {
    Image(systemName: "square.and.pencil")
        .font(.title3)
        .padding(8)
}
.hoverEffect(.highlight) // Standard morphing cursor highlight
```

### Hover Effect Variations
- `.hoverEffect(.highlight)`: Merges the cursor with the button background (ideal for toolbar items and icon buttons).
- `.hoverEffect(.lift)`: Elevates the card or button with subtle shadow and slight scale (ideal for dashboard cards).
- `.hoverEffectDisabled()`: Explicitly disables cursor morphing when custom hover animations are applied.

---

## 4. Hardware Keyboard Shortcuts

iPad power users expect the same keyboard efficiency found on macOS. Pressing and holding the Command (`⌘`) key displays the system shortcut discoverability overlay.

```swift
.toolbar {
    ToolbarItem(placement: .primaryAction) {
        Button("Save") { save() }
            .keyboardShortcut("s", modifiers: .command)
    }
}
.sheet(isPresented: $showSearch) {
    SearchView()
}
.keyboardShortcut("f", modifiers: .command)
```

---

## 5. Direct Drag and Drop

iPad workflows rely heavily on dragging content between split windows and applications:

```swift
// Draggable source item
DocumentCard(doc: document)
    .draggable(document)

// Drop destination container
FolderRow(folder: folder)
    .dropDestination(for: Document.self) { droppedDocs, location in
        for doc in droppedDocs {
            folder.add(doc)
        }
        return true
    }
```

---

## 6. Official HIG References
- [Apple HIG - Designing for iPadOS](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG - Sidebars](https://developer.apple.com/design/human-interface-guidelines/sidebars)
- [Apple HIG - Split Views](https://developer.apple.com/design/human-interface-guidelines/split-views)
- [Apple HIG - Pointer Interactions](https://developer.apple.com/design/human-interface-guidelines/pointers)
