# Native Components

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Every control in this page already handles: keyboard and pointer navigation, VoiceOver, Dynamic Type, RTL
mirroring, Increase Contrast, Reduce Motion, the focus ring, and the next three OS releases. A hand-built
imitation handles whatever you remembered on the day.

Reaching for the system control is the single highest-leverage decision in an iOS codebase.

---

## 1. Custom-drawn system chrome is a defect, not a style choice

| Rebuilt by hand | Should be | Linter |
| :--- | :--- | :--- |
| `HStack` of `Text` + `.onTapGesture` as a button | `Button` | — |
| Scroll view of `VStack` rows with dividers | `List` | `SWU018` |
| Custom tab bar floating over content | `TabView` + `Tab` | — |
| `TextField` in a `VStack` with a magnifier glyph | `.searchable(text:)` | — |
| Card with `.ultraThinMaterial` + `.blur` | `.glassEffect(_:in:)` (iOS 26+) | `LG010` |
| `.frame(height: 44)` press-state math | `.buttonStyle(.bordered)` + `.controlSize(.large)` | — |
| "Nothing here" `Image` + two `Text` views | `ContentUnavailableView` | — |
| `Rectangle().frame(height: 8)` as a progress bar | `ProgressView` / `Gauge` | — |

The tell for a rebuild is *state you have to manage yourself*: a pressed flag, a hover flag, a focus flag, a bar
that has to be clipped. The system control owns that state; yours will drift out of sync with the platform.

---

## 2. Choosing the scrolling container

| Need | Use | Why not the other |
| :--- | :--- | :--- |
| Heterogeneous, selectable rows | `List` | Gets swipe actions, edit mode, selection, separators free |
| Settings with sections and footers | `Form` | Same machinery, correct grouping and insets |
| A few cards, fixed count | `ScrollView { VStack }` | Everything is laid out eagerly, which is fine at 6 items |
| Long homogeneous collection, custom cells | `ScrollView { LazyVStack }` | Lazy, but you lose selection and swipe actions |
| Grid, bounded count | `LazyVGrid` inside `ScrollView` | `List` cannot do multi-column |
| A single long document | `ScrollView` + `Text` | — |

```swift
// ✅ Settings: Form supplies grouping, insets, footers and Dynamic Type rows
Form {
    Section {
        Toggle("Notifications", isOn: $notifications)
        Toggle("Face ID", isOn: $biometrics)
    } header: {
        Text("Security")
    } footer: {
        Text("Biometric data stays in the Secure Enclave.")
    }
}
```

`Section { } header: { } footer: { }` is all a settings screen needs. `.insetGrouped` is a `List` style; `Form`
already is one on iOS.

`.listStyle(.sidebar)` is for `NavigationSplitView` on iPad and Mac only. Using it on iPhone gives you a list
that looks wrong in a way users cannot name.

---

## 3. Tabs

`TabView` + `Tab` is the modern form (iOS 18+). `Tab` replaces `.tabItem` and is the only form that supports
`TabSection` and sidebar adaptation.

```swift
// ✅ iOS 18+: typed tabs, sidebar on iPad, tab bar on iPhone
TabView(selection: $tab) {
    Tab("Inbox", systemImage: "tray", value: TabItem.inbox) { InboxView() }
    Tab("Archive", systemImage: "archivebox", value: TabItem.archive) { ArchiveView() }
}
.tabViewStyle(.sidebarAdaptable)   // iOS 18+
```

```swift
// ✅ iOS 17 floor: same content, the pre-18 spelling
TabView(selection: $tab) {
    InboxView()
        .tabItem { Label("Inbox", systemImage: "tray") }
        .tag(TabItem.inbox)
    ArchiveView()
        .tabItem { Label("Archive", systemImage: "archivebox") }
        .tag(TabItem.archive)
}
```

`.tabViewStyle(.sidebarAdaptable)` is iOS 18.0+, so on an iOS 17 floor it sits inside an availability guard or
is omitted. Five tabs maximum on iPhone; the sixth becomes "More", which is a design smell, not a bug.

**Never float a custom bar over content.** It covers the safe area, ignores the scroll edge effect, breaks
VoiceOver's traversal order, and cannot participate in the iOS 26 glass merging.

---

## 4. Search

`.searchable` places the field in the navigation bar, collapses it on scroll, and wires the cancel button:

```swift
NavigationStack {
    List(results) { item in
        ItemRow(item: item)
    }
    .navigationTitle("Documents")
    .searchable(text: $query, prompt: "Search files, tags, authors")
    .searchScopes($scope) {
        Text("All").tag(Scope.all)
        Text("Shared").tag(Scope.shared)
    }
    .searchSuggestions {
        ForEach(recent) { term in
            Label(term.text, systemImage: "clock").searchCompletion(term.text)
        }
    }
}
```

`.searchable` needs a `NavigationStack` ancestor. Placed anywhere else it silently does nothing — the most
common "search is broken" report that has no bug.

---

## 5. Buttons and control size

| Style | Role | Note |
| :--- | :--- | :--- |
| `.borderedProminent` | The one primary action | One per viewport |
| `.bordered` | Secondary actions | Cancel, Save draft |
| `.borderless` / `.plain` | Tertiary, inline in lists | — |
| `.glass` / `.glassProminent` | iOS 26+ floating controls over content | Guard it |

```swift
Button("Continue") { submit() }
    .buttonStyle(.borderedProminent)
    .controlSize(.large)
```

`ControlSize` is `.mini`, `.small`, `.regular`, `.large`, `.extraLarge` (`.extraLarge` is iOS 17+). Set it where
the control is dense; do not shrink the hit target — `.controlSize` shrinks the visual, and the system keeps the
44pt target around it.

On iOS 26+, floating controls over content use the system glass styles rather than a material behind a
`.bordered` button:

```swift
if #available(iOS 26.0, macOS 26.0, *) {
    Button("Share", systemImage: "square.and.arrow.up") { share() }
        .buttonStyle(.glass)
} else {
    Button("Share", systemImage: "square.and.arrow.up") { share() }
        .buttonStyle(.bordered)
}
```

**Destructive actions** take `role: .destructive`; that supplies the red treatment *and* the VoiceOver
announcement. Colour alone does not.

---

## 6. Menus and pickers

```swift
Menu("Sort") {
    Picker("Sort by", selection: $sort) {
        Text("Date").tag(Sort.date)
        Text("Name").tag(Sort.name)
    }
    Divider()
    Button("Clear filters", role: .destructive) { filters.removeAll() }
}
```

A `Menu` containing a `Picker` renders the checkmark list users expect. `Menu` also gives you the press state,
the dismiss-on-scroll-out, and the iPad pointer highlight — none of which a `.popover` of `Button`s does.

`Picker` styles: `.segmented` for 2–5 mutually exclusive options, `.menu` for compact toolbar choices, `.wheel`
for date and time only. `.segmented` with six options is unreadable at AX5.

---

## 7. Status: progress and gauges

| Case | Control |
| :--- | :--- |
| Unknown duration | `ProgressView()` — determinate spinners do not exist |
| Known fraction, inline | `ProgressView(value:)` with `.progressViewStyle(.linear)` |
| A value in a range, with a scale | `Gauge(value:in:)` (iOS 16+) |
| A ring in a widget or complication | `.gaugeStyle(.accessoryCircularCapacity)` |

```swift
Gauge(value: progress, in: 0...1) {
    Text("Upload")
} currentValueLabel: {
    Text(progress, format: .percent.precision(.fractionLength(0)))
}
.gaugeStyle(.accessoryCircularCapacity)   // iOS 16+
.tint(.accentColor)
```

A `Rectangle` with a computed width is not a progress bar: it does not animate, does not announce its value to
VoiceOver, and cannot be read by Assistive Access.

---

## 8. Empty, search-empty and error states

```swift
if items.isEmpty {
    ContentUnavailableView(
        "No Documents",
        systemImage: "doc.on.doc",
        description: Text("Tap + to create your first document.")
    )
} else if results.isEmpty {
    ContentUnavailableView.search(text: query)   // iOS 17+
} else {
    List(results) { ItemRow(item: $0) }
}
```

`ContentUnavailableView` is iOS 17+. It centres correctly at every Dynamic Type size and provides the right
VoiceOver grouping. A hand-built empty state is usually a `VStack` that drifts off-centre at AX5.

Never ship a blank screen. `.redacted(reason: .placeholder)` for content that is loading, `ContentUnavailableView`
for content that is absent.

---

## 9. Scroll edges and presented sheets

```swift
List(items) { ItemRow(item: $0) }
    .contentMargins(.horizontal, 16, for: .scrollContent)

.sheet(isPresented: $showFilters) {
    FilterView()
        .presentationDetents([.fraction(0.35), .medium, .large])
        .presentationDragIndicator(.visible)
}
```

Since iOS 26 the soft fade under bars is a scroll edge effect, not a background colour — `.scrollEdgeEffectStyle(_:for:)`.
Painting a solid background behind a navigation bar to "fix" text collision is the pre-26 workaround and it now
fights the system. See [liquid-glass.md](liquid-glass.md).

`.presentationDetents` needs the sheet's content to be scrollable for `.medium` and `.large` to behave; a
fixed-height content view will jump.

---

## 10. Checklist

- [ ] Every tappable thing is a `Button`, `Toggle`, `Picker` or `Link` — not a `.onTapGesture`
- [ ] Collections use `List`, `Form` or a `Lazy*` container
- [ ] Tabs use `TabView`; no custom bar
- [ ] Search uses `.searchable` inside a `NavigationStack`
- [ ] Pressed, focused and disabled states come from a `ButtonStyle`, not from `@State`
- [ ] `ContentUnavailableView` for every empty and search-empty branch
- [ ] Progress uses `ProgressView` or `Gauge`
- [ ] No `.ultraThinMaterial` + `.blur` imitation of system chrome (`LG010`)
- [ ] Every iOS 18+ and iOS 26+ control is behind an availability guard with a real fallback

---

## 11. Sources

- Apple HIG, *Lists and tables* — <https://developer.apple.com/design/human-interface-guidelines/lists-and-tables>
- Apple HIG, *Tab bars* — <https://developer.apple.com/design/human-interface-guidelines/tab-bars>
- Apple HIG, *Search fields* — <https://developer.apple.com/design/human-interface-guidelines/search-fields>
- Apple HIG, *Buttons* — <https://developer.apple.com/design/human-interface-guidelines/buttons>
- Apple HIG, *Gauges* — <https://developer.apple.com/design/human-interface-guidelines/gauges>
- Apple HIG, *Menus* — <https://developer.apple.com/design/human-interface-guidelines/menus>
- `SwiftUI` iOS 27.2 — `Tab`, `.tabViewStyle(.sidebarAdaptable)`, `.buttonStyle(.glass)`, `Gauge`,
  `ContentUnavailableView.search(text:)`, `.controlSize(_:)`
