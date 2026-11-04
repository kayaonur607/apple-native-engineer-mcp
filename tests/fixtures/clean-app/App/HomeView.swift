import SwiftUI

/// Home screen of the reference app: native navigation, semantic styling,
/// Dynamic Type text, 44pt targets and a real accessibility label on every
/// control. This file is linted by the test suite and must stay clean.
struct HomeView: View {
    @Environment(AppModel.self) private var model
    @State private var isShowingSettings = false

    var body: some View {
        NavigationStack {
            List {
                Section {
                    ForEach(model.items) { item in
                        Label(item.title, systemImage: item.symbol)
                            .accessibilityHint(Text("Opens details"))
                    }
                } header: {
                    Text("Recent")
                } footer: {
                    Text("Synced with iCloud")
                        .foregroundStyle(.secondary)
                }
            }
            .navigationTitle(Text("Home"))
            .toolbar {
                ToolbarItem(placement: .primaryAction) {
                    Button {
                        isShowingSettings = true
                    } label: {
                        Label("Settings", systemImage: "gearshape")
                    }
                    .frame(minWidth: 44, minHeight: 44)
                }
            }
            .sheet(isPresented: $isShowingSettings) {
                SettingsView()
            }
        }
    }
}

/// Settings uses a real Form, native controls and the design tokens rather than
/// hardcoded values.
struct SettingsView: View {
    @Environment(AppModel.self) private var model

    var body: some View {
        NavigationStack {
            Form {
                Section {
                    Toggle("Background sync", isOn: Binding(
                        get: { model.syncEnabled },
                        set: { model.syncEnabled = $0 }
                    ))
                    Stepper(value: Binding(
                        get: { model.refreshInterval },
                        set: { model.refreshInterval = $0 }
                    ), in: 5...60, step: 5) {
                        Text("Refresh every \(model.refreshInterval) seconds")
                    }
                }
                Section {
                    Text("Liquid Glass is used only where the system provides it.")
                        .font(.callout)
                        .padding(DesignTokens.Spacing.md)
                        .background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
                }
            }
            .navigationTitle(Text("Settings"))
        }
    }
}

enum DesignTokens {
    enum Spacing {
        static let md: CGFloat = 16
    }
}

#Preview {
    HomeView()
        .environment(AppModel.preview)
}
