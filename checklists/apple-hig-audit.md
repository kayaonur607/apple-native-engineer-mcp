# Apple HIG Compliance & Systematic Audit Protocol

This document provides a systematic review protocol for auditing native Apple applications. When conducting an audit, evaluate the codebase across all audit dimensions, categorize findings by severity, and format the report using the standard template.

---

## 1. Severity Classification Framework

Every identified issue must be assigned one of the following five severity tiers:

| Severity | Definition | Action Required |
| :--- | :--- | :--- |
| **Critical** | Violation of App Store Review Guidelines, crash hazard, broken navigation, or total accessibility failure (e.g., tap target under 44pt, missing camera privacy string, non-MainActor UI mutations). | Must fix immediately before release. |
| **High** | Direct departure from Apple Human Interface Guidelines that severely degrades usability (e.g., hardcoded hex colors breaking Dark Mode, fixed frame heights breaking Dynamic Type, iPad app lacking multi-column layout). | Strong remediation required. |
| **Medium** | Inconsistent platform idiom or un-native interaction pattern (e.g., using sheets instead of popovers on iPad, non-continuous corner radii, non-standard back navigation). | Fix to achieve native look and feel. |
| **Low** | Minor visual polish or micro-interaction omission (e.g., missing `.sensoryFeedback`, lacking SF Symbol bounce effect, slightly uneven padding). | Recommended polish. |
| **Suggestion** | Architectural optimization or optional enhancement (e.g., migrating from `ObservableObject` to `@Observable`, adopting Swift Testing). | Future enhancement. |

---

## 2. The 10-Step Audit Workflow

1. **Hierarchy & Authority Check**: Identify whether issues violate Level 1 Requirements, Level 2 Recommendations, or Level 3 Conventions.
2. **Platform & Form Factor Verification**:
   - iPhone: Verify thumb reach, safe area insets, bottom sheets.
   - iPad: Verify `NavigationSplitView`, pointer hover effects, keyboard shortcuts.
   - Mac: Verify menu bar integration, settings window, unified toolbar.
3. **Accessibility Audit**:
   - Dynamic Type: Test text at `.accessibility3` and `.accessibility5`.
   - VoiceOver: Check `.accessibilityElement`, labels, hints, and traits.
   - Contrast: Ensure minimum 4.5:1 ratio for body text, 3:1 for large text.
   - Touch Targets: Verify all interactive elements meet 44×44pt minimum.
4. **Appearance & Themes**:
   - Test in Light Mode, Dark Mode, High Contrast Mode, and Reduce Transparency.
   - Check for hardcoded color literals (`Color.white`, `Color(hex:)`).
5. **Component Authenticity**:
   - Confirm use of native SwiftUI components (`List`, `Form`, `ContentUnavailableView`, `Menu`).
   - Flag web-like custom recreation of native controls.
6. **Navigation Integrity**:
   - Check for nested `NavigationStack` bugs.
   - Verify modal dismissability and state preservation.
7. **Motion & Interaction Polish**:
   - Audit animation curves: replace linear easing with `.spring()`.
   - Eliminate `scale(0)` pops.
   - Verify `@Environment(\.accessibilityReduceMotion)` compliance.
8. **Materials & Depth**:
   - Verify proper use of `.regularMaterial`, continuous corner squircles, and subtle ambient shadows.
9. **SwiftUI Code Quality & Concurrency**:
   - Ensure all view models and UI mutations are isolated to `@MainActor`.
   - Audit view body complexity and unnecessary state invalidation cascades.
10. **Report Synthesis**: Generate structured report with Before vs. After code snippets.

---

## 3. Standard Audit Report Template

```markdown
# Apple HIG Compliance Audit Report

**Application / Target**: [Target Name]
**Evaluator**: Apple Native Engineer Agent
**Date**: [Date]
**Overall HIG Compliance Score**: [e.g., 88/100]

---

## Executive Summary
[Concise 2-3 paragraph summary of architectural strengths, native feel, and primary areas of concern.]

---

## Findings Summary
- 🔴 Critical Issues: [Count]
- 🟠 High Priority: [Count]
- 🟡 Medium Priority: [Count]
- 🟢 Low Priority: [Count]
- 💡 Suggestions: [Count]

---

## Detailed Findings

### [CRITICAL | HIGH | MEDIUM | LOW | SUGGESTION] #1: [Issue Title]
- **Category**: [Accessibility | Navigation | Typography | Motion | Layout]
- **Authority**: [Official Requirement | Official Recommendation | Platform Convention | Community Best Practice | Design Engineering]
- **Apple Guidance Reference**: [Link to Apple HIG or API docs]
- **Finding Description**: [Detailed explanation of what was found in code]
- **User Impact**: [How this affects real-world users on Apple devices]
- **Remediation**:
\`\`\`swift
// ❌ Current Implementation
...

// ✅ Recommended Apple Native Fix
...
\`\`\`
```
