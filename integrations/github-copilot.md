# GitHub Copilot Integration Guide

This guide details how to integrate the `apple-native-engineer` skill into **GitHub Copilot** in VS Code, Xcode, and JetBrains IDEs.

---

## 1. Copilot Custom Instructions (`.github/copilot-instructions.md`)

GitHub Copilot supports project-wide custom instructions defined in `.github/copilot-instructions.md`. When present, Copilot includes these instructions in every completion and chat turn.

### Setup Instructions:
Create or append to `.github/copilot-instructions.md` in your project repository:

```markdown
# Apple Native Engineering Guidelines
All Swift, SwiftUI, UIKit, and AppKit code in this repository must comply with Apple's official Human Interface Guidelines and the design engineering standards defined in the `apple-native-engineer` skill.

Key Mandates:
- Always enforce a minimum 44x44pt touch target on interactive controls.
- Use semantic colors (`Color(uiColor: .systemBackground)`, `.secondarySystemGroupedBackground`, `.tint`) and system materials (`.ultraThinMaterial`, `.regularMaterial`).
- Support Dynamic Type by using standard text styles (`.title`, `.headline`, `.body`) and flexible layouts with `minHeight`.
- Isolate all view models and UI mutations to `@MainActor`.
- Apply Emil Kowalski motion principles: use physics springs (`.spring(.snappy)`), avoid `scale(0)` pops, and respect `@Environment(\.accessibilityReduceMotion)`.
```

---

## 2. The MCP server — agent mode with real checks

Custom instructions are advice Copilot may follow. The MCP server is 25 tools that run the audits and return
finding codes, and VS Code's agent mode supports it directly.

This repository already ships a portable `.mcp.json` at the root, which VS Code offers as a workspace
configuration. To write it by hand, use `.vscode/mcp.json` — note that this file uses `servers`, not `mcpServers`:

```json
{
  "servers": {
    "apple-native-engineer": {
      "type": "stdio",
      "command": "node",
      "args": ["/absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs"],
      "env": { "APPLE_NATIVE_PYTHON": "python3" }
    }
  }
}
```

Or use the guided flow: **Chat: Open Customizations → MCP Servers → Add Server → Command (stdio)**, and enter
`node /absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs`. Choose **Workspace** to share it with the repository, or **Copilot Global** to
write `~/.copilot/mcp-config.json` for every project.

Inside a session:

| Surface | Where |
| :--- | :--- |
| Tools | the tool picker, or let the agent choose — the tool descriptions say what each answers |
| Prompts | `/<server>.<prompt>`, for example `/apple-native-engineer.apple-native-release` |
| Resources | **Add Context → MCP Resources**, or **MCP: Browse Resources** |

Ask for one named call the first time, so you can see it happen rather than trust it:

```text
Use the apple-native-engineer audit_project tool on this workspace, then fix every error-severity finding and
re-run until it passes. Do not change files outside the findings.
```

The value over instructions alone: `status: "fail"` is a blocker the model cannot argue with, and `review_diff`
scopes the check to your `git diff` so the loop stays fast.

---

## 3. Invocation in Copilot Chat

In VS Code or Xcode, prompt GitHub Copilot Chat:

```text
@workspace Refer to apple-native-engineer and refactor this Form view to follow native iOS 18 design conventions.

@workspace Audit our iPad navigation architecture for multi-column split view and Stage Manager adaptability.
```
Installation is from GitHub only. Replace `/absolute/path` with your checkout location. See the [update policy](../docs/UPDATES.md) for automatic updates, first-start prewarming, version pins and rollback.
