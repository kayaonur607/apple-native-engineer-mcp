# Visual Design & Polish Review Checklist

Use this checklist to perform an aesthetic and craftsmanship review, evaluating visual hierarchy, spacing, materials, typography, and motion quality against Apple Design Award standards.

---

## 1. Visual Hierarchy & Typography
- [ ] **One Primary Action**: Each screen features at most one prominent call-to-action button (`.borderedProminent`).
- [ ] **Clear Typographic Scale**: The screen clearly distinguishes titles, section headers, primary copy, and secondary metadata without visual ambiguity.
- [ ] **Standard Font Families**: Typography utilizes SF Pro, New York, or SF Pro Rounded; custom branding fonts are used sparingly and scaled relative to standard styles.
- [ ] **Leading Alignment**: Content consistently aligns along a primary vertical guide (standard 16pt or 20pt leading margin).

---

## 2. Spacing & The 8pt System Grid
- [ ] **Mathematical Spacing Grid**: All margins, paddings, and spacings conform to an 8pt-based token system (4, 8, 12, 16, 20, 24, 32, 48pt).
- [ ] **No Arbitrary Magic Numbers**: Random paddings like `13.5pt` or `27pt` are eliminated.
- [ ] **Proportional Grouping**: Related elements (e.g. title and subtitle) have tighter spacing (4–8pt) than unrelated sections (24–32pt).

---

## 3. Materials, Glass & Elevation
- [ ] **Continuous Corner Curvature**: Every rounded rectangle, card, and modal specifies continuous curvature (`style: .continuous`) to avoid harsh circular junction points.
- [ ] **Authentic Apple Materials**: Translucency uses native SwiftUI materials (`.regularMaterial`, `.ultraThinMaterial`) rather than hardcoded semi-transparent color fills.
- [ ] **Specular Edge Highlights**: Elevated glass surfaces feature subtle hairline (0.5pt) light-gradient borders to simulate optical refraction.
- [ ] **Ambient Shadows**: Shadows are soft, multi-layered, and low-opacity (5%–15%), avoiding muddy black drop shadows.

---

## 4. Light Mode & Dark Mode Parity
- [ ] **Pure Black vs Dark Gray**: Backgrounds use semantic system grouped backgrounds (`Color(uiColor: .systemGroupedBackground)`), which adjust between pure white in Light and deep tones in Dark.
- [ ] **Vibrancy Preservation**: Secondary text uses `.foregroundStyle(.secondary)` to maintain readable contrast across both color schemes.
- [ ] **Asset Assets Dual-Tinted**: Custom icons or illustrations provide dedicated Light and Dark mode asset variants.

---

## 5. Motion & Micro-Interaction Polish (Kowalski Principles)
- [ ] **Physics Springs Over Linear**: Spatial animations use `.spring(.snappy)` or `.spring(.bouncy)` rather than robotic linear or easing curves.
- [ ] **No `scale(0)` Pops**: Appearing elements scale from `0.88`–`0.92` to `1.0` combined with opacity fade.
- [ ] **Interruptible State**: In-flight animations can be reversed or interrupted by user touch without visual snapping.
- [ ] **Micro-Haptics**: Critical interactions (toggle switches, bookmark clicks, successful submissions) trigger subtle sensory feedback (`.sensoryFeedback`).
- [ ] **SF Symbol Effects**: Icons take advantage of native symbol animations (`.symbolEffect(.bounce)` or `.symbolEffect(.pulse)`).
