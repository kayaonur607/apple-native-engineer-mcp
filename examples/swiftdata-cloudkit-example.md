# SwiftData & CloudKit Sync Example

This example demonstrates a complete, production-grade SwiftUI and SwiftData architecture with iCloud CloudKit synchronization and search filtering.

```swift
import SwiftUI
import SwiftData

// MARK: - 1. Model Definitions (CloudKit-Compatible)
// NOTE: For CloudKit sync, properties must have default values or be optional.
@Model
final class HabitTrackerItem {
    var id: UUID = UUID()
    var name: String = ""
    var category: String = "Health"
    var targetCountPerWeek: Int = 5
    var currentCompletions: Int = 0
    var createdAt: Date = Date()
    var isArchived: Bool = false
    
    @Relationship(deleteRule: .cascade)
    var logs: [HabitLogEntry] = []

    init(name: String, category: String = "Health", targetCountPerWeek: Int = 5) {
        self.id = UUID()
        self.name = name
        self.category = category
        self.targetCountPerWeek = targetCountPerWeek
        self.currentCompletions = 0
        self.createdAt = Date()
        self.isArchived = false
        self.logs = []
    }
}

@Model
final class HabitLogEntry {
    var id: UUID = UUID()
    var timestamp: Date = Date()
    var notes: String? = nil

    init(notes: String? = nil) {
        self.id = UUID()
        self.timestamp = Date()
        self.notes = notes
    }
}

// MARK: - 2. SwiftUI Main View with @Query
struct HabitsDashboardView: View {
    @Environment(\.modelContext) private var modelContext
    @State private var searchText = ""
    @State private var isShowingCreateSheet = false

    @Query(
        filter: #Predicate<HabitTrackerItem> { !$0.isArchived },
        sort: \HabitTrackerItem.createdAt,
        order: .reverse
    ) private var habits: [HabitTrackerItem]

    var filteredHabits: [HabitTrackerItem] {
        if searchText.isEmpty {
            return habits
        } else {
            return habits.filter { $0.name.localizedStandardContains(searchText) }
        }
    }

    var body: some View {
        NavigationStack {
            List {
                ForEach(filteredHabits) { habit in
                    HabitCardRow(habit: habit) {
                        logCompletion(for: habit)
                    }
                }
                .onDelete(perform: archiveHabits)
            }
            .searchable(text: $searchText, prompt: "Search habits")
            .navigationTitle("Habits")
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        isShowingCreateSheet = true
                    } label: {
                        Label("Add Habit", systemImage: "plus")
                    }
                }
            }
            .sheet(isPresented: $isShowingCreateSheet) {
                CreateHabitSheet()
            }
            .overlay {
                if filteredHabits.isEmpty {
                    ContentUnavailableView(
                        "No Habits Found",
                        systemImage: "checklist",
                        description: Text("Create a new habit to start tracking your daily progress.")
                    )
                }
            }
        }
    }

    private func logCompletion(for habit: HabitTrackerItem) {
        habit.currentCompletions += 1
        let log = HabitLogEntry()
        habit.logs.append(log)
        try? modelContext.save()
    }

    private func archiveHabits(at offsets: IndexSet) {
        for index in offsets {
            let habit = filteredHabits[index]
            habit.isArchived = true
        }
        try? modelContext.save()
    }
}

// MARK: - 3. Habit Row Component
struct HabitCardRow: View {
    let habit: HabitTrackerItem
    let onLog: () -> Void

    var body: some View {
        HStack {
            VStack(alignment: .leading, spacing: 4) {
                Text(habit.name)
                    .font(.headline)
                Text("\(habit.currentCompletions) of \(habit.targetCountPerWeek) this week")
                    .font(.caption)
                    .foregroundStyle(.secondary)
            }
            Spacer()
            Button(action: onLog) {
                Image(systemName: "plus.circle.fill")
                    .font(.title2)
                    .foregroundStyle(.blue)
            }
            .buttonStyle(.plain)
        }
        .padding(.vertical, 4)
    }
}

// MARK: - 4. Create Habit Sheet
struct CreateHabitSheet: View {
    @Environment(\.dismiss) private var dismiss
    @Environment(\.modelContext) private var modelContext

    @State private var name = ""
    @State private var category = "Health"
    @State private var targetCount = 5

    let categories = ["Health", "Productivity", "Mindfulness", "Fitness"]

    var body: some View {
        NavigationStack {
            Form {
                Section("Habit Details") {
                    TextField("Name", text: $name)
                    Picker("Category", selection: $category) {
                        ForEach(categories, id: \.self) { cat in
                            Text(cat).tag(cat)
                        }
                    }
                }

                Section("Weekly Target") {
                    Stepper("\(targetCount) times per week", value: $targetCount, in: 1...14)
                }
            }
            .navigationTitle("New Habit")
            .navigationBarTitleDisplayMode(.inline)
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Cancel") { dismiss() }
                }
                ToolbarItem(placement: .confirmationAction) {
                    Button("Save") {
                        let newHabit = HabitTrackerItem(
                            name: name,
                            category: category,
                            targetCountPerWeek: targetCount
                        )
                        modelContext.insert(newHabit)
                        dismiss()
                    }
                    .disabled(name.trimmingCharacters(in: .whitespaces).isEmpty)
                }
            }
        }
    }
}
```
