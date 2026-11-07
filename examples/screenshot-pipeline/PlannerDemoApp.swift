import SwiftUI

// A controlled demo app for the screenshot pipeline (capture_screenshots →
// audit_screenshots → compose_marketing_screenshots). It shows the two hooks a
// real app needs for automated App Store captures:
//
//   1. Locale comes from the launch arguments the capture tool passes
//      (-AppleLanguages / -AppleLocale), so String Catalog lookups, dates and
//      numbers are localized exactly as they will be for customers.
//   2. A `-screen <name>` launch argument routes straight to the screen being
//      captured, so no UI scripting is required.
//
// Strings are inline here to keep the example to one file; a production app
// uses a String Catalog (Localizable.xcstrings).

@main
struct PlannerDemoApp: App {
    var body: some Scene {
        WindowGroup {
            RootView(initial: Screen(argument: UserDefaults.standard.string(forKey: "screen")))
        }
    }
}

enum Screen: String, CaseIterable {
    case today, insights

    init(argument: String?) {
        self = argument.flatMap(Screen.init(rawValue:)) ?? .today
    }
}

struct Copy {
    let today, insights, focus, done, upcoming, weekly, tasksDone: String

    static var current: Copy {
        Locale.current.language.languageCode?.identifier == "tr"
            ? Copy(today: "Bugün", insights: "Özet", focus: "Odak", done: "Tamamlandı",
                   upcoming: "Sıradakiler", weekly: "Bu hafta", tasksDone: "görev tamamlandı")
            : Copy(today: "Today", insights: "Insights", focus: "Focus", done: "Done",
                   upcoming: "Up next", weekly: "This week", tasksDone: "tasks done")
    }
}

struct RootView: View {
    @State var initial: Screen
    private let copy = Copy.current

    var body: some View {
        TabView(selection: $initial) {
            Tab(copy.today, systemImage: "sun.max", value: Screen.today) {
                NavigationStack { TodayView(copy: copy) }
            }
            Tab(copy.insights, systemImage: "chart.bar", value: Screen.insights) {
                NavigationStack { InsightsView(copy: copy) }
            }
        }
    }
}

struct TodayView: View {
    let copy: Copy
    private let tasks = [("Design review", true), ("Ship build 42", false), ("Plan sprint", false)]

    var body: some View {
        List {
            Section(copy.focus) {
                ForEach(tasks, id: \.0) { task in
                    Label {
                        Text(task.0)
                    } icon: {
                        Image(systemName: task.1 ? "checkmark.circle.fill" : "circle")
                            .foregroundStyle(task.1 ? Color.green : Color.secondary)
                    }
                    .accessibilityValue(task.1 ? copy.done : "")
                }
            }
            Section(copy.upcoming) {
                Text(Date.now.addingTimeInterval(86_400), format: .dateTime.weekday(.wide).day().month(.wide))
            }
        }
        .navigationTitle(copy.today)
    }
}

struct InsightsView: View {
    let copy: Copy

    var body: some View {
        List {
            Section(copy.weekly) {
                LabeledContent(copy.tasksDone) {
                    Text(27, format: .number)
                }
                Gauge(value: 0.72) {
                    Text(copy.focus)
                } currentValueLabel: {
                    Text(0.72, format: .percent)
                }
            }
        }
        .navigationTitle(copy.insights)
    }
}
