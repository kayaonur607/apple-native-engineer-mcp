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

## 3. The MCP server — tools, prompts and `@`-addressable resources

The skill is instructions. The MCP server adds 16 tools that run the audits, and Gemini CLI maps its 12 prompts to
slash commands and its 53 resources to `@` references.

```bash
gemini mcp add apple-native-engineer npx -y apple-native-engineer-mcp
```

Add `-s user` for `~/.gemini/settings.json` instead of the project scope, and `--trust` only if you accept
bypassing per-call confirmation. By hand, it is the usual `mcpServers` block:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "npx",
      "args": ["-y", "apple-native-engineer-mcp"],
      "env": { "APPLE_NATIVE_PYTHON": "python3" },
      "timeout": 120000
    }
  }
}
```

Two Gemini CLI features are worth knowing here, because this server uses both:

- **Resources as `@` references.** Type `@apple-native://references/liquid-glass` and the guide is read into the
  conversation — the whole knowledge base is addressable instead of pasted.
- **Prompts as slash commands.** `/apple-native-release --project=. --focus="the paywall copy"`.

Run `/mcp` to see the server listed as `CONNECTED` with its tools. Then ask for one explicitly so the call is
visible:

```text
Use the apple-native-engineer audit_project tool on this repository and list the finding codes by severity.
```

---

## 4. Verification

Once linked, the skill is automatically indexed. When asking the agent about Apple HIG, SwiftUI architecture, or mobile UI reviews, the agent activates the skill instructions and references.

### Example Prompts:
```text
> Review this SwiftUI NavigationStack implementation for memory leaks and deep-link routing.

> Create a production-grade Liquid Glass card component in SwiftUI with continuous squircle corners.
```