# Cursor Integration Guide

This guide explains how to install and invoke the `apple-native-engineer` skill in **Cursor** (the AI-first code editor).

---

## 1. Installation Locations

Cursor supports native skill and context discovery through either of the following directories:

| Scope | Path | Discovery Context |
| :--- | :--- | :--- |
| **Cursor Skills** | `.cursor/skills/apple-native-engineer/SKILL.md` | Primary Cursor skills discovery path. |
| **Universal Agents** | `.agents/skills/apple-native-engineer/SKILL.md` | Standard Agent Skills path also indexed by Cursor Composer. |

---

## 2. Installation Methods

### Method A: Local installer from the GitHub checkout
```bash
# Add to current workspace
./scripts/install-skill.sh
```

### Method B: Manual Symlink
```bash
# Create target directory and link repository
mkdir -p .cursor/skills
ln -s ~/Desktop/apple-native-engineer .cursor/skills/apple-native-engineer
```

---

## 3. The MCP server — the version that actually checks the code

A `.cursorrules` file is advice. The MCP server is 25 tools that run the same audits a senior reviewer would, and
return finding codes instead of opinions. Cursor supports both, and they compose.

Project config, `.cursor/mcp.json` (or `~/.cursor/mcp.json` for every workspace):

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["/absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs"],
      "env": { "APPLE_NATIVE_PYTHON": "python3" }
    }
  }
}
```

Restart Cursor, then check **Settings → MCP** for a green connection. The server registers three things beyond
tools:

- **13 prompts** become slash commands — type `/` and look for `apple-native-review`.
- **55 resources** — ask for `apple-native://references/liquid-glass` by URI and Cursor reads the guide instead of
  you pasting it.
- **Server instructions** — the operating loop arrives with the tools, not in your prompt.

The first message worth sending:

```text
Use review_diff from apple-native-engineer to audit only what I changed, then explain each finding code.
```

`review_diff` reads `git diff`, so an edit loop costs seconds and reports nothing you did not just write.

---

## 4. Configuring Cursor Rules (`.cursorrules`)

To ensure Cursor's agent model prioritizes the skill during all Swift and SwiftUI editing sessions, reference the skill in your project's `.cursorrules`:

```markdown
# Apple Native Design & Engineering Rules
When generating, modifying, or reviewing Swift and SwiftUI code:
1. Always adhere to Apple Human Interface Guidelines and the instructions in `.cursor/skills/apple-native-engineer/SKILL.md`.
2. Use standard Dynamic Type text styles, semantic colors, and minimum 44x44pt touch targets.
3. Follow Emil Kowalski's motion principles: use physics springs, avoid scale(0) pops, and respect Reduced Motion.
```

---

## 5. Example Prompts in Cursor Composer

Open Cursor Composer (`⌘-I` or `Ctrl-I`) and prompt:

```text
@apple-native-engineer Audit our payment confirmation sheet for HIG compliance, thumb ergonomics, and VoiceOver accessibility.

Design an adaptive navigation layout for our iPad app that supports 3-column NavigationSplitView and Inspector panel.
```
Installation is from GitHub only. Replace `/absolute/path` with your checkout location. See the [update policy](../docs/UPDATES.md) for automatic updates, first-start prewarming, version pins and rollback.
