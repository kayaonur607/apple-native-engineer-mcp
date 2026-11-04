# Internationalization & Localization (i18n / l10n)

> **Authority**: [Apple Human Interface Guidelines — Localization](https://developer.apple.com/design/human-interface-guidelines/localization), [Apple Developer Documentation — Localization](https://developer.apple.com/documentation/xcode/localization), [WWDC23: Discover String Catalogs](https://developer.apple.com/videos/play/wwdc2023/10155/)  
> **Status**: Official Apple Standards & Best Practices

Building an Apple-native app requires designing for a global audience from day one. This includes String Catalogs (`.xcstrings`), pluralization, dynamic date/number formatting, and Right-to-Left (RTL) layout mirroring.

---

## 1. String Catalogs (`.xcstrings`)

Xcode 15+ deprecates legacy `.strings` and `.stringsdict` files in favor of **String Catalogs** (`Localizable.xcstrings`).

### Key Benefits
- Automatically extracts strings defined in SwiftUI `Text("...")`, `Label("...", systemImage: "...")`, and `LocalizedStringResource`.
- Tracks translation progress (new, needs review, translated) directly in Xcode.
- Provides native handling for pluralization (zero, one, two, few, many, other) and device variants without complex dictionary plists.

```json
{
  "sourceLanguage": "en",
  "strings": {
    "welcome_message": {
      "extractionState": "manual",
      "localizations": {
        "en": {
          "stringUnit": {
            "state": "translated",
            "value": "Welcome back to your workspace"
          }
        },
        "de": {
          "stringUnit": {
            "state": "translated",
            "value": "Willkommen zurück in Ihrem Arbeitsbereich"
          }
        },
        "ar": {
          "stringUnit": {
            "state": "translated",
            "value": "مرحبًا بك مرة أخرى في مساحة عملك"
          }
        }
      }
    }
  },
  "version": "1.0"
}
```

---

## 2. Pluralization & Grammatical Inflection

Never assemble strings by manually appending count numbers (e.g. `\(count) files`). Different languages have complex plural rules (such as Russian having 3 distinct plural forms).

```swift
// In SwiftUI, use automatic inflection
Text("^[\(itemCount) item](inflect: true)")
// When itemCount = 1 -> "1 item"
// When itemCount = 4 -> "4 items"
// Automatically localized correctly across languages in String Catalogs
```

---

## 3. Right-to-Left (RTL) Layout Mirroring

Languages like Arabic and Hebrew read from right to left.

### SwiftUI Automatic Mirroring
SwiftUI layouts automatically mirror horizontally:
- `HStack` places the first child on the right in RTL.
- `leading` aligns to the right side in RTL.
- Navigation back button points right instead of left.

### Directional Rules to Watch Out For:
1. **Never use `.left` or `.right` padding**: Always use `.leading` and `.trailing`.
2. **Icons with Directional Meaning**:
   - Icons that represent progression or forward/back (e.g. `chevron.forward`, `arrow.right`) should use standard SF Symbols which mirror automatically in RTL environments.
   - Icons that represent physical objects (e.g., a clock face, a camera, a magnifying glass) should generally **not** mirror.

```swift
// ❌ WRONG: Hardcoded left/right breaks in Arabic
.padding(.left, 16)

// ✅ CORRECT: Automatically mirrors in RTL
.padding(.leading, 16)
```

---

## 4. Date, Time & Number Formatting

Never format dates or numbers with hardcoded template strings like `"dd/MM/yyyy"`. Use modern Swift `FormatStyle`:

```swift
// Formatted according to user's device locale
Text(Date.now, format: .dateTime.year().month().day())

// Currency formatting respects local currency symbol placement and decimals
Text(price, format: .currency(code: "USD"))
// In US: "$49.99"
// In France: "49,99 $US"

// Percentage
Text(0.85, format: .percent)
// In US: "85%"
// In Turkey: "%85"
```

---

## 5. Localization Audit Checklist

1. [ ] **No Hardcoded Strings**: All user-facing strings are wrapped in `String(localized:)` or `LocalizedStringKey`.
2. [ ] **Dynamic Layout Expansion**: Labels support 30% text expansion (German/Finnish text is often significantly longer than English).
3. [ ] **No Truncation with Large Dynamic Type**: Views adapt gracefully when large font size is combined with longer translations.
4. [ ] **RTL Pseudolocalization Verified**: Tested with Xcode Scheme > Run > Options > Application Language: "Right-to-Left Pseudolanguage".
