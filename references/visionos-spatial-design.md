# visionOS Spatial Design & Engineering

> **Authority**: [Apple Human Interface Guidelines — visionOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-visionos), [WWDC23: Design for spatial user interfaces](https://developer.apple.com/videos/play/wwdc2023/10076/), [WWDC24: Design great visionOS apps](https://developer.apple.com/videos/play/wwdc2024/10151/)  
> **Status**: Official Apple Recommendations & Specifications

visionOS introduces spatial computing where apps exist in a shared infinite canvas alongside physical surroundings. Designing for visionOS requires understanding spatial depth, gaze-and-pinch input, dynamic lighting, and window management.

---

## 1. Core Spatial Paradigms

visionOS applications utilize three core visual containers:

| Container | Purpose | Dimension | Presentation |
| :--- | :--- | :--- | :--- |
| **Windows** | Primary 2D content, documents, lists, settings | Planar with depth ornaments | Placed in Shared Space |
| **Volumes** | 3D volumetric assets, models, charts, board games | Bounded 3D bounding box | Placed in Shared Space |
| **Immersive Spaces** | Full immersion, 360° environments, games | Unbounded 3D world | Replaces Shared Space (Exclusive) |

### Immersion Styles

```swift
@main
struct SpatialApp: App {
    @State private var immersionStyle: ImmersionStyle = .mixed

    var body: some Scene {
        WindowGroup {
            ContentView()
        }

        ImmersiveSpace(id: "SolarSystemSpace") {
            SolarSystemImmersiveView()
        }
        .immersionStyle(selection: $immersionStyle, in: .mixed, .progressive, .full)
    }
}
```

- **`.mixed`**: Virtual objects blend directly into the user's real room (passthrough enabled).
- **`.progressive`**: The digital environment partially surrounds the user, controlled smoothly by the Digital Crown.
- **`.full`**: The real world is completely occluded, placing the user entirely inside the virtual world.

---

## 2. Gaze and Pinch Interaction Model

In visionOS, the system tracks the user's eyes to highlight elements, while hands rest naturally on the lap or desk to perform gestures.

### Critical Privacy Rule
> [!IMPORTANT]
> **Eye Tracking Privacy**: Your app **never** receives direct eye-tracking data. You cannot detect where the user is looking until they actively perform a pinch or tap gesture. All hover states are rendered by the system compositor outside app process memory.

### Touch Target Sizing

- **Minimum Hit Target**: 60pt × 60pt (system hover highlight extends at least 4pt around it).
- **Inner Content**: Can be 44pt or smaller, but the interaction region must be padded to 60pt.
- **Spacing Between Interactive Elements**: Minimum 16pt clearance to prevent accidental gaze-target ambiguity.

```swift
Button(action: handleAction) {
    Label("Inspect", systemImage: "magnifyingglass")
        .frame(minWidth: 44, minHeight: 44)
}
.buttonStyle(.bordered)
.frame(minWidth: 60, minHeight: 60) // Hit target padding
.hoverEffect() // Explicit system hover effect
```

---

## 3. Glass Material & Dynamic Lighting

Windows in visionOS do not use static solid backgrounds (like solid white or black). Instead, they use a dynamic translucent glass material that adapts to ambient room lighting, contrast, and objects behind the window.

```swift
// Standard visionOS window background
struct WindowRootView: View {
    var body: some View {
        NavigationSplitView {
            SidebarView()
        } detail: {
            DetailContentView()
        }
        // System handles window glass background automatically.
        // Do NOT add .background(Color.white) or .background(Color.black)
    }
}
```

### Contrast and Hierarchy
- Use secondary and tertiary materials (`.regularMaterial`, `.thickMaterial`) only for sub-panels or elevated floating sheets.
- Text must use semantic colors (`Color.primary`, `Color.secondary`) to maintain dynamic contrast against both bright sunny rooms and dark nighttime rooms.

---

## 4. Ornaments

Ornaments anchor controls and navigation bars outside or slightly in front of the main window frame, preserving window real estate.

```swift
struct SpatialMediaViewer: View {
    @State private var isPlaying = false

    var body: some View {
        Canvas3DView()
            .ornament(
                visibility: .visible,
                attachmentAnchor: .scene(.bottom),
                contentAlignment: .center
            ) {
                HStack(spacing: 16) {
                    Button(action: { isPlaying.toggle() }) {
                        Image(systemName: isPlaying ? "pause.fill" : "play.fill")
                    }
                    Button(action: rewind) {
                        Image(systemName: "gobackward.15")
                    }
                    Button(action: fastForward) {
                        Image(systemName: "goforward.15")
                    }
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .glassBackgroundEffect() // Native visionOS ornament glass
            }
    }
}
```

---

## 5. Spatial Audio

Sound in visionOS should originate from virtual objects in physical space, anchoring user attention.

```swift
import RealityKit
import AVFoundation

func attachSpatialAudio(to entity: Entity, audioResourceName: String) {
    guard let audioResource = try? AudioFileResource.load(
        named: audioResourceName,
        configuration: .init(shouldLoop: true)
    ) else { return }

    // Spatial sound will emit from the entity's 3D coordinates
    let audioPlaybackController = entity.playAudio(audioResource)
    entity.components.set(SpatialAudioComponent(gain: -6.0))
}
```

---

## 6. Ergonomics and Depth Budget

- **Placement Distance**: Position default windows 1.5 to 2.0 meters away from the user. Placing windows closer than 1 meter causes eye strain (vergence-accommodation conflict).
- **Z-Index Layering**: Keep depth subtle (10mm to 50mm offsets between elements). Never stack deep layers that force user focus shifts across large distances.
- **Motion Sickness Prevention**: Avoid moving the user's camera or coordinate system artificially. Let the user physically move their head and body.
