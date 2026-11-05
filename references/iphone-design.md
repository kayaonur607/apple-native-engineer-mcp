# iPhone Design & Ergonomics

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

The iPhone is held in one hand while the user is walking. The thumb reaches the bottom, the eye forgives
the top, and anything that breaks the app's physical edges — safe areas, the keyboard, the Dynamic
Island — breaks the app.

---

## 1. The thumb zone

Modern iPhones run from 5.4" to 6.9". On a Pro Max the top quarter is only reachable by shifting grip, so
the screen divides into three bands: secondary information on top, reading in the middle, actions at the
bottom.

| Band | Content | Reachable |
| :--- | :--- | :--- |
| Top 25% | Titles, counts, non-urgent detail | Only with a regrip |
| Middle 35% | Content, media, canvas | Either hand |
| Bottom 40% | Primary buttons, tab bar, sheets | Resting thumb |

| Pattern | API | Why it works |
| :--- | :--- | :--- |
| Floating primary action | `.safeAreaInset(edge: .bottom)` | Sits in the thumb zone, scrolls content behind it |
| Bottom toolbar | `ToolbarItem(placement: .bottomBar)` | System bar, correct margins and blur |
| Quick selection | `.presentationDetents([.medium])` | Half-height sheet, dismissable with one thumb |
| Persistent top control | `ToolbarItem(placement: .topBarPinnedTrailing)` (iOS 27) | Keeps one critical action visible |

The iOS 27 `.topBarPinnedTrailing` placement is for the single control that must survive scrolling and
toolbar collapse — not a second row of actions, and it needs an `if #available(iOS 27.0, *)` guard with a
`.topBarTrailing` fallback. Never disable the interactive pop gesture: the leading edge swipe is the only
back affordance that works one-handed.

---

## 2. Safe areas

Three different intents, three tools. Mixing them is what puts a button under the Home indicator.

| Intent | Tool | Example |
| :--- | :--- | :--- |
| Let decoration bleed to the edges | `.ignoresSafeArea()` **on the decoration only** | Background gradient, hero image, map |
| Add a persistent bar above the Home indicator | `.safeAreaInset(edge: .bottom) { }` | Checkout button, playback bar |
| Push content away from the notch and island | Do nothing — the safe area is already applied | Text, lists, controls |

```swift
// ❌ the button is now under the Home indicator and the scroll inset is gone
VStack {
    Spacer()
    Button("Confirm") { confirm() }
}
.ignoresSafeArea()

// ✅ decoration bleeds; content keeps its safe area
ZStack {
    LinearGradient(colors: [.accentColor.opacity(0.25), .clear],
                   startPoint: .top, endPoint: .bottom)
        .ignoresSafeArea()

    ScrollView {
        CheckoutSummary()
    }
    .safeAreaInset(edge: .bottom) {
        Button("Confirm") { confirm() }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
            .frame(maxWidth: .infinity)
            .padding(.horizontal)
    }
}
```

`.safeAreaInset(edge:)` inserts the bar **and** insets the scroll view by its height. Manual
`.padding(.bottom, 96)` does neither: it breaks at accessibility text sizes and double-pads on devices
with a home indicator. `.safeAreaPadding(_:)` is the other half of the pair — it pads *inside* the safe
area and composes with the system inset instead of replacing it. `.ignoresSafeArea(.keyboard)` is almost
always wrong: content that ignores the keyboard ends up underneath the keys.

---

## 3. Dynamic Island and Live Activities

The island is three shapes of one surface: **compact** (leading + trailing beside the sensor), **minimal**
(one glyph when another activity takes the other slot), and **expanded** (a pull-down card). All three
render in your widget extension, not in the app.

```swift
import ActivityKit
import SwiftUI
import WidgetKit

struct DeliveryAttributes: ActivityAttributes {
    struct ContentState: Codable, Hashable {
        var status: String
        var minutesRemaining: Int
    }
    var orderNumber: String
}

@main
struct DeliveryWidget: Widget {
    var body: some WidgetConfiguration {
        ActivityConfiguration(for: DeliveryAttributes.self) { context in
            DeliveryLockScreenView(context: context)
        } dynamicIsland: { context in
            DynamicIsland {
                DynamicIslandExpandedRegion(.leading) { Image(systemName: "bicycle") }
                DynamicIslandExpandedRegion(.trailing) {
                    Text("\(context.state.minutesRemaining) min")
                }
                DynamicIslandExpandedRegion(.bottom) { Text(context.state.status) }
            } compactLeading: {
                Image(systemName: "bicycle")
            } compactTrailing: {
                Text("\(context.state.minutesRemaining)m")
            } minimal: {
                Image(systemName: "bicycle")
            }
            .keylineTint(.accentColor)
        }
    }
}
```

- **The island is a status surface, not a notification.** It is for an activity already happening that
  ends on its own. News, ads, and reminders belong in Notification Centre.
- **The compact slots are two glyphs wide.** A sentence truncates to nothing; put the number trailing and
  the icon leading.
- **Design the Lock Screen first.** The same `ActivityConfiguration` renders there with more room than
  the island ever will. **Guard the request:** `Activity.request(attributes:content:pushType:)` is iOS
  16.1+, and `await activity.end(nil, dismissalPolicy: .default)` retires it when the event ends.

---

## 4. Context menus, swipe actions, or edit mode

| Need | Use | Why |
| :--- | :--- | :--- |
| Occasional action on one row | `.contextMenu` | No permanent chrome; long-press is discoverable |
| Frequent action on one row | `.swipeActions` | One gesture, and the affordance appears after the first swipe |
| Reorder, multi-select, or bulk delete | `EditButton` + `editMode` | The system supplies handles, selection circles, and Done |
| Irreversible action | `.confirmationDialog` | A menu item is too easy to hit by accident |

`EditButton` toggles the `editMode` environment value for its `List`; a custom toolbar must read the
same `@Environment(\.editMode)` value so the two never disagree. Context menus open by accident, so never
put a destructive action there without a `.confirmationDialog`.

---

## 5. Size classes, and the foldable question

The iOS 27.2 SDK exposes **no foldable, posture, or hinge API** — no `UIDevice` property, no SwiftUI
environment value. A folding iPhone therefore presents as ordinary size-class changes, including splits
that change while your view is on screen.

| Rule | Why |
| :--- | :--- |
| Read `\.horizontalSizeClass` and `\.verticalSizeClass`, never the device model | The same app ships to every case size and to iPad |
| Use `ViewThatFits(in:)` for layouts that must reflow | It picks a variant that fits instead of clipping one that does not |
| Avoid fixed `.frame(width:)` on text and cards | The container proposes a width; a fixed one breaks on split |
| Wrap full-screen stacks in a `ScrollView` | iPhone landscape is compact height, and a `Spacer` will clip |

---

## 6. Keyboard

The keyboard occupies 35–50% of the screen. Treat it as layout, not as an event.

1. `.scrollDismissesKeyboard(.interactively)` lets a downward drag dismiss the keyboard, matching the
   system's own scroll behaviour.
2. Numeric keypads have no Return key. Add a `.keyboard` toolbar item with "Done".
3. Set `.textContentType` on every field the system can autofill — it is the difference between one tap
   and typing an address. `.keyboardType(.numberPad)` picks the keypad; the toolbar item adds the exit.

---

## 7. The 44pt target

Every interactive control needs a 44×44pt hit region even when the glyph is 20pt. Grow the region with a
frame and `.contentShape`, not with a larger symbol.

```swift
Button {
    toggleFavorite()
} label: {
    Image(systemName: isFavorite ? "star.fill" : "star")
        .font(.title3)
        .foregroundStyle(isFavorite ? .yellow : .secondary)
        .frame(minWidth: 44, minHeight: 44)
        .contentShape(Rectangle())
}
.buttonStyle(.plain)
.accessibilityLabel(isFavorite ? "Remove from favourites" : "Add to favourites")
```

`.frame(minWidth:minHeight:)` beats a fixed 44×44 frame: at accessibility text sizes the glyph grows and
the target grows with it.

---

## 8. Review checklist

- [ ] Primary action reachable with a resting thumb
- [ ] Decoration ignores the safe area; interactive content never does
- [ ] Bottom bars use `.safeAreaInset(edge:)`, not manual padding
- [ ] Live Activity has a Lock Screen layout and a compact island layout, and ends itself
- [ ] Row actions use context menu, swipe actions, or edit mode — one, deliberately
- [ ] Layout survives compact height and both size classes
- [ ] Numeric fields have a keyboard "Done" button
- [ ] Every control is at least 44×44pt with a VoiceOver label

---

## 9. Official HIG references

- [Apple HIG — Layout](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG — Keyboards](https://developer.apple.com/design/human-interface-guidelines/keyboards)
- [Apple HIG — Live Activities](https://developer.apple.com/design/human-interface-guidelines/live-activities)
