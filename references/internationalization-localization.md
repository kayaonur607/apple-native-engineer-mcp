# Internationalization & Localization

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Human Interface Guidelines — Localization](https://developer.apple.com/design/human-interface-guidelines/localization), [Apple Developer Documentation — Localization](https://developer.apple.com/documentation/xcode/localization), [WWDC23: Discover String Catalogs](https://developer.apple.com/videos/play/wwdc2023/10155/)

Localization is decided when you write the string, not when you translate it. A SwiftUI literal is a lookup
key; a `String` is already resolved text. Get that distinction wrong and no amount of translation fixes it.

---

## 1. Literal or value

| You write | Type received | Looked up in the catalog |
| :--- | :--- | :--- |
| `Text("Welcome back")` | `LocalizedStringKey` | ✅ |
| `Label("Settings", systemImage: "gear")` | `LocalizedStringKey` | ✅ |
| `Text(verbatim: "v2.4.1")` | `String` | ❌ by design |
| `Text(greeting)` | `String` overload | ❌ — `L10N003` |
| `String(localized: "Welcome back")` | `String` | ✅ resolved immediately |
| `LocalizedStringResource("Welcome back")` | deferred resource | ✅ resolved at display |

```swift
import SwiftUI

struct Greeting: View {
    let name: String

    var body: some View {
        VStack {
            // Literal key: translated.
            Text("Welcome back")
            // Interpolation stays a LocalizedStringKey, so the catalog sees "%@" .
            Text("Hello, \(name)")
            // Already a String: wrap it if it is user-facing copy.
            Text(String(localized: "Your trial ends soon."))
            // Version strings must not be translated.
            Text(verbatim: "v2.4.1")
        }
    }
}
```

`NSLocalizedString` and `String(localized:)` are equivalent at runtime. `LocalizedStringResource` is the one
to store in metadata — `AppIntent.title`, widget display names, `AppShortcut` copy — because the system
resolves it in the right locale and bundle later.

---

## 2. String Catalog shape

A `Localizable.xcstrings` file is JSON. The key is the source string unless you set an explicit key.

```json
{
  "sourceLanguage": "en",
  "version": "1.0",
  "strings": {
    "Welcome back": {
      "extractionState": "extracted_with_value",
      "localizations": {
        "en": { "stringUnit": { "state": "translated", "value": "Welcome back" } },
        "de": { "stringUnit": { "state": "translated", "value": "Willkommen zurück" } },
        "ar": { "stringUnit": { "state": "translated", "value": "مرحبًا بعودتك" } }
      }
    }
  }
}
```

`extractionState: "manual"` marks a key that does not appear literally in source. `state` is `translated`,
`new` or `needs_review`; a key left in `needs_review` is not finished — `L10N022` reports it. Xcode's build
setting **Generate String Catalog Symbols** (`STRING_CATALOG_GENERATE_SYMBOLS`) emits compile-time symbols for
catalog keys, which turns a typo in a key into a build error instead of a missing translation.

---

## 3. Plurals

Never assemble a count sentence from pieces. Give the catalog one key with plural variations:

```json
{
  "sourceLanguage": "en",
  "version": "1.0",
  "strings": {
    "%lld items": {
      "localizations": {
        "en": {
          "variations": {
            "plural": {
              "one": { "stringUnit": { "state": "translated", "value": "%lld item" } },
              "other": { "stringUnit": { "state": "translated", "value": "%lld items" } }
            }
          }
        },
        "ru": {
          "variations": {
            "plural": {
              "one": { "stringUnit": { "state": "translated", "value": "%lld предмет" } },
              "few": { "stringUnit": { "state": "translated", "value": "%lld предмета" } },
              "many": { "stringUnit": { "state": "translated", "value": "%lld предметов" } },
              "other": { "stringUnit": { "state": "translated", "value": "%lld предмета" } }
            }
          }
        }
      }
    }
  }
}
```

```swift
import SwiftUI

struct ItemCount: View {
    let count: Int

    var body: some View {
        // The key is "%lld items"; the catalog picks one/few/many/other.
        Text("\(count) items")
    }
}
```

Russian needs `one`, `few`, `many`, `other`; English needs `one` and `other`; Arabic adds `zero` and `two`.
Writing `"\(count) item" + (count == 1 ? "" : "s")` only ever works in English.

For grammatical agreement beyond number — gender, definiteness — use the inflection syntax:

```swift
import SwiftUI

struct LikeNotice: View {
    let name: String

    var body: some View {
        // The markup lets the catalog inflect the verb for the subject's gender.
        Text("^[\(name) liked your post](inflect: true)")
    }
}
```

---

## 4. Dates, numbers, currency, measurements

```swift
import SwiftUI

struct PriceRow: View {
    let price: Decimal
    let distance: Measurement<UnitLength>

    var body: some View {
        VStack(alignment: .leading) {
            Text(price, format: .currency(code: "USD"))
            Text(0.85, format: .percent)
            Text(distance, format: .measurement(width: .abbreviated, usage: .asProvided))
            Text(Date.now, format: .dateTime.day().month(.wide).year())
        }
    }
}
```

`FormatStyle` reads the current locale: `$49.99` becomes `49,99 $US` in France, `85%` becomes `%85` in
Turkey, and a distance stored in metres renders in miles for a US locale. `usage: .asProvided` keeps the
unit the value was created with; `usage: .person` would render a height the way a person states it.

Never use `DateFormatter` with a hardcoded `dateFormat`, and never concatenate a currency symbol.

---

## 5. Layout for text expansion

| Rule | Why |
| :--- | :--- |
| No fixed width on a label | German and Finnish run 30–40% longer than English |
| `lineLimit(nil)` or 2+ lines for body copy | One line truncates at large Dynamic Type in every language |
| `.fixedSize(horizontal: false, vertical: true)` on wrapping text | Lets the label take the height it needs inside a stack |
| Buttons size to their title | A fixed-width button clips the longest translation |
| Test with Double-Length Pseudolanguage | Xcode scheme option, no translation required |
| Test with an accessibility text size | Expansion plus AX5 is the real worst case |

Pseudolocalization is the cheapest test you will ever run: Scheme → Run → Options → App Language →
"Double-Length Pseudolanguage", then again with "Right-to-Left Pseudolanguage".

---

## 6. Right to left

```swift
import SwiftUI

struct SideRule: View {
    @Environment(\.layoutDirection) private var layoutDirection

    var body: some View {
        Rectangle()
            .frame(width: 2)
            .frame(maxWidth: .infinity, alignment: layoutDirection == .rightToLeft ? .trailing : .leading)
    }
}
```

- `.padding(.leading)` and `.padding(.trailing)` mirror; `.padding(.left)` and `.padding(.right)` do not —
  `L10N010` flags them.
- `HStack` reverses child order automatically in RTL. Do not reverse it yourself.
- Directional SF Symbols (`chevron.forward`, `arrow.right`) mirror automatically. Physical objects (a clock,
  a camera) must not; wrap one in `.flipsForRightToLeftLayoutDirection(false)` if it mirrors anyway.
- Images that contain text need an RTL-localized asset; the system cannot mirror baked-in pixels.
- Numbers, code and phone numbers stay left-to-right inside RTL text; `.environment(\.layoutDirection, .leftToRight)`
  on that one view is correct.

---

## 7. What the checker catches

`tools/localization-checker/check_localization.py` reports the defects that survive code review.

| Code | Severity | Trigger |
| :--- | :--- | :--- |
| `L10N001` | warn | `Text(verbatim:)` or another verbatim string bypasses the catalog |
| `L10N002` | warn | UIKit string assignment (`.text = "..."`, `.title = "..."`) is never localized |
| `L10N003` | info | `Text(someString)` receives a resolved `String` |
| `L10N010` | warn | RTL-hostile `.left` / `.right` padding or alignment |
| `L10N020` | error | String Catalog is not valid JSON |
| `L10N021` | warn | Catalog key has no translations |
| `L10N022` | info | Translation is marked `needs_review` |
| `L10N023` | info | No `.xcstrings` catalog found in the project |
| `L10N030` | info | No localization issues detected |

```bash
python3 tools/localization-checker/check_localization.py path/to/Project
```

---

## 8. Checklist

- [ ] Every user-facing literal goes through `Text("…")`, `String(localized:)` or `LocalizedStringResource`
- [ ] `Text(verbatim:)` only for user data, identifiers and version strings
- [ ] Counts use plural variations, not string concatenation
- [ ] Dates, prices and measurements use `FormatStyle`, never templates
- [ ] Layout survives Double-Length Pseudolanguage at an accessibility text size
- [ ] RTL pass run; no `.left` / `.right` padding remains
- [ ] Catalog has no `needs_review` entries at release
- [ ] Metadata (`AppIntent.title`, widget names) stores `LocalizedStringResource`, not `String`
