# Animation & Micro-Interaction Examples

This document demonstrates production SwiftUI animations incorporating **Emil Kowalski's design engineering principles**: natural spring physics, no `scale(0)` pops, interruptibility, tactile haptics, and accessibility fallbacks.

---

## 1. Grounded Entry Card (Eliminating the `scale(0)` Pop)

```swift
import SwiftUI

struct GroundedCardDialog: View {
    @Binding var isPresented: Bool
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    
    var body: some View {
        ZStack {
            if isPresented {
                // Dimmed ambient backdrop
                Color.black.opacity(0.4)
                    .ignoresSafeArea()
                    .transition(.opacity)
                    .onTapGesture {
                        dismiss()
                    }
                
                // Grounded Dialog Surface
                VStack(spacing: 20) {
                    Image(systemName: "checkmark.seal.fill")
                        .font(.system(size: 48))
                        .foregroundStyle(.blue)
                        .symbolEffect(.bounce, value: isPresented)
                    
                    VStack(spacing: 6) {
                        Text("Update Installed")
                            .font(.title3)
                            .fontWeight(.bold)
                        Text("Your device is now running the latest native design system.")
                            .font(.subheadline)
                            .foregroundStyle(.secondary)
                            .multilineTextAlignment(.center)
                    }
                    
                    Button("Done") {
                        dismiss()
                    }
                    .buttonStyle(.borderedProminent)
                    .controlSize(.large)
                }
                .padding(24)
                .background(
                    RoundedRectangle(cornerRadius: 24, style: .continuous)
                        .fill(Color(uiColor: .secondarySystemGroupedBackground))
                        .shadow(color: .black.opacity(0.12), radius: 24, x: 0, y: 12)
                )
                .padding(32)
                // ✅ Kowalski Motion: Subtle scale from 0.92, never from 0.0
                .transition(
                    reduceMotion 
                    ? .opacity 
                    : .scale(scale: 0.92).combined(with: .opacity)
                )
            }
        }
        .animation(.spring(response: 0.34, dampingFraction: 0.8), value: isPresented)
    }
    
    private func dismiss() {
        withAnimation(.spring(response: 0.28, dampingFraction: 0.85)) {
            isPresented = false
        }
    }
}
```

---

## 2. Tactile Interactive Bookmark with SF Symbol Animation

```swift
import SwiftUI

struct TactileBookmarkButton: View {
    @State private var isBookmarked: Bool = false
    
    var body: some View {
        Button {
            withAnimation(.spring(.bouncy(duration: 0.32, extraBounce: 0.12))) {
                isBookmarked.toggle()
            }
        } label: {
            HStack(spacing: 8) {
                Image(systemName: isBookmarked ? "bookmark.fill" : "bookmark")
                    .symbolEffect(.bounce, value: isBookmarked)
                Text(isBookmarked ? "Saved" : "Save")
                    .fontWeight(.medium)
            }
            .font(.subheadline)
            .padding(.horizontal, 16)
            .padding(.vertical, 8)
            .background(
                Capsule(style: .continuous)
                    .fill(isBookmarked ? Color.accentColor.opacity(0.15) : Color.clear)
                    .overlay(
                        Capsule(style: .continuous)
                            .stroke(isBookmarked ? Color.accentColor : Color(uiColor: .separator), lineWidth: 1)
                    )
            )
            .foregroundStyle(isBookmarked ? Color.accentColor : .primary)
        }
        .buttonStyle(.plain)
        .sensoryFeedback(.impact(weight: .light, intensity: 0.75), trigger: isBookmarked)
    }
}
```

---

## 3. Fluid Interactive Expandable Card

```swift
import SwiftUI

struct ExpandableNoteCard: View {
    @State private var isExpanded: Bool = false
    @Environment(\.accessibilityReduceMotion) private var reduceMotion
    
    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack {
                Label("Design System Update", systemImage: "sparkles")
                    .font(.headline)
                    .foregroundStyle(.primary)
                Spacer()
                Image(systemName: "chevron.right")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .rotationEffect(.degrees(isExpanded ? 90 : 0))
            }
            
            if isExpanded {
                Text("Version 2.0 introduces full support for iOS 18 floating tab bars, continuous squircle geometry, and fluid Kowalski physics springs.")
                    .font(.subheadline)
                    .foregroundStyle(.secondary)
                    .transition(reduceMotion ? .opacity : .move(edge: .top).combined(with: .opacity))
            }
        }
        .padding(16)
        .background(
            Color(uiColor: .secondarySystemGroupedBackground),
            in: RoundedRectangle(cornerRadius: 16, style: .continuous)
        )
        .contentShape(Rectangle())
        .onTapGesture {
            withAnimation(.spring(response: 0.36, dampingFraction: 0.82)) {
                isExpanded.toggle()
            }
        }
        .sensoryFeedback(.selection, trigger: isExpanded)
    }
}
```
