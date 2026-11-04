# Adaptive & Responsive Layout Examples

This document demonstrates how to engineer native SwiftUI layouts that adapt gracefully across iPhone form factors, iPad multitasking split views, orientation shifts, and extreme Dynamic Type scales.

---

## 1. Adaptive Header with `ViewThatFits` and Dynamic Type

When text scales under Dynamic Type (AX1–AX5), a horizontal layout overflows. `ViewThatFits` evaluates candidate layouts in order and picks the first one that fits the available space without clipping.

```swift
import SwiftUI

struct AdaptiveStatWidget: View {
    let title: String
    let value: String
    let subtitle: String
    let trend: String
    
    var body: some View {
        ViewThatFits(in: .horizontal) {
            // Priority 1: Spacious Horizontal Layout (Default / iPhone Standard)
            HStack(alignment: .firstTextBaseline) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(title)
                        .font(.subheadline)
                        .foregroundStyle(.secondary)
                    Text(value)
                        .font(.title2)
                        .fontWeight(.bold)
                }
                
                Spacer()
                
                VStack(alignment: .trailing, spacing: 4) {
                    Text(trend)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(.green)
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }
            
            // Priority 2: Compact Vertical Reflow (Large Dynamic Type or Narrow Split View)
            VStack(alignment: .leading, spacing: 8) {
                Text(title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text(value)
                    .font(.title2)
                    .fontWeight(.bold)
                
                HStack {
                    Text(trend)
                        .font(.subheadline)
                        .fontWeight(.semibold)
                        .foregroundStyle(.green)
                    Text(subtitle)
                        .font(.caption)
                        .foregroundStyle(.tertiary)
                }
            }
        }
        .padding(16)
        .background(
            Color(uiColor: .secondarySystemGroupedBackground),
            in: RoundedRectangle(cornerRadius: 16, style: .continuous)
        )
    }
}
```

---

## 2. Size-Class Aware Dashboard Grid (iPhone vs. iPad)

This example automatically presents a single-column stacked card feed in compact width (iPhone), but expands into a multi-column adaptive dashboard in regular width (iPadOS / macOS):

```swift
import SwiftUI

struct DashboardCardItem: Identifiable {
    let id = UUID()
    let title: String
    let icon: String
    let count: Int
}

struct AdaptiveDashboardView: View {
    @Environment(\.horizontalSizeClass) private var horizontalSizeClass
    
    let items = [
        DashboardCardItem(title: "Active Projects", icon: "folder.fill", count: 12),
        DashboardCardItem(title: "Pending Invoices", icon: "doc.plaintext.fill", count: 4),
        DashboardCardItem(title: "Team Members", icon: "person.2.fill", count: 28),
        DashboardCardItem(title: "Completed Tasks", icon: "checkmark.circle.fill", count: 142)
    ]
    
    var body: some View {
        ScrollView {
            if horizontalSizeClass == .regular {
                // iPad / Mac: Adaptive Multi-Column Grid
                LazyVGrid(columns: [GridItem(.adaptive(minimum: 240, maximum: 360), spacing: 16)], spacing: 16) {
                    ForEach(items) { item in
                        MetricCard(item: item)
                    }
                }
                .padding(20)
            } else {
                // iPhone: Clean Single-Column Stack
                LazyVStack(spacing: 12) {
                    ForEach(items) { item in
                        MetricCard(item: item)
                    }
                }
                .padding(.horizontal, 16)
                .padding(.vertical, 12)
            }
        }
        .background(Color(uiColor: .systemGroupedBackground))
        .navigationTitle("Overview")
    }
}

struct MetricCard: View {
    let item: DashboardCardItem
    
    var body: some View {
        HStack(spacing: 16) {
            Image(systemName: item.icon)
                .font(.title2)
                .foregroundStyle(Color.accentColor)
                .frame(width: 44, height: 44)
                .background(Color.accentColor.opacity(0.12), in: Circle())
            
            VStack(alignment: .leading, spacing: 4) {
                Text(item.title)
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                Text("\(item.count)")
                    .font(.title2)
                    .fontWeight(.bold)
            }
            Spacer()
        }
        .padding(16)
        .background(
            Color(uiColor: .secondarySystemGroupedBackground),
            in: RoundedRectangle(cornerRadius: 16, style: .continuous)
        )
    }
}
```
