# MCP Server

Exposes every auditor in this repository to any Model Context Protocol client, plus the knowledge base as
resources and the workflows as prompts.

Built on the official [`@modelcontextprotocol/sdk`](https://github.com/modelcontextprotocol/typescript-sdk)
(v1.32). Not a hand-rolled JSON-RPC loop — the protocol surface, schema validation and structured output are the
SDK's job.

```
Client (Claude Desktop / Cursor / Codex / any MCP client)
        │  stdio · JSON-RPC 2.0
        ▼
integrations/mcp-server  ──►  python3 tools/<tool>/<script>.py --json
        │                          │
        │                          └── stable envelope (schema_version 2.0)
        ├── 13 tools
        ├── 53 resources  (references, checklists, examples, SKILL.md)
        └── 12 prompts    (the slash commands)
```

## Install

```bash
cd integrations/mcp-server
npm install
```

## Configure

### Claude Desktop / Claude Code

`~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["/absolute/path/to/apple-native-engineer-mcp/integrations/mcp-server/src/index.js"],
      "env": {
        "APPLE_NATIVE_PYTHON": "python3"
      }
    }
  }
}
```

### Cursor

`.cursor/mcp.json` in the project (relative paths resolve against the workspace):

```json
{
  "mcpServers": {
    "apple-native-engineer": {
      "command": "node",
      "args": ["./integrations/mcp-server/src/index.js"]
    }
  }
}
```

### App Store Connect (optional)

Only needed for the `app_store_connect` tool. Everything else works offline.

```json
{
  "env": {
    "ASC_KEY_ID": "XXXXXXXXXX",
    "ASC_ISSUER_ID": "00000000-0000-0000-0000-000000000000",
    "ASC_PRIVATE_KEY_PATH": "/Users/you/.appstoreconnect/AuthKey_XXXXXXXXXX.p8"
  }
}
```

`ASC_PRIVATE_KEY` (inline PEM) and `ASC_PRIVATE_KEY_BASE64` are also supported for CI. Signing requires
`python3 -m pip install cryptography`.

## Verify the install

```bash
node src/index.js --selftest
```

```json
{
  "name": "apple-native-engineer",
  "version": "2.0.0",
  "tools": ["inspect_apple_project", "audit_privacy_manifest", "…"],
  "resources": 52,
  "prompts": ["apple-native-apple-native", "apple-native-release", "…"]
}
```

Then, from any MCP client, call `inspect_apple_project` with no arguments — it analyses the client's working
directory.

## Tools

| Tool | Backing script |
| :--- | :--- |
| `inspect_apple_project` | `tools/project-inspector/inspect_project.py` |
| `audit_privacy_manifest` | `tools/privacy-auditor/audit_privacy.py` |
| `validate_app_icon` | `tools/asset-validator/validate_assets.py` |
| `validate_app_metadata` | `tools/metadata-validator/validate_metadata.py` |
| `check_localization` | `tools/localization-checker/check_localization.py` |
| `validate_widgets` | `tools/widget-validator/validate_widget.py` |
| `lint_swiftui` | `tools/swiftui-linter/lint_swiftui.py` |
| `audit_accessibility` | `tools/accessibility-auditor/audit_accessibility.py` |
| `audit_liquid_glass` | `tools/liquid-glass-auditor/audit_liquid_glass.py` |
| `validate_sf_symbols` | `tools/sf-symbols-catalog/check_symbols.py` |
| `forge_design_tokens` | `tools/design-token-forge/forge_tokens.py` |
| `generate_release_report` | `tools/release-readiness/generate_report.py` |
| `app_store_connect` | `tools/app-store-connect/cli.py` |

## Results

Each tool result contains:

- a short human summary,
- the full JSON envelope as text,
- the same envelope as `structuredContent`, validated against the tool's declared `outputSchema`,
- `isError: true` when the tool reports `status: "fail"` or exits non-zero.

```json
{
  "schema_version": "2.0",
  "tool": "swiftui-linter",
  "status": "fail",
  "summary": { "critical": 0, "error": 3, "warning": 7, "info": 3, "total": 13 },
  "findings": [
    { "code": "SWU003", "severity": "error", "message": "NavigationView is deprecated…",
      "file": "App/ContentView.swift", "line": 12, "hint": "Use NavigationStack…" }
  ],
  "data": {}
}
```

## Resources

- `apple-native://skill` — the operating standard
- `apple-native://references/<name>` — 30 guides (e.g. `apple-native://references/liquid-glass`)
- `apple-native://checklists/<name>` — 12 review checklists
- `apple-native://examples/<name>` — 9 worked examples

Clients that support resource autocompletion will list them from the server; there is nothing to configure.

## Prompts

`apple-native-apple-native`, `apple-native-design`, `apple-native-code`, `apple-native-review`,
`apple-native-privacy`, `apple-native-icon`, `apple-native-screenshots`, `apple-native-connect`,
`apple-native-metadata`, `apple-native-widgets`, `apple-native-localization`, `apple-native-release`.

Each takes one optional `project` argument (absolute path; defaults to the client's working directory).

## Environment

| Variable | Default | Purpose |
| :--- | :--- | :--- |
| `APPLE_NATIVE_PYTHON` | `python3` | Interpreter used for the CLI tools |
| `APPLE_NATIVE_ROOT` | repository root | Override when the server is installed outside the repo |
| `APPLE_NATIVE_TIMEOUT_MS` | `180000` | Per-tool timeout |
| `ASC_KEY_ID` / `ASC_ISSUER_ID` / `ASC_PRIVATE_KEY_PATH` | — | App Store Connect credentials |

## Tests

```bash
npm test
```

Eight protocol tests drive a real `Client` against an in-memory `McpServer`: tool inventory, annotations, resource
reading, prompt listing, a live audit, a failing lint, a missing-path error and a symbol lookup.
