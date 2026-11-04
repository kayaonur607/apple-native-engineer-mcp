# Contributing to Apple Native Engineer

Thank you for your interest in contributing to `apple-native-engineer`! Our goal is to build and maintain the premier open-source, cross-agent Apple design engineering skill.

---

## 1. Ground Rules & Guiding Principles

1. **Official Apple Authority First**: Every rule, recommendation, or guideline added must be grounded in official Apple documentation, WWDC sessions, or proven engineering practice.
2. **Strict Authority Categorization**: Clearly classify all additions into the 5-tiered authority taxonomy (Requirement, Recommendation, Convention, Best Practice, Design Engineering).
3. **No Web-Slop**: Avoid generic web development habits (arbitrary hex colors, linear CSS-like animations, `scale(0)` pops, fixed frame heights on text).
4. **Original Content**: Do not copy copyrighted text or entire third-party repositories. Cite all research and external inspirations in `references/community-resources.md`.

---

## 2. Development & Validation Workflow

Before submitting a Pull Request, run the local validation suite:

```bash
# Run full repository validation
./scripts/validate-skill.sh

# Verify markdown links and references
./scripts/check-references.sh
```

All validation scripts must pass with zero errors.

---

## 3. Pull Request Guidelines

1. **Fork the Repository**: Create a topic branch from `main` (e.g. `feature/visionos-materials` or `fix/ipad-splitview`).
2. **Write Focused Changes**: Keep PRs focused on a single topic, component, or checklist.
3. **Include Examples**: If introducing a new component or guideline, provide both `// ❌ Anti-Pattern` and `// ✅ Correct Native Implementation` code snippets.
4. **Update Documentation**: Update `README.md`, `CHANGELOG.md`, or relevant reference files where appropriate.
5. **Open PR**: Submit your PR with a clear summary using the provided PR template.

---

## 4. Code Style & Swift Conventions

- Follow standard Swift API Design Guidelines.
- Target modern SwiftUI (iOS 17/18+, Swift 5.9/6).
- Use continuous squircle curvature for rounded corners (`RoundedRectangle(cornerRadius: ..., style: .continuous)`).
- Ensure all interactive controls adhere to the minimum 44×44pt touch target rule.
