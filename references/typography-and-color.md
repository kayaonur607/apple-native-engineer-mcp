# Typography & Color Systems

Typography and color are the two most critical vectors of communication in Apple native software. Apple provides mathematically harmonized typographic scales and semantic color palettes designed to adapt automatically across screen densities, Dynamic Type sizes, Light and Dark Modes, and High Contrast accessibility settings.

---

## 1. System Typography

### A. The San Francisco & New York Font Families
- **SF Pro**: The default system typeface for iOS, iPadOS, macOS, and tvOS. Highly legible at small sizes, expressive at large sizes.
- **SF Pro Rounded**: Used in informal, friendly, or health/fitness contexts (e.g., Apple Fitness, Reminders icons).
- **New York**: Apple's companion serif typeface. Excellent for editorial, reading, book, or luxury brand contexts.
- **SF Mono**: Fixed-width font for code, technical parameters, or terminal output.
- **SF Compact**: Optimized for Apple Watch and visionOS UI elements where tight glyph spacing improves legibility.

### B. Standard Dynamic Type Scale (at Large / Default Setting)

| Text Style | Default Size (pt) | Default Weight | Leading (Line Height) | Primary Use Case |
| :--- | :--- | :--- | :--- | :--- |
| `.largeTitle` | 34pt | Regular | 41pt | Top-level screen headers in NavigationStack |
| `.title` | 28pt | Regular | 34pt | Primary section headings |
| `.title2` | 22pt | Regular | 28pt | Secondary section titles, card headers |
| `.title3` | 20pt | Regular | 25pt | Sub-card headings, modal titles |
| `.headline` | 17pt | Semibold | 22pt | List row titles, prominent emphasized text |
| `.body` | 17pt | Regular | 22pt | Primary reading copy, form input values |
| `.callout` | 16pt | Regular | 21pt | Standout tips, secondary callouts |
| `.subheadline`| 15pt | Regular | 20pt | Metadata, subtitles below headlines |
| `.footnote` | 13pt | Regular | 18pt | Disclaimers, timestamps, auxiliary labels |
| `.caption` | 12pt | Regular | 16pt | Image captions, secondary metadata |
| `.caption2` | 11pt | Regular | 13pt | Badge counts, tiny secondary badges |

### C. Dynamic Type Implementation Rules

1. **Always use standard styles or `.custom(..., relativeTo:)`**:
```swift
// ❌ WRONG: Hardcoded fixed font size that never scales when user changes text size
Text("Total Balance")
    .font(.system(size: 24))

// ✅ CORRECT: Standard semantic text style that scales automatically
Text("Total Balance")
    .font(.title2)

// ✅ CORRECT: Custom brand font scaled relative to a standard style
Text("Total Balance")
    .font(.custom("Avenir-Heavy", size: 24, relativeTo: .title2))
```

2. **Never constrain text containers with rigid heights**:
```swift
// ❌ WRONG: Fixed 44pt height will clip text when user enables Accessibility sizes (AX1-AX5)
HStack {
    Text("Confirm Transaction")
}
.frame(height: 44) // Clips and truncates at large Dynamic Type!

// ✅ CORRECT: Flexible minHeight with vertical padding
HStack {
    Text("Confirm Transaction")
}
.padding(.vertical, 12)
.frame(minHeight: 44) // Meets touch target minimum while allowing vertical growth
```

3. **Adapt layouts when Dynamic Type expands**:
```swift
// ✅ Automatically switches from horizontal to vertical layout when text grows large
@Environment(\.dynamicTypeSize) private var dynamicTypeSize

var body: some View {
    let layout = dynamicTypeSize.isAccessibilitySize 
        ? AnyLayout(VStackLayout(alignment: .leading, spacing: 8)) 
        : AnyLayout(HStackLayout(spacing: 12))
    
    layout {
        Image(systemName: "creditcard.fill")
        Text("Payment Details")
    }
}
```

---

## 2. Semantic Color System

Apple apps must never rely on hardcoded hex colors for structural UI elements. Colors must be defined semantically to guarantee immediate support for **Dark Mode**, **High Contrast**, and **Reduce Transparency**.

### A. Semantic System Backgrounds

| SwiftUI / UIKit Color | Recommended Use |
| :--- | :--- |
| `Color(uiColor: .systemBackground)` | Primary background for standard canvas views in plain style. (Pure white in Light, pure black in Dark). |
| `Color(uiColor: .secondarySystemBackground)` | Layered background on top of primary background (e.g. grouped content). |
| `Color(uiColor: .tertiarySystemBackground)` | Third-tier layered element background (e.g. cards inside grouped cards). |
| `Color(uiColor: .systemGroupedBackground)` | Background for grouped lists, settings screens, and structured forms. |
| `Color(uiColor: .secondarySystemGroupedBackground)` | Background for cells, rows, and cards inside grouped lists. |
| `Color(uiColor: .tertiarySystemGroupedBackground)` | Background for controls or nested elements inside grouped cells. |

### B. Hierarchical Foreground Styles

Modern SwiftUI (iOS 15+) uses `.foregroundStyle()` with hierarchical levels that automatically calculate appropriate contrast and vibrancy:

```swift
VStack(alignment: .leading, spacing: 4) {
    Text("John Appleseed")
        .font(.headline)
        .foregroundStyle(.primary)      // 100% opacity, highest contrast
    
    Text("Software Engineer")
        .font(.subheadline)
        .foregroundStyle(.secondary)    // ~60% opacity, secondary emphasis
    
    Text("Cupertino, CA • Active 5m ago")
        .font(.caption)
        .foregroundStyle(.tertiary)     // ~30% opacity, auxiliary metadata
}
```

### C. System Accent & Semantic Colors

Apple provides standard tint colors that automatically adjust values between Light and Dark mode for optimal perceptual balance:
- `Color.blue`
- `Color.purple`
- `Color.pink`
- `Color.red` (Destructive actions, critical alerts)
- `Color.orange` (Warnings, pending state)
- `Color.yellow` (Caution, rating stars)
- `Color.green` (Success, positive balances, active states)
- `Color.mint`
- `Color.teal`
- `Color.cyan`

```swift
// Apply tint across view hierarchy
ContentView()
    .tint(.indigo)
```

---

## 3. Contrast Ratios & Accessibility Compliance

### WCAG Standards Enforced by Apple
- **Body Text (< 18pt or < 14pt bold)**: Minimum **4.5:1** contrast ratio against its background.
- **Large Text (≥ 18pt or ≥ 14pt bold)**: Minimum **3:1** contrast ratio.
- **Interactive Controls & Icons**: Minimum **3:1** contrast against adjacent background.

### High Contrast Mode (`Increase Contrast`)
When users enable "Increase Contrast" in Settings → Accessibility → Display & Text Size:
- Dark colors become darker, light colors become lighter.
- Subdued borders become prominent.
- Subtle background tints are replaced by solid demarcations.

In SwiftUI, inspect `@Environment(\.colorSchemeContrast)`:
```swift
@Environment(\.colorSchemeContrast) private var contrast

var body: some View {
    RoundedRectangle(cornerRadius: 12)
        .fill(Color(uiColor: .secondarySystemGroupedBackground))
        .overlay(
            RoundedRectangle(cornerRadius: 12)
                .stroke(contrast == .increased ? Color.primary : Color.clear, lineWidth: 1)
        )
}
```
