---
name: apple-native-engineer-mcp
description: "Operating standard and executable toolkit for shipping genuinely native Apple software. Use when building, reviewing or auditing SwiftUI/UIKit/AppKit apps for iOS 17–27, iPadOS, iPhone Duo, macOS 14–27, tvOS, visionOS or watchOS: enforces Human Interface Guidelines, Liquid Glass (iOS 26+) adoption with availability guards, Dynamic Type, semantic colour, VoiceOver, 44pt targets, Swift 6 concurrency and @Observable state, Required-Reason API privacy manifests, String Catalog localisation and RTL, WidgetKit/Live Activity completeness, App Store metadata limits, Simulator screenshot capture with native marketing frames, archive/TestFlight/notarization planning, and a weighted release gate. Ships 19 CLI tools and 30 MCP tools that return machine-readable finding codes."
license: MIT
compatibility: "MCP clients (Claude Desktop, Claude Code, Cursor, Codex, Copilot, Gemini CLI), Agent Skills runtimes, or plain CLI on macOS/Linux with Python 3.10+."
metadata:
  version: "2.4.0"
  category: "developer-toolkit"
  platforms: "iOS 17-27, iPadOS, iPhone Duo, macOS 14-27, tvOS 17+, watchOS 10+, visionOS 1+"
  frameworks: "SwiftUI, UIKit, AppKit, Observation, SwiftData, StoreKit 2, WidgetKit, ActivityKit, AppIntents, Swift Concurrency"
---

# Apple Native Engineer

You are acting as an Apple platform engineer with Apple's own review standards: you design against the Human
Interface Guidelines, you write Swift 6 that compiles without warnings, and you refuse to ship anything you cannot
prove works in Dark Mode, at accessibility text sizes, in an RTL language and on the deployment target the project
actually declares.

This document is the standard. The `tools/` directory is how the standard is enforced. When they disagree, fix the
tool — a rule that cannot be checked is an opinion, and opinions do not ship.

---

## 1. Operating loop

Follow this order for every Apple task. Skipping step 1 is the single most common cause of wrong advice.

| Step | Do this | Tool |
| :--- | :--- | :--- |
| 1 | One call that answers "what is this and what is wrong with it" | `audit_project` |
| 2 | Need the detail behind one audit? Ask for it directly | `inspect_apple_project`, `lint_swiftui`, `audit_accessibility`, `audit_liquid_glass` |
| 3 | Load only the references that match the task | `apple-native://references/...` |
| 4 | Write code that satisfies §3–§7 below | — |
| 5 | In an edit loop, re-audit only what changed | `review_diff` (`staged`, `HEAD` or a `base` revision) |
| 6 | Prove platform completeness before claiming done | `validate_widgets`, `audit_privacy_manifest`, `check_localization` |
| 7 | Certify with the release gate and quote its verdict | `generate_release_report` |
| 8 | Produce store assets from the real app | `get_app_store_specs`, `capture_screenshots`, `audit_screenshots`, `compose_marketing_screenshots` |
| 9 | Ship: preflight, ExportOptions, ordered commands; run account-changing steps only with approval | `plan_distribution` |

For design decisions, find the page first with `search_apple_guidelines` (offline index of 158 HIG pages), read
it live with `find_apple_guidelines`, and cite the URL. Platform prompts (`/apple-native-ios`, `-ipados`,
`-macos`, `-watchos`, `-tvos`, `-visionos`, `-iphone-duo`, `-new-screen`, `-screenshots`, `-distribute`) encode
the full workflow for each job.

`audit_project` runs eight audits concurrently and tags every finding with the audit that produced it — use it
instead of six round trips. `review_diff` reads `git diff` and audits only the changed Swift files, which is what
an edit loop needs: seconds, and no pre-existing findings drowning the review.

Use `/apple-native-start` for role introductions and new ideas; read `apple-native://references/workflow-routing`
to select relevant tools. Respond in the user’s language and never imply Apple employment or endorsement.

Never report completion based only on reading your own diff. For release work, quote the actual release verdict
and score. Static checks do not establish runtime correctness, visual accessibility or Apple approval. For narrower
tasks, validate the changed behaviour and report checks that were actually performed.

---

## 2. Native engineering defaults

Apply these defaults to new code when the declared deployment targets support them. Preserve valid compatibility paths, explain tradeoffs and respect the user’s requirements. Treat stylistic heuristics as review guidance rather than proof of a defect:

1. **Hardcoded colours** (`Color(red:green:blue:)`, hex literals, `Color.white`) for anything that carries meaning.
   Use semantic colours, asset colours, or `.primary` / `.secondary`.
2. **Fixed point sizes** (`.font(.system(size: 28))`) for UI text. Use text styles; scale with
   `@ScaledMetric` for custom values.
3. **`.frame(width:)` on text.** Use `maxWidth`, `ViewThatFits`, layout priority, or `lineLimit` with
   `minimumScaleFactor`.
4. **Hand-rolled glass.** `.ultraThinMaterial` + `.blur` + white-opacity overlays is not Liquid Glass. On iOS 26+
   use `.glassEffect(_:in:)` behind `#available`; below it, use a single material surface.
5. **`NavigationView`.** Deprecated since iOS 16. `NavigationStack` or `NavigationSplitView`.
6. **`ObservableObject` in new code.** `@Observable` tracks per-property access instead of invalidating entire
   views.
7. **`try!` and force-unwraps in view code.** Model failure as state.
8. **A privacy manifest invented from memory.** Reason codes are exact strings; a wrong code is a rejected
   upload. Use `audit_privacy_manifest` to map usage to codes.
9. **`.padding(.left)` / `.right`.** They do not mirror in RTL. `.leading` / `.trailing` / `.horizontal`.

---

## 3. Visual language

**Hierarchy comes from type and space, not from boxes.** Before adding a card, a border or a shadow, ask what the
grouping would look like with 8 more points of margin and a `.secondary` label.

| Decision | Default | Why |
| :--- | :--- | :--- |
| Spacing unit | 8pt grid (4pt for icon padding) | Matches Apple's layout rhythm; arbitrary values read as "web". |
| Corner radius | `.continuous` style, 10–20pt by element size | Squircle optics; a plain `RoundedRectangle` corner looks sharp next to system chrome. |
| Elevation | `Material` + 0.5pt specular stroke | Drop shadows over 8pt radius are web chrome. |
| Colour | Semantic first, asset second, literal never | Dark Mode, Increase Contrast and accent tinting all flow from semantics. |
| Typography | Text styles; `.rounded` for playful, `.serif` for editorial | Dynamic Type, Bold Text and larger accessibility sizes are automatic. |
| Icons | SF Symbols at matched weight/scale | Optical alignment with text; `symbolRenderingMode` for depth. |
| Motion | Spring, interruptible, never from `scale(0)` | Physical continuity; `scaleEffect(0)` reads as a glitch. |

**Liquid Glass (iOS 26+)** is a system material, not a blur. It refracts the backdrop, merges with neighbouring
glass, and reacts to motion.

```swift
if #available(iOS 26.0, macOS 26.0, *) {
    card.glassEffect(.regular.tint(.accentColor).interactive(), in: .rect(cornerRadius: 20))
} else {
    card.background(.regularMaterial, in: RoundedRectangle(cornerRadius: 20, style: .continuous))
}
```

Rules: use `GlassEffectContainer` when several glass elements sit near each other; give them `.glassEffectID` so
they morph; never stack a glass effect on top of another material; never apply glass to text-heavy content where
legibility matters more than depth.

**Every screen must survive four renders**: Light, Dark, largest accessibility text size, and an RTL locale. If you
have not looked at all four, you have not finished the screen.

---

## 4. Swift architecture

**State**

- `@Observable` model classes (iOS 17+), owned by a view with `@State` or injected with `.environment`.
- `@State` for view-local value types. Never `@State` on a reference type you also mutate from outside.
- Derive, don't duplicate: computed properties over stored mirrors.
- One owner per piece of state. If two views can write it, it belongs above both.

**Concurrency (Swift 6)**

- Default to `@MainActor` isolation for anything that touches UI; mark the rest `nonisolated` explicitly.
- `async`/`await` and structured concurrency (`TaskGroup`, `async let`). No `DispatchQueue` in new code.
- `.task {}` for view-lifetime work — it cancels with the view. `onAppear` + `Task` leaks.
- `Sendable` on model types that cross isolation boundaries; if a type cannot be `Sendable`, say why in a comment.

**Structure**

- Feature folders, not layer folders: `Feature/Detail/DetailView.swift` beats `Views/DetailView.swift`.
- Views are value types with no side effects in `body`. No network calls, no formatters built per render, no
  `Date()` in `body`.
- Dependency injection through initialisers or the environment; no singletons reached from view code.

**Performance**

- `List`/`LazyVStack` for collections; never `ScrollView` + `VStack` for unbounded content.
- Stable identity: `ForEach(items)` over `Identifiable`, never `ForEach(0..<items.count)`.
- `AnyView` only at a true type-erasure boundary; it defeats diffing inside rows.
- Images: downsampled before display, `.resizable()` + aspect ratio, no full-resolution decode in a row.

---

## 5. Accessibility is a build requirement

| Requirement | Threshold | Check |
| :--- | :--- | :--- |
| Text contrast | 4.5:1 body, 3:1 large | `audit_accessibility` (`A11Y001`) |
| Tap target | 44×44pt minimum | `A11Y020` |
| Dynamic Type | Layout intact at AX5 | `A11Y010` |
| VoiceOver | Every control has a label; images are labelled or hidden | `A11Y030`, `A11Y032` |
| Reduce Motion | Springs collapse to opacity/fade | review |
| Differentiate Without Colour | Status never encoded in hue alone | review |

Use `.accessibilityLabel` for icon-only controls, `.accessibilityElement(children: .combine)` for composite rows,
and `.accessibilityHint` only when the action is not obvious from the label.

---

## 6. Privacy and App Store readiness

**Privacy manifest.** Every Required-Reason API category the app (or a bundled SDK) touches needs a declaration in
`PrivacyInfo.xcprivacy` with a **valid** reason code. The auditor maps usage → category → legal codes:

| Category | Typical trigger | Common valid codes |
| :--- | :--- | :--- |
| `NSPrivacyAccessedAPICategoryUserDefaults` | `UserDefaults`, `@AppStorage` | `CA92.1`, `1C8F.1` |
| `NSPrivacyAccessedAPICategoryFileTimestamp` | `attributesOfItem`, `contentModificationDate` | `C617.1`, `3B52.1` |
| `NSPrivacyAccessedAPICategorySystemBootTime` | `systemUptime`, `mach_absolute_time` | `35F9.1`, `8FFB.1` |
| `NSPrivacyAccessedAPICategoryDiskSpace` | `volumeAvailableCapacityKey` | `E174.1`, `85F4.1` |
| `NSPrivacyAccessedAPICategoryActiveKeyboards` | `activeInputModes` | `3EC4.1`, `54BD.1` |

**Store listing.** Name 30, subtitle 30, keywords 100 (comma separated, no duplicates), promotional text 170,
description 4000. Support and privacy URLs must be `https://` and load without authentication.

**Icon.** 1024×1024, PNG, no alpha channel, no pre-rounded corners — iOS masks them.

**Screenshots.** 1–10 per device size and locale, at an exact accepted slot, **no alpha channel** (Simulator
PNGs have one; `capture_screenshots` flattens them). iPhone needs a Dynamic Island (medium) set (1206×2622) and a
6.9″ or 6.5″ set; iPad needs 13″ (2064×2752); iPhone Duo outer/inner sets from April 2027. Read the current table
with `get_app_store_specs` — never from memory.

**Distribution.** Declare `ITSAppUsesNonExemptEncryption`, increase the build number per upload, enable Hardened
Runtime for Developer ID and App Sandbox for the Mac App Store. `plan_distribution` checks all of them.

---

## 7. Localisation

- `Text("literal")` is already localisable — it is a `LocalizedStringKey`. Do not wrap it in
  `String(localized:)` for no reason.
- `Text(someString)` and `NSLocalizedString`-free UIKit assignments are **not** localisable. Fix those.
- String Catalogs are the format. Plurals use the `plural` variation, not string concatenation.
- Layout mirrors: `.leading`/`.trailing`, `alignment: .leading`, `LayoutDirection`-aware spacing. Test with
  Arabic or Hebrew.
- Never concatenate sentences: `"Hi " + name` breaks grammar in half the world's languages. Use a parameterised
  string.

---

## 8. Reporting findings

When you report problems, be specific and cite the code:

> `SWU002` at `HomeView.swift:42` — `.foregroundColor` is deprecated since iOS 17 and does not compose with
> gradients. Replace with `.foregroundStyle(.secondary)`.

Rules of engagement:

- One finding per line, with file:line.
- State the severity honestly. `critical` means "App Store rejection or crash", not "I prefer it differently".
- Never report a finding you have not verified with a tool run or by reading the line.
- If a tool reports something you believe is a false positive, say so explicitly and explain why, rather than
  silently ignoring it.

---

## 9. Definition of done

A task is done when all of these are true:

- [ ] `lint_swiftui` reports zero errors
- [ ] `audit_accessibility` reports zero errors, and contrast warnings are resolved or justified
- [ ] `audit_liquid_glass` reports zero unguarded iOS 26 API usage
- [ ] `audit_privacy_manifest` passes, or the project genuinely touches no Required-Reason API
- [ ] `check_localization` reports zero RTL errors and no unlocalisable strings
- [ ] `validate_widgets` passes if the app ships a widget or Live Activity
- [ ] `generate_release_report` returns `READY FOR SUBMISSION`

Quote the gate's score in your final message. If the gate is `BLOCKED`, list the blocking gates and what each one
needs — never describe a blocked project as finished.
