# `/apple-native-design` — Native UI/UX Polish & HIG Audit

Audits and refactors user interfaces according to Apple's Human Interface Guidelines and Emil Kowalski motion principles.

---

## Agent Execution Steps

1. **Hierarchy & Spacing**:
   - Align all margins to the 8pt mathematical grid (`4`, `8`, `12`, `16`, `24`, `32`).
   - Eliminate arbitrary non-system paddings.

2. **Typography & Dynamic Type**:
   - Replace fixed font sizes with standard Dynamic Type styles (`.largeTitle`, `.title`, `.headline`, `.body`, `.caption`).
   - Replace fixed `.frame(height: N)` on text containers with `.frame(minHeight: 44)` and flexible padding.

3. **Color & Materials**:
   - Replace hardcoded hex colors with semantic colors (`Color(uiColor: .systemBackground)`, `.secondarySystemGroupedBackground`, `.tint`).
   - Implement authentic Apple Liquid Glass using `.regularMaterial` and continuous squircles (`style: .continuous`).

4. **Kowalski Motion**:
   - Replace linear transitions with physics springs (`.spring(.snappy)`).
   - Eliminate `scale(0)` pops; scale smoothly from `0.92` to `1.0` with opacity fade.
   - Pair interactive toggles with `.sensoryFeedback`.
