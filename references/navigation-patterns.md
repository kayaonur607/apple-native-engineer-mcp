# Navigation Architecture & Patterns

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Navigation decides how lost a user can get, what the system restores after termination, and whether the
app adapts to iPad and Mac without a second codebase. Choose the container first; the screens are easy.

---

## 1. Pick the container

| Container | API | Use when | Don't use when |
| :--- | :--- | :--- | :--- |
| Hierarchy | `NavigationStack` | Drill-down inside one tab, three or more levels | You need a sidebar |
| Peers | `TabView` + `Tab` | Two to five top-level destinations | More than five, or a Mac-first app |
| Columns | `NavigationSplitView` | iPad/Mac; collapses to a stack on iPhone | A single-column iPhone app |
| Interruption | `.sheet` | One self-contained task or a confirmation | Browsing a second hierarchy |
| Blocking task | `.fullScreenCover` | Camera, onboarding, checkout | Anything the user may want to peek out of |

**`NavigationView` is removed from new code.** It is deprecated since iOS 16, cannot express a typed
path, and `tools/project-inspector/inspect_project.py` reports it as `PROJ008` on every scan.

---

## 2. NavigationStack: type the path

```swift
enum Route: Hashable, Codable {
    case profile(id: String)
    case order(id: UUID)
}

struct AppShell: View {
    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            InboxView { orderID in path.append(.order(id: orderID)) }
                .navigationTitle("Inbox")
                .navigationDestination(for: Route.self) { route in
                    switch route {
                    case .profile(let id): ProfileView(userID: id)
                    case .order(let id): OrderView(orderID: id)
                    }
                }
        }
    }
}
```

| Rule | Why |
| :--- | :--- |
| Type the path as `[Route]` when every destination shares one type | You get `append`, `removeLast`, indexing and `Codable` restoration for free |
| Reach for `NavigationPath` only with heterogeneous routes | It boxes `Hashable` values and you lose typed access |
| Attach `.navigationDestination(for:)` inside the stack, never in a lazy row | A destination declared in a `List` row is unregistered when the row scrolls away |
| Never nest a stack inside a stack | Duplicate bars, wrong back titles, broken transitions |

Because the path is plain state, routing is mutation: `path.append(.order(id:))` pushes,
`removeLast()` pops, `removeAll()` returns to root, and `path = [route]` replaces the stack on a cold
deep link. `.navigationDestination(isPresented:)` exists, but a Boolean is not a route — it cannot be
restored or inspected.

---

## 3. Deep links and state restoration

```swift
struct RootView: View {
    @SceneStorage("navigation.path") private var storedPath: Data?
    @State private var path: [Route] = []

    var body: some View {
        NavigationStack(path: $path) {
            HomeView()
                .navigationDestination(for: Route.self) { route in
                    destination(for: route)
                }
        }
        .onOpenURL { url in
            guard let route = Route(url: url) else { return }
            path = [route]        // cold link replaces; a warm link appends
        }
        .task {
            path = storedPath.flatMap { try? JSONDecoder().decode([Route].self, from: $0) } ?? []
        }
        .onChange(of: path) { _, newPath in
            storedPath = try? JSONEncoder().encode(newPath)
        }
    }
}
```

`.onOpenURL` belongs on the root view, above the stack — not on a destination that may not exist yet.
`SceneStorage` is restored per scene, so iPad multi-window keeps two independent stacks.

---

## 4. NavigationSplitView

```swift
struct WorkspaceView: View {
    @State private var selectedFolderID: Folder.ID?
    @State private var columnVisibility: NavigationSplitViewVisibility = .all

    var body: some View {
        NavigationSplitView(columnVisibility: $columnVisibility) {
            List(folders, selection: $selectedFolderID) { folder in
                Label(folder.name, systemImage: "folder")
            }
            .navigationTitle("Folders")
            .navigationSplitViewColumnWidth(min: 200, ideal: 240, max: 320)
        } detail: {
            if let selectedFolderID {
                FolderView(folderID: selectedFolderID)
            } else {
                ContentUnavailableView("No Folder", systemImage: "folder")
            }
        }
        .navigationSplitViewStyle(.balanced)
    }
}
```

- The detail column must handle `nil`. A blank pane on launch looks broken; `ContentUnavailableView` is
  the system answer.
- `columnVisibility` is a `Binding`, so a toolbar button can collapse the sidebar to `.detailOnly`.
- On iPhone the split view **collapses automatically** into a push stack.
  `NavigationSplitView(columnVisibility:preferredCompactColumn:)` picks which column the compact
  presentation starts on.

Add an inspector with `.inspector(isPresented:)` plus `.inspectorColumnWidth(min:ideal:max:)` — see
[iPad Design](ipad-design.md).

---

## 5. TabView: `Tab`, not `.tabItem`

`Tab` is the iOS 18 replacement for the `.tabItem`/`.tag` pair, typed end to end, so the selection can
never point at a missing tab. Guard it — the deployment floor is iOS 17.

```swift
enum AppTab: Hashable { case home, library }

struct RootTabs: View {
    @State private var selection: AppTab = .home

    var body: some View {
        if #available(iOS 18.0, *) {
            TabView(selection: $selection) {
                Tab("Home", systemImage: "house", value: AppTab.home) {
                    NavigationStack { HomeView() }
                }
                Tab("Library", systemImage: "books.vertical", value: AppTab.library) {
                    NavigationStack { LibraryView() }
                }
            }
        } else {
            TabView(selection: $selection) {
                NavigationStack { HomeView() }
                    .tabItem { Label("Home", systemImage: "house") }
                    .tag(AppTab.home)
                NavigationStack { LibraryView() }
                    .tabItem { Label("Library", systemImage: "books.vertical") }
                    .tag(AppTab.library)
            }
        }
    }
}
```

| Refinement | Availability | Effect |
| :--- | :--- | :--- |
| `Tab(_:systemImage:value:role: .search)` | iOS 18 | Puts search in the system search slot instead of a peer tab |
| `.tabViewStyle(.sidebarAdaptable)` | iOS 18 | Lets iPad users switch between tab bar and sidebar |
| `.tabBarMinimizeBehavior(.onScrollDown)` | iOS 26 | Hides the bar while reading; returns on scroll up |
| `.toolbarOverflowMenu { }` | iOS 27 | Moves low-priority toolbar items into an overflow menu |

Every row needs a guard: an unguarded iOS 26 call on an iOS 17 target is a compile error, not a runtime
surprise.

---

## 6. Sheet, push, or cover

| The user is… | Present as | Why |
| :--- | :--- | :--- |
| Going deeper in the same hierarchy | Push | Back gesture, title, and restoration come free |
| Completing one task, then returning | `.sheet` | Context stays visible behind the sheet |
| Blocked from proceeding without finishing | `.fullScreenCover` | No accidental dismissal mid-task |
| Reading a short detail beside content | `.popover` (iPad/Mac) | Keeps the source visible |

Use `.sheet(item:)` rather than `.sheet(isPresented:)` when the sheet needs data: no optional unwrap in
the body. A popover becomes a sheet on iPhone by default — `.presentationCompactAdaptation(.sheet)`
states that intent. `.interactiveDismissDisabled()` belongs only on screens with unsaved work; permanent
use traps the user.

---

## 7. Review checklist

- [ ] No `NavigationView` anywhere (`PROJ008` is clean)
- [ ] Every stack has a typed path; no `isActive`/`isPresented` booleans drive navigation
- [ ] `.navigationDestination(for:)` sits inside the stack, outside lazy containers
- [ ] Deep links replace the path on cold start and append on warm start
- [ ] The path survives termination via `SceneStorage`
- [ ] Split-view detail handles the empty selection with `ContentUnavailableView`
- [ ] Tabs use `Tab` on iOS 18+ with a `.tabItem` fallback below it
- [ ] Toolbar items use semantic placements, not `Spacer()` — see [iPhone Design](iphone-design.md)

---

## 8. Official HIG references

- [Apple HIG — Navigation](https://developer.apple.com/design/human-interface-guidelines/navigation)
- [Apple HIG — Tab bars](https://developer.apple.com/design/human-interface-guidelines/tab-bars)
- [Apple HIG — Toolbars](https://developer.apple.com/design/human-interface-guidelines/toolbars)
- [Apple HIG — Modality](https://developer.apple.com/design/human-interface-guidelines/modality)
