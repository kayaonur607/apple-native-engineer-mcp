# OpenAI Codex Integration Guide

This guide explains how to install and invoke the `apple-native-engineer` skill in **OpenAI Codex** and agents adhering to the **Agent Skills standard** (`agentskills.io`).

---

## 1. Installation Locations

OpenAI Codex discovers skills using the canonical Agent Skills directory structure:

| Scope | Path | Discovery Context |
| :--- | :--- | :--- |
| **Project-Level** | `.agents/skills/apple-native-engineer/SKILL.md` | Active within the repository. |
| **Personal/Global** | `~/.agents/skills/apple-native-engineer/SKILL.md` | Active across all repositories for the local developer. |

---

## 2. Installation Methods

### Method A: Automated via Vercel Skills CLI
```bash
# Project-level install
npx skills add kayaonur607/apple-native-engineer -a codex

# Global install
npx skills add kayaonur607/apple-native-engineer -g -a codex
```

### Method B: Manual Symlink / Directory Copy
```bash
# Project-level
mkdir -p .agents/skills
ln -s ~/Desktop/apple-native-engineer .agents/skills/apple-native-engineer

# Global
mkdir -p ~/.agents/skills
ln -s ~/Desktop/apple-native-engineer ~/.agents/skills/apple-native-engineer
```

---

## 3. Verification & Usage

Codex evaluates skill descriptions in `SKILL.md` frontmatter at startup. When user prompts touch on SwiftUI, Apple HIG, iOS, iPadOS, macOS, or UI auditing, Codex dynamically loads the skill's instructions.

### Example Prompts:
```text
$ codex "Review ContentView.swift for Apple HIG compliance and touch target sizes."

$ codex "Design a native Liquid Glass card using SwiftUI materials and squircle continuous corners."
```
