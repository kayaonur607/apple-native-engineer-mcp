# visionOS Spatial Design & Engineering

> **Verified against** Xcode 27.2 · iOS 27.2 SDK · every API below exists in the installed SDK.
> **Deployment floor**: iOS 17 for code without an availability guard; iOS 26+ APIs are always guarded.

> **Authority**: [Apple Human Interface Guidelines — visionOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-visionos), [WWDC23: Design for spatial user interfaces](https://developer.apple.com/videos/play/wwdc2023/10076/), [WWDC24: Design great visionOS apps](https://developer.apple.com/videos/play/wwdc2024/10151/)

visionOS is the one platform where the window is not the interface. Content sits in the user's room, at a
distance they did not choose, lit by light you do not control. Design for comfort first, density second.

Every visionOS-only API in this guide (`immersionStyle`, `glassBackgroundEffect`) is absent from the iOS
interface, so a multiplatform target must isolate it in a visionOS-only file or behind `#if os(visionOS)`.

---

## 1. Three containers, three jobs

| Container | What it is | Declare with | Use for |
| :--- | :--- | :--- | :--- |
| **Window** | A flat plane with depth, in the shared space | `WindowGroup { }` | Documents, lists, settings, controls |
| **Volume** | A bounded 3D box, in the shared space | `WindowGroup { }.windowStyle(.volumetric)` | A single model, a board game, a chart |
| **Immersive space** | An unbounded world that can replace the room | `ImmersiveSpace(id:)` | 360° media, full environments, spatial games |

Only one immersive space is open at a time, and opening one is an explicit user decision — never a
launch default. Windows and volumes can coexist; an immersive space is entered and left.

---

## 2. Windows

A window is content plus chrome, floating at a comfortable distance. It sizes itself to its content
unless you say otherwise.

```swift visionOS
@main
struct OrbitApp: App {
    var body: some Scene {
        WindowGroup(id: "controls") {
            OrbitControls()
        }
        .defaultSize(width: 900, height: 620)
        .windowResizability(.contentSize)
    }
}
```

- `.defaultSize(width:height:)` is a hint, not a constraint — the user can resize, and the system may
  open smaller on later launches because it restores the last size.
- `.windowResizability(.contentSize)` pins the minimum to the content's ideal size, which stops a
  `NavigationSplitView` from collapsing into an unusable column in a narrow window.
- Do not paint an opaque background. The system supplies the glass; `.background(Color.white)` turns the
  window into a floating rectangle and destroys the depth cue.
- Use `.regularMaterial` or `.thickMaterial` only for panels *inside* the window. The window itself is
  already a material.

---

## 3. Volumes

A volume gives a 3D object its own bounded stage. It is the right container when the object *is* the
content, and it demands a declared size in meters — a volume without one opens at a default that may
exceed the user's field of view.

Keep the app's scene and the RealityKit content in separate files. `RealityKit` declares its own `Scene`
type, so importing it alongside the `App` declaration makes `some Scene` ambiguous — the error reads
`'Scene' is ambiguous for type lookup`, which is not obvious from the import list.

```swift visionOS
@main
struct GlobeApp: App {
    var body: some Scene {
        WindowGroup(id: "globe") {
            GlobeView()
        }
        .windowStyle(.volumetric)
        .defaultSize(width: 0.5, height: 0.5, depth: 0.5)
    }
}
```

```swift visionOS
import RealityKit

struct GlobeView: View {
    var body: some View {
        RealityView { content in
            if let globe = try? Entity.loadModel(named: "Globe") {
                content.add(globe)
            }
        }
    }
}
```

| Volume size | Reads as |
| :--- | :--- |
| 0.2 m | A handheld object — inspectable, intimate |
| 0.5 m | A tabletop object — the default for a single model |
| 1.0 m+ | An installation — needs a reason and a lot of empty space |

Content that spills past the volume's bounds is clipped, not scaled. Size the volume to the model, then
place the model at the origin.

---

## 4. Immersive spaces

An immersive space is a separate scene with its own content and its own immersion style. The style is
`any ImmersionStyle` state because the system, not the app, decides how much of the room remains.

```swift visionOS
@main
struct OrbitApp: App {
    @State private var immersionStyle: any ImmersionStyle = .mixed

    var body: some Scene {
        WindowGroup(id: "controls") {
            OrbitControls()
        }

        ImmersiveSpace(id: "orbit") {
            OrbitScene()
        }
        .immersionStyle(selection: $immersionStyle, in: .mixed, .progressive, .full)
    }
}
```

| Style | Room visible | Use for |
| :--- | :--- | :--- |
| `.mixed` | Yes, passthrough | Virtual objects placed around real furniture |
| `.progressive` | Partly, user-controlled via Digital Crown | A sky that grows as the user turns the crown |
| `.full` | No | 360° video, a complete environment |

Opening and closing are async actions on the environment, and the result tells you whether the user
agreed:

```swift visionOS
struct OrbitControls: View {
    @Environment(\.openImmersiveSpace) private var openImmersiveSpace
    @Environment(\.dismissImmersiveSpace) private var dismissImmersiveSpace
    @State private var isImmersed = false

    var body: some View {
        Button(isImmersed ? "Leave Orbit" : "Enter Orbit") {
            Task {
                if isImmersed {
                    await dismissImmersiveSpace()
                    isImmersed = false
                } else {
                    let result = await openImmersiveSpace(id: "orbit")
                    isImmersed = (result == .opened)
                }
            }
        }
    }
}
```

`OpenImmersiveSpaceAction.Result` is `.opened`, `.userCancelled`, or `.error`. Treat `.userCancelled` as a
normal outcome — the system asks for confirmation, and a no is a real answer.

---

## 5. Gaze, pinch, and hit targets

The system tracks the eyes; the app never sees where the user looks. Hover highlighting is drawn by the
system compositor, outside your process. What you control is the size of the target and what happens when
it is pinched.

- **60 × 60 pt minimum** for anything interactive. At arm's length a 44pt target is a guess, not a target.
- **16pt clearance** between neighbouring targets, or gaze ambiguity turns a pinch into a coin flip.
- **Hover is feedback, never information.** It does not exist for VoiceOver users and it is not a
  selection state you can read.

```swift visionOS
Button {
    inspect()
} label: {
    Label("Inspect", systemImage: "magnifyingglass")
        .frame(minWidth: 44, minHeight: 44)
}
.buttonStyle(.bordered)
.frame(minWidth: 60, minHeight: 60) // the actual hit target
.hoverEffect()
```

`.hoverEffect()` without arguments applies the system default (`.automatic`). Override it with
`.hoverEffect(.lift)` only when the content is a physical card or tile that should rise toward the user.

---

## 6. Ornaments

An ornament is chrome that floats outside the window's plane — the place for playback controls, filters,
and navigation that would otherwise eat the document's area.

```swift visionOS
struct PlaybackWindow: View {
    @State private var isPlaying = false

    var body: some View {
        FilmstripPlayer(isPlaying: isPlaying)
            .ornament(
                visibility: .visible,
                attachmentAnchor: .scene(.bottom),
                contentAlignment: .center
            ) {
                HStack(spacing: 24) {
                    Button("Rewind", systemImage: "gobackward.15") { rewind() }
                    Button(isPlaying ? "Pause" : "Play",
                           systemImage: isPlaying ? "pause.fill" : "play.fill") {
                        isPlaying.toggle()
                    }
                    Button("Forward", systemImage: "goforward.15") { fastForward() }
                }
                .padding(.horizontal, 24)
                .padding(.vertical, 12)
                .glassBackgroundEffect()
            }
    }
}
```

- `attachmentAnchor: .scene(.bottom)` hangs the ornament off the window's bottom edge, so it stays put
  when the window is resized. `.parent` anchors to the content view instead.
- `contentAlignment` is an `Alignment3D`: `.center` is the sane default, `.back` pushes the ornament
  behind the window plane.
- `.glassBackgroundEffect()` is what makes an ornament read as system chrome. Without it the controls
  float as flat text.
- Every control in an ornament still needs 60pt of target and a real label for VoiceOver.

---

## 7. Spatial audio

Sound should come from the object that makes it. A voice anchored to a character's mouth tells the user
where to look; a stereo track centred on the window does not.

```swift visionOS
import RealityKit

@MainActor
func attachSpatialAudio(named name: String, to entity: Entity) async throws {
    let resource = try await AudioFileResource(named: name, configuration: .init(shouldLoop: true))
    entity.components.set(SpatialAudioComponent(gain: -6, directLevel: -3))
    entity.playAudio(resource)
}
```

- `SpatialAudioComponent(gain:directLevel:)` takes decibels. `gain` is the source level, `directLevel` the
  dry path; both negative keeps an object audible without dominating the room.
- Load with the async `AudioFileResource(named:configuration:)` initializer. The old synchronous
  `load(named:in:configuration:)` is deprecated.
- Attach the component *before* `playAudio`, or the first moments of the sound play non-spatially.

---

## 8. Comfort and depth budget

Spatial interfaces cause discomfort through motion you did not intend. The camera belongs to the user.

| Source of discomfort | Rule |
| :--- | :--- |
| Moving content toward the user | Keep it still; let the user walk closer |
| Windows that follow the head | Anchor once, at a comfortable distance (about 1.5–2 m) |
| Large depth jumps | Keep related layers within 10–50 mm of each other |
| Rapid scale changes | Animate over 0.3 s or longer, or not at all |
| Wide-field self-motion | Never move the world; move an object inside it |
| Conflicting depth cues | Do not put a sharp near object over a far background in the same plane |

A comfortable scene has one obvious focal object, a background that stays behind it, and nothing that
moves unless the user moves it. If a camera animation would look impressive in a trailer, it is probably
uncomfortable in the headset.

---

## 9. Review checklist

- [ ] The default launch state is a window, not an immersive space
- [ ] Every interactive control has a 60 × 60 pt target and 16pt of clearance
- [ ] No information is conveyed by hover alone
- [ ] Windows use the system glass; no opaque `Color` fills on the root view
- [ ] Volumes declare a size in meters and content fits inside it
- [ ] Immersive spaces are entered explicitly and handle `.userCancelled`
- [ ] Ornaments use `.glassBackgroundEffect()` and stay inside the 60pt rule
- [ ] Spatial audio is attached before playback and mixed below the room
- [ ] Nothing moves the user's viewpoint without their input

---

## 10. Official HIG references

- [Apple HIG — Designing for visionOS](https://developer.apple.com/design/human-interface-guidelines/designing-for-visionos)
- [Apple HIG — Spatial layout](https://developer.apple.com/design/human-interface-guidelines/spatial-layout)
- [Apple HIG — Eyes](https://developer.apple.com/design/human-interface-guidelines/eyes)
- [Apple HIG — Ornaments](https://developer.apple.com/design/human-interface-guidelines/ornaments)
- [Apple HIG — Immersive experiences](https://developer.apple.com/design/human-interface-guidelines/immersive-experiences)
- [Apple HIG — Motion](https://developer.apple.com/design/human-interface-guidelines/motion)
