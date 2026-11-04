# SwiftData & CloudKit Sync Engineering

> **Authority**: [Apple Developer Documentation — SwiftData](https://developer.apple.com/documentation/swiftdata), [WWDC23: Meet SwiftData](https://developer.apple.com/videos/play/wwdc2023/10187/), [WWDC24: Create a custom data store with SwiftData](https://developer.apple.com/videos/play/wwdc2024/10138/)  
> **Status**: Official Apple Recommendations & Specifications

SwiftData is Apple's native persistence framework designed specifically for modern Swift and SwiftUI. Paired with CloudKit, it synchronizes models seamlessly across a user's devices without third-party backends.

---

## 1. Defining SwiftData Models

Models in SwiftData are regular Swift classes annotated with `@Model`.

```swift
import SwiftData
import Foundation

@Model
final class NoteItem {
    @Attribute(.unique) var id: UUID
    var title: String
    var content: String
    var createdAt: Date
    var isArchived: Bool
    
    // Relationships
    @Relationship(deleteRule: .cascade, inverse: \TagItem.notes)
    var tags: [TagItem] = []

    init(title: String, content: String, tags: [TagItem] = []) {
        self.id = UUID()
        self.title = title
        self.content = content
        self.createdAt = Date()
        self.isArchived = false
        self.tags = tags
    }
}

@Model
final class TagItem {
    @Attribute(.unique) var name: String
    var notes: [NoteItem] = []

    init(name: String) {
        self.name = name
    }
}
```

---

## 2. CloudKit Sync Requirements

To enable automatic CloudKit syncing with SwiftData, models must obey strict schema constraints:

1. **Every property must either be optional or have a default value**: CloudKit stores records in an eventually consistent schema where new fields may be missing from older device payloads.
2. **All relationships must be optional or default to an empty array (`[]`)**.
3. **No `@Attribute(.unique)`**: CloudKit distributed syncing cannot enforce global uniqueness without custom server-side transactions. If uniqueness is required, manage it in client code.
4. **App Entitlements**:
   - Enable `iCloud` capability in Xcode target.
   - Check `CloudKit` services and specify container `iCloud.com.example.app`.
   - Enable `Background Modes` -> `Remote notifications`.

```swift
@Model
final class CloudSyncableItem {
    var id: UUID = UUID()
    var title: String = ""
    var timestamp: Date = Date()
    var isPinned: Bool = false
    
    init(title: String) {
        self.id = UUID()
        self.title = title
        self.timestamp = Date()
        self.isPinned = false
    }
}
```

---

## 3. Configuring the Container

```swift
import SwiftUI
import SwiftData

@main
struct NotesApp: App {
    var sharedModelContainer: ModelContainer = {
        let schema = Schema([
            NoteItem.self,
            TagItem.self
        ])
        
        let configuration = ModelConfiguration(
            schema: schema,
            isStoredInMemoryOnly: false,
            cloudKitDatabase: .private("iCloud.com.example.NotesApp")
        )

        do {
            return try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            fatalError("Could not create ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup {
            NotesListView()
        }
        .modelContainer(sharedModelContainer)
    }
}
```

---

## 4. SwiftUI Queries & Predicates

Use `@Query` in SwiftUI views for reactive list updates whenever items are inserted, updated, or deleted.

```swift
struct NotesListView: View {
    @Environment(\.modelContext) private var modelContext
    
    // Declarative query with sorting and predicate
    @Query(
        filter: #Predicate<NoteItem> { !$0.isArchived },
        sort: \NoteItem.createdAt,
        order: .reverse
    ) private var activeNotes: [NoteItem]

    var body: some View {
        List {
            ForEach(activeNotes) { note in
                VStack(alignment: .leading) {
                    Text(note.title).font(.headline)
                    Text(note.createdAt.formatted(date: .abbreviated, time: .shortened))
                        .font(.caption)
                        .foregroundStyle(.secondary)
                }
            }
            .onDelete(perform: deleteNotes)
        }
    }

    private func deleteNotes(offsets: IndexSet) {
        for index in offsets {
            modelContext.delete(activeNotes[index])
        }
    }
}
```

---

## 5. Schema Migration (`SchemaMigrationPlan`)

When updating production models with existing user data:

```swift
enum NotesMigrationPlan: SchemaMigrationPlan {
    static var schemas: [any VersionedSchema.Type] {
        [NotesSchemaV1.self, NotesSchemaV2.self]
    }

    static var stages: [MigrationStage] {
        [migrateV1toV2]
    }

    static let migrateV1toV2 = MigrationStage.custom(
        fromVersion: NotesSchemaV1.self,
        toVersion: NotesSchemaV2.self,
        willMigrate: { context in
            // Pre-migration transformation
        },
        didMigrate: { context in
            // Post-migration validation
        }
    )
}
```
