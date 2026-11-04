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

## 3. Dependency Tracking

When installed in a project, the CLI creates and maintains:
- `.skills.json`: Declares the skill dependency and target agent configurations.
- `skills-lock.json`: Locks the exact Git commit SHA for reproducible agent environments across team members.
