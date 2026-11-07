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

### Method A: Local installer from the GitHub checkout
```bash
# Install to current project
./scripts/install-skill.sh

# Install globally to user profile
./scripts/install-skill.sh
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

## 3. The MCP server — where the audits actually run

The skill is a policy document. The MCP server adds 31 tools that run the audits, 64 resources and 25 prompts.
Claude Code supports both, and the server is the one that can say `status: fail`.

```bash
claude mcp add apple-native-engineer -- node /absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs
```

Add `--scope project` to write a committed `.mcp.json` instead of the default local scope. This repository ships
one, so a clone is already configured:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["integrations/mcp-server/src/index.js"],
      "env": { "APPLE_NATIVE_PYTHON": "python3" }
    }
  }
}
```

What shows up in Claude Code:

| Surface | How to reach it |
| :--- | :--- |
| Tools | `mcp__apple-native-engineer__audit_project`, `…__review_diff`, `…__check_environment` |
| Prompts | `/mcp__apple-native-engineer__apple-native-release` |
| Resources | the `apple-native://` URIs, read on demand instead of pasted |

Check the connection with `/mcp`. Then:

```text
Use review_diff from apple-native-engineer, then fix every finding it reports and re-run until it passes.
```

That loop is the reason to install it: the agent stops guessing when it is finished.

---

## 4. Verification

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

## 5. Example Invocation Prompts

Once installed, Claude Code activates the skill automatically when working on Apple platform code, or when directly commanded:

```text
> Audit our profile settings view against Apple HIG and accessibility standards.

> Build an adaptive navigation view for our iPad app that supports Stage Manager and 3-column NavigationSplitView.

> Refactor this card button animation according to Emil Kowalski's motion principles in SwiftUI.
```
Installation is from GitHub only. Replace `/absolute/path` with your checkout location. See the [update policy](../docs/UPDATES.md) for automatic updates, first-start prewarming, version pins and rollback.
