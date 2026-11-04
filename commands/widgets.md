# `/apple-native-widgets` — WidgetKit, Dynamic Island & Live Activities

Audits widget extensions, Live Activity lifecycle, Dynamic Island presentation and App Group data sharing.

---

## Agent Execution Steps

1. **Automated Audit**

   ```bash
   python3 tools/widget-validator/validate_widget.py . --json
   ```

2. **Dynamic Island completeness**

   Every Live Activity must declare all four presentation surfaces, or it degrades badly on iPhone:
   `compactLeading`, `compactTrailing`, `minimal`, and an expanded layout built from
   `DynamicIslandExpandedRegion(.leading/.trailing/.center/.bottom)`.

3. **Live Activity lifecycle**

   - `NSSupportsLiveActivities` must be `true` in the **app** target's `Info.plist`.
   - `Activity.request(...)` belongs in the app process, not the widget extension.
   - Capture `activity.pushToken` updates for server-driven state; otherwise the activity only updates while the
     app runs.
   - End activities explicitly (`await activity.end(nil, dismissalPolicy: .after(date))`) — stale activities are
     removed from the Lock Screen by the system and look like a crash to users.

4. **Widget configuration**

   - `supportedFamilies` must include Lock Screen accessories (`accessoryRectangular`, `accessoryCircular`,
     `accessoryInline`) if you want presence there.
   - Use `AppIntentConfiguration` (iOS 17+), not the deprecated `IntentConfiguration`.
   - Timelines must return a realistic `policy`; `.never` on a clock widget is a bug.

5. **Shared container**

   The widget and the app exchange data through an App Group
   (`UserDefaults(suiteName: "group.…")` or a shared `ModelContainer`). If you find no `group.` identifier, the
   widget is showing stale placeholder data.

6. **Interactive widgets (iOS 17+)**

   Buttons and toggles inside widgets run through App Intents (`Button(intent:)`), not SwiftUI actions. Verify the
   intent performs the work in a `perform()` that can complete within the widget's time budget.

## Report

Return the finding codes, the exact file and line, and a fixed code snippet for each. Never report "widgets look
fine" without quoting the tool verdict.
