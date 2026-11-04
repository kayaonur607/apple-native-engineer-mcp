# Google Gemini CLI & Antigravity Integration Guide

This guide explains how to install and invoke the `apple-native-engineer` skill in the **Gemini CLI** and the **Google Antigravity** agent platform.

---

## 1. Skill Discovery Mechanism

Antigravity and Gemini CLI discover skills from two primary directories:

| Scope | Location |
| :--- | :--- |
| **Workspace-Level** | `.gemini/skills/apple-native-engineer/SKILL.md` |
| **User Global** | `~/.gemini/antigravity/skills/apple-native-engineer/SKILL.md` |

---

## 2. Installation Instructions

### Global Installation (Available across all workspaces)
```bash
# Create global skills directory if it does not exist
mkdir -p ~/.gemini/antigravity/skills

# Symlink or clone the skill
ln -s ~/Desktop/apple-native-engineer ~/.gemini/antigravity/skills/apple-native-engineer
```

### Workspace Installation
```bash
mkdir -p .gemini/skills
ln -s ~/Desktop/apple-native-engineer .gemini/skills/apple-native-engineer
```

---

## 3. Verification

Once linked, the skill is automatically indexed. When asking the agent about Apple HIG, SwiftUI architecture, or mobile UI reviews, the agent activates the skill instructions and references.

### Example Prompts:
```text
> Review this SwiftUI NavigationStack implementation for memory leaks and deep-link routing.

> Create a production-grade Liquid Glass card component in SwiftUI with continuous squircle corners.
```
