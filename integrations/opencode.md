# OpenCode Integration Guide

This guide details how to install and invoke the `apple-native-engineer` skill in **OpenCode** and other emerging open-source agent environments supporting the Agent Skills standard (`agentskills.io`).

---

## 1. Discovery Paths

OpenCode parses the canonical `.agents/skills/` hierarchy:

| Scope | Location |
| :--- | :--- |
| **Workspace** | `.agents/skills/apple-native-engineer/SKILL.md` |
| **Global User** | `~/.config/opencode/skills/apple-native-engineer/SKILL.md` |

---

## 2. Installation Instructions

```bash
# Add to workspace
mkdir -p .agents/skills
ln -s ~/Desktop/apple-native-engineer .agents/skills/apple-native-engineer

# Or install globally
mkdir -p ~/.config/opencode/skills
ln -s ~/Desktop/apple-native-engineer ~/.config/opencode/skills/apple-native-engineer
```

---

## 3. Invocation in OpenCode

OpenCode reads `SKILL.md` frontmatter metadata and description at boot. When a task requires iOS/macOS interface design, accessibility auditing, or SwiftUI refactoring, the skill is automatically injected into the agent context.
