# Integrations

Two ways to put this repository inside an agent. They are not alternatives — the skill carries the standards, the
MCP server runs the audits — but you should know which is which before you install anything.

| | Skill | MCP server |
| :--- | :--- | :--- |
| **What it is** | A `SKILL.md` the agent reads | A process exposing 30 tools, 61 resources, 22 prompts |
| **What it can do** | Advise | *Check*: run the audits, return finding codes, fail |
| **Install** | copy or symlink one directory | `node /absolute/path/apple-native-engineer-mcp/integrations/mcp-server/scripts/github-launcher.mjs` |
| **Works offline** | yes | yes — no network call in any audit |
| **Needs** | nothing | Node 20+, `python3` 3.10+ |
| **Client support** | agents that read the Agent Skills standard | any MCP client |

If you only take one, take the MCP server: an agent that can be told it is wrong is worth more than one that has
been told what right looks like.

---

## Pick your client

Every guide below covers both surfaces for that client, including the exact config file it reads.

| Client | Guide | MCP config lives in |
| :--- | :--- | :--- |
| Claude Code | [claude-code.md](claude-code.md) | `.mcp.json`, or `claude mcp add` |
| Claude Desktop | [mcp-server/README.md](mcp-server/README.md) | `claude_desktop_config.json` |
| Cursor | [cursor.md](cursor.md) | `.cursor/mcp.json`, or `~/.cursor/mcp.json` |
| OpenAI Codex | [codex.md](codex.md) | `~/.codex/config.toml`, or `.codex/config.toml` |
| Gemini CLI | [gemini-cli.md](gemini-cli.md) | `~/.gemini/settings.json` |
| GitHub Copilot (VS Code) | [github-copilot.md](github-copilot.md) | `.vscode/mcp.json`, or the Copilot global config |
| OpenCode | [opencode.md](opencode.md) | `opencode.jsonc` → `mcp.servers` |
| Any client, via the skills CLI | [vercel-skills.md](vercel-skills.md) | — |

A generic stdio server; anything that speaks MCP accepts this shape.

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

For a container, a shared machine, or a browser-based client that cannot spawn a process, the same server speaks
Streamable HTTP: `node src/index.js --http` serves `POST /mcp` and `GET /health`, loopback-bound and origin-checked
by default. See [mcp-server/README.md](mcp-server/README.md#http-mode).

---

## What to ask for first

One call tells you whether the installation worked, and it is the call that changes how the agent behaves:

```text
Use the apple-native-engineer audit_project tool on this repository.
```

You get a merged envelope: every finding tagged with the audit that produced it, a severity count, and a
`status` of `pass`, `warn` or `fail`. From then on, ask for `review_diff` inside an edit loop — it reads
`git diff` and audits only the files you touched, which is seconds instead of a full sweep.

If a tool behaves unexpectedly, ask for `check_environment` before reporting a bug. It checks Node, Python, the
auditors, the guides, git, Xcode and credentials, and tells you which one is missing.

---

## Configuration that matters

| Variable | Default | When you need it |
| :--- | :--- | :--- |
| `APPLE_NATIVE_PYTHON` | `python3` | A machine with several interpreters, only one on the client's `PATH` |
| `APPLE_NATIVE_ROOT` | detected | Point the server at a different checkout |
| `APPLE_NATIVE_TIMEOUT_MS` | `180000` | Very large projects on slow disks |
| `APPLE_NATIVE_TELEMETRY` | `off` | You want aggregate usage counts; `local` or `anonymous` only |
| `ASC_*` | — | Only for `app_store_connect`; everything else works without credentials |

Telemetry is off unless you set it, records five fields, and `--telemetry-preview` prints the exact bytes. There is
no default collector, so there is nothing to opt out of. The full posture is in [SECURITY.md](../SECURITY.md) and
[mcp-server/README.md](mcp-server/README.md#privacy).

Installation is from GitHub only. Replace `/absolute/path` with your checkout location. See the [update policy](../docs/UPDATES.md) for automatic updates, first-start prewarming, version pins and rollback.
