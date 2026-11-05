# Animation & Motion Engineering

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

Motion does three jobs: it shows where a view came from, it confirms that an action landed, and it holds the
frame steady while content changes. It has no fourth job. The HIG's *Motion* page opens with the same rule —
"Add motion purposefully, supporting the experience without overshadowing it."

For whether a motion suggestion is worth making, see [`design-principles.md`](design-principles.md) §6: motion
is Level 5 polish. For motion belonging to the glass material, see [`liquid-glass.md`](liquid-glass.md).

---

## 1. Springs

`Spring` is a value; `Animation.spring(_:)` turns it into an animation. The presets are fixed bounce values,
each with a `static var` (0.5s default) and a `static func (duration:extraBounce:)`:

| Preset | Bounce | Behaviour | Use for |
| :--- | :--- | :--- | :--- |
| `Spring.smooth` | `0.0` | Decelerates, never overshoots | Sheets, expansion, large surfaces |
| `Spring.snappy` | `0.15` | Fast, barely overshoots | Toggles, selection, small state changes |
| `Spring.bouncy` | `0.30` | Visible overshoot, quick settle | Confirmation: a save, a checkmark, a badge |

Each has a `static var` with a 0.5s default and a `static func (duration:extraBounce:)`:

```swift
withAnimation(.spring(.snappy)) { isOn.toggle() }
withAnimation(.spring(.bouncy(duration: 0.32, extraBounce: 0.05))) { celebrate() }
```

`bounce` is the only dial that matters: `0` is critically damped, `1` is a full elastic rebound, and the presets
sit at 0, 0.15 and 0.3. Past about 0.5, overshoot reads as a bug rather than as energy. For a gesture that ends
with velocity, use `.interpolatingSpring(_:initialVelocity:)` (§4); for opacity or colour alone, `.easeInOut`,
because a non-spatial property gains nothing from physics.

---

## 2. Scope the animation to one value

`.animation(_:)` without `value:` animates every change in the subtree, including layout you did not ask for. It
is deprecated in the SDK since iOS 15, and `SWU010` flags it.

```swift
.animation(.snappy)                    // ❌ also animates scrolling and text updates
.animation(.snappy, value: isExpanded) // ✅ only isExpanded animates
```

Use `withAnimation` inside an action; use `.animation(_:value:)` when the view always animates that property.
Both on the same property doubles the animation. To exempt one child, use
`.transaction { $0.disablesAnimations = true }`.

---

## 3. Never animate from zero

`SWU009` exists because scale-from-zero is the most common motion bug in generated code.

```swift
.scaleEffect(isVisible ? 1 : 0.94) // ✅ a body arriving
.opacity(isVisible ? 1 : 0)
.animation(.snappy(duration: 0.28), value: isVisible)
```

Start between `0.9` and `0.96`. The exception is a view anchored to a pointer, where `0` is not a starting size
but a real measurement — a magnifier lens. For insertion and removal, prefer `.transition(.blurReplace)`: the
blur hides the sub-pixel shimmer a pure fade leaves.

---

## 4. Gesture-driven motion

A drag that snaps back with a fixed spring ignores how fast the user was moving.
`interpolatingSpring(_:initialVelocity:)` carries that velocity into the animation:

```swift
@State private var settled: CGFloat = 0
@GestureState private var drag: CGFloat = 0

var body: some View {
    RoundedRectangle(cornerRadius: 20, style: .continuous)
        .offset(y: settled + drag)
        .gesture(DragGesture()
            .updating($drag) { value, state, _ in state = value.translation.height }
            .onEnded { value in
                let projected = value.predictedEndTranslation.height
                withAnimation(.interpolatingSpring(.snappy,
                                                  initialVelocity: value.velocity.height)) {
                    settled = projected > 140 ? 400 : 0
                }
            }
        )
}
```

`predictedEndTranslation` is where the finger was heading, not where it stopped, so threshold on it — a fast
flick that travels 40pt will otherwise fail to dismiss. `@GestureState` resets when the gesture ends, which is
what makes the hand-off to `settled` seamless.

---

## 5. Interruptibility and cost

An animation is interruptible when the animated value is state: change it mid-flight and the spring retargets
from the current position and velocity. Chaining motion through completion handlers defeats that, so
`withAnimation(_:completionCriteria:_:completion:)` is for work that must follow the animation — releasing a
captured frame, playing a sound — not for sequencing. The HIG is direct: "Let people cancel motion."

`scaleEffect`, `offset` and `opacity` resolve without re-running layout; `frame`, `padding` and stack spacing
re-measure the subtree every frame. A scaled view keeps its original frame, so hit testing and text wrapping do
not change — when the size change is real, animate the frame and pay for the layout.

---

## 6. Keyframes

Three or more steps is a state machine, and one written as nested `withAnimation` calls is unreadable.
`PhaseAnimator` cycles `Equatable` phases and takes `trigger:` to run once per change instead of looping. When
each property needs different timing, use `KeyframeAnimator`, the only place SwiftUI specifies timing per segment:

```swift
Image(systemName: "checkmark.seal.fill")
    .keyframeAnimator(initialValue: 1.0, trigger: presses) { view, scale in
        view.scaleEffect(scale)
    } keyframes: { _ in
        KeyframeTrack {
            SpringKeyframe(1.18, duration: 0.16, spring: .snappy)
            SpringKeyframe(1.00, duration: 0.30, spring: .bouncy)
        }
    }
```

A `KeyframeTrack` with no key path animates the root value itself, which is why it works on a bare `Double`.

---

## 7. Feedback: symbols and haptics

Do not hand-roll a bounce with `scaleEffect` on a symbol. The symbol carries per-layer geometry and the built-in
effect uses it. Discrete effects take `value:` and fire on change; indefinite effects take `isActive:` and run
while true — passing the wrong one is a compile error, not a silent no-op.

```swift
Image(systemName: starred ? "star.fill" : "star")
    .symbolEffect(.bounce, value: starred)                       // discrete
    .symbolEffect(.variableColor.iterative, isActive: isSyncing) // indefinite
```

`sensoryFeedback(_:trigger:)` covers the rest: `.selection` for a changed choice, `.impact(weight:intensity:)`
for a physical snap, `.success` / `.warning` / `.error` when an operation resolves. It needs no permission and is
a no-op where there is no Taptic Engine — iPad, Mac, the Simulator. One haptic per action: two on the same tap
reads as a buzz.

---

## 8. Reduce Motion

System components honour Reduce Motion automatically. Custom animations do not — nothing inside `withAnimation`
checks the setting, and no auditor in this repository catches it.

```swift
@Environment(\.accessibilityReduceMotion) private var reduceMotion
@State private var isOpen = false

var body: some View {
    PanelContent()
        .opacity(isOpen ? 1 : 0)
        .scaleEffect(reduceMotion ? 1 : (isOpen ? 1 : 0.94))
        .animation(reduceMotion ? nil : Animation.smooth, value: isOpen)
}
```

Geometry is removed rather than shortened, the information survives, and the fallback is a crossfade rather
than a cut. For app-wide suppression, `.transaction { $0.disablesAnimations = true }` stops implicit animations
too.

---

## 9. Navigation transitions

`matchedGeometryEffect` still works for a shape shared inside one hierarchy. For a push, mark the source with
`.matchedTransitionSource(id:in:)` and let the navigation stack own the geometry:

```swift
@ViewBuilder
var zoomedDetail: some View {
    if #available(iOS 18.0, *) {
        Detail(item: item)
            .navigationTransition(.zoom(sourceID: item.id, in: zoomNamespace))
    } else {
        Detail(item: item)
    }
}
```

`.zoom` is iOS 18+ and unavailable on macOS. iOS 27 adds `.navigationTransition(.crossFade)`, also
macOS-unavailable, for a destination with no source geometry; guard it with `if #available(iOS 27.0, *)`. A zoom
needs a visible source — if the row is already offscreen when the push happens, the system falls back to a slide.

---

## 10. Review checklist

| # | Check | Fail means |
| :--- | :--- | :--- |
| 1 | Every animation names a `value:` or sits inside `withAnimation` | `SWU010` — animating the whole subtree |
| 2 | No `scaleEffect(0)` | `SWU009` — arrives from nothing |
| 3 | A Reduce Motion path exists and preserves the information | Users who disable motion see a broken state |
| 4 | Gesture animations use the end velocity | Snapping back ignores the flick |
| 5 | One haptic per action | Buzz |
| 6 | Nothing waits on an animation to become interactive | HIG: "Let people cancel motion" |

---

## 11. Sources

- Apple HIG, *Motion* — <https://developer.apple.com/design/human-interface-guidelines/motion>
- Apple HIG, *Playing haptics* — <https://developer.apple.com/design/human-interface-guidelines/playing-haptics>
- `SwiftUICore` iOS 27.2 — `Spring`, `interpolatingSpring(_:initialVelocity:)`, `PhaseAnimator`,
  `KeyframeAnimator`, `KeyframeTrack`
- `SwiftUI` iOS 27.2 — `sensoryFeedback(_:trigger:)`, `matchedTransitionSource(id:in:)`,
  `NavigationTransition.zoom(sourceID:in:)`, `CrossFadeNavigationTransition`
- Rules `SWU009`, `SWU010` — `tools/swiftui-linter/lint_swiftui.py`
