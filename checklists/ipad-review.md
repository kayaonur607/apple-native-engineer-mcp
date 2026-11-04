# iPadOS Design & Architecture Review Checklist

Use this checklist to verify that an application provides a first-class, desktop-grade iPad experience rather than functioning as an enlarged iPhone port.

---

## 1. Multi-Column Navigation & Hierarchy
- [ ] **No Stretched iPhone Views**: Content does not span across an entire 13-inch display with absurdly long, unreadable line lengths.
- [ ] **NavigationSplitView Architecture**: The root navigation utilizes a 2-column or 3-column `NavigationSplitView` with a native sidebar.
- [ ] **Adaptive Collapsing**: When the app is resized into compact width (e.g., Slide Over or narrow Stage Manager window), the split view collapses cleanly into a standard hierarchical stack.
- [ ] **Inspector Panel**: Contextual metadata and editing tools reside in a native `.inspector(isPresented:)` panel on the trailing edge.

---

## 2. Window Resizing & Stage Manager
- [ ] **Fluid Geometry Resizing**: The app responds smoothly to real-time window resizing without crashing, clipping, or displaying blank screens.
- [ ] **Dynamic Layout Adaptability**: Layouts intelligently transition between multi-column grids and single-column stacks based on `@Environment(\.horizontalSizeClass)`.
- [ ] **Multiple Window Support**: If appropriate for the document model, the app supports opening multiple simultaneous windows (`openWindow` environment action).

---

## 3. Pointer & Trackpad Interactions
- [ ] **Hover Highlighting**: Toolbar buttons, navigation items, and interactive controls provide native pointer hover morphing (`.hoverEffect(.highlight)` or `.lift`).
- [ ] **Custom Cursor Affordances**: Canvas views, resizable dividers, and text editors switch to appropriate cursor styles (e.g. resize arrows, I-beam).
- [ ] **Context Menus**: Right-click (or two-finger tap) reveals a rich `.contextMenu` with relevant actions.

---

## 4. Hardware Keyboard Shortcuts
- [ ] **Command Key Discovery**: Pressing and holding `⌘` reveals a comprehensive shortcut menu.
- [ ] **Standard Shortcuts**: Essential actions support standard key combinations:
  - `⌘-N`: New Document / Item
  - `⌘-F`: Trigger Search
  - `⌘-S`: Save
  - `⌘-W`: Close window / dismiss modal
  - `⌘-,`: Open Settings

---

## 5. Modal Presentation Adaptation
- [ ] **Popovers Over Sheets**: Contextual menus and pickers appear as `.popover` anchored to the triggering element, rather than full-width bottom sheets.
- [ ] **Compact Adaptation**: Popovers specify `.presentationCompactAdaptation(.sheet)` so they automatically present as sheets on iPhone and popovers on iPad.

---

## 6. Drag and Drop Support
- [ ] **Draggable Content**: Primary entities (documents, photos, list items) implement `.draggable()`.
- [ ] **Drop Targets**: Collections, folders, and canvas views implement `.dropDestination()` with clear visual drop proposal feedback.
