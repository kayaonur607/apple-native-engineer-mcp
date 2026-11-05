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

## 3. The MCP server — the version that actually checks the code

The skill sets policy. The MCP server adds 16 tools that run the audits, 53 resources and 12 prompts, and OpenCode
exposes all three.

```bash
opencode mcp add apple-native-engineer -- npx -y apple-native-engineer-mcp
opencode mcp list          # expect: ✓ apple-native-engineer  connected
```

Config changes reload without a restart. By hand, in `opencode.jsonc` — note the V2 shape, `mcp.servers`, not bare
names under `mcp`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "servers": {
      "apple-native-engineer": {
        "type": "local",
        "command": ["npx", "-y", "apple-native-engineer-mcp"],
        "environment": { "APPLE_NATIVE_PYTHON": "python3" }
      }
    }
  }
}
```

How it surfaces, given OpenCode's naming rules:

| Surface | Name |
| :--- | :--- |
| Tools (Code Mode) | `tools.apple_native_engineer.review_diff(...)` |
| Prompts | `/apple_native_engineer:apple-native-release` |
| Resources | `list_mcp_resources` / `read_mcp_resource`, or `/mcps` to browse |

Tool names are normalised to `<server>_<tool>`, so `apple-native-engineer` becomes `apple_native_engineer` — use
that spelling in `permissions` rules, for example a deny on `apple_native_engineer_app_store_connect` if the server
should never read your App Store Connect account.

The server's `instructions` are added to the system prompt automatically, which is why the operating loop —
inspect, read the reference, `review_diff`, then `generate_release_report` — arrives without you writing it down.

---

## 4. Invocation in OpenCode

OpenCode reads `SKILL.md` frontmatter metadata and description at boot. When a task requires iOS/macOS interface design, accessibility auditing, or SwiftUI refactoring, the skill is automatically injected into the agent context.