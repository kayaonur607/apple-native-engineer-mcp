# SwiftData & CloudKit Sync

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Developer Documentation — SwiftData](https://developer.apple.com/documentation/swiftdata), [WWDC23: Meet SwiftData](https://developer.apple.com/videos/play/wwdc2023/10187/), [WWDC24: Create a custom data store with SwiftData](https://developer.apple.com/videos/play/wwdc2024/10138/)

SwiftData plus CloudKit is the shortest path to sync with no backend. It is also the path with the strictest
schema rules: CloudKit decides what a valid model is, and it rejects at runtime what the compiler accepted.
When you need control over conflict resolution or record shapes, use `CKSyncEngine` instead.

---

## 1. A model that survives CloudKit

```swift
import Foundation
import SwiftData

@Model
final class Note {
    var title: String = ""
    var body: String = ""
    var createdAt: Date = Date()
    var isArchived: Bool = false

    @Relationship(deleteRule: .cascade, inverse: \Tag.notes)
    var tags: [Tag] = []

    init(title: String, body: String = "") {
        self.title = title
        self.body = body
    }
}

@Model
final class Tag {
    var name: String = ""
    var notes: [Note] = []

    init(name: String) {
        self.name = name
    }
}
```

Every stored property has a default. That is not style — a CloudKit record can arrive without the field, and a
non-optional attribute with no default fails container creation.

---

## 2. What CloudKit will not accept

| Rule | Why |
| :--- | :--- |
| Every attribute optional or defaulted | Older records and other devices omit fields |
| No `@Attribute(.unique)`, no `#Unique` | No global uniqueness across a distributed store |
| Relationships optional or defaulted to `[]` | The inverse may not have synced yet |
| Explicit inverse on every relationship | CloudKit merges by record identifier; the graph must be traversable |
| Schema changes are additive after production deploy | Deleting or retyping a field breaks clients on the old schema |
| Model and property names are the CloudKit schema | A rename is a migration, not a refactor |

`#Unique` exists in SwiftData (iOS 18+) and works locally. It is incompatible with CloudKit for the same
reason as `@Attribute(.unique)`: uniqueness cannot be enforced without a server-side transaction.

---

## 3. Container configuration

```swift
import SwiftData
import SwiftUI

@main
struct NotesApp: App {
    private let container: ModelContainer = {
        let schema = Schema([Note.self, Tag.self])
        let configuration = ModelConfiguration(
            "Notes",
            schema: schema,
            cloudKitDatabase: .private("iCloud.com.example.notes")
        )
        do {
            return try ModelContainer(for: schema, configurations: [configuration])
        } catch {
            // Loud failure beats a silent in-memory container that looks like data loss.
            fatalError("ModelContainer: \(error)")
        }
    }()

    var body: some Scene {
        WindowGroup { NoteList() }
            .modelContainer(container)
    }
}
```

`CloudKitDatabase` is `.automatic`, `.none` or `.private(_:)`. `.automatic` picks the first container in the
entitlements; name it explicitly when the app ships more than one. The entitlement also needs the iCloud
capability, CloudKit service, your container identifier, and the Remote notifications background mode.

---

## 4. Querying

```swift
import SwiftData
import SwiftUI

struct NoteList: View {
    @Environment(\.modelContext) private var context
    @Query(
        filter: #Predicate<Note> { !$0.isArchived },
        sort: \Note.createdAt,
        order: .reverse
    ) private var notes: [Note]

    var body: some View {
        List(notes) { note in
            VStack(alignment: .leading) {
                Text(note.title).font(.headline)
                Text(note.createdAt, format: .dateTime.day().month().year())
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .onDelete(perform: delete)
    }

    private func delete(_ offsets: IndexSet) {
        for index in offsets {
            context.delete(notes[index])
        }
    }
}
```

`@Query` re-runs when the store changes, including changes that arrive from CloudKit. A predicate you cannot
translate to `NSPredicate` is a runtime crash, not a compile error — keep predicates to stored properties and
simple comparisons.

---

## 5. Work off the main actor

```swift
import SwiftData

@ModelActor
actor NoteImporter {
    func importNotes(_ payloads: [NotePayload]) throws {
        for payload in payloads {
            modelContext.insert(Note(title: payload.title, body: payload.body))
        }
        try modelContext.save()
    }
}

// let importer = NoteImporter(modelContainer: container)
// try await importer.importNotes(payloads)
```

`@ModelActor` generates the `modelContainer` and a private `modelContext` on the actor. Never pass a
`PersistentModel` between actors — pass `PersistentIdentifier` and re-fetch inside the actor.

---

## 6. Errors you must handle

```swift
import CloudKit

func handle(_ error: Error) {
    guard let cloudError = error as? CKError else { return }
    switch cloudError.code {
    case .serverRecordChanged:
        // Another device won. Re-fetch, merge, retry the save.
        break
    case .partialFailure:
        // Per-item errors live in userInfo[CKPartialErrorsByItemIDKey].
        break
    case .accountTemporarilyUnavailable:
        // Keep local data, retry after CKAccountChanged.
        break
    case .zoneNotFound:
        // Recreate the zone, then replay the change batch.
        break
    case .unknownItem:
        // The record was deleted on another device; delete it locally.
        break
    default:
        break
    }
}
```

SwiftData resolves most of these for you. If you hand-roll CloudKit, `serverRecordChanged` is the one that
silently discards edits when you ignore it: merge field-by-field, do not overwrite with the local copy.

---

## 7. CKSyncEngine (iOS 17+) for custom stores

| Piece | Role |
| :--- | :--- |
| `CKSyncEngine.Configuration(database:stateSerialization:delegate:)` | Engine setup; `stateSerialization` resumes where you left off |
| `fetchChanges()` / `sendChanges()` | Explicit pushes when `automaticallySync` is off |
| `CKSyncEngineDelegate.handleEvent(_:syncEngine:)` | Account changes, fetched changes, sent changes, failures |
| `CKSyncEngineDelegate.nextRecordZoneChangeBatch(_:syncEngine:)` | Supplies the next batch of records to upload |

```swift
import CloudKit

final class SyncDelegate: CKSyncEngineDelegate {
    func handleEvent(_ event: CKSyncEngine.Event, syncEngine: CKSyncEngine) async {
        switch event {
        case .stateUpdate(let update):
            persist(update.stateSerialization)
        case .accountChange(let change):
            handleAccountChange(change)
        case .fetchedRecordZoneChanges(let changes):
            apply(changes.modifications, changes.deletions)
        case .sentRecordZoneChanges(let changes):
            markSynced(changes.savedRecords, changes.failedRecordSaves)
        default:
            break
        }
    }

    func nextRecordZoneChangeBatch(
        _ context: CKSyncEngine.SendChangesContext,
        syncEngine: CKSyncEngine
    ) async -> CKSyncEngine.RecordZoneChangeBatch? {
        nil
    }
}
```

Persist `stateSerialization` on every `.stateUpdate`. Losing it forces a full refetch on next launch — the
engine cannot tell what you already applied.

---

## 8. Sharing

```swift
import CloudKit

func makeShare(in database: CKDatabase, zone: CKRecordZone) async throws -> CKShare {
    let share = CKShare(recordZoneID: zone.zoneID)
    share[CKShare.SystemFieldKey.title] = "Shared Notes"
    _ = try await database.save(share)
    return share
}
```

`CKShare(rootRecord:)` shares one record and its hierarchy; `CKShare(recordZoneID:)` shares the whole zone
(iOS 15+). A share is itself a record: save it through the same database, and handle `.serverRecordChanged`
when two participants edit the same field.

---

## 9. Account status

```swift
import CloudKit

func checkiCloud() async throws -> Bool {
    let container = CKContainer(identifier: "iCloud.com.example.notes")
    switch try await container.accountStatus() {
    case .available:
        return true
    case .noAccount, .restricted, .couldNotDetermine, .temporarilyUnavailable:
        return false
    @unknown default:
        return false
    }
}
```

Check before offering sync UI, and observe `CKAccountChanged` to re-check. `.temporarilyUnavailable` means the
account exists but CloudKit is not ready — do not delete local data when you see it.

---

## 10. Review checklist

- [ ] No unique constraints on any model in the CloudKit schema
- [ ] Every attribute optional or defaulted; every relationship has a default and an inverse
- [ ] Container identifier matches the entitlement exactly
- [ ] Remote notifications background mode enabled
- [ ] Production schema deployed before the first App Store build
- [ ] `serverRecordChanged` and `partialFailure` handled, not swallowed
- [ ] Background imports run through `@ModelActor`, not the main context
- [ ] Account status checked; signed-out state does not delete local data

For the local-only side of SwiftData, see `swiftui-engineering.md`; for record-shaped work outside SwiftData,
the CloudKit headers are the authority.
