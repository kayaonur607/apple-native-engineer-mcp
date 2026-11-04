# Claude Code Integration Guide

This guide explains how to install and invoke the `apple-native-engineer` skill in **Claude Code** (Anthropic's agentic CLI).

---

## 1. Installation Locations

Claude Code discovers skills placed in either of two locations:

| Scope | Path | Discovery Context |
| :--- | :--- | :--- |
| **Project-Level** | `.claude/skills/apple-native-engineer/SKILL.md` | Active only when running Claude Code within this project. |
| **User/Personal** | `~/.claude/skills/apple-native-engineer/SKILL.md` | Universally available across all projects on your machine. |

---

## 2. Installation Methods

### Method A: Automated via Vercel Skills CLI (Recommended)
```bash
# Install to current project
npx skills add kayaonur607/apple-native-engineer-mcp -a claude-code

# Install globally to user profile
npx skills add kayaonur607/apple-native-engineer-mcp -g -a claude-code
```

### Method B: Native Symlink / Clone (Fastest for Local Development)
```bash
# Project-level install
mkdir -p .claude/skills
ln -s ~/Desktop/apple-native-engineer .claude/skills/apple-native-engineer

# User-level (global) install
mkdir -p ~/.claude/skills
ln -s ~/Desktop/apple-native-engineer ~/.claude/skills/apple-native-engineer
```

---

## 3. Verification

To verify that Claude Code recognizes the skill:
1. Launch Claude Code:
   ```bash
   claude
   ```
2. Run the status or ask Claude Code to list available skills:
   ```text
   > Which skills are currently installed?
   ```
   Claude Code should report `apple-native-engineer` with its description.

---

## 4. Example Invocation Prompts

Once installed, Claude Code activates the skill automatically when working on Apple platform code, or when directly commanded:

```text
> Audit our profile settings view against Apple HIG and accessibility standards.

> Build an adaptive navigation view for our iPad app that supports Stage Manager and 3-column NavigationSplitView.

> Refactor this card button animation according to Emil Kowalski's motion principles in SwiftUI.
```
