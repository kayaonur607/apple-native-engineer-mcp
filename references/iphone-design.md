# iPhone Design & Ergonomics

The iPhone is an intimate, handheld device primarily operated with one thumb while on the move. Designing for iPhone requires deep consideration of physical grip, screen reachability, safe areas, Dynamic Island hardware cutouts, and virtual software keyboard transitions.

---

## 1. The Thumb Zone & Ergonomics

Modern iPhones range in screen diagonal from 5.4 inches to 6.9 inches. On larger devices (Pro Max / Plus), users cannot reach the top 30% of the screen with a standard one-handed grip without shifting their hand.

```
┌─────────────────────────┐
│     HARD TO REACH       │  Secondary info, Navigation Title, Dismiss
│       (Top 25%)         │
├─────────────────────────┤
│     NATURAL REACH       │  Reading area, Primary viewing canvas
│       (Middle 35%)      │
├─────────────────────────┤
│      EASY REACH         │  Primary buttons, Tab Bar, Search trigger,
│     (Bottom 40%)        │  Bottom sheets, Gestural swipe actions
└─────────────────────────┘
```

### iPhone Ergonomic Rules
1. **Place Primary Action Buttons at the Bottom**: Floating bottom buttons or bottom toolbars are vastly superior to top-trailing navigation buttons for primary workflows.
2. **Support Interactive Pop Gesture**: Never disable the interactive edge-swipe gesture. Users expect to swipe from the left edge to dismiss detail views.
3. **Use Bottom Sheets for Complex Inputs**: Instead of forcing the user into a full-screen view for simple selections, present an interactive bottom sheet with `.presentationDetents([.medium, .large])`.

---

## 2. Safe Areas & Hardware Cutouts

Never draw critical text, buttons, or interactive controls outside the **Safe Area**. The safe area protects UI from:
- The **Dynamic Island** or Sensor Housing (Notch) at the top.
- The **Home Indicator bar** at the bottom.
- Rounded screen corners.

### Safe Area Best Practices in SwiftUI

```swift
// ❌ WRONG: Ignoring safe area on interactive buttons places them under the Home Indicator
VStack {
    Spacer()
    Button("Continue") { submit() }
}
.ignoresSafeArea() // Catastrophic: Unclickable or conflicts with Home swipe!

// ✅ CORRECT: Allow background to bleed into safe area, but keep interactive content safe
ZStack {
    Color(uiColor: .systemGroupedBackground)
        .ignoresSafeArea() // Background bleeds gracefully edge-to-edge
    
    VStack {
        // Content remains safe
        Text("Payment Summary")
            .font(.title2)
        Spacer()
        Button("Confirm") { submit() }
            .buttonStyle(.borderedProminent)
            .controlSize(.large)
    }
    .padding(.horizontal, 20)
    .padding(.bottom, 12) // Sits comfortably above Home Indicator
}
```

---

## 3. Keyboard Handling & Text Input

Virtual keyboards on iPhone occupy 35% to 50% of the screen height. 

### Best Practices:
1. **Automatic Scroll Dismissal**: Set `.scrollDismissesKeyboard(.interactively)` so dragging down dismisses the keyboard smoothly.
2. **Keyboard Toolbar Actions**: Always provide a "Done" or "Next" button in the `.keyboard` toolbar placement for numeric keypads which lack a return key.

```swift
ScrollView {
    VStack(spacing: 16) {
        TextField("Street Address", text: $address)
            .textContentType(.fullStreetAddress)
        
        TextField("ZIP Code", text: $zipCode)
            .keyboardType(.numberPad)
    }
    .padding()
}
.scrollDismissesKeyboard(.interactively)
.toolbar {
    ToolbarItemGroup(placement: .keyboard) {
        Spacer()
        Button("Done") {
            hideKeyboard()
        }
    }
}
```

---

## 4. Minimum Touch Target Standard (Level 1 Requirement)

Every interactive control must offer a minimum tappable area of **44×44 points**. If visual styling demands a smaller icon (e.g. a 20pt bookmark icon), extend the tappable bounds using padding and `.contentShape`:

```swift
Button {
    toggleFavorite()
} label: {
    Image(systemName: isFavorite ? "star.fill" : "star")
        .font(.system(size: 20))
        .foregroundStyle(isFavorite ? .yellow : .secondary)
        .frame(width: 44, height: 44) // Meets 44x44pt requirement
        .contentShape(Rectangle())    // Expands hit target to entire frame
}
```

---

## 5. Official HIG References
- [Apple HIG - Designing for iOS](https://developer.apple.com/design/human-interface-guidelines/layout)
- [Apple HIG - Inputs & Keyboards](https://developer.apple.com/design/human-interface-guidelines/keyboards)
- [Apple HIG - Touch Targets](https://developer.apple.com/design/human-interface-guidelines/buttons)
