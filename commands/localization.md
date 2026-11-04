# `/apple-native-localization` — String Catalogs, RTL & Formatting

Audits translatable strings, RTL layout mirroring, pluralisation and locale-aware formatting.

---

## Agent Execution Steps

1. **Automated Audit**

   ```bash
   python3 tools/localization-checker/check_localization.py . --json
   ```

2. **What is and is not a defect**

   | Pattern | Verdict |
   | :--- | :--- |
   | `Text("Settings")` | Fine — the literal is a `LocalizedStringKey` and is looked up automatically |
   | `Text(verbatim: "AES-256")` | Intentional bypass; acceptable only for non-translatable technical strings |
   | `Text(someString)` | Not localisable — wrap with `String(localized:)` at construction time |
   | `label.text = "Hello"` | Never localised — use `String(localized:)` |

3. **String Catalog hygiene**

   - `sourceLanguage` must match the development language declared in the project.
   - Missing translations surface as English fallbacks at runtime; flag them before release.
   - Plurals use the `plural` variation with `one`/`other` (and `few`/`many` for languages that need them).
   - Never concatenate sentences around a variable — use a parameterised string with a `%@`/`%lld` placeholder.

4. **RTL mirroring**

   Replace every directional constant:

   ```swift
   // Wrong: does not mirror
   .padding(.left, 8)
   .padding(.right, 8)
   // Right: mirrors with layout direction
   .padding(.leading, 8)
   .padding(.trailing, 8)
   ```

   Also check `UIRectEdge.left`, `textAlignment: .left`, `UIEdgeInsets(left:)`, and manual `frame` positioning
   that assumes origin at the leading edge. Symbols that encode direction (`arrow.forward`, `chevron.right`) should
   use the automatic-mirroring variants or `.imageScale` + `flipsForRightToLeftLayoutDirection`.

5. **Locale-aware formatting**

   Numbers, dates, currency, measurements and lists must go through `FormatStyle`:

   ```swift
   Text(value, format: .number.precision(.fractionLength(0...2)))
   Text(date, format: .dateTime.month(.wide).day())
   Text(price, format: .currency(code: locale.currency?.identifier ?? "USD"))
   ```

   `String(format: "%.2f")` is locale-blind and wrong in most of the world.

6. **Verification**

   Run the app in a pseudo-RTL language (Edit Scheme ▸ Run ▸ Options ▸ App Language ▸ Right-to-Left Pseudolanguage)
   and at the longest translation you ship. Layout that survives English-only will still break here.

## Report

Group findings by file, cite `L10N###` codes, and separate "must fix before release" from "nice to have".
