import SwiftUI

@main
struct ProofApp: App {
    var body: some Scene {
        WindowGroup {
            NavigationStack {
                Form {
                    Section("Free and open source") {
                        Label("Apple Native Engineer", systemImage: "checkmark.seal")
                        Text("Local tools. Inspectable evidence.")
                            .foregroundStyle(.secondary)
                    }
                    Section("Native interface") {
                        Toggle("Enable reminders", isOn: .constant(true))
                        NavigationLink("Accessibility review") {
                            Text("Review on a real device with VoiceOver.")
                        }
                    }
                    Section("Evidence scope") {
                        Text("This is a controlled demonstration app, not a customer project.")
                    }
                }
                .navigationTitle("Native proof")
            }
        }
    }
}
