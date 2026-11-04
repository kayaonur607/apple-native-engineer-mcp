# Native UI Components Guide

Apple provides a rich set of native UI components designed for high performance, ergonomic touch response, keyboard and pointer navigation, and full accessibility compliance. Using native components ensures your app immediately inherits system behaviors and upgrades across iOS and iPadOS versions.

---

## 1. Buttons & Controls

### A. Standard Button Styles
Never build custom button shapes with arbitrary `.background()` rectangles when SwiftUI's native button styles exist:

```swift
// ❌ ANTI-PATTERN: Custom button recreating system styles poorly without hit testing or press states
Text("Continue")
    .foregroundColor(.white)
    .padding()
    .background(Color.blue)
    .cornerRadius(10)
    .onTapGesture { submit() }

// ✅ CORRECT: Semantic button styles with native press states, sound, and keyboard support
Button("Continue") {
    submit()
}
.buttonStyle(.borderedProminent)
.controlSize(.large)
.tint(.blue)
```

### B. Button Hierarchy & Roles
- **`.borderedProminent`**: Use for the single primary call-to-action (CTA) on a screen. Avoid having more than one prominent button per visible viewport.
- **`.bordered`**: Use for secondary actions (e.g., "Cancel", "Save Draft").
- **`.borderless` / `.plain`**: Use for tertiary actions or inline list item buttons.
- **Destructive Role**: Always flag destructive buttons with `role: .destructive`. This automatically styles the button in system red and marks it appropriately for VoiceOver.

```swift
Button("Delete Account", role: .destructive) {
    showDeleteConfirmation = true
}
.buttonStyle(.bordered)
```

---

## 2. Lists & Forms

Lists and Forms represent the backbone of Apple data presentation.

### A. Choosing the Right Style
- **`.insetGrouped`**: The standard for iOS settings, configuration screens, and content groupings.
- **`.plain`**: Standard for continuous homogeneous data feeds (e.g., Mail message list, Notes list).
- **`.sidebar`**: Exclusively used for top-level navigation on iPadOS and macOS.

```swift
List {
    Section {
        Toggle("Push Notifications", isOn: $notificationsEnabled)
        Toggle("Face ID Unlock", isOn: $biometricsEnabled)
    } header: {
        Text("Security & Alerts")
    } footer: {
        Text("Biometric data is securely processed in the Secure Enclave and never leaves your device.")
    }
}
.listStyle(.insetGrouped)
```

### B. Swipe Actions
Provide direct manipulation shortcuts using `.swipeActions`:
```swift
.swipeActions(edge: .trailing, allowsFullSwipe: true) {
    Button(role: .destructive) {
        delete(item)
    } label: {
        Label("Delete", systemImage: "trash")
    }
    
    Button {
        archive(item)
    } label: {
        Label("Archive", systemImage: "archivebox")
    }
    .tint(.indigo)
}
```

---

## 3. Sheets, Popovers & Presentation Detents

### Bottom Sheet Ergonomics (iOS 16+)
Modal sheets should present with interactive detents that allow the user to reference underlying screen data while interacting with the sheet.

```swift
.sheet(isPresented: $showFilterSheet) {
    FilterView()
        .presentationDetents([.fraction(0.35), .medium, .large])
        .presentationDragIndicator(.visible)
        .presentationCornerRadius(24)
        .presentationBackground(.regularMaterial)
}
```

### Adapting Sheet to Popover on iPadOS
On iPhone, secondary workflows present as bottom sheets. On iPad, presenting a giant full-screen sheet disorients the user; use `.popover` anchored to the triggering button:

```swift
Button {
    showInfo.toggle()
} label: {
    Image(systemName: "info.circle")
}
.popover(isPresented: $showInfo) {
    InfoDetailView()
        .frame(minWidth: 320, minHeight: 240)
        .presentationCompactAdaptation(.sheet) // Sheet on iPhone, Popover on iPad!
}
```

---

## 4. Search Interfaces & Suggestions

Native search integrates seamlessly into the navigation bar and hides/reveals automatically during scroll:

```swift
NavigationStack {
    List(filteredItems) { item in
        ItemRow(item: item)
    }
    .navigationTitle("Documents")
    .searchable(text: $searchText, prompt: "Search files, tags, or authors")
    .searchSuggestions {
        ForEach(recentSearches, id: \.self) { suggestion in
            Text(suggestion).searchCompletion(suggestion)
        }
    }
    .searchScopes($selectedScope) {
        Text("All").tag(SearchScope.all)
        Text("Favorites").tag(SearchScope.favorites)
        Text("Shared").tag(SearchScope.shared)
    }
}
```

---

## 5. Modern Empty, Loading & Error States (iOS 17+)

Never build home-grown empty states with disconnected text and icons. Use the official `ContentUnavailableView`:

```swift
// ✅ Standard Empty State
if items.isEmpty && searchText.isEmpty {
    ContentUnavailableView(
        "No Documents Yet",
        systemImage: "doc.on.doc",
        description: Text("Tap the + button to create your first document.")
    )
} else if items.isEmpty && !searchText.isEmpty {
    // ✅ Standard Search Not Found State
    ContentUnavailableView.search(text: searchText)
}
```

---

## 6. Pickers, Toggles & Sliders

Use native pickers with appropriate styles:
- **`.pickerStyle(.segmented)`**: For 2 to 5 mutually exclusive choices.
- **`.pickerStyle(.menu)`**: For compact dropdown selections in toolbars or forms.
- **`.pickerStyle(.wheel)`**: Reserved primarily for date/time selection or specialized countdown pickers.

```swift
Picker("Filter Category", selection: $category) {
    ForEach(Category.allCases) { cat in
        Text(cat.title).tag(cat)
    }
}
.pickerStyle(.segmented)
```

---

## 7. Official HIG References
- [Apple HIG - Components](https://developer.apple.com/design/human-interface-guidelines/components)
- [Apple HIG - Buttons](https://developer.apple.com/design/human-interface-guidelines/buttons)
- [Apple HIG - Sheets](https://developer.apple.com/design/human-interface-guidelines/sheets)
- [Apple HIG - Popovers](https://developer.apple.com/design/human-interface-guidelines/popovers)
