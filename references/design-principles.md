# Design Principles & Authority Classification

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Agents erode trust by presenting taste as requirement. This document is the antidote: five authority levels, each
with a test you can apply to a line of Swift, and each with the language you should use when you report a finding.

The purpose is not classification for its own sake. It is so that a reviewer can say *"this is Level 5, my
preference, take it or leave it"* instead of *"Apple requires this"* when Apple does not.

---

## 1. The five levels

| Level | Name | Test | Enforcement |
| :--- | :--- | :--- | :--- |
| 1 | Apple requirement | Would this crash, fail review, or break a platform contract? | Reject |
| 2 | Apple recommendation | Is it stated on a HIG page? | Strongly recommend, explain exceptions |
| 3 | Platform convention | Would a long-time iOS user notice the difference? | Recommend unless branding justifies departure |
| 4 | Engineering best practice | Does it make the code testable, or the diff smaller? | Adapt to the existing codebase |
| 5 | Design engineering taste | Is the only argument "it feels better"? | Optional; say so |

If you cannot name the HIG page for a Level 2 claim, it is Level 5.

---

## 2. Level 1 — Apple requirement

Enforced by App Store Review, by a HIG minimum, or by the runtime.

- 44×44pt minimum hit target for anything tappable.
- Content must not sit under the Home indicator, the Dynamic Island or the status bar.
- Every UI mutation on `@MainActor`.
- `Info.plist` usage strings for every capability you call.
- App icon: 1024×1024, no alpha channel.
- A `PrivacyInfo.xcprivacy` with valid reason codes for every Required-Reason API.

```swift
// ❌ Level 1 failure: the button's hit area is 24×24pt
Button("Close", systemImage: "xmark") { dismiss() }
    .labelStyle(.iconOnly)
    .frame(width: 24, height: 24)

// ✅ Level 1: the glyph keeps its semantic size, the target reaches 44pt
Button("Close", systemImage: "xmark") { dismiss() }
    .labelStyle(.iconOnly)
    .font(.body)
    .frame(minWidth: 44, minHeight: 44)
    .contentShape(.rect)
```

`Button(_:systemImage:action:)` gives VoiceOver a label for free. An `Image(systemName:)` inside a `Button` does
not — that is `A11Y030`.

---

## 3. Level 2 — Apple recommendation

Stated on a HIG page. Quote the page, not the vibe.

- Navigation: `NavigationStack` / `NavigationSplitView`, typed `path`.
- Colour: semantic (`Color(uiColor: .systemBackground)`, `.primary`, `.secondary`) or an asset colour.
- Type: text styles, so Dynamic Type, Bold Text and the accessibility sizes are automatic.
- Containers: `List`, `Form`, `TabView`, `.searchable` — not reconstructions of them.
- Glass: `.glassEffect(_:in:)` on iOS 26+, one material below it.

```swift
// ❌ Level 2 failure: hex literals plus a fixed point size
Text("Account")
    .font(.system(size: 20, weight: .semibold))
    .foregroundStyle(Color(hex: "#1A1A1A"))
    .background(Color(hex: "#F5F5F7"))

// ✅ Level 2: the platform supplies size, weight and colour for both appearances
Text("Account")
    .font(.headline)
    .foregroundStyle(.primary)
    .background(.background)
```

Two linter codes cover the ❌: `SWU001` (hex literal) and `SWU012` (fixed point size).

**Level 2 includes exit ramps.** An iOS 26 API on an iOS 17 floor needs `if #available(iOS 26.0, macOS 26.0, *)`
*and* a fallback that is not a worse-looking copy. Missing the guard is `LG001`, an error.

---

## 4. Level 3 — Platform convention

Unwritten rules users have internalised. Breaking them makes an app feel foreign without failing any check.

| Convention | Why it matters |
| :--- | :--- |
| Edge-swipe pops the navigation stack | Users navigate without looking for a button |
| Pull-to-refresh on feeds, not on static forms | The gesture implies freshness the form cannot deliver |
| Search lives in the navigation bar | `.searchable` places it where the thumb and the eye expect it |
| Destructive actions use `role: .destructive` and sit last | Red plus position is the confirmation |
| Sheets dismiss downward; popovers dismiss by tapping out | Each has one dismissal gesture, and it is learned |

```swift
// ❌ Level 3 failure: a custom back button also kills the interactive pop gesture
.navigationBarBackButtonHidden(true)

// ✅ Level 3: keep the system back button; add your action beside it
.toolbar {
    ToolbarItem(placement: .topBarTrailing) {
        Button("Edit") { isEditing = true }
    }
}
```

If you hide the back button, you must re-implement the edge-swipe yourself or accept that the app feels broken to
anyone who has used an iPhone since 2013.

---

## 5. Level 4 — Engineering best practice

Validated across the Swift ecosystem rather than documented by Apple.

- `@Observable` over `ObservableObject`; per-property tracking instead of whole-view invalidation.
- Feature folders (`Feature/Detail/DetailView.swift`), not layer folders.
- Design tokens in a namespace (`Spacing.md`), so a spacing change is one edit.
- `List` for collections; `ForEach` over `Identifiable` values, never over `0..<count`.
- Swift Testing (`@Test`, `#expect`) for new tests.

```swift
// ✅ Level 4: one owner per piece of state, injected, testable
@Observable
final class BalanceModel {
    private(set) var balance: Decimal = 0
    private let service: BalanceService

    init(service: BalanceService) { self.service = service }

    func refresh() async throws {
        balance = try await service.currentBalance()
    }
}

struct BalanceView: View {
    @State private var model: BalanceModel

    init(service: BalanceService) {
        _model = State(initialValue: BalanceModel(service: service))
    }

    var body: some View {
        Text(model.balance, format: .currency(code: "USD"))
            .task { try? await model.refresh() }
    }
}
```

`.task` cancels with the view. `onAppear { Task { … } }` does not, and leaks work into the next screen.

---

## 6. Level 5 — Design engineering taste

The polish layer. Real, valuable, and optional. Say so when you recommend it.

| Recommendation | The argument |
| :--- | :--- |
| Springs over linear/ease curves | Real objects carry momentum; linear motion reads as mechanical |
| Enter from `0.92`–`0.95` scale plus opacity, never from `0` | Zero reads as a glitch, not an arrival (`SWU009`) |
| `.sensoryFeedback(.selection, trigger:)` on a snap | Confirms the state change without a visual |
| 2% press scale on a card | The surface acknowledges the touch before the action fires |
| `.contentTransition(.numericText())` on changing numbers | The digits travel; the eye keeps its place |

```swift
// ❌ Level 5 failure: pops from nothing, and the cost is a visible snap
.scaleEffect(isVisible ? 1 : 0)

// ✅ Level 5: a body arriving, with the same curve as system chrome
.scaleEffect(isVisible ? 1 : 0.94)
.opacity(isVisible ? 1 : 0)
.animation(.snappy(duration: 0.28), value: isVisible)
```

Every Level 5 item must survive Reduce Motion. If it does not, it is Level 1 broken.

---

## 7. Language for findings

| Level | Say | Do not say |
| :--- | :--- | :--- |
| 1 | "Required by HIG / App Review / runtime" | "Best practice" |
| 2 | "The HIG *{page name}* page recommends …" | "Apple requires …" |
| 3 | "iOS users expect …" | "Everyone does it this way" |
| 4 | "This makes the view testable" | "This is the correct architecture" |
| 5 | "Polish suggestion, optional" | "This is wrong" |

One finding per line, with `file:line`, the level, and the fix. Severity `critical` means rejection or crash —
not "I would have done it differently".

---

## 8. Decision procedure

1. Does it crash, fail review, or break a platform contract? → Level 1, fix it, no discussion.
2. Is it on a HIG page? → Level 2, cite the page.
3. Would a long-time user notice? → Level 3, recommend with the reason.
4. Does it affect testability or maintainability? → Level 4, adapt to the codebase.
5. None of the above → Level 5. Say "optional" and move on.

The failure mode this prevents: an agent rewrites a working design system to Level 5 taste and calls it a bug fix.

---

## 9. Sources

- Apple HIG, *Design principles* — <https://developer.apple.com/design/human-interface-guidelines/design-principles>
- Apple HIG, *Accessibility* — <https://developer.apple.com/design/human-interface-guidelines/accessibility>
- Apple HIG, *Layout* — <https://developer.apple.com/design/human-interface-guidelines/layout>
- Rule codes: `tools/swiftui-linter/lint_swiftui.py`, `tools/accessibility-auditor/audit_accessibility.py`
