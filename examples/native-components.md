# Native Components Implementation Examples

This document demonstrates production implementations of standard Apple native components, contrasting anti-patterns with clean, HIG-compliant SwiftUI code.

---

## 1. Native Settings Form

A production-quality grouped form with section headers, footers, pickers, toggles, and destructive confirmation.

```swift
import SwiftUI

enum StorageTier: String, CaseIterable, Identifiable {
    case basic = "50 GB"
    case standard = "200 GB"
    case premium = "2 TB"
    
    var id: String { rawValue }
}

struct AccountSettingsView: View {
    @State private var syncEnabled: Bool = true
    @State private var selectedTier: StorageTier = .standard
    @State private var downloadOverCellular: Bool = false
    @State private var showDeleteConfirmation: Bool = false
    
    var body: some View {
        Form {
            Section {
                Toggle("iCloud Sync", isOn: $syncEnabled)
                    .tint(.blue)
                
                Picker("Storage Plan", selection: $selectedTier) {
                    ForEach(StorageTier.allCases) { tier in
                        Text(tier.rawValue).tag(tier)
                    }
                }
                .pickerStyle(.menu)
            } header: {
                Text("Cloud Storage")
            } footer: {
                Text("Data is encrypted end-to-end using your Apple ID.")
            }
            
            Section("Network Preferences") {
                Toggle("Download Over Cellular", isOn: $downloadOverCellular)
                    .tint(.blue)
            }
            
            Section {
                Button(role: .destructive) {
                    showDeleteConfirmation = true
                } label: {
                    Label("Delete Cached Data", systemImage: "trash")
                }
            } footer: {
                Text("Deletes local offline cache. Cloud data remains untouched.")
            }
        }
        .navigationTitle("Account Settings")
        .confirmationDialog(
            "Are you sure you want to delete cache?",
            isPresented: $showDeleteConfirmation,
            titleVisibility: .visible
        ) {
            Button("Delete Cache", role: .destructive) {
                // Clear cache action
            }
            Button("Cancel", role: .cancel) { }
        } message: {
            Text("This action cannot be undone.")
        }
    }
}
```

---

## 2. Interactive Search with Scopes & Suggestions

```swift
import SwiftUI

struct AssetSearchItem: Identifiable {
    let id = UUID()
    let name: String
    let type: String
}

enum AssetScope: String, CaseIterable {
    case all = "All"
    case images = "Images"
    case documents = "Docs"
}

struct NativeSearchExperienceView: View {
    @State private var searchText = ""
    @State private var selectedScope: AssetScope = .all
    
    let allAssets = [
        AssetSearchItem(name: "Annual Report 2026.pdf", type: "Docs"),
        AssetSearchItem(name: "Brand Logo.png", type: "Images"),
        AssetSearchItem(name: "Team Photo.jpg", type: "Images"),
        AssetSearchItem(name: "Specifications.pdf", type: "Docs")
    ]
    
    var filteredAssets: [AssetSearchItem] {
        allAssets.filter { asset in
            let matchesScope = selectedScope == .all || asset.type == selectedScope.rawValue
            let matchesQuery = searchText.isEmpty || asset.name.localizedCaseInsensitiveContains(searchText)
            return matchesScope && matchesQuery
        }
    }
    
    var body: some View {
        NavigationStack {
            List(filteredAssets) { asset in
                Label(asset.name, systemImage: asset.type == "Images" ? "photo" : "doc.text")
            }
            .navigationTitle("Assets")
            .searchable(text: $searchText, prompt: "Search files...")
            .searchScopes($selectedScope) {
                ForEach(AssetScope.allCases, id: \.self) { scope in
                    Text(scope.rawValue).tag(scope)
                }
            }
            .overlay {
                if filteredAssets.isEmpty {
                    ContentUnavailableView.search(text: searchText)
                }
            }
        }
    }
}
```
