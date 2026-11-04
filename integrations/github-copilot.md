# GitHub Copilot Integration Guide

This guide details how to integrate the `apple-native-engineer` skill into **GitHub Copilot** in VS Code, Xcode, and JetBrains IDEs.

---

## 1. Copilot Custom Instructions (`.github/copilot-instructions.md`)

GitHub Copilot supports project-wide custom instructions defined in `.github/copilot-instructions.md`. When present, Copilot includes these instructions in every completion and chat turn.

### Setup Instructions:
Create or append to `.github/copilot-instructions.md` in your project repository:

```markdown
# Apple Native Engineering Guidelines
All Swift, SwiftUI, UIKit, and AppKit code in this repository must comply with Apple's official Human Interface Guidelines and the design engineering standards defined in the `apple-native-engineer` skill.

Key Mandates:
- Always enforce a minimum 44x44pt touch target on interactive controls.
- Use semantic colors (`Color(uiColor: .systemBackground)`, `.secondarySystemGroupedBackground`, `.tint`) and system materials (`.ultraThinMaterial`, `.regularMaterial`).
- Support Dynamic Type by using standard text styles (`.title`, `.headline`, `.body`) and flexible layouts with `minHeight`.
- Isolate all view models and UI mutations to `@MainActor`.
- Apply Emil Kowalski motion principles: use physics springs (`.spring(.snappy)`), avoid `scale(0)` pops, and respect `@Environment(\.accessibilityReduceMotion)`.
```

---

## 2. Invocation in Copilot Chat

In VS Code or Xcode, prompt GitHub Copilot Chat:

```text
@workspace Refer to apple-native-engineer and refactor this Form view to follow native iOS 18 design conventions.

@workspace Audit our iPad navigation architecture for multi-column split view and Stage Manager adaptability.
```
