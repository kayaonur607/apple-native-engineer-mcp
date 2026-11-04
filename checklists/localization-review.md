# Internationalization & Localization Review Checklist

Use this checklist to verify that an Apple-platform application is fully prepared for international distribution, Right-to-Left (RTL) reading directions, and multi-locale formatting.

---

## 1. String Management & String Catalogs
- [ ] **Zero Hardcoded Strings**: No visible user-facing strings are hardcoded without `String(localized:)`, `LocalizedStringKey`, or `Text()`.
- [ ] **String Catalog Migration**: All localizable assets are consolidated in `Localizable.xcstrings` (Xcode 15+ standard).
- [ ] **Translation Completeness**: String catalogs show 100% translated state with zero unreviewed or missing keys for target release languages.
- [ ] **Grammatical Inflection**: Counts and plurals use `^[count item](inflect: true)` or pluralized keys rather than naive string concatenation (`"\(count) items"`).

---

## 2. Right-to-Left (RTL) Mirroring (Arabic / Hebrew)
- [ ] **Directional Alignment**: Layouts use `.leading` and `.trailing` rather than `.left` and `.right`.
- [ ] **Navigation Flow**: Back and forward transitions reverse correctly in RTL mode.
- [ ] **SF Symbols Mirroring**: Progression icons (e.g., `chevron.forward`, `arrow.right`) mirror automatically, while physical icons remain unmirrored.
- [ ] **Text Alignment**: Paragraph text naturally aligns to the right side of the container in RTL environments.

---

## 3. Dynamic Type & Layout Expansion
- [ ] **Text Expansion Resilience**: Buttons, navigation titles, and cards accommodate at least 30% longer strings without awkward clipping or ellipsis (`...`).
- [ ] **No Fixed Widths on Text Containers**: Text views do not use rigid `.frame(width: 80)` constraints that clip translated words.
- [ ] **Dynamic Type AX Compatibility**: Translated text remains legible and avoids truncation even at accessibility font sizes (AX1–AX5).

---

## 4. Date, Number & Currency Formatting
- [ ] **Standard Formatters**: Dates and times use `FormatStyle` (e.g. `date.formatted(date: .abbreviated, time: .shortened)`) rather than hardcoded format strings (`"yyyy-MM-dd"`).
- [ ] **Currency Codes**: Prices are formatted using the user's current locale currency formatting (`.currency(code:)`).
- [ ] **Unit Conversions**: Metric vs Imperial units adapt to the user's regional measurement system via `MeasurementFormatter`.
