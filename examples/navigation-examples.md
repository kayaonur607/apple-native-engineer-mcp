# Navigation Architecture Examples

This document provides production-ready, copy-pasteable SwiftUI navigation architectures demonstrating type-safe routing, adaptive iPadOS-to-iPhone transitions, and deep linking.

---

## 1. Type-Safe `NavigationStack` with Programmatic Routing (iPhone)

This pattern demonstrates a clean, decoupled navigation stack that supports deep linking and programmatic resets without view coupling.

```swift
import SwiftUI

// MARK: - Navigation Routes
enum AppDestination: Hashable {
    case customerDetail(id: UUID)
    case invoiceDetail(number: String)
    case settings
}

// MARK: - Navigation Router (MainActor State)
@Observable
@MainActor
final class NavigationRouter {
    var path = NavigationPath()
    
    func navigate(to destination: AppDestination) {
        path.append(destination)
    }
    
    func popToRoot() {
        path.removeLast(path.count)
    }
}

// MARK: - Root View
struct MainNavigationView: View {
    @State private var router = NavigationRouter()
    
    var body: some View {
        NavigationStack(path: $router.path) {
            DashboardHomeView()
                .navigationTitle("Overview")
                .navigationDestination(for: AppDestination.self) { destination in
                    switch destination {
                    case .customerDetail(let id):
                        CustomerDetailView(customerId: id)
                    case .invoiceDetail(let number):
                        InvoiceDetailView(invoiceNumber: number)
                    case .settings:
                        AppSettingsView()
                    }
                }
        }
        .environment(router)
    }
}

struct DashboardHomeView: View {
    @Environment(NavigationRouter.self) private var router
    
    var body: some View {
        List {
            Section("Recent Customers") {
                Button("Acme Corporation") {
                    router.navigate(to: .customerDetail(id: UUID()))
                }
            }
        }
    }
}

struct CustomerDetailView: View {
    let customerId: UUID
    @Environment(NavigationRouter.self) private var router
    
    var body: some View {
        VStack(spacing: 20) {
            Text("Customer: \(customerId.uuidString)")
                .font(.headline)
            
            Button("Pop to Root") {
                router.popToRoot()
            }
            .buttonStyle(.borderedProminent)
        }
        .navigationTitle("Customer Details")
        .navigationBarTitleDisplayMode(.inline)
    }
}
```

---

## 2. Universal Adaptive `NavigationSplitView` (iPad & iPhone)

This implementation renders a 3-column split view with an inspector on iPadOS, and automatically collapses into a standard hierarchical stack on iPhone compact width.

```swift
import SwiftUI

struct WorkspaceDocument: Identifiable, Hashable {
    let id = UUID()
    let title: String
    let category: String
}

struct UniversalAppRoot: View {
    @State private var selectedCategory: String? = "Design"
    @State private var selectedDocument: WorkspaceDocument?
    @State private var showInspector: Bool = false
    
    let categories = ["Design", "Engineering", "Marketing", "Archive"]
    let sampleDocs = [
        WorkspaceDocument(title: "HIG Design System", category: "Design"),
        WorkspaceDocument(title: "SwiftUI Architecture", category: "Engineering"),
        WorkspaceDocument(title: "Product Launch", category: "Marketing")
    ]
    
    var body: some View {
        NavigationSplitView {
            // Sidebar Column
            List(categories, id: \.self, selection: $selectedCategory) { category in
                NavigationLink(category, value: category)
            }
            .navigationTitle("Folders")
        } content: {
            // Content Column
            List(sampleDocs.filter { $0.category == selectedCategory }, selection: $selectedDocument) { doc in
                NavigationLink(value: doc) {
                    VStack(alignment: .leading) {
                        Text(doc.title).font(.headline)
                        Text(doc.category).font(.subheadline).foregroundStyle(.secondary)
                    }
                }
            }
            .navigationTitle(selectedCategory ?? "Documents")
        } detail: {
            // Detail Column
            if let selectedDocument {
                DocumentContentView(document: selectedDocument)
            } else {
                ContentUnavailableView("No Document Selected", systemImage: "doc.text")
            }
        }
        .inspector(isPresented: $showInspector) {
            if let selectedDocument {
                InspectorMetadataView(document: selectedDocument)
                    .inspectorColumnWidth(min: 220, ideal: 260, max: 320)
            } else {
                ContentUnavailableView("No Selection", systemImage: "info.circle")
            }
        }
        .toolbar {
            ToolbarItem(placement: .topBarTrailing) {
                Button {
                    showInspector.toggle()
                } label: {
                    Label("Info", systemImage: "info.circle")
                }
            }
        }
    }
}

struct DocumentContentView: View {
    let document: WorkspaceDocument
    
    var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text(document.title)
                    .font(.largeTitle)
                    .fontWeight(.bold)
                Text("Editing document in \(document.category)...")
                    .foregroundStyle(.secondary)
            }
            .padding()
        }
        .navigationTitle(document.title)
        .navigationBarTitleDisplayMode(.inline)
    }
}

struct InspectorMetadataView: View {
    let document: WorkspaceDocument
    
    var body: some View {
        List {
            Section("Document Info") {
                LabeledContent("Title", value: document.title)
                LabeledContent("Category", value: document.category)
                LabeledContent("Identifier", value: document.id.uuidString.prefix(8))
            }
        }
        .navigationTitle("Inspector")
    }
}
```
