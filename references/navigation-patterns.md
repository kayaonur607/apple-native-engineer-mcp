# Navigation Architecture & Patterns

Navigation is the skeletal structure of an Apple application. A well-designed navigation architecture aligns with the user's mental model, preserves navigation state across app restarts, supports deep linking, and adapts seamlessly across iPhone, iPad, and Mac.

---

## 1. Primary Navigation Paradigms

Apple recognizes two primary navigation mental models:

1. **Hierarchical Navigation (Stack Drill-down)**:
   - One primary screen branches down into detail screens.
   - Pushes from trailing edge to leading edge; pops back via edge swipe or leading back button.
   - Engineered via `NavigationStack`.
2. **Flat / Lateral Navigation (Peer Contexts)**:
   - Several distinct categories or domains accessible without traversing a hierarchy.
   - Engineered via `TabView` (iPhone) or `NavigationSplitView` sidebar (iPad/macOS).
3. **Modal Presentation**:
   - A temporary, focused workflow presented on top of the current context (e.g., compose message, filter settings).
   - Engineered via `.sheet`, `.fullScreenCover`, or `.popover`.

---

## 2. Modern NavigationStack (iOS 16+)

Never use the deprecated `NavigationView`. Use `NavigationStack` with type-safe `NavigationPath` to support programmatic routing and deep linking:

```swift
enum AppRoute: Hashable {
    case userProfile(userId: String)
    case transactionDetail(id: UUID)
    case settings
}

struct MainFlowView: View {
    @State private var path = NavigationPath()
    
    var body: some View {
        NavigationStack(path: $path) {
            HomeDashboardView()
                .navigationTitle("Dashboard")
                .navigationDestination(for: AppRoute.self) { route in
                    switch route {
                    case .userProfile(let userId):
                        UserProfileView(userId: userId)
                    case .transactionDetail(let id):
                        TransactionDetailView(transactionId: id)
                    case .settings:
                        SettingsView()
                    }
                }
        }
    }
}
```

### Critical Rules for NavigationStack
- **Never nest `NavigationStack` inside another `NavigationStack`**: This causes duplicate navigation bars, incorrect back button titles, and broken transitions.
- **Always attach `.navigationTitle()` to the child view inside the stack**, never to the `NavigationStack` itself.

---

## 3. NavigationSplitView for iPad & Mac

`NavigationSplitView` is Apple's recommended architecture for multi-column navigation. On iPad and Mac it displays 2 or 3 columns simultaneously; when run on an iPhone, it **automatically collapses** into a standard hierarchical stack!

```swift
struct AdaptiveRootView: View {
    @State private var selectedCategory: Category?
    @State private var selectedItem: Item?
    @State private var columnVisibility: NavigationSplitViewVisibility = .all
    
    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            // Column 1: Sidebar
            List(Category.allCases, selection: $selectedCategory) { category in
                NavigationLink(value: category) {
                    Label(category.title, systemImage: category.icon)
                }
            }
            .navigationTitle("Categories")
        } content: {
            // Column 2: Content List
            if let selectedCategory {
                ItemList(category: selectedCategory, selectedItem: $selectedItem)
            } else {
                ContentUnavailableView("Select a Category", systemImage: "folder")
            }
        } detail: {
            // Column 3: Detail View
            if let selectedItem {
                ItemDetailView(item: selectedItem)
            } else {
                ContentUnavailableView("Select an Item", systemImage: "doc")
            }
        }
    }
}
```

---

## 4. Modern TabView (iOS 18+ Evolution)

In iOS 18 and iPadOS 18, `TabView` introduces a unified floating tab bar on iPad that can dynamically morph into a sidebar.

```swift
struct AppTabView: View {
    @State private var selectedTab: TabSelection = .home
    
    var body: some View {
        TabView(selection: $selectedTab) {
            NavigationStack {
                HomeView()
            }
            .tabItem {
                Label("Home", systemImage: "house.fill")
            }
            .tag(TabSelection.home)
            
            NavigationStack {
                ExploreView()
            }
            .tabItem {
                Label("Explore", systemImage: "safari.fill")
            }
            .tag(TabSelection.explore)
            
            NavigationStack {
                ProfileView()
            }
            .tabItem {
                Label("Profile", systemImage: "person.crop.circle.fill")
            }
            .tag(TabSelection.profile)
        }
    }
}
```

---

## 5. Toolbar Placements & Semantics

Always use semantic toolbar item placements rather than positioning buttons with spacers:

| Placement | Description & Idiom |
| :--- | :--- |
| `.topBarLeading` | Secondary actions, dismiss/back, or profile avatar. |
| `.topBarTrailing` | Primary action (Edit, Save, Add (+)). |
| `.bottomBar` | Auxiliary utilities, filters, or status counts on iPhone. |
| `.principal` | Custom title area (e.g. segmented control in navigation bar). |
| `.cancellationAction` | Sheet "Cancel" button (automatically placed leading on iOS, trailing on macOS). |
| `.confirmationAction`| Sheet "Done" / "Save" button (prominent, automatically positioned). |

```swift
.toolbar {
    ToolbarItem(placement: .cancellationAction) {
        Button("Cancel") { dismiss() }
    }
    ToolbarItem(placement: .confirmationAction) {
        Button("Save") { save() }
            .fontWeight(.semibold)
    }
}
```

---

## 6. Official HIG References
- [Apple HIG - Navigation](https://developer.apple.com/design/human-interface-guidelines/navigation)
- [Apple HIG - Tab Bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- [Apple HIG - Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)
