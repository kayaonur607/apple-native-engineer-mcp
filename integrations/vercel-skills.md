# Vercel Skills CLI Integration Guide

The **Vercel Skills CLI** (`npx skills`) is the official package manager for AI agent skills, maintained by Vercel Labs. It enables developers to install, manage, update, and remove skills across multiple coding agents with a single command.

---

## 1. Quick Installation Commands

Once the repository is published on GitHub, developers can install it directly using:

### Install into Current Project (Default)
```bash
npx skills add kayaonur607/apple-native-engineer-mcp
```

### Install Globally (Available Across All Workspaces)
```bash
npx skills add kayaonur607/apple-native-engineer-mcp -g
```

### Target Specific Agents
```bash
# Target Claude Code only
npx skills add kayaonur607/apple-native-engineer-mcp -a claude-code

# Target Cursor only
npx skills add kayaonur607/apple-native-engineer-mcp -a cursor

# Target multiple agents simultaneously
npx skills add kayaonur607/apple-native-engineer-mcp -a claude-code -a cursor -a codex
```

---

## 2. Managing Skills in Your Project

### Check for Updates
```bash
npx skills check
```

### Update to Latest Version
```bash
npx skills update
```

### List Installed Skills
```bash
npx skills list
```

### Remove the Skill
```bash
npx skills remove apple-native-engineer
```

---

## 3. The other distribution surface: MCP

The skills CLI installs instructions — one `SKILL.md` per agent. It does **not** install the MCP server, which is
what runs the audits. If your client speaks MCP, that is the surface with the executable checks:

```bash
npx -y apple-native-engineer-mcp --doctor    # Node, Python, auditors, git, Xcode
npx -y apple-native-engineer-mcp --selftest  # 16 tools, 53 resources, 12 prompts
```

Either point the client at the package directly, or install it through the client's own command:

```bash
codex    mcp add apple-native-engineer -- npx -y apple-native-engineer-mcp
gemini   mcp add apple-native-engineer npx -y apple-native-engineer-mcp
opencode mcp add apple-native-engineer -- npx -y apple-native-engineer-mcp
claude   mcp add apple-native-engineer -- npx -y apple-native-engineer-mcp
```

Install both when the client supports both: the skill carries the standards, the server enforces them with finding
codes. Per-client details are in the sibling guides in this directory.

---

## 4. Dependency Tracking

When installed in a project, the CLI creates and maintains:
- `.skills.json`: Declares the skill dependency and target agent configurations.
- `skills-lock.json`: Locks the exact Git commit SHA for reproducible agent environments across team members.