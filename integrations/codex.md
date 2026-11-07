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

### Method A: Local installer from the GitHub checkout
```bash
# Project-level install
./scripts/install-skill.sh

# Global install
./scripts/install-skill.sh
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

## 3. The MCP server — stronger than the skill

The skill is instructions. The MCP server is instructions **plus 25 tools that actually check the code**, 53
resources and 13 prompts. If Codex is your daily client, use both: the skill sets policy, the server enforces it.

```bash
codex mcp add apple-native-engineer -- node /absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs
```

Or in `~/.codex/config.toml` (project-scoped: `.codex/config.toml`, trusted projects only):

```toml
[mcp_servers.apple-native-engineer]
command = "node"
args = ["/absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs"]
startup_timeout_sec = 600
tool_timeout_sec = 120

[mcp_servers.apple-native-engineer.env]
APPLE_NATIVE_PYTHON = "python3"
```

Codex reads the server's `instructions` field as server-wide guidance, so the operating loop — inspect, read the
reference, `review_diff`, then `generate_release_report` — arrives with the tools rather than in your prompt.

Verify with `codex mcp list`, then ask for one named tool so the call is visible rather than inferred:

```text
Run the apple-native-engineer audit_project tool on this repository and quote the finding codes.
```

Why it is worth the extra step: the server returns finding codes (`SWU003`, `A11Y002`, `PRIV010`) rather than
prose, and `status: fail` is a blocker the agent cannot talk its way past.

---

## 4. Verification & Usage

Codex evaluates skill descriptions in `SKILL.md` frontmatter at startup. When user prompts touch on SwiftUI, Apple HIG, iOS, iPadOS, macOS, or UI auditing, Codex dynamically loads the skill's instructions.

### Example Prompts:
```text
$ codex "Review ContentView.swift for Apple HIG compliance and touch target sizes."

$ codex "Design a native Liquid Glass card using SwiftUI materials and squircle continuous corners."
```
Installation is from GitHub only. Replace `/absolute/path` with your checkout location. See the [update policy](../docs/UPDATES.md) for automatic updates, first-start prewarming, version pins and rollback.

Codex MCP configuration reference: [official documentation](https://learn.chatgpt.com/docs/extend/mcp?surface=cli).
