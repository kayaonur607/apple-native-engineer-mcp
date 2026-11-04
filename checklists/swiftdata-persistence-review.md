# SwiftData & Persistence Review Checklist

Use this checklist to audit SwiftData architecture, schema design, migration plans, and iCloud CloudKit synchronization for safety, performance, and data integrity.

---

## 1. Schema & Model Design
- [ ] **Model Macro**: All entity classes use the modern `@Model` macro.
- [ ] **Explicit Relationships**: Relationships specify explicit deletion rules (e.g. `deleteRule: .cascade`, `deleteRule: .nullify`).
- [ ] **Inverse Relationships**: Bidirectional relationships define explicit inverse relationships (`inverse: \Tag.notes`).
- [ ] **Unique Constraints**: Unique identifiers use `@Attribute(.unique)` only when CloudKit sync is **not** active (CloudKit cannot enforce client unique constraints).

---

## 2. CloudKit Synchronization Compatibility
- [ ] **Default Values / Optionality**: All attributes have either default initial values or are declared as optionals (`?`).
- [ ] **Array Defaults**: To-many relationships default to empty arrays (`= []`).
- [ ] **iCloud Container Entitlement**: Target entitlement includes `iCloud` capability with `CloudKit` enabled and remote notification background mode active.
- [ ] **Private Database Configuration**: The `ModelConfiguration` targets the correct `.private` CloudKit container identifier.

---

## 3. Concurrency & Context Safety
- [ ] **Actor Isolation**: Models bound to SwiftUI views are accessed on `@MainActor`.
- [ ] **Background Operations**: Large background batch insertions use a separate dedicated `ModelContext(modelContainer)`.
- [ ] **No Cross-Context Model Passing**: Model instances are never passed across actor boundaries; pass persistent identifiers (`PersistentIdentifier`) instead and refetch.

---

## 4. Migrations & Versioning
- [ ] **Versioned Schemas**: Production schema iterations implement `VersionedSchema` protocols (e.g. `SchemaV1`, `SchemaV2`).
- [ ] **Migration Plan**: Custom transformations implement `SchemaMigrationPlan` with tested `MigrationStage` blocks.
- [ ] **Test Coverage**: Migrations are verified with unit tests migrating from legacy databases to current versions.
